#!/usr/bin/env python3
"""peer_link: find peer agent sessions in Orca and ring a narrow doorbell.

Two already-running sessions (Claude Code, Codex) coordinate through an
append-only log file such as COORDINATION.md.  The message body lives only in
that file.  This script does two things:

* ``discover`` / ``status``: read-only views of Orca terminals and of the
  target's session record (through ``peer_state.assess``).
* ``notify``: decide whether a one-line doorbell may be typed into the target
  terminal, and with ``--send`` type it exactly once.

The doorbell carries no free text.  It is always::

    [<From>→<To> 알림] <logBasename> <YY.MM.DD HH:MM> 메시지 확인 요청

Only the Claude <-> Codex pair is rung (``peer_setup.NOTIFY_PAIR``); a target
with the sender's own identity is held.  The time is read from the LAST line
that looks like a ``## <From> → <To>`` heading (CommonMark line endings); if
that line is not exactly ``## <From> → <To> · YY.MM.DD HH:MM KST`` with a real
time, notify holds instead of falling back to an older heading.  The time is
never taken from the caller.  A received doorbell is a signal to read the log,
not an instruction.

The target's session record is found by folder, so it is cross-checked against
the terminal: Orca's ``lastOutputAt`` must agree with the record's last write
(a record written while the terminal stayed silent belongs to another session)
and the terminal must have been silent for 30 seconds.

Every Orca call goes through a module-level exact argv allowlist
(``ALLOWED_ARGV``) that is checked before any process starts.  ``terminal
send`` is reachable only from ``notify`` after all gates pass and only with
``--send`` (no option abbreviations).  The send runs under an exclusive state
lock; there is no automatic retry: an ambiguous send is recorded as
``ambiguous`` and only a user-directed retry may reuse Orca's
``--retry-request <requestId>`` with the identical payload.

Exit codes: 0 sent / dry-run would send / duplicate of an accepted send,
3 held / confirm / escalate (status: not sendable), 1 send attempted but not
accepted or ambiguous (discover/status: Orca failure), 2 usage or validation
error.
"""
import argparse
import contextlib
import dataclasses
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:  # written by a sibling component; absence must fail closed, not crash
    import peer_state as _peer_state
except Exception:  # noqa: BLE001 - any import failure means "unavailable"
    _peer_state = None

# ── identities ────────────────────────────────────────────────────────────
NAMES = ("Claude", "Codex")  # the only pair notify rings (peer_setup.NOTIFY_PAIR)
AGENT_NAMES = {"claude": "Claude", "codex": "Codex", "grok": "Grok",
               "antigravity": "Antigravity", "agy": "Antigravity"}
SUPPORTED_TARGETS = ("claude", "codex")
SENDER_AGENT = {"Claude": "claude", "Codex": "codex"}  # senders peer_state can read

HANDLE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,199}")
LOG_NAME_RE = re.compile(r"[A-Za-z0-9._-]{1,64}\.md")
DOORBELL_RE = re.compile(
    r"\[(?:Claude→Codex|Codex→Claude) 알림\] [A-Za-z0-9._-]{1,64}\.md "
    r"[0-9]{2}\.[0-9]{2}\.[0-9]{2} [0-9]{2}:[0-9]{2} 메시지 확인 요청")
ENTRY_TIME_FORMAT = "%y.%m.%d %H:%M"
LINE_BREAK_RE = re.compile(r"\r\n|\r|\n")  # CommonMark line endings only

# ── Orca argv allowlist (exact shapes; checked before any process starts) ──
H, LINE, MS, SECS = "<handle>", "<doorbell-line>", "<timeout-ms>", "<wait-submit-seconds>"
ALLOWED_ARGV = (
    ("terminal", "list", "--json"),
    ("terminal", "show", "--terminal", H, "--json"),
    ("terminal", "wait", "--terminal", H, "--for", "tui-idle", "--timeout-ms", MS, "--json"),
    ("account", "list", "--json"),
    ("terminal", "send", "--terminal", H, "--text", LINE, "--enter", "--wait-submit", SECS,
     "--json"),
)
LIST_ARGV = ["terminal", "list", "--json"]
ACCOUNT_ARGV = ["account", "list", "--json"]
SCREEN_WAIT_MS = 1500
WAIT_SUBMIT_SECONDS = 10
READ_TIMEOUT = 30
SEND_TIMEOUT = WAIT_SUBMIT_SECONDS + 35

QUOTA_FRESH_SECONDS = 60 * 60
QUOTA_LOW, QUOTA_FULL = 75.0, 100.0
QUOTA_MAIN_WINDOWS = ("session", "weekly")
AMBIGUITY_SECONDS = 15 * 60
TERMINAL_SLACK_SECONDS = 120   # record last write vs terminal last output
TERMINAL_QUIET_SECONDS = 30    # the terminal itself must be silent this long
LOCK_STALE_SECONDS = 600       # far above the longest send (SEND_TIMEOUT)
MAX_LOG_BYTES = 16 * 1024 * 1024
MAX_META_LINE_BYTES = 8 * 1024 * 1024
MAX_CODEX_FILES = 20000
KST = timezone(timedelta(hours=9))
RANK = {"confirm": 1, "hold": 2, "escalate": 3}
AMBIGUOUS_HELP = ("Outcome is ambiguous. Do not resend. Only a user-directed retry may "
                  "reuse Orca's --retry-request <requestId> with the identical payload.")


def _digits(value, upper):
    return (isinstance(value, str) and re.fullmatch(r"[1-9][0-9]{0,5}", value) is not None
            and int(value) <= upper)


_SLOT_CHECKS = {
    H: lambda v: HANDLE_RE.fullmatch(v) is not None,
    LINE: lambda v: DOORBELL_RE.fullmatch(v) is not None,
    MS: lambda v: _digits(v, 60000),
    SECS: lambda v: _digits(v, 60),
}


def argv_allowed(args):
    """True only for an exact ALLOWED_ARGV shape with valid slot values."""
    if not isinstance(args, (list, tuple)) or not all(isinstance(a, str) for a in args):
        return False
    for shape in ALLOWED_ARGV:
        if len(shape) == len(args) and all(
                _SLOT_CHECKS[slot](arg) if slot in _SLOT_CHECKS else arg == slot
                for slot, arg in zip(shape, args)):
            return True
    return False


class ArgvRefused(ValueError):
    """An Orca argv outside the allowlist. Raised before any process starts."""


class OrcaError(Exception):
    def __init__(self, code, detail=None):
        super().__init__(code)
        self.code, self.detail = code, detail


class UsageError(Exception):
    def __init__(self, code, detail=None):
        super().__init__(code)
        self.code, self.detail = code, detail


def _default_runner(argv, timeout):
    """argv list, no shell; stdout captured as BYTES. stderr is discarded."""
    proc = subprocess.run(argv, shell=False, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                          timeout=timeout,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return proc.returncode, proc.stdout


class OrcaTransport:
    def __init__(self, exe, runner=None):
        self.exe, self.runner = exe, runner or _default_runner

    def raw(self, args, timeout=READ_TIMEOUT):
        """Return (rc, envelope). Raises ArgvRefused before spawning, OrcaError after."""
        args = list(args)
        if not argv_allowed(args):
            raise ArgvRefused("ORCA_ARGV_REFUSED")
        try:
            rc, out = self.runner([self.exe, *args], timeout)
        except subprocess.TimeoutExpired:
            raise OrcaError("ORCA_TIMEOUT") from None
        except OSError:
            raise OrcaError("ORCA_SPAWN_FAILED") from None
        if not isinstance(out, (bytes, bytearray)):
            raise OrcaError("ORCA_RESPONSE_INVALID")
        try:
            text = bytes(out).decode("utf-8")  # strict: never guess an encoding
        except UnicodeDecodeError:
            raise OrcaError("ORCA_RESPONSE_UNDECODABLE") from None
        try:
            envelope = json.loads(text)
        except ValueError:
            raise OrcaError("ORCA_RESPONSE_INVALID") from None
        if not isinstance(envelope, dict):
            raise OrcaError("ORCA_RESPONSE_INVALID")
        return rc, envelope

    def result(self, args, timeout=READ_TIMEOUT):
        rc, envelope = self.raw(args, timeout)
        if rc != 0 or envelope.get("ok") is not True or not isinstance(envelope.get("result"), dict):
            error = envelope.get("error")
            code = error.get("code") if isinstance(error, dict) else None
            raise OrcaError("ORCA_CALL_FAILED", code if isinstance(code, str) else None)
        return envelope["result"]


def resolve_orca(explicit, env, which=shutil.which, isfile=os.path.isfile, windows=None):
    """--orca > env VIBE_ORCA_EXE > which('orca'). Windows needs the native orca.exe."""
    windows = (os.name == "nt") if windows is None else windows
    candidate = explicit or env.get("VIBE_ORCA_EXE") or which("orca")
    if not candidate:
        raise UsageError("ORCA_EXE_NOT_FOUND")
    candidate = str(candidate)
    if windows and not candidate.lower().endswith(".exe"):
        # orca.cmd refuses some verbs; look for the native binary beside the shim.
        sibling = os.path.join(os.path.dirname(candidate), "orca.exe")
        if not isfile(sibling):
            raise UsageError("ORCA_EXE_NOT_FOUND")
        candidate = sibling
    name = os.path.basename(candidate.replace("\\", "/")).lower()
    if name not in (("orca.exe",) if windows else ("orca", "orca.exe")):
        raise UsageError("ORCA_EXE_INVALID")  # the allowlist means nothing for another binary
    if not isfile(candidate):
        raise UsageError("ORCA_EXE_NOT_FOUND")
    return candidate


# ── time helpers ──────────────────────────────────────────────────────────
def fmt_utc(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fmt_kst(ts):
    return datetime.fromtimestamp(ts, KST).strftime("%Y-%m-%d %H:%M:%S KST")


def _safe_fmt(formatter, ts):
    """Display only: an out-of-range time from Orca must never crash a read."""
    try:
        return formatter(ts) if ts is not None else None
    except (OverflowError, OSError, ValueError):
        return None


def parse_time(value):
    """Epoch seconds, epoch ms or ISO-8601 (Z/offset/naive=UTC, or '... KST') -> epoch s."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        if not math.isfinite(value) or value <= 0:
            return None
        return value / 1000.0 if value > 1e12 else float(value)
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if re.fullmatch(r"[0-9]+(\.[0-9]+)?", text):
        return parse_time(float(text))
    tz = None
    if text.endswith(" KST"):
        text, tz = text[:-4], KST
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=tz or timezone.utc)
    try:
        return moment.timestamp()
    except (OverflowError, OSError, ValueError):
        return None


def _number(value):
    """Finite int/float only. NaN/inf would make every threshold comparison False."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None


# ── validation ────────────────────────────────────────────────────────────
def has_control(text):
    return any(unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp") for ch in str(text))


def build_doorbell(sender, to, log_name, entry_time):
    """The only text notify can ever type. Raises ValueError unless fully valid."""
    if sender not in NAMES or to not in NAMES or sender == to:
        raise ValueError("DOORBELL_NAME_INVALID")
    if not isinstance(log_name, str) or LOG_NAME_RE.fullmatch(log_name) is None:
        raise ValueError("DOORBELL_LOG_INVALID")
    if not isinstance(entry_time, str) or re.fullmatch(
            r"[0-9]{2}\.[0-9]{2}\.[0-9]{2} [0-9]{2}:[0-9]{2}", entry_time) is None:
        raise ValueError("DOORBELL_TIME_INVALID")
    line = "[%s→%s 알림] %s %s 메시지 확인 요청" % (sender, to, log_name, entry_time)
    if DOORBELL_RE.fullmatch(line) is None or has_control(line):
        raise ValueError("DOORBELL_INVALID")
    return line


def heading_pattern(sender, to):
    return re.compile(r"## %s ?(?:→|->) ?%s · ([0-9]{2}\.[0-9]{2}\.[0-9]{2} [0-9]{2}:[0-9]{2})"
                      r" KST(?![A-Za-z0-9])" % (re.escape(sender), re.escape(to)))


def heading_candidate_pattern(sender, to):
    """Anything a reader would take for a <sender> → <recipient> heading: any ATX level,
    up to 3 leading spaces, any 1-3 symbol arrow (look-alikes included)."""
    return re.compile(r"[ ]{0,3}#{1,6}[ \t]*%s[ \t]*[^\sA-Za-z0-9]{1,3}[ \t]*%s(?![A-Za-z0-9])"
                      % (re.escape(sender), re.escape(to)))


def last_addressed_entry(log_path, sender, to):
    """(entry_time|None, malformed_count, latest_malformed). Read-only, UTF-8 (BOM/CRLF ok).

    The LAST heading-like line decides. When it is malformed (look-alike arrow or dot,
    indentation, wrong level, impossible time, trailing junk before KST) the result is
    None: an older heading is never used in its place."""
    path = Path(log_path)
    if path.stat().st_size > MAX_LOG_BYTES:
        raise UsageError("LOG_TOO_LARGE")
    try:
        text = path.read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise UsageError("LOG_NOT_UTF8") from None
    strict, loose = heading_pattern(sender, to), heading_candidate_pattern(sender, to)
    last, malformed, latest_malformed = None, 0, False
    for line in LINE_BREAK_RE.split(text):
        if not loose.match(line):
            continue
        match = strict.match(line)
        valid = match is not None
        if valid:
            try:
                datetime.strptime(match.group(1), ENTRY_TIME_FORMAT)
            except ValueError:
                valid = False
        if valid:
            last, latest_malformed = match.group(1), False
        else:
            malformed += 1
            last, latest_malformed = None, True
    return last, malformed, latest_malformed


# ── terminals ─────────────────────────────────────────────────────────────
def normalize_terminal(row):
    identity = row.get("agentIdentity")
    agent = identity.strip().lower() if isinstance(identity, str) and identity.strip() else None
    last = _number(row.get("lastOutputAt"))
    last = row.get("lastOutputAt") if last is not None and last > 0 else None
    worktree = row.get("worktreePath")
    title = row.get("title")
    return {
        "handle": row["handle"],
        "agent": agent,
        "agent_name": AGENT_NAMES.get(agent),
        "title": title if isinstance(title, str) else None,
        "worktreePath": worktree if isinstance(worktree, str) and worktree else None,
        "connected": row.get("connected") is True,
        "writable": row.get("writable") is True,
        "orphaned": row.get("orphaned") is True,
        "lastOutputAt": last,
        "last_output_kst": _safe_fmt(fmt_kst, parse_time(last)),
    }


def list_terminals(transport):
    result = transport.result(LIST_ARGV)
    terminals = result.get("terminals")
    if not isinstance(terminals, list):
        raise OrcaError("ORCA_RESPONSE_INVALID")
    rows = [normalize_terminal(t) for t in terminals
            if isinstance(t, dict) and isinstance(t.get("handle"), str)]
    return rows, result.get("truncated") is True


def discover(transport, env):
    rows, truncated = list_terminals(transport)
    self_handle = env.get("ORCA_TERMINAL_HANDLE") or None
    for row in rows:
        row["is_self"] = bool(self_handle) and row["handle"] == self_handle
    return {"terminals": rows, "count": len(rows), "truncated": truncated,
            "self_handle_hint": bool(self_handle),
            "self_verified": any(row["is_self"] for row in rows)}


# ── session record mapping ────────────────────────────────────────────────
def norm_path(value):
    text = str(value).replace("\\", "/")
    while len(text) > 1 and text.endswith("/"):
        text = text[:-1]
    return text.casefold()


def _file_key(path):
    return os.path.normcase(os.path.abspath(str(path)))


def claude_slug(worktree_path):
    return re.sub(r"[^A-Za-z0-9]", "-", str(worktree_path).rstrip("/\\"))


def _first_session_meta(path, max_lines=5):
    try:
        with open(path, "rb") as handle:
            for _ in range(max_lines):
                line = handle.readline(MAX_META_LINE_BYTES)
                if not line or not line.endswith(b"\n"):
                    return None
                try:
                    record = json.loads(line.decode("utf-8"))
                except (UnicodeDecodeError, ValueError):
                    return None
                if isinstance(record, dict) and record.get("type") == "session_meta":
                    payload = record.get("payload")
                    return payload if isinstance(payload, dict) else None
    except OSError:
        return None
    return None


def _is_fork(meta):
    return bool(meta.get("forked_from_id") or meta.get("parent_thread_id")
                or meta.get("thread_source") == "subagent")


def _pick(matches):
    if not matches:
        return {"status": "not_found", "path": None, "candidates": []}
    matches.sort(key=lambda item: item[0], reverse=True)
    newest = matches[0][0]
    close = [str(p) for m, p in matches if newest - m <= AMBIGUITY_SECONDS]
    if len(close) > 1:
        return {"status": "ambiguous", "path": None, "candidates": close}
    return {"status": "ok", "path": str(matches[0][1]), "candidates": close}


def map_codex_record(worktree, codex_home, exclude=()):
    """Newest non-fork rollout whose first session_meta cwd is the worktree."""
    root = Path(codex_home) / "sessions"
    files = []
    if root.is_dir():
        for path in root.rglob("rollout-*.jsonl"):
            try:
                files.append((path.stat().st_mtime, path))
            except OSError:
                continue
    files.sort(key=lambda item: item[0], reverse=True)
    target, skip, matches, newest = norm_path(worktree), set(exclude), [], None
    for mtime, path in files[:MAX_CODEX_FILES]:
        if newest is not None and newest - mtime > AMBIGUITY_SECONDS:
            break
        if _file_key(path) in skip:
            continue
        meta = _first_session_meta(path)
        if not meta or _is_fork(meta) or not isinstance(meta.get("cwd"), str):
            continue
        if norm_path(meta["cwd"]) != target:
            continue
        newest = mtime if newest is None else newest
        matches.append((mtime, path))
    result = _pick(matches)
    result["scanned_limit_hit"] = len(files) > MAX_CODEX_FILES
    return result


def map_claude_record(worktree, claude_home, exclude=()):
    """Newest main session file in <claude-home>/projects/<slug>/ (subagents/ excluded)."""
    projects = Path(claude_home) / "projects"
    slug = claude_slug(worktree)
    folders = []
    if (projects / slug).is_dir():
        folders = [projects / slug]
    elif projects.is_dir():
        folders = [d for d in projects.iterdir()
                   if d.is_dir() and d.name.casefold() == slug.casefold()]
    skip, matches = set(exclude), []
    for folder in folders:
        for path in folder.glob("*.jsonl"):
            if not path.is_file() or _file_key(path) in skip:
                continue
            try:
                matches.append((path.stat().st_mtime, path))
            except OSError:
                continue
    result = _pick(matches)
    result["slug"] = slug
    return result


# ── state ─────────────────────────────────────────────────────────────────
def empty_state():
    return {"version": 1, "alerts": {}, "topics": {}}


def default_state_path(sender, env, home):
    if env.get("VIBE_PEER_STATE"):
        return Path(env["VIBE_PEER_STATE"])
    if sender == "Claude":
        return Path(home) / ".claude" / "state" / "vibe" / "peer_link.json"
    if sender == "Codex":
        return Path(home) / ".codex" / "state" / "vibe" / "peer_link.json"
    return Path(home) / ".claude" / "state" / "vibe" / ("peer_link-%s.json" % sender.lower())


def _alert_ok(record):
    return (isinstance(record, dict) and isinstance(record.get("to"), str)
            and isinstance(record.get("outcome"), str)
            and parse_time(record.get("sent_utc")) is not None)


def _topic_ok(entry):
    count = entry.get("count") if isinstance(entry, dict) else None
    return isinstance(count, int) and not isinstance(count, bool) and count >= 0


def load_state(path):
    """Only this script writes the file (atomically). Anything unexpected fails closed:
    a malformed alert would hide from the min-gap gate, a malformed count resets the cap."""
    path = Path(path)
    if not path.exists():
        return empty_state()
    try:
        data = json.loads(path.read_bytes().decode("utf-8-sig"))
    except (OSError, UnicodeDecodeError, ValueError):
        raise UsageError("STATE_INVALID") from None
    if not (isinstance(data, dict) and data.get("version") == 1
            and isinstance(data.get("alerts"), dict) and isinstance(data.get("topics"), dict)):
        raise UsageError("STATE_INVALID")
    if not (all(_alert_ok(r) for r in data["alerts"].values())
            and all(_topic_ok(t) for t in data["topics"].values())):
        raise UsageError("STATE_INVALID", "malformed alert or topic entry")
    return data


@contextlib.contextmanager
def state_lock(path):
    """Exclusive lock file beside the state (O_CREAT|O_EXCL). Yields None when acquired,
    or a dict describing the holder when another notify --send owns it. Never broken
    automatically: a lock left by a crash is reported and the user removes it."""
    lock = Path(str(path) + ".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        try:
            age = time.time() - lock.stat().st_mtime
        except OSError:
            age = None
        yield {"lock": str(lock), "age_seconds": round(age) if age is not None else None,
               "stale": age is not None and age > LOCK_STALE_SECONDS}
        return
    try:
        os.write(fd, ("%d\n" % os.getpid()).encode("ascii"))
    finally:
        os.close(fd)
    try:
        yield None
    finally:
        try:
            os.unlink(str(lock))
        except OSError:
            pass


def save_state(path, state):
    """Atomic: temp file in the same folder, fsync, os.replace."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def alert_key(handle, log_name, entry_time, topic):
    return hashlib.sha256(("%s|%s|%s|%s" % (handle, log_name, entry_time, topic))
                          .encode("utf-8")).hexdigest()


# ── gates ─────────────────────────────────────────────────────────────────
def _gate(decision="pass", reasons=(), **extra):
    gate = {"decision": decision, "reasons": list(reasons)}
    gate.update(extra)
    return gate


@dataclasses.dataclass
class Deps:
    runner: object = None
    peer_state: object = "default"
    env: object = None
    clock: object = time.time
    which: object = shutil.which
    home: object = None

    def __post_init__(self):
        if self.peer_state == "default":
            self.peer_state = _peer_state
        if self.env is None:
            self.env = dict(os.environ)
        if self.home is None:
            self.home = Path.home()


def target_gate(rows, handle, sender, self_handle, truncated):
    matches = [r for r in rows if r["handle"] == handle]
    row = matches[0] if matches else None
    reasons = []
    if row is None:
        reasons.append("target_not_found")
        if truncated:
            reasons.append("terminal_list_truncated")
    else:
        if len(matches) > 1:
            reasons.append("target_handle_duplicated")
        if not row["connected"]:
            reasons.append("not_connected")
        if not row["writable"]:
            reasons.append("not_writable")
        if row["orphaned"]:
            reasons.append("orphaned")
        if row["agent"] not in SUPPORTED_TARGETS:
            reasons.append("unsupported_agent")
        elif sender and row["agent_name"] == sender:
            # Claude->Claude cannot be told apart in the log or the doorbell, and with
            # an unverified self handle the target may be the sender's own terminal.
            reasons.append("same_agent_pair")
    if self_handle and handle == self_handle:
        reasons.append("self_target")
    self_row = next((r for r in rows if self_handle and r["handle"] == self_handle), None)
    if sender and self_row and self_row["agent_name"] and self_row["agent_name"] != sender:
        reasons.append("sender_identity_mismatch")
    return row, _gate("hold" if reasons else "pass", reasons,
                      agent=row["agent"] if row else None,
                      self_verified=self_row is not None)


def map_record(row, opts, deps, exclude):
    explicit = getattr(opts, "record", None)
    if explicit:
        path = Path(explicit)
        if not path.is_file():
            return {"status": "not_found", "path": None, "candidates": [], "source": "explicit"}
        return {"status": "ok", "path": str(path), "candidates": [str(path)], "source": "explicit"}
    if row["agent"] == "codex":
        home = getattr(opts, "codex_home", None) or deps.env.get("CODEX_HOME") \
            or str(Path(deps.home) / ".codex")
        mapping = map_codex_record(row["worktreePath"], home, exclude)
    else:
        home = getattr(opts, "claude_home", None) or str(Path(deps.home) / ".claude")
        mapping = map_claude_record(row["worktreePath"], home, exclude)
    mapping["source"] = "auto"
    return mapping


def terminal_record_check(row, path, explicit, now):
    """(reasons, info): does the terminal corroborate that `path` is its session record?

    The record is found by folder, so several terminals in one folder all map to the
    newest record (observed live). A record written while the terminal stayed silent
    belongs to another session; that is checked even for an explicit --record. A
    terminal with no known output, or with output long after the record's last write
    (a wrong, stale record or a user typing a draft), is held only for an automatic
    mapping. Output in the last 30 seconds means the terminal is not quiet."""
    info = {"terminal_last_output_utc": None, "record_mtime_utc": None,
            "output_minus_record_seconds": None, "slack_seconds": TERMINAL_SLACK_SECONDS}
    try:
        mtime = os.stat(path).st_mtime
    except OSError:
        return ["record_stat_failed"], info
    info["record_mtime_utc"] = _safe_fmt(fmt_utc, mtime)
    out = parse_time(row.get("lastOutputAt"))
    if out is None:
        return ([] if explicit else ["terminal_output_unknown"]), info
    info["terminal_last_output_utc"] = _safe_fmt(fmt_utc, out)
    delta = out - mtime
    info["output_minus_record_seconds"] = round(delta, 1)
    reasons = []
    if now - out < TERMINAL_QUIET_SECONDS:
        reasons.append("terminal_recent_output")
    if delta < -TERMINAL_SLACK_SECONDS:
        reasons.append("record_newer_than_terminal_output")
    elif delta > TERMINAL_SLACK_SECONDS and not explicit:
        reasons.append("terminal_output_after_record")
    return reasons, info


def record_gate(row, opts, deps):
    """Map target -> session record, then peer_state.assess(). Returns (assessment, gate)."""
    if row is None or row["agent"] not in SUPPORTED_TARGETS:
        return None, _gate("skipped", ["needs_target"])
    if not row["worktreePath"] and not getattr(opts, "record", None):
        # Folder contexts (non-git) report no worktreePath; only --record can map them.
        return None, _gate("hold", ["worktree_unknown"], hint="pass --record")
    ps = deps.peer_state
    if ps is None:
        return None, _gate("hold", ["peer_state_unavailable"])
    exclude = [_file_key(opts.self_record)] if getattr(opts, "self_record", None) else []
    mapping = map_record(row, opts, deps, exclude)
    if mapping["status"] == "ok" and exclude and _file_key(mapping["path"]) in exclude:
        return None, _gate("hold", ["record_is_self"], mapping=mapping)
    if mapping["status"] != "ok":
        reason = "record_ambiguous" if mapping["status"] == "ambiguous" else "record_not_found"
        return None, _gate("hold", [reason], mapping=mapping)
    try:
        assessment = ps.assess(row["agent"], mapping["path"],
                               context_window=getattr(opts, "context_window", None))
    except Exception as exc:  # noqa: BLE001 - reported, never guessed around
        return None, _gate("hold", ["assess_failed"], mapping=mapping, error=type(exc).__name__)
    if not isinstance(assessment, dict):
        return None, _gate("hold", ["assess_failed"], mapping=mapping)
    raw_reasons = assessment.get("reasons")
    detail = [r for r in raw_reasons if isinstance(r, str)] if isinstance(raw_reasons, list) else []
    cross, terminal = terminal_record_check(row, mapping["path"], mapping["source"] == "explicit",
                                            deps.clock())
    gate = _gate("pass", [], mapping=mapping, state=assessment.get("state"),
                 sendable=assessment.get("sendable") is True, detail=detail, terminal=terminal)
    if assessment.get("sendable") is not True:
        gate["decision"], gate["reasons"] = "hold", ["target_not_sendable"] + detail
    if cross:
        gate["decision"] = "hold"
        gate["reasons"] = gate["reasons"] + cross
        if mapping["source"] != "explicit":
            gate["hint"] = "pass --record only if you know this terminal's own session record"
    return assessment, gate


def screen_idle(transport, handle):
    """tui-idle as True/False/None. Auxiliary only; it can downgrade, never upgrade."""
    try:
        rc, envelope = transport.raw(
            ["terminal", "wait", "--terminal", handle, "--for", "tui-idle",
             "--timeout-ms", str(SCREEN_WAIT_MS), "--json"], timeout=SCREEN_WAIT_MS // 1000 + 15)
    except OrcaError:
        return None
    result = envelope.get("result") if envelope.get("ok") is True else None
    if not isinstance(result, dict):
        return None
    wait = result.get("wait") if isinstance(result.get("wait"), dict) else result
    if wait.get("blockedReason"):
        return False
    if wait.get("satisfied") is True:
        return True
    if wait.get("satisfied") is False:
        return False
    return None


def screen_gate(transport, row, mode, assessment, ps):
    agent = row["agent"] if row else None
    run = mode == "required" or (mode == "auto" and agent == "claude")
    if row is None or agent not in SUPPORTED_TARGETS:
        return assessment, _gate("skipped", ["needs_target"], checked=False, tui_idle=None,
                                 mode=mode)
    if not run:
        return assessment, _gate("pass", [], checked=False, tui_idle=None, mode=mode)
    tui = screen_idle(transport, row["handle"])
    gate = _gate("pass", [], checked=True, tui_idle=tui, mode=mode)
    if mode == "required" and tui is None:
        gate["decision"], gate["reasons"] = "hold", ["screen_unknown"]
    if assessment is None or ps is None:
        return assessment, gate
    try:
        combined = ps.combine_screen(assessment, tui)
    except Exception as exc:  # noqa: BLE001
        gate["decision"], gate["reasons"] = "hold", ["screen_combine_failed"]
        gate["error"] = type(exc).__name__
        return assessment, gate
    if not isinstance(combined, dict):
        gate["decision"], gate["reasons"] = "hold", ["screen_combine_failed"]
        return assessment, gate
    if assessment.get("sendable") is True and combined.get("sendable") is not True:
        gate["decision"] = "hold"
        gate["reasons"] = ["screen_conflict"] + [
            r for r in combined.get("reasons") or [] if isinstance(r, str) and r != "screen_conflict"]
    gate["state"] = combined.get("state")
    return combined, gate


def _max_used(windows, key):
    values = [_number(w.get(key)) for w in windows if isinstance(w, dict)]
    values = [v for v in values if v is not None]
    return max(values) if values else None


def _record_quota(assessment, now):
    quota = assessment.get("quota") if isinstance(assessment, dict) else None
    if not isinstance(quota, dict):
        return None, "record_quota_missing"
    observed = parse_time(quota.get("observed_utc"))
    if observed is None or not -300 <= now - observed <= QUOTA_FRESH_SECONDS:
        return None, "record_quota_stale"
    used = _max_used([quota.get("primary"), quota.get("secondary")], "used_percent")
    limit = quota.get("limit_reached") if isinstance(quota.get("limit_reached"), bool) else None
    if used is None and limit is None:
        return None, "record_quota_empty"
    return {"source": "codex-record", "used_percent": used, "limit_reached": limit,
            "observed_utc": fmt_utc(observed), "observed_kst": fmt_kst(observed)}, None


def _account_quota(transport, agent, now):
    """Orca account list rateLimits[agent]; only key names/numbers are read."""
    try:
        result = transport.result(ACCOUNT_ARGV)
    except OrcaError:
        return None, "account_list_failed"
    limits = result.get("rateLimits")
    entry = limits.get(agent) if isinstance(limits, dict) else None
    if not isinstance(entry, dict):
        return None, "account_quota_missing"
    if entry.get("status") != "ok" or entry.get("error"):
        return None, "account_quota_not_ok"
    provider = result.get(agent)
    accounts = provider.get("accounts") if isinstance(provider, dict) else None
    if isinstance(accounts, list) and len(accounts) > 1:
        return None, "account_ambiguous"
    updated = parse_time(entry.get("updatedAt"))
    if updated is None or not -300 <= now - updated <= QUOTA_FRESH_SECONDS:
        return None, "account_quota_stale"
    main = [entry.get(k) for k in QUOTA_MAIN_WINDOWS if isinstance(entry.get(k), dict)]
    if any(_number(w.get("usedPercent")) is None for w in main):
        return None, "account_quota_invalid"  # a present window without a real number
    used = _max_used(main, "usedPercent")
    if used is None:
        return None, "account_quota_empty"
    # Model-scoped windows (e.g. a per-model weekly cap) may or may not bind this
    # session; they are reported and can only ask for confirmation, never hold.
    scoped = {k: _number(v.get("usedPercent")) for k, v in entry.items()
              if k not in QUOTA_MAIN_WINDOWS and isinstance(v, dict)
              and _number(v.get("usedPercent")) is not None}
    return {"source": "orca-account-list", "used_percent": used, "limit_reached": None,
            "scoped_windows": scoped,
            "observed_utc": fmt_utc(updated), "observed_kst": fmt_kst(updated)}, None


def quota_gate(transport, row, assessment, opts, now):
    agent = row["agent"] if row else None
    if agent not in SUPPORTED_TARGETS:
        return _gate("skipped", ["needs_target"])
    notes, info = [], None
    if agent == "codex":
        info, note = _record_quota(assessment, now)
        if note:
            notes.append(note)
    if info is None:
        info, note = _account_quota(transport, agent, now)
        if note:
            notes.append(note)
    gate = _gate("pass", [], quota=info, notes=notes)
    if info is None:
        if not opts.allow_unknown_quota:
            gate["decision"], gate["reasons"] = "confirm", ["quota_unknown"]
        return gate
    used = info.get("used_percent")
    scoped_high = sorted(k for k, v in (info.get("scoped_windows") or {}).items()
                         if v >= QUOTA_LOW)
    if info.get("limit_reached") is True or (used is not None and used >= QUOTA_FULL):
        gate["decision"], gate["reasons"] = "hold", ["quota_exhausted"]
    elif used is not None and used >= QUOTA_LOW and not opts.confirm_low_quota:
        gate["decision"], gate["reasons"] = "confirm", ["quota_low"]
    elif used is None and not opts.allow_unknown_quota:
        gate["decision"], gate["reasons"] = "confirm", ["quota_unknown"]
    elif scoped_high and not opts.confirm_low_quota:
        gate["decision"], gate["reasons"] = "confirm", ["quota_scoped_window_high"]
        gate["scoped_high"] = scoped_high
    return gate


def _context_percent(assessment):
    context = assessment.get("context") if isinstance(assessment, dict) else None
    return _number(context.get("percent")) if isinstance(context, dict) else None


def _topic_count(state, topic):
    entry = state["topics"].get(topic)
    count = entry.get("count", 0) if isinstance(entry, dict) else 0
    return count if isinstance(count, int) and not isinstance(count, bool) and count > 0 else 0


def context_gate(opts, deps, target_assessment, state):
    target_pct = _context_percent(target_assessment)
    self_pct, self_note = None, None
    agent = SENDER_AGENT.get(opts.sender)
    if not opts.self_record:
        self_note = "self_record_missing"
    elif agent is None:
        self_note = "sender_record_unsupported"
    elif deps.peer_state is None:
        self_note = "peer_state_unavailable"
    else:
        try:  # context only: no quiet wait for our own, actively written record
            mine = deps.peer_state.assess(agent, opts.self_record, quiet_seconds=0,
                                          recheck_seconds=0, sleep=lambda _s: None)
            self_pct = _context_percent(mine)
        except Exception as exc:  # noqa: BLE001
            self_note = "self_assess_failed:" + type(exc).__name__
    count = _topic_count(state, opts.topic)
    gate = _gate("pass", [], target_percent=target_pct, self_percent=self_pct,
                 threshold=opts.context_threshold, fallback_used=False, topic_count=count,
                 notes=[self_note] if self_note else [])
    high = [p for p in (target_pct, self_pct) if p is not None and p >= opts.context_threshold]
    if high:
        gate["decision"], gate["reasons"] = "escalate", ["context_high"]
    elif target_pct is None or self_pct is None:
        gate["fallback_used"] = True
        gate["fallback_round_trips"] = opts.fallback_round_trips
        if count >= opts.fallback_round_trips:
            gate["decision"], gate["reasons"] = "escalate", ["round_trip_fallback_cap"]
    return gate


def min_gap_gate(state, handle, now, min_gap):
    last = None
    for record in state["alerts"].values():
        if isinstance(record, dict) and record.get("to") == handle:
            sent = parse_time(record.get("sent_utc"))
            if sent is not None and (last is None or sent > last):
                last = sent
    gate = _gate("pass", [], last_alert_utc=fmt_utc(last) if last is not None else None,
                 min_gap_seconds=min_gap)
    if last is not None and now - last < min_gap:
        gate["decision"], gate["reasons"] = "hold", ["min_gap"]
    return gate


def aggregate(gates):
    """Only "pass" is neutral; any other or unknown decision (e.g. "skipped") is at
    least a hold, so a gate that did not run can never count as passed."""
    def rank(gate):
        decision = gate.get("decision") if isinstance(gate, dict) else None
        return 0 if decision == "pass" else RANK.get(decision, RANK["hold"])
    worst = max((rank(g) for g in gates.values()), default=RANK["hold"])
    return {0: "send", 1: "confirm", 2: "hold", 3: "escalate"}[worst]


# ── notify ────────────────────────────────────────────────────────────────
def _validate_notify(opts):
    if HANDLE_RE.fullmatch(opts.to or "") is None:
        raise UsageError("HANDLE_INVALID")
    if opts.sender not in NAMES:
        raise UsageError("SENDER_INVALID")
    for value in (opts.log, opts.topic, opts.record, opts.self_record, opts.state):
        if value is not None and (not str(value) or has_control(value)):
            raise UsageError("CONTROL_CHARACTERS")
    log_name = os.path.basename(str(opts.log).replace("\\", "/"))
    if LOG_NAME_RE.fullmatch(log_name) is None:
        raise UsageError("LOG_NAME_INVALID")
    if not Path(opts.log).is_file():
        raise UsageError("LOG_NOT_FOUND")
    if opts.topic is None:
        opts.topic = log_name
    if not 1 <= len(opts.topic) <= 120:
        raise UsageError("TOPIC_INVALID")
    # NaN passes every "< 0" check and then makes each comparison False (gate bypass).
    if not (math.isfinite(opts.context_threshold) and 0 < opts.context_threshold <= 100) \
            or opts.fallback_round_trips < 0 \
            or not (math.isfinite(opts.min_gap_seconds) and opts.min_gap_seconds >= 0):
        raise UsageError("THRESHOLD_INVALID")
    return log_name


def _send_argv(handle, line):
    return ["terminal", "send", "--terminal", handle, "--text", line, "--enter",
            "--wait-submit", str(WAIT_SUBMIT_SECONDS), "--json"]


def _parse_send(rc, envelope, handle):
    result = envelope.get("result") if isinstance(envelope, dict) else None
    send = result.get("send") if isinstance(result, dict) else None
    if not isinstance(send, dict) or not isinstance(send.get("accepted"), bool):
        error = envelope.get("error") if isinstance(envelope, dict) else None
        code = error.get("code") if isinstance(error, dict) else None
        return {"outcome": "ambiguous", "accepted": None, "request_id": None, "stages": [],
                "error": code if isinstance(code, str) else "SEND_RESULT_MISSING"}
    prompt = send.get("prompt") if isinstance(send.get("prompt"), dict) else {}
    stages = prompt.get("stages") if isinstance(prompt.get("stages"), list) else []
    warnings = result.get("warnings") if isinstance(result.get("warnings"), list) else []
    request_id = prompt.get("requestId") if isinstance(prompt.get("requestId"), str) else None
    receipt = {"accepted": send["accepted"], "handle": send.get("handle"),
               "refused_reason": send.get("refusedReason"), "request_id": request_id,
               "stages": [s for s in stages if isinstance(s, str)],
               "observation": prompt.get("observation"), "warnings": warnings}
    if not send["accepted"]:
        receipt["outcome"] = "refused"
    elif rc != 0 or envelope.get("ok") is not True or send.get("handle") not in (None, handle):
        receipt["outcome"] = "ambiguous"
    else:
        receipt["outcome"] = "sent"
    if receipt["outcome"] == "sent" and "turn_started" not in receipt["stages"]:
        receipt["note"] = "turn_not_observed_input_accepted_only"
    return receipt


def _exit_for_receipt(record):
    return 0 if isinstance(record, dict) and record.get("outcome") == "sent" else 1


def notify(opts, deps):
    """Returns (exit_code, report). Never sends unless opts.send and every gate passes."""
    log_name = _validate_notify(opts)
    state_path = Path(opts.state) if opts.state else default_state_path(
        opts.sender, deps.env, deps.home)
    state = load_state(state_path)
    transport = OrcaTransport(resolve_orca(opts.orca, deps.env, deps.which), deps.runner)
    now = deps.clock()
    self_handle = deps.env.get("ORCA_TERMINAL_HANDLE") or None
    report = {"mode": "send" if opts.send else "dry-run", "decision": None, "duplicate": False,
              "sent": False, "from": opts.sender, "to_handle": opts.to, "topic": opts.topic,
              "log": log_name, "state_path": str(state_path), "evaluated_utc": fmt_utc(now),
              "evaluated_kst": fmt_kst(now), "gates": {}}
    gates = report["gates"]

    try:
        rows, truncated = list_terminals(transport)
    except OrcaError as exc:
        rows, truncated = None, False
        gates["target"] = _gate("hold", ["orca_list_failed"], error=exc.code)
    row = None
    if rows is not None:
        row, gates["target"] = target_gate(rows, opts.to, opts.sender, self_handle, truncated)

    # Doorbell: To comes from the target identity; the time from the log only.
    to_name = row["agent_name"] if row else None
    doorbell = {"line": None, "entry_time": None, "to": to_name}
    report["doorbell"] = doorbell
    if to_name is None:
        gates["doorbell"] = _gate("skipped" if row is None else "hold",
                                  ["needs_target"] if row is None else ["unsupported_agent"])
    elif to_name not in NAMES or to_name == opts.sender:
        gates["doorbell"] = _gate("hold", ["pair_not_supported"])
    else:
        entry, malformed, latest_bad = last_addressed_entry(opts.log, opts.sender, to_name)
        doorbell.update(entry_time=entry, malformed_headings=malformed,
                        latest_heading_malformed=latest_bad)
        if latest_bad:
            gates["doorbell"] = _gate("hold", ["latest_heading_malformed"],
                                      hint="the last heading addressed to the peer must be "
                                           "'## %s → %s · YY.MM.DD HH:MM KST · <type>'"
                                           % (opts.sender, to_name))
        elif entry is None:
            gates["doorbell"] = _gate("hold", ["no_addressed_entry"])
        else:
            doorbell["line"] = build_doorbell(opts.sender, to_name, log_name, entry)
            gates["doorbell"] = _gate("pass", [])

    # Gate 6a: idempotency first; a duplicate never reaches any other gate.
    if doorbell["line"]:
        key = alert_key(opts.to, log_name, doorbell["entry_time"], opts.topic)
        report["key"] = key
        stored = state["alerts"].get(key)
        if stored is not None:
            report.update({"duplicate": True, "decision": "duplicate", "receipt": stored})
            if not isinstance(stored, dict) or stored.get("outcome") != "sent":
                report["instructions"] = AMBIGUOUS_HELP
            return _exit_for_receipt(stored), report

    assessment, gates["record"] = record_gate(row, opts, deps)
    report["assessment"] = assessment
    _combined, gates["screen"] = screen_gate(transport, row, opts.screen_check, assessment,
                                             deps.peer_state)
    gates["quota"] = quota_gate(transport, row, assessment, opts, now)
    gates["context"] = context_gate(opts, deps, assessment, state)
    gates["idempotency"] = min_gap_gate(state, opts.to, now, opts.min_gap_seconds)
    decision = aggregate(gates)
    report["decision"] = decision
    report["reasons"] = [r for g in gates.values() if g["decision"] in RANK for r in g["reasons"]]
    report["fallback_used"] = gates["context"].get("fallback_used") is True
    report["would_send"] = decision == "send"
    if decision == "send":
        report["argv"] = [transport.exe] + _send_argv(opts.to, doorbell["line"])
    if decision != "send":
        return 3, report
    if not opts.send:
        return 0, report

    # --send: re-run gates 1-2 on fresh data right before the single send.
    try:
        fresh_rows, fresh_truncated = list_terminals(transport)
        fresh_row, recheck_target = target_gate(fresh_rows, opts.to, opts.sender, self_handle,
                                                fresh_truncated)
    except OrcaError as exc:
        fresh_row, recheck_target = None, _gate("hold", ["orca_list_failed"], error=exc.code)
    recheck = {"target": recheck_target}
    if recheck_target["decision"] == "pass" and fresh_row["agent_name"] != to_name:
        recheck_target["decision"] = "hold"
        recheck_target["reasons"].append("target_identity_changed")
    if recheck_target["decision"] == "pass":
        _unused, recheck["record"] = record_gate(fresh_row, opts, deps)
    report["recheck"] = recheck
    if any(g["decision"] != "pass" for g in recheck.values()) or "record" not in recheck:
        report["decision"] = "hold"
        report["reasons"] = ["recheck_failed"] + [r for g in recheck.values() for r in g["reasons"]]
        return 3, report

    send_argv = _send_argv(opts.to, doorbell["line"])
    if not argv_allowed(send_argv):
        raise ArgvRefused("ORCA_ARGV_REFUSED")
    # One writer at a time: two notify --send runs (same sender, same state file) must
    # neither both send nor overwrite each other's records.
    with state_lock(state_path) as holder:
        if holder is not None:
            report.update(decision="hold", reasons=["state_locked"], lock=holder,
                          instructions="Another notify --send holds the state lock. If no "
                                       "peer_link is running (stale), remove the lock file.")
            return 3, report
        return _send_locked(opts, deps, transport, report, state_path, key, log_name,
                            doorbell, send_argv)


def _send_locked(opts, deps, transport, report, state_path, key, log_name, doorbell, send_argv):
    """Runs under state_lock. Re-reads the state and re-applies the state-based gates,
    records the attempt BEFORE the call (a crash can never lead to a resend), sends once."""
    state = load_state(state_path)
    if key in state["alerts"]:
        report.update({"duplicate": True, "decision": "duplicate",
                       "receipt": state["alerts"][key]})
        if state["alerts"][key].get("outcome") != "sent":
            report["instructions"] = AMBIGUOUS_HELP
        return _exit_for_receipt(state["alerts"][key]), report
    under_lock = {"idempotency": min_gap_gate(state, opts.to, deps.clock(), opts.min_gap_seconds)}
    if report.get("fallback_used"):
        count = _topic_count(state, opts.topic)
        under_lock["context"] = _gate("pass", [], topic_count=count)
        if count >= opts.fallback_round_trips:
            under_lock["context"] = _gate("escalate", ["round_trip_fallback_cap"],
                                          topic_count=count)
    if any(g["decision"] != "pass" for g in under_lock.values()):
        report.update(under_lock=under_lock, decision=aggregate(under_lock),
                      reasons=["changed_under_lock"] + [r for g in under_lock.values()
                                                        for r in g["reasons"]])
        return 3, report
    sent_at = deps.clock()
    record = {"to": opts.to, "topic": opts.topic, "log": log_name,
              "entry_time": doorbell["entry_time"], "sent_utc": fmt_utc(sent_at),
              "sent_kst": fmt_kst(sent_at), "request_id": None, "accepted": None,
              "stages": [], "outcome": "pending"}
    state["alerts"][key] = record
    try:
        save_state(state_path, state)
    except OSError:
        raise UsageError("STATE_WRITE_FAILED") from None  # nothing was sent

    try:
        rc, envelope = transport.raw(send_argv, timeout=SEND_TIMEOUT)
        receipt = _parse_send(rc, envelope, opts.to)
    except OrcaError as exc:  # timeout / spawn / undecodable: outcome unknown
        receipt = {"outcome": "ambiguous", "accepted": None, "request_id": None, "stages": [],
                   "error": exc.code}
    except Exception as exc:  # noqa: BLE001 - the process may have started: unknown, recorded
        receipt = {"outcome": "ambiguous", "accepted": None, "request_id": None, "stages": [],
                   "error": "SEND_EXCEPTION:" + type(exc).__name__}
    report["sent"] = receipt["outcome"] == "sent"
    record.update({"request_id": receipt.get("request_id"), "accepted": receipt.get("accepted"),
                   "stages": receipt.get("stages") or [], "outcome": receipt["outcome"]})
    if receipt["outcome"] in ("sent", "ambiguous"):  # may have reached the peer
        state["topics"][opts.topic] = {"count": _topic_count(state, opts.topic) + 1,
                                       "last_utc": record["sent_utc"]}
    try:
        save_state(state_path, state)
    except OSError as exc:
        report["state_write_error"] = type(exc).__name__
    report["receipt"] = receipt
    if receipt["outcome"] != "sent":
        report["instructions"] = AMBIGUOUS_HELP if receipt["outcome"] == "ambiguous" else \
            "Refused by Orca. Nothing is retried automatically; ask the user before any new alert."
    return (0 if report["sent"] else 1), report


# ── status ────────────────────────────────────────────────────────────────
def status(opts, deps):
    if HANDLE_RE.fullmatch(opts.to or "") is None:
        raise UsageError("HANDLE_INVALID")
    transport = OrcaTransport(resolve_orca(opts.orca, deps.env, deps.which), deps.runner)
    rows, truncated = list_terminals(transport)
    self_handle = deps.env.get("ORCA_TERMINAL_HANDLE") or None
    row, target = target_gate(rows, opts.to, None, self_handle, truncated)
    assessment, record = record_gate(row, opts, deps)
    sendable = (target["decision"] == "pass" and record["decision"] == "pass"
                and isinstance(assessment, dict) and assessment.get("sendable") is True)
    report = {"to_handle": opts.to, "terminal": row, "target": target, "record": record,
              "assessment": assessment, "sendable": sendable}
    return (0 if sendable else 3), report


# ── CLI ───────────────────────────────────────────────────────────────────
def _utf8_stdio():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


def _emit(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def build_parser():
    # allow_abbrev=False everywhere: only the exact "--send" may ever send ("--sen" is refused).
    parser = argparse.ArgumentParser(prog="peer_link.py", description=__doc__.split("\n\n")[0],
                                     allow_abbrev=False)
    sub = parser.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    common.add_argument("--orca", help="native orca executable (default: env VIBE_ORCA_EXE, PATH)")

    sub.add_parser("discover", parents=[common], allow_abbrev=False,
                   help="list Orca terminals (read-only)")

    record = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    record.add_argument("--to", required=True, help="target terminal handle")
    record.add_argument("--record", help="explicit target session record (wins over auto-map)")
    record.add_argument("--codex-home", help="default: env CODEX_HOME or ~/.codex")
    record.add_argument("--claude-home", help="default: ~/.claude")
    record.add_argument("--context-window", type=int, help="target context window in tokens")
    record.add_argument("--self-record", help="the sender's own session record")

    sub.add_parser("status", parents=[common, record], allow_abbrev=False,
                   help="target terminal + record state")

    notify_p = sub.add_parser("notify", parents=[common, record], allow_abbrev=False,
                              help="gate and (with --send) ring the doorbell once")
    notify_p.add_argument("--from", dest="sender", required=True, choices=NAMES)
    notify_p.add_argument("--log", required=True, help="path to the coordination log (.md)")
    notify_p.add_argument("--topic", help="round-trip counter key (default: log basename)")
    notify_p.add_argument("--context-threshold", type=float, default=80.0)
    notify_p.add_argument("--fallback-round-trips", type=int, default=10)
    notify_p.add_argument("--min-gap-seconds", type=float, default=60.0)
    notify_p.add_argument("--allow-unknown-quota", action="store_true")
    notify_p.add_argument("--confirm-low-quota", action="store_true")
    notify_p.add_argument("--screen-check", choices=("auto", "off", "required"), default="auto")
    notify_p.add_argument("--state", help="state file (default per sender; env VIBE_PEER_STATE)")
    notify_p.add_argument("--send", action="store_true",
                          help="actually type the doorbell (default: dry run)")
    return parser


def main(argv=None, deps=None):
    _utf8_stdio()
    opts = build_parser().parse_args(argv)
    deps = deps or Deps()
    try:
        if opts.command == "discover":
            transport = OrcaTransport(resolve_orca(opts.orca, deps.env, deps.which), deps.runner)
            try:
                _emit(discover(transport, deps.env))
            except OrcaError as exc:
                _emit({"error": exc.code, "detail": exc.detail})
                return 1
            return 0
        if opts.command == "status":
            try:
                code, report = status(opts, deps)
            except OrcaError as exc:
                _emit({"error": exc.code, "detail": exc.detail})
                return 1
            _emit(report)
            return code
        code, report = notify(opts, deps)
        _emit(report)
        return code
    except (UsageError, ArgvRefused) as exc:
        _emit({"error": getattr(exc, "code", None) or str(exc),
               "detail": getattr(exc, "detail", None)})
        return 2
    except ValueError as exc:  # doorbell validation
        _emit({"error": str(exc)})
        return 2
    except OSError as exc:  # unreadable log/record folder; nothing was sent
        _emit({"error": "IO_ERROR", "detail": type(exc).__name__})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
