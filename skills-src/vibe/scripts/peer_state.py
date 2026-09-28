#!/usr/bin/env python3
"""peer_state.py - record-first state detector for an already running peer session.

Answers one question for /vibe peer sessions: may a one-line doorbell be typed into
this Codex or Claude Code session right now?  The answer comes from the session's
own JSONL record, never from the terminal screen.  The screen (Orca ``tui-idle``)
may only DOWNGRADE a verdict (``combine_screen``); it never upgrades one.

Read-only.  Standard library only.  No subprocess, no network, no writes.

Accepted record types (checked structurally against codex-tui 0.155.0, Codex
Desktop 0.155.0-alpha and Claude Code 2.1.2xx files; values were never copied)
-----------------------------------------------------------------------------
Codex rollout (``~/.codex/sessions/**/rollout-*.jsonl``, timestamps are UTC "Z"):
  * lifecycle  ``event_msg`` payload.type ``task_started`` / ``task_complete`` /
    ``turn_aborted``, each with ``turn_id``.  Turns are PAIRED BY turn_id (a set
    of open turns).  "Last lifecycle event wins" is wrong: turns can overlap
    (A start, B start, B complete, A complete) and the session is working until
    A completes.  Completion without a start is ignored (``unmatched_complete``).
    The same turn_id started twice -> ``unknown``.
  * root only  the FIRST record must be ``session_meta`` (else ``unknown``,
    ``no_session_meta``).  ``forked_from_id`` -> the file replays parent history
    -> ``unknown`` (``fork_file``).  ``parent_thread_id``, a ``thread_source``
    other than ``user``/absent (``subagent``, ``guardian_review``, ...) or a dict
    ``source`` (``{"subagent": ...}``) -> ``unknown`` (``non_root_thread``).
  * question   top-level ``response_item`` whose payload.type is
    ``function_call`` or ``custom_tool_call`` and payload.name starts with
    ``request_user_input`` (real name: ``request_user_input_async``) after the
    last human-input marker.  Text inside arguments, tool input/output,
    instructions, compacted history or world_state never counts.
  * human input marker  ``event_msg`` payload.type ``item_completed`` with
    ``item.type == "UserMessage"`` (present in both codex-tui and Codex Desktop;
    one per human turn).  ``response_item`` message role=user is NOT a marker:
    it also carries injected context.  There is no close event: a later marker
    closes an open question, and so does a later ``turn_aborted`` of a turn
    that was open when the question was asked (aborting another turn does not).
  * quota/context  last ``event_msg`` ``token_count``: ``rate_limits.primary`` /
    ``secondary`` {used_percent, window_minutes, resets_at (epoch seconds)},
    ``rate_limit_reached_type`` / ``spend_control_reached``; ``info``
    {last_token_usage, total_token_usage, model_context_window}.  Context
    "used" = last_token_usage.input_tokens + output_tokens (the most recent
    model request, i.e. what occupied the window then); total_token_usage is
    cumulative and never used.  Omitted fields stay None (never guessed as 0).
Claude Code main-session JSONL (``~/.claude/projects/<proj>/<session>.jsonl``,
not the ``subagents/`` directory):
  * valid records: ``assistant``, ``user``, ``system`` subtype ``turn_duration``.
    Everything else (meta records without timestamp, attachment,
    queue-operation, file-history-*, other system subtypes, unknown types,
    sidechain records) is ignored.  Order is LINE order, never timestamps.
  * assistant records are grouped by ``message.id``; stop_reason is read from
    the last record of the group (thinking records may carry null).
  * tool_use without a matching ``tool_result`` is pending unless a later human
    prompt shows it was abandoned.  Pending ``AskUserQuestion`` -> ``question``.
  * a user record whose text is exactly Claude Code's interrupt marker ends the
    turn without ``turn_duration``; it is reported as ``unknown`` (hold).
  * ``queue-operation``: an ``enqueue`` after the last ``turn_duration`` that no
    ``dequeue``/``remove``/``popAll`` balanced means queued input has not been
    taken yet -> ``unknown`` (``queued_input_pending``) instead of idle.
  * quota is not recorded (None).  Context "used" = last assistant
    message.usage input + cache_creation_input + cache_read_input + output
    tokens; the window comes only from the ``context_window`` argument.

Records are streamed line by line (memory is bounded by the longest line; real
root rollouts reach hundreds of MB to GB).  Any unreadable line -> ``unknown``.

CLI:  python -B peer_state.py --agent codex|claude --record <path>
      [--context-window N] [--quiet-seconds 30]
Prints assess() JSON.  Exit 0 = sendable, 3 = not sendable, 2 = usage error.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone

AGENTS = ("codex", "claude")
STATES = ("working", "idle", "question", "unknown")
KST = timezone(timedelta(hours=9), "KST")
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_EPOCH_MS_THRESHOLD = 1e11  # >= 1e11 is read as milliseconds (1e11 s would be year 5138)

CODEX_LIFECYCLE = ("task_started", "task_complete", "turn_aborted")
CODEX_TOOL_CALLS = ("function_call", "custom_tool_call")
CODEX_QUESTION_PREFIX = "request_user_input"
CLAUDE_ASK_TOOL = "AskUserQuestion"
_BOM = b"\xef\xbb\xbf"
CLAUDE_INTERRUPT_MARKERS = ("[Request interrupted by user]",
                            "[Request interrupted by user for tool use]")


# ── time ─────────────────────────────────────────────────────────────────────
def _to_datetime(value):
    """ISO-8601 with Z/offset, epoch seconds or epoch ms -> aware UTC datetime."""
    if isinstance(value, bool) or value is None:
        raise ValueError("timestamp missing")
    if isinstance(value, (int, float)):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("timestamp not finite")
        seconds = number / 1000.0 if abs(number) >= _EPOCH_MS_THRESHOLD else number
        try:
            return _EPOCH + timedelta(seconds=seconds)
        except OverflowError as exc:
            raise ValueError("timestamp out of range") from exc
    if not isinstance(value, str):
        raise ValueError("timestamp type unsupported")
    text = value.strip()
    if re.fullmatch(r"-?[0-9]+", text):
        return _to_datetime(int(text))
    if re.fullmatch(r"-?[0-9]+\.[0-9]+", text):
        return _to_datetime(float(text))
    if text[-1:] in ("Z", "z"):
        text = text[:-1] + "+00:00"
    moment = datetime.fromisoformat(text)
    if moment.tzinfo is None:
        raise ValueError("timestamp has no offset")
    return moment.astimezone(timezone.utc)


def to_kst(value):
    """Return "YYYY-MM-DD HH:MM:SS KST" (seconds floored). Raises ValueError."""
    return _to_datetime(value).astimezone(KST).strftime("%Y-%m-%d %H:%M:%S KST")


def _to_utc(value):
    return _to_datetime(value).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_kst(value):
    try:
        return _to_utc(value), to_kst(value)
    except (ValueError, TypeError, OverflowError):
        return None, None


# ── reading ──────────────────────────────────────────────────────────────────
def _parse_line(number, raw):
    """One raw line (with its newline) -> (dict, None) or (None, error). Errors never echo content."""
    if not raw.endswith(b"\n"):
        return None, "line %d: trailing partial line (no newline)" % number
    chunk = raw[:-1]
    if chunk.endswith(b"\r"):
        chunk = chunk[:-1]
    if number == 1 and chunk.startswith(_BOM):
        chunk = chunk[3:]
    if not chunk.strip():
        return None, "line %d: blank line" % number
    try:
        value = json.loads(chunk.decode("utf-8"))
    except UnicodeDecodeError:
        return None, "line %d: not UTF-8" % number
    except (ValueError, RecursionError):
        return None, "line %d: invalid JSON" % number
    if not isinstance(value, dict):
        return None, "line %d: not a JSON object" % number
    return value, None


class _LineStream:
    """Yields (line_no, dict) from a binary handle, one line in memory at a time.

    Single use.  ``errors`` and ``bytes_read`` are complete once iteration ends."""

    def __init__(self, handle):
        self._handle = handle
        self.errors = []
        self.bytes_read = 0

    def __iter__(self):
        for number, raw in enumerate(self._handle, 1):
            self.bytes_read += len(raw)
            record, error = _parse_line(number, raw)
            if error is None:
                yield number, record
            else:
                self.errors.append(error)


def _parse_lines(data):
    """bytes -> ([(line_no, dict)], [error])."""
    stream = _LineStream(io.BytesIO(data or b""))
    records = list(stream)
    return records, stream.errors


def read_records(path):
    """Read a JSONL record. Returns (records, errors); records = [(line_no, dict)].

    Keeps every record in a list; ``assess`` streams instead."""
    with open(path, "rb") as handle:
        stream = _LineStream(handle)
        records = list(stream)
    return records, stream.errors


def _payload(record):
    payload = record.get("payload")
    return payload if isinstance(payload, dict) else {}


def _str(value):
    return value if isinstance(value, str) and value else None


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(float(value)) else None


def _event(kind, line, timestamp):
    utc, kst = _utc_kst(timestamp)
    return {"type": kind, "line": line, "utc": utc, "kst": kst}


def _context(source, used, window):
    used = int(used) if _number(used) is not None else None
    window = int(window) if _number(window) is not None and window > 0 else None
    percent = round(used / window * 100.0, 2) if used is not None and window else None
    return {"source": source, "used_tokens": used, "window_tokens": window, "percent": percent}


def _status(state, reasons, *, open_turns=(), question=None, last_event=None,
            quota=None, context=None):
    line, name = question if question else (None, None)
    return {"state": state, "reasons": list(reasons), "open_turns": list(open_turns),
            "question": {"open": question is not None, "line": line, "name": name},
            "last_event": last_event, "quota": quota, "context": context}


# ── codex ────────────────────────────────────────────────────────────────────
def _codex_window(window):
    if not isinstance(window, dict):
        return None
    utc, kst = _utc_kst(window.get("resets_at")) if "resets_at" in window else (None, None)
    minutes = _number(window.get("window_minutes"))
    return {"used_percent": _number(window.get("used_percent")),
            "window_minutes": int(minutes) if minutes is not None else None,
            "resets_at_utc": utc, "resets_at_kst": kst}


def _codex_quota(record):
    limits = _payload(record).get("rate_limits")
    observed_utc, observed_kst = _utc_kst(record.get("timestamp"))
    reached = None
    if "rate_limit_reached_type" in limits:
        reached = bool(limits.get("rate_limit_reached_type"))
    if limits.get("spend_control_reached"):
        reached = True
    return {"source": "codex-record", "observed_utc": observed_utc, "observed_kst": observed_kst,
            "primary": _codex_window(limits.get("primary")),
            "secondary": _codex_window(limits.get("secondary")),
            "limit_reached": reached}


def _codex_context(record):
    """used = last request's input_tokens + output_tokens (cumulative usage is NOT context)."""
    info = _payload(record).get("info")
    last = info.get("last_token_usage") if isinstance(info.get("last_token_usage"), dict) else {}
    used_in, used_out = _number(last.get("input_tokens")), _number(last.get("output_tokens"))
    if used_in is not None and used_out is not None:
        used = used_in + used_out
    else:
        used = _number(last.get("total_tokens"))
    return _context("codex-record", used, info.get("model_context_window"))


def _codex_root_problem(first):
    """None when the file is a root thread's own record, else the reason it is not."""
    if first is None or first.get("type") != "session_meta":
        return "no_session_meta"
    head = _payload(first)
    if head.get("forked_from_id"):
        return "fork_file"
    if (head.get("parent_thread_id") or head.get("thread_source") not in (None, "user")
            or isinstance(head.get("source"), dict)):
        return "non_root_thread"
    return None


def codex_status(records):
    """Pure verdict for a Codex rollout (single pass over any iterable of (line, dict)).

    See the module docstring for the rules."""
    reasons = []
    first, seen = None, False
    open_turns = {}
    started, duplicate, bad_lifecycle, unmatched = set(), False, False, 0
    question = None  # (line, name, turn ids open when it was asked)
    quota_at = context_at = last = None
    for line, rec in records:
        if not seen:
            first, seen = rec, True
        payload = _payload(rec)
        kind = rec.get("type")
        sub = _str(payload.get("type"))
        last = (line, rec, "%s/%s" % (kind, sub) if sub else str(kind))
        if kind == "event_msg":
            if sub in CODEX_LIFECYCLE:
                turn = _str(payload.get("turn_id"))
                if turn is None:
                    bad_lifecycle = True
                elif sub == "task_started":
                    duplicate = duplicate or turn in started
                    started.add(turn)
                    open_turns[turn] = line
                else:
                    if turn in open_turns:
                        del open_turns[turn]
                    else:
                        unmatched += 1
                    if sub == "turn_aborted" and question is not None and turn in question[2]:
                        question = None
            elif sub == "item_completed":
                item = payload.get("item")
                if isinstance(item, dict) and item.get("type") == "UserMessage":
                    question = None
            elif sub == "token_count":
                if isinstance(payload.get("rate_limits"), dict):
                    quota_at = rec
                if isinstance(payload.get("info"), dict):
                    context_at = rec
        elif kind == "response_item" and sub in CODEX_TOOL_CALLS:
            name = payload.get("name")
            if isinstance(name, str) and name.startswith(CODEX_QUESTION_PREFIX):
                question = (line, name, frozenset(open_turns))
    root_problem = _codex_root_problem(first)
    if unmatched:
        reasons.append("unmatched_complete")
    if root_problem:
        state = "unknown"
        reasons.append(root_problem)
    elif bad_lifecycle:
        state = "unknown"
        reasons.append("lifecycle_without_turn_id")
    elif duplicate:
        state = "unknown"
        reasons.append("duplicate_turn_start")
    elif not started:
        state = "unknown"
        reasons.append("no_lifecycle_events")
    elif open_turns:
        state = "working"
        reasons.append("open_turn")
    elif question is not None:
        state = "question"
    else:
        state = "idle"
    if question is not None:
        reasons.append("question_open")
    last_event = _event(last[2], last[0], last[1].get("timestamp")) if last else None
    return _status(state, reasons, open_turns=open_turns,
                   question=question[:2] if question else None, last_event=last_event,
                   quota=_codex_quota(quota_at) if quota_at else None,
                   context=_codex_context(context_at) if context_at else None)


# ── claude ───────────────────────────────────────────────────────────────────
def _claude_content(record):
    message = record.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return [block for block in content if isinstance(block, dict)] if isinstance(content, list) else []


def _claude_user_kind(record):
    blocks = _claude_content(record)
    if any(block.get("type") == "tool_result" for block in blocks):
        return "tool_result"
    texts = [block.get("text") for block in blocks if block.get("type") == "text"]
    if any(text in CLAUDE_INTERRUPT_MARKERS for text in texts):
        return "interrupt"
    return "prompt"


def claude_status(records):
    """Pure verdict for a Claude Code main-session JSONL (single pass). See module docstring."""
    pending, usage, last = {}, None, None
    queued = 0  # enqueues after the last turn_duration not yet dequeued/removed
    for line, rec in records:
        kind = rec.get("type")
        if rec.get("isSidechain") is True:
            continue
        if kind == "queue-operation":
            operation = rec.get("operation")
            if operation == "enqueue":
                queued += 1
            elif operation in ("dequeue", "remove"):
                queued = max(0, queued - 1)
            elif operation == "popAll":
                queued = 0
            continue
        if kind == "system" and rec.get("subtype") == "turn_duration":
            last, queued = (line, rec, "system/turn_duration"), 0
            continue
        if kind not in ("assistant", "user"):
            continue
        last = (line, rec, kind)
        if kind == "assistant":
            message = rec.get("message") if isinstance(rec.get("message"), dict) else {}
            if isinstance(message.get("usage"), dict):
                usage = message["usage"]
            for block in _claude_content(rec):
                if block.get("type") == "tool_use" and _str(block.get("id")):
                    pending[block["id"]] = (line, _str(block.get("name")))
        else:
            for block in _claude_content(rec):
                if block.get("type") == "tool_result":
                    pending.pop(block.get("tool_use_id"), None)
            if _claude_user_kind(rec) != "tool_result" and not rec.get("isMeta"):
                # A later prompt or interrupt proves older unanswered tool_use ids were
                # abandoned (observed: an unanswered AskUserQuestion followed by 33 turns).
                pending.clear()
    if last is None:
        return _status("unknown", ["no_valid_records"])
    reasons = []
    asks = sorted(v for v in pending.values() if v[1] == CLAUDE_ASK_TOOL)
    last_line, last_rec, last_kind = last
    question = asks[-1] if asks else None
    if last_kind == "system/turn_duration":
        if question:
            state = "question"
        elif queued:
            state = "unknown"
            reasons.append("queued_input_pending")
        else:
            state = "idle"
    elif question:
        state = "question"
    elif pending:
        state = "working"
        reasons.append("tool_pending")
    elif last_kind == "user":
        user_kind = _claude_user_kind(last_rec)
        if user_kind == "interrupt":
            state = "unknown"
            reasons.append("interrupt_marker")
        else:
            state = "working"
            reasons.append("user_%s_last" % user_kind)
    else:
        # The last valid record is the last record of its message.id group, so its own
        # stop_reason is the group's (thinking records earlier in a group may carry null).
        message = last_rec.get("message") if isinstance(last_rec.get("message"), dict) else {}
        stop = message.get("stop_reason")
        if stop == "end_turn":
            state = "working"
            reasons.append("end_turn_without_turn_duration")
        else:
            state = "unknown"
            reasons.append("assistant_stop_%s" % (stop if isinstance(stop, str) else "null"))
    if question:
        reasons.append("question_open")
    context = None
    if usage is not None:
        parts = [_number(usage.get(key)) for key in ("input_tokens", "cache_creation_input_tokens",
                                                     "cache_read_input_tokens", "output_tokens")]
        known = [part for part in parts if part is not None]
        context = _context("claude-record", sum(known) if known else None, None)
    return _status(state, reasons, question=question,
                   last_event=_event(last_kind, last_line, last_rec.get("timestamp")),
                   quota=None, context=context)


# ── quiet check ──────────────────────────────────────────────────────────────
def _mtime_ns(result):
    value = getattr(result, "st_mtime_ns", None)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return int(float(result.st_mtime) * 1e9)


def _seconds_ok(value):
    return _number(value) is not None and value >= 0


def quiet_check(path, *, quiet_seconds=30, recheck_seconds=2, stat=os.stat, sleep=time.sleep,
                clock=time.time):
    """ok = last write >= quiet_seconds ago AND two stats >= recheck_seconds apart agree."""
    result = {"ok": False, "age_seconds": 0.0, "stable": False, "size": 0, "mtime_ns": 0,
              "reasons": []}
    try:
        first = stat(path)
    except FileNotFoundError:
        result["reasons"].append("record_missing")
        return result
    except OSError:
        result["reasons"].append("record_stat_failed")
        return result
    first_at = clock()
    size, mtime = int(first.st_size), _mtime_ns(first)
    age = first_at - mtime / 1e9
    result.update(size=size, mtime_ns=mtime, age_seconds=round(age, 3))
    if not (_seconds_ok(quiet_seconds) and _seconds_ok(recheck_seconds)):
        # NaN or a negative value would let every comparison below pass.
        result["reasons"].append("invalid_quiet_parameters")
        return result
    if age < quiet_seconds:
        result["reasons"].append("recent_write")
        return result
    for _ in range(3):
        remaining = recheck_seconds - (clock() - first_at)
        if remaining <= 0:
            break
        sleep(remaining)
    second_at = clock()
    if second_at - first_at < recheck_seconds:
        result["reasons"].append("recheck_interval_short")
        return result
    try:
        second = stat(path)
    except OSError:
        result["reasons"].append("record_vanished")
        return result
    if (int(second.st_size), _mtime_ns(second)) != (size, mtime):
        result["reasons"].append("record_changed")
        return result
    result["stable"] = True
    result["ok"] = True
    return result


# ── assess ───────────────────────────────────────────────────────────────────
def assess(agent, path, *, quiet_seconds=30, recheck_seconds=2, stale_open_turn_seconds=600,
           context_window=None, stat=os.stat, sleep=time.sleep, clock=time.time):
    """Record-first verdict. sendable = idle AND quiet ok AND no question AND no parse error."""
    if agent not in AGENTS:
        raise ValueError("agent must be one of %s" % ", ".join(AGENTS))
    path = os.fspath(path)
    judge = codex_status if agent == "codex" else claude_status
    status, stream, read_reason = None, None, None
    try:
        with open(path, "rb") as handle:
            stream = _LineStream(handle)  # streamed: never the whole file in memory
            status = judge(stream)
    except FileNotFoundError:
        read_reason = "record_missing"
    except OSError:
        read_reason = "record_unreadable"
    errors = stream.errors if stream is not None else []
    if status is None:  # nothing, or only part, of the record was read
        status = judge([])
    quiet = quiet_check(path, quiet_seconds=quiet_seconds, recheck_seconds=recheck_seconds,
                        stat=stat, sleep=sleep, clock=clock)
    state, reasons = status["state"], list(status["reasons"])
    if read_reason:
        state = "unknown"
        reasons.append(read_reason)
    if errors:
        state = "unknown"
        reasons.append("parse_error")
    exists = "record_missing" not in quiet["reasons"] and "record_stat_failed" not in quiet["reasons"]
    if state == "working" and exists and quiet["age_seconds"] > stale_open_turn_seconds:
        state = "unknown"
        reasons.append("open_turn_stale")
    changed = read_reason is None and exists and quiet["size"] != stream.bytes_read
    if changed:
        reasons.append("changed_during_read")
    for reason in quiet["reasons"]:
        if reason not in reasons:
            reasons.append(reason)
    context = status["context"]
    arg_window = context_window if _number(context_window) is not None and context_window > 0 else None
    if context is not None and context["window_tokens"] is None and arg_window is not None:
        # Codex: the record's model_context_window wins; the argument is only a fallback.
        # Claude: the record has no window, so the argument is the only source.
        context = _context(context["source"] + "+window-arg", context["used_tokens"], arg_window)
    sendable = (state == "idle" and quiet["ok"] and not status["question"]["open"]
                and not errors and not read_reason and not changed)
    mtime_utc = mtime_kst = None
    if exists:
        mtime_utc, mtime_kst = _utc_kst(quiet["mtime_ns"] / 1e9)
    return {"agent": agent, "path": path, "state": state, "sendable": bool(sendable),
            "reasons": reasons, "open_turns": status["open_turns"], "question": status["question"],
            "last_event": status["last_event"], "quota": status["quota"], "context": context,
            "record": {"size": quiet["size"], "mtime_utc": mtime_utc, "mtime_kst": mtime_kst,
                       "quiet": quiet}}


def combine_screen(assessment, tui_idle):
    """Screen evidence can only DOWNGRADE: record idle + tui_idle False -> unknown."""
    combined = dict(assessment)
    combined["reasons"] = list(assessment.get("reasons") or [])
    combined["screen"] = {"tui_idle": tui_idle}
    if tui_idle is False and assessment.get("state") == "idle":
        combined["state"] = "unknown"
        combined["sendable"] = False
        combined["reasons"].append("screen_conflict")
    elif tui_idle is False:
        combined["sendable"] = False
    return combined


# ── CLI ──────────────────────────────────────────────────────────────────────
class _UsageError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise _UsageError(message)


def _positive_int(text):
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def _non_negative_float(text):
    value = float(text)
    if not math.isfinite(value) or value < 0:
        raise argparse.ArgumentTypeError("must be a finite number >= 0")
    return value


def _configure_stdio():
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def main(argv=None):
    _configure_stdio()
    parser = _Parser(prog="peer_state.py",
                     description="Read-only record-first state of a Codex/Claude peer session.")
    parser.add_argument("--agent", required=True, choices=AGENTS)
    parser.add_argument("--record", required=True, help="session JSONL record path")
    parser.add_argument("--context-window", type=_positive_int, default=None)
    parser.add_argument("--quiet-seconds", type=_non_negative_float, default=30.0)
    try:
        args = parser.parse_args(argv)
    except _UsageError as exc:
        print("usage error: %s" % exc, file=sys.stderr)
        return 2
    except SystemExit as exc:  # --help
        return exc.code if isinstance(exc.code, int) else 0
    result = assess(args.agent, args.record, quiet_seconds=args.quiet_seconds,
                    context_window=args.context_window)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["sendable"] else 3


if __name__ == "__main__":
    sys.exit(main())
