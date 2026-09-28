"""Grok Bot bus watcher (read-only on the bus); see references/relay-handshake.md.

Lists bus files that changed since the previous run, grouped by priority, and
tracks this session's outbound tasks until a result appears in ANY outbox.
It never writes to the bus. It only updates its own state file.

Priorities (Simon handshake request 2026-09-26 14:29):
  ALERT   *simon-go*               production change reported by a bot
  CODING  vb-* / ping-* / STATUS   coding queue, replies, status boards
  NOISE   hr-* / _tmp-* / _relay-* org HR drafts and scratch copies

Outbound rule (vibe-bot charter): before saying "no reply", check
  <bus>/*/outbox/<nonce>*.result.md  and the top of Relay STATUS.
A claim older than PING_AFTER_MIN with no result marks PING-DUE once;
at most one reminder per nonce (charter: one authorized reminder).

Watch mode (--watch) streams one line per unprocessed bus file for a host
monitor. Its baseline is the saved state, not the moment it starts, so a file
that lands between the last scan and arming the monitor is still reported
(2026-09-26: a review result at 22:18 was missed because a monitor armed at
22:19 treated it as already seen). Watch mode never writes the state; the scan
that processes the files does.

Agents (2026-09-28): a Codex session runs the same watcher with --agent codex.
The agent picks the name this session signs with (--self-label, default
"Claude Code" or "Codex") and its own state file, so two sessions on one bus
never share a baseline by default: a peer's scan must not mark a file as seen
for this session. --coding-label names the owner that addresses a task to the
coding session (default "Coding LLM"); --bus, --drafts and --hub-status
override VIBE_BOT_BUS / VIBE_BOT_DRAFTS / VIBE_BOT_HUB_STATUS.

A file that vanishes or turns unreadable between glob and stat/open (Relay
replaces files, scratch copies are removed) is skipped for this pass; a scan
keeps the saved entry of a file it had already seen, so a transient failure is
not reported as REMOVED and then NEW again.

usage: python bus_watch.py [--baseline-before "YYYY-MM-DD HH:MM"] [--no-save]
       python bus_watch.py --track <nonce> [--track <nonce> ...]
       python bus_watch.py --pinged <nonce>
       python bus_watch.py --watch [--interval 20] [--once]
common: [--agent claude|codex] [--state <file>] [--self-label <name>]
        [--coding-label <name>] [--bus <dir>] [--drafts <dir>] [--hub-status <file>]
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import stat
import sys
import time

KST = dt.timezone(dt.timedelta(hours=9))
# State lives OUTSIDE the skill folder: the SimonK-stack sync replaces skill folders.
DEFAULT_STATE = os.path.join(os.path.expanduser("~"), ".claude", "state", "vibe-bot", "bus_watch.json")
# One state file per agent: a shared file would let one session's scan hide a
# new file from the other session's watcher.
DEFAULT_STATES = {
    "claude": DEFAULT_STATE,
    "codex": os.path.join(os.path.expanduser("~"), ".codex", "state", "vibe-bot", "bus_watch.json"),
}
SELF_LABELS = {"claude": "Claude Code", "codex": "Codex"}
DEFAULT_CODING_LABEL = "Coding LLM"
DEFAULT_BUS = os.environ.get("VIBE_BOT_BUS", "E:/2ndB/.bots")
DEFAULT_DRAFTS = os.environ.get("VIBE_BOT_DRAFTS", "E:/2ndB/docs/drafts")
DEFAULT_HUB_STATUS = os.environ.get("VIBE_BOT_HUB_STATUS", "E:/Coding Infra/AI Infra/Communication/bots/STATUS.md")
PING_AFTER_MIN = 20
NOISE = re.compile(r"(^|/)(hr-|_tmp-|_relay-)")


def _literal(text):
    """re.escape that leaves spaces readable, so the default pattern is unchanged."""
    return re.escape(text).replace("\\ ", " ")


def coding_mark(label):
    """Relay addresses coding work in several shapes: an owner line ("담당 봇: Coding
    LLM"), a heading ("# Task — Coding · ..."), or a "Coding LLM (...)" mention.
    The heading form uses the label's first word."""
    full = _literal(label)
    first = _literal(label.split()[0])
    return re.compile(
        r"(담당 봇|보낼 봇|수신|Task for)\s*[:：—-]?.*" + full
        + r"|^#\s*Task\s*[—-]+\s*" + first + r"\b"
        + r"|" + full + r"\s*[:·(]",
        re.I | re.M,
    )


def configure(agent="claude", state=None, self_label=None, coding_label=None,
              bus=None, drafts=None, hub_status=None):
    """Set the module paths and labels. Derived paths always follow the bus."""
    global AGENT, STATE, SELF_LABEL, CODING_LABEL, CODING_MARK
    global BUS, DRAFTS, HUB_STATUS, RELAY_STATUS, WATCH
    AGENT = agent
    STATE = state or DEFAULT_STATES[agent]
    SELF_LABEL = (self_label or "").strip() or SELF_LABELS[agent]
    CODING_LABEL = (coding_label or "").strip() or DEFAULT_CODING_LABEL
    CODING_MARK = coding_mark(CODING_LABEL)
    BUS = bus or DEFAULT_BUS
    DRAFTS = drafts or DEFAULT_DRAFTS
    HUB_STATUS = hub_status or DEFAULT_HUB_STATUS
    RELAY_STATUS = BUS + "/relay/STATUS.md"
    WATCH = [
        BUS + "/*/inbox/*",
        BUS + "/*/outbox/*",
        DRAFTS + "/*.md",
        HUB_STATUS,
        RELAY_STATUS,
    ]


configure()


def kst(ns):
    return dt.datetime.fromtimestamp(ns / 1e9, KST).strftime("%m-%d %H:%M:%S")


def stat_or_none(path):
    """os.stat, or None when the file vanished or became unreadable after glob."""
    try:
        return os.stat(path)
    except OSError:
        return None


def read_or_none(path, limit):
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
            return f.read(limit)
    except OSError:
        return None


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
    try:
        with open(STATE, "r", encoding="utf-8") as f:
            state.update(json.load(f))
    except FileNotFoundError:
        pass
    state.setdefault("outbound", {})
    for n in state.pop("outbound_waiting", []) or []:
        state["outbound"].setdefault(n, {"pinged": False})
    return state


def save_state(state):
    folder = os.path.dirname(STATE)
    if folder:
        os.makedirs(folder, exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    for attempt in range(5):
        try:
            os.replace(tmp, STATE)
            return
        except PermissionError:
            # Windows refuses to replace a file that a watcher tick is reading
            # at this instant; the read takes milliseconds.
            if attempt == 4:
                raise
            time.sleep(0.05 * (attempt + 1))


def snapshot(previous=None):
    """Current bus files. A path the glob listed but stat could not read keeps
    its entry from `previous` for this pass: dropping it would report a seen
    file as REMOVED now, as NEW on the next scan and to a running monitor in
    between. A file that is really gone is missing from the next glob."""
    previous = previous or {}
    now = {}
    for pat in WATCH:
        for p in glob.glob(pat):
            if p.endswith(".tmp"):
                continue
            key = p.replace("\\", "/")
            st = stat_or_none(p)
            if st is None:
                if key in previous:
                    now[key] = previous[key]
                continue
            if stat.S_ISDIR(st.st_mode):
                continue
            now[key] = [st.st_mtime_ns, st.st_size]
    return now


def addressed_to_coding(text):
    """A task addressed to the coding session. Scan and watch share this test:
    a task this session issued itself ("발행 <self-label>") is not work for it,
    even when it names the Coding LLM (a peer session reads the same file)."""
    return f"발행 {SELF_LABEL}" not in text and CODING_MARK.search(text) is not None


def watch_events(state, current, emitted):
    """Lines for files the saved state has not seen yet, most urgent first."""
    lines = []
    for p in sorted(current, key=lambda k: current[k][0]):
        if p in state["files"] or p in emitted:
            continue
        emitted.add(p)
        if classify(p) == "NOISE":
            continue
        name = p.rsplit("/", 1)[-1]
        answer = next((n for n in state["outbound"] if name.startswith(n) and name.endswith(".result.md")), None)
        if answer:
            lines.append((0, f"ANSWER {answer}: {p}"))
        elif "simon-go" in name:
            lines.append((1, f"ALERT production change: {p}"))
        elif p.endswith(".md") and "/inbox/" in p and addressed_to_coding(" ".join(head(p, 12))):
            lines.append((2, f"CODING TASK: {p}"))
        else:
            lines.append((3, f"NEW bus file: {p}"))
    return [text for _, text in sorted(lines, key=lambda x: x[0])]


def watch_tick(state, emitted):
    """Re-read the saved state, then report. A scan may track a new request or
    process files while the monitor runs; a state read once at start would
    report that request's answer as an ordinary file."""
    try:
        fresh = load_state()
    except (OSError, ValueError):
        fresh = None  # a scan is replacing the file; keep the last good copy
    if fresh:
        state["files"] = fresh["files"]
        state["outbound"] = fresh["outbound"]
    return watch_events(state, snapshot(), emitted)


def watch(state, interval, once=False):
    emitted = set()
    while True:
        for line in watch_tick(state, emitted):
            print(line, flush=True)
        if once:
            return
        time.sleep(interval)


def outbound_status(nonce, meta):
    results = [p for p in sorted(glob.glob(f"{BUS}/*/outbox/{nonce}*.result.md"))
               if stat_or_none(p) is not None]
    if results:
        return "ANSWERED", results
    claims = []
    for p in glob.glob(f"{BUS}/*/inbox/{nonce}.claim"):
        st = stat_or_none(p)
        if st is not None:
            claims.append((p, st))
    if not claims:
        return "UNCLAIMED", []
    age_min = (time.time() - claims[0][1].st_mtime) / 60
    paths = [p for p, _ in claims]
    if age_min >= PING_AFTER_MIN and not meta.get("pinged"):
        return f"PING-DUE ({age_min:.0f}m since claim)", paths
    return f"CLAIMED ({age_min:.0f}m)", paths


def answered_by_self(nonce):
    """Only a result written by this coding session answers the task. Relay may
    publish its own dispatch note under the same nonce (2ndB 2026-09-26,
    vb-1865-date-q5-fix), and that note mentions the Coding LLM too."""
    for rp in glob.glob(f"{BUS}/*/outbox/{nonce}*.result.md"):
        text = read_or_none(rp, 800)
        if text is not None and SELF_LABEL in text:
            return True
    return False


def utf8_stdio():
    """Bus headings carry em dashes; a cp949 or ascii console would crash on them."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass


def main(argv=None):
    utf8_stdio()
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline-before")
    ap.add_argument("--no-save", action="store_true")
    ap.add_argument("--track", action="append", default=[])
    ap.add_argument("--pinged", action="append", default=[])
    ap.add_argument("--agent", choices=sorted(SELF_LABELS), default="claude",
                    help="session running the watcher; picks the default --self-label and --state")
    ap.add_argument("--state", default=None, help="state file (default: one per --agent, outside the skill)")
    ap.add_argument("--self-label", default=None,
                    help='name this session signs tasks and results with (default "Claude Code" or "Codex")')
    ap.add_argument("--coding-label", default=DEFAULT_CODING_LABEL,
                    help="owner name that addresses a task to the coding session (default %(default)s)")
    ap.add_argument("--bus", default=DEFAULT_BUS, help="bus root (default: $VIBE_BOT_BUS or %(default)s)")
    ap.add_argument("--drafts", default=DEFAULT_DRAFTS, help="drafts folder (default: $VIBE_BOT_DRAFTS)")
    ap.add_argument("--hub-status", default=DEFAULT_HUB_STATUS, help="hub STATUS.md (default: $VIBE_BOT_HUB_STATUS)")
    ap.add_argument("--watch", action="store_true", help="stream unprocessed bus files for a monitor")
    ap.add_argument("--interval", type=float, default=20.0)
    ap.add_argument("--once", action="store_true", help="with --watch: one pass, for tests")
    a = ap.parse_args(argv)
    for flag, value in (("--self-label", a.self_label), ("--coding-label", a.coding_label)):
        if value is not None and not value.strip():
            ap.error(f"{flag} must not be empty")
    configure(agent=a.agent, state=a.state, self_label=a.self_label, coding_label=a.coding_label,
              bus=a.bus, drafts=a.drafts, hub_status=a.hub_status)

    state = load_state()
    owner = state.get("agent")
    if owner and owner != AGENT:
        print(f"WARN state {STATE} was written by agent {owner}, not {AGENT}; "
              "give each session its own --state", file=sys.stderr, flush=True)
    for n in a.track:
        state["outbound"].setdefault(n, {"pinged": False})
    for n in a.pinged:
        state["outbound"].setdefault(n, {})["pinged"] = True
    if a.watch:
        watch(state, a.interval, a.once)
        return

    cut = None
    if a.baseline_before:
        cut = dt.datetime.strptime(a.baseline_before, "%Y-%m-%d %H:%M").replace(tzinfo=KST).timestamp() * 1e9

    now = snapshot(state["files"])

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
        body = read_or_none(p, 4000)
        if body is None:
            continue  # vanished or unreadable since glob
        if not addressed_to_coding(body):
            continue
        if answered_by_self(nonce):
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
        st = stat_or_none(path)
        if st is not None:
            print(f"  {label} {kst(st.st_mtime_ns)}: " + " / ".join(x for x in head(path, 3) if x))

    if not a.no_save:
        state["files"] = now
        state["runs"] = state.get("runs", 0) + 1
        state["last_run"] = dt.datetime.now(KST).isoformat(timespec="seconds")
        state["agent"] = AGENT
        state["outbound"] = {n: m for n, m in state["outbound"].items() if "answered_at" not in m or n in a.track}
        save_state(state)


if __name__ == "__main__":
    main()
