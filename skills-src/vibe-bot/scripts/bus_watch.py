"""Grok Bot bus watcher (read-only on the bus). DRAFT 2026-09-26: needs
process/network-denied tests before release; see references/relay-handshake.md.

Lists bus files that changed since the previous run, grouped by priority, and
tracks this session's outbound tasks until a result appears in ANY outbox.
It never writes to the bus. It only updates its own state file.

Priorities (Simon handshake request 2026-09-26 14:29):
  ALERT   *simon-go*               production change reported by a bot
  CODING  vb-* / ping-* / STATUS   coding queue, replies, status boards
  NOISE   hr-* / _tmp-* / _relay-* org HR drafts and scratch copies

Outbound rule (vibe-bot charter): before saying "no reply", check
  E:/2ndB/.bots/*/outbox/<nonce>*.result.md  and the top of Relay STATUS.
A claim older than PING_AFTER_MIN with no result marks PING-DUE once;
at most one reminder per nonce (charter: one authorized reminder).

usage: python bus_scan.py [--baseline-before "YYYY-MM-DD HH:MM"] [--no-save]
       python bus_scan.py --track <nonce> [--track <nonce> ...]
       python bus_scan.py --pinged <nonce>
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import time

KST = dt.timezone(dt.timedelta(hours=9))
# State lives OUTSIDE the skill folder: the SimonK-stack sync replaces skill folders.
DEFAULT_STATE = os.path.join(os.path.expanduser("~"), ".claude", "state", "vibe-bot", "bus_watch.json")
BUS = os.environ.get("VIBE_BOT_BUS", "E:/2ndB/.bots")
DRAFTS = os.environ.get("VIBE_BOT_DRAFTS", "E:/2ndB/docs/drafts")
HUB_STATUS = os.environ.get("VIBE_BOT_HUB_STATUS", "E:/Coding Infra/AI Infra/Communication/bots/STATUS.md")
STATE = DEFAULT_STATE
RELAY_STATUS = BUS + "/relay/STATUS.md"
PING_AFTER_MIN = 20
WATCH = [
    BUS + "/*/inbox/*",
    BUS + "/*/outbox/*",
    DRAFTS + "/*.md",
    HUB_STATUS,
    RELAY_STATUS,
]
# Relay addresses coding work in several shapes: an owner line ("담당 봇: Coding
# LLM"), a heading ("# Task — Coding · ..."), or a "Coding LLM (...)" mention.
CODING_MARK = re.compile(
    r"(담당 봇|보낼 봇|수신|Task for)\s*[:：—-]?.*Coding LLM"
    r"|^#\s*Task\s*[—-]+\s*Coding\b"
    r"|Coding LLM\s*[:·(]",
    re.I | re.M,
)
NOISE = re.compile(r"(^|/)(hr-|_tmp-|_relay-)")


def kst(ns):
    return dt.datetime.fromtimestamp(ns / 1e9, KST).strftime("%m-%d %H:%M:%S")


def head(path, n=2):
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
            return [f.readline().strip()[:140] for _ in range(n)]
    except OSError:
        return []


def classify(path):
    name = path.rsplit("/", 1)[-1]
    if NOISE.search(path):
        return "NOISE"
    if "simon-go" in name:
        return "ALERT"
    return "CODING"


def load_state():
    state = {"files": {}, "answered": [], "runs": 0, "outbound": {}}
    if os.path.exists(STATE):
        with open(STATE, "r", encoding="utf-8") as f:
            state.update(json.load(f))
    state.setdefault("outbound", {})
    for n in state.pop("outbound_waiting", []) or []:
        state["outbound"].setdefault(n, {"pinged": False})
    return state


def save_state(state):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATE)


def outbound_status(nonce, meta):
    results = sorted(glob.glob(f"{BUS}/*/outbox/{nonce}*.result.md"))
    claims = glob.glob(f"{BUS}/*/inbox/{nonce}.claim")
    if results:
        return "ANSWERED", results
    if not claims:
        return "UNCLAIMED", []
    age_min = (time.time() - os.stat(claims[0]).st_mtime) / 60
    if age_min >= PING_AFTER_MIN and not meta.get("pinged"):
        return f"PING-DUE ({age_min:.0f}m since claim)", claims
    return f"CLAIMED ({age_min:.0f}m)", claims


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline-before")
    ap.add_argument("--no-save", action="store_true")
    ap.add_argument("--track", action="append", default=[])
    ap.add_argument("--pinged", action="append", default=[])
    ap.add_argument("--state", default=DEFAULT_STATE)
    a = ap.parse_args()
    global STATE
    STATE = a.state

    state = load_state()
    for n in a.track:
        state["outbound"].setdefault(n, {"pinged": False})
    for n in a.pinged:
        state["outbound"].setdefault(n, {})["pinged"] = True

    cut = None
    if a.baseline_before:
        cut = dt.datetime.strptime(a.baseline_before, "%Y-%m-%d %H:%M").replace(tzinfo=KST).timestamp() * 1e9

    now = {}
    for pat in WATCH:
        for p in glob.glob(pat):
            if os.path.isdir(p) or p.endswith(".tmp"):
                continue
            st = os.stat(p)
            now[p.replace("\\", "/")] = [st.st_mtime_ns, st.st_size]

    changed = []
    for p, (m, s) in sorted(now.items(), key=lambda kv: kv[1][0]):
        old = state["files"].get(p)
        if cut is not None and not state["files"]:
            if m >= cut:
                changed.append((p, m, s, "NEW"))
            continue
        if old is None:
            changed.append((p, m, s, "NEW"))
        elif old != [m, s]:
            changed.append((p, m, s, "CHANGED"))
    removed = sorted(set(state["files"]) - set(now))

    open_tasks = []
    for p in glob.glob(BUS + "/relay/inbox/*.md"):
        nonce = os.path.basename(p)[:-3]
        if nonce in state.get("answered", []) or nonce in state["outbound"]:
            continue
        try:
            with open(p, "r", encoding="utf-8-sig", errors="replace") as f:
                body = f.read(4000)
        except OSError:
            continue
        if "발행 Claude Code" in body or not CODING_MARK.search(body):
            continue
        # Only a result written by the coding session answers the task. Relay may
        # publish its own dispatch note under the same nonce (2ndB 2026-09-26,
        # vb-1865-date-q5-fix), and that note mentions "Coding LLM" too.
        answered = False
        for rp in glob.glob(f"{BUS}/*/outbox/{nonce}*.result.md"):
            with open(rp, "r", encoding="utf-8-sig", errors="replace") as f:
                if "Claude Code" in f.read(800):
                    answered = True
        if answered:
            continue
        open_tasks.append(nonce)

    groups = {"ALERT": [], "CODING": [], "NOISE": []}
    for item in changed:
        groups[classify(item[0])].append(item)

    print(f"scan {dt.datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')} KST  files={len(now)}  "
          f"alert={len(groups['ALERT'])} coding={len(groups['CODING'])} noise={len(groups['NOISE'])}  "
          f"removed={len(removed)}  open_coding_tasks={len(open_tasks)}")
    for g in ("ALERT", "CODING"):
        for p, m, s, kind in groups[g]:
            print(f"  [{g}] {kind:7} {kst(m)} {s:>7}B {p}")
            if p.endswith(".md"):
                for line in head(p):
                    if line:
                        print(f"            | {line}")
    if groups["NOISE"]:
        print(f"  [NOISE] {len(groups['NOISE'])} file(s) skipped (hr-/_tmp-/_relay-)")
    for p in removed:
        print(f"  REMOVED {p}")
    for n in open_tasks:
        print(f"  OPEN-CODING-TASK {n}")

    for n, meta in sorted(state["outbound"].items()):
        status, paths = outbound_status(n, meta)
        print(f"  OUTBOUND {n}: {status}" + (f" -> {paths[0]}" if paths else ""))
        if status == "ANSWERED":
            meta["answered_at"] = meta.get("answered_at") or dt.datetime.now(KST).isoformat(timespec="seconds")
    for label, path in (("RELAY STATUS", RELAY_STATUS), ("HUB STATUS", HUB_STATUS)):
        if os.path.exists(path):
            st = os.stat(path)
            print(f"  {label} {kst(st.st_mtime_ns)}: " + " / ".join(x for x in head(path, 3) if x))

    if not a.no_save:
        state["files"] = now
        state["runs"] = state.get("runs", 0) + 1
        state["last_run"] = dt.datetime.now(KST).isoformat(timespec="seconds")
        state["outbound"] = {n: m for n, m in state["outbound"].items() if "answered_at" not in m or n in a.track}
        save_state(state)


if __name__ == "__main__":
    main()
