#!/usr/bin/env python3
"""Read-only scan for agents stuck on one task too long; feeds ai-debate interject.

Reads bounded tails of Codex rollouts, Claude Code transcripts, Grok CLI session
updates and agy (Antigravity CLI) step transcripts. No agent or model is
contacted and nothing is written except an optional snapshot file.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote

KST = timezone(timedelta(hours=9))
CODEX_HEAD = 64 * 1024
CODEX_TAIL = 16 * 1024 * 1024
CLAUDE_TAIL = 8 * 1024 * 1024
GROK_TAIL = 8 * 1024 * 1024
AGY_TAIL = 8 * 1024 * 1024
SIDE_TAIL = 4 * 1024 * 1024  # Grok billing log, agy prompt history
TAIL_STEP = 16 * 1024 * 1024  # grow backwards by this much while the open turn's start is missing
TAIL_CAP = 128 * 1024 * 1024
SNAPSHOT_CHARS = 6000
SNAPSHOT_BYTES = 16000  # stays under debate.py's 16384-byte evidence cap
STALE_MIN = 30
STOP_GRACE_MIN = 5
LOOP_WINDOW_MIN = 60
LOOP_MIN_MESSAGES = 3
GOAL_LONG_MIN = 120
RECENT_HOURS = 3
DUP_SECONDS = 2
MID_TURN_SECONDS = 5  # the message that opened the turn is not feedback on that turn
LOOP_RE = re.compile(r"HOLD|NO-GO|보류|재판정|재확인")
FRUSTRATION_RE = re.compile(r"오래 ?걸|왜 이렇게|언제 끝|답답|too long|taking forever", re.I)
STOP_RE = re.compile(r"멈춰|멈추고|그만해|그만(?!큼)|\bstop(?: it| now)?\b|중단", re.I)
NOT_HUMAN = ("# AGENTS.md", "<heartbeat", "<user_instructions", "<environment_context", "<permissions",
             "<codex_internal_context", "<turn_aborted", "<in-app-browser-context", "<task-notification",
             "<local-command", "<command-name", "<command-message", "<bash-")
AMBIENT_RE = re.compile(r"<in-app-browser-context\b.*?</in-app-browser-context>", re.S)
GOAL_BLOCK_RE = re.compile(r'<codex_internal_context source="goal">.*?<objective>(.*?)</objective>', re.S)
GOAL_HINT_RE = re.compile(r'(timeUsedSeconds|createdAt)"?\s*[:=]\s*"?(\d+(?:\.\d+)?)')
INTERRUPTED = "[Request interrupted by user"
GOAL_SEEN = "goal turns in read window (lower bound)"
MASK = "[REDACTED]"
# agy cuts long prompts (truncated_fields) before the closing tag, so the end of the text also closes it.
USER_REQUEST_RE = re.compile(r"<USER_REQUEST>\s*(.*?)\s*(?:</USER_REQUEST>|\Z)", re.S)
GROK_GLOB = "*/*/updates.jsonl"  # <urlencoded cwd>/<session id>/updates.jsonl
AGY_GLOB = "*/.system_generated/logs/transcript.jsonl"  # <conversation id>/...
# Grok records that only happen inside a running turn, and the ones that end it.
GROK_ACTIVITY = frozenset({"agent_message_chunk", "agent_thought_chunk", "tool_call", "tool_call_update", "plan",
                           "hook:pre_tool_use", "hook:post_tool_use"})
GROK_TURN_END = frozenset({"turn_completed", "hook:stop", "hook:stop_failure", "hook:session_end"})
SECRET_RES = [re.compile(p) for p in (
    r"(?<![\w-])sk-ant-[\w-]{20,}", r"(?<![\w-])sk-[\w-]{20,}", r"(?<![\w-])gh[pousr]_\w{30,}",
    r"(?<![\w-])xai-[\w-]{20,}", r"(?<![\w-])AIza[\w-]{30,}", r"Bearer\s+\S{20,}")]
SECRET_KV_RE = re.compile(r"(?i)(api[_-]?key|token|secret|password)([\"']?\s*[=:]\s*)(?!\[REDACTED\])(\S+)")


def parse_iso(value):
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    moment = datetime.fromisoformat(text)
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def now():
    raw = os.environ.get("AI_DEBATE_NOW")
    return parse_iso(raw) if raw else datetime.now(timezone.utc)


def stamp_of(record):
    try:
        return parse_iso(record.get("timestamp"))
    except (TypeError, ValueError):
        return None


def from_epoch(value):
    try:
        return datetime.fromtimestamp(float(value), timezone.utc) if value else None
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def number(value):
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def kst(moment, short=False):
    if not moment:
        return "?"
    return moment.astimezone(KST).strftime("%m-%d %H:%M KST" if short else "%Y-%m-%d %H:%M KST")


def redact(text):
    """Mask API keys and tokens; returns (text, number of masked spans)."""
    count = 0
    for pattern in SECRET_RES:
        text, n = pattern.subn(MASK, text)
        count += n
    text, n = SECRET_KV_RE.subn(lambda m: m.group(1) + m.group(2) + MASK, text)
    return text, count + n


def json_lines(data):
    records = []
    for line in data.split(b"\n"):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


class Window:
    """Parsed tail of a JSONL file that can grow backwards, never past TAIL_CAP bytes."""

    def __init__(self, path, first):
        self.path = path
        with open(path, "rb") as stream:
            stream.seek(0, 2)
            self.size = stream.tell()
        self.begin, self.capped, self.records = self.size, False, []
        self.grow(first)

    @property
    def truncated(self):
        return self.begin > 0

    def grow(self, step=None):
        step = step or TAIL_STEP
        floor = max(0, self.size - TAIL_CAP)
        while self.begin > 0 and not self.capped:
            start = max(floor, self.begin - step)
            self.capped = start == floor > 0
            with open(self.path, "rb") as stream:
                stream.seek(start)
                data = stream.read(self.begin - start)
            if start > 0:  # drop the partial first line; the next chunk re-reads it whole
                cut = data.find(b"\n")
                if cut < 0 or cut == len(data) - 1:  # one line longer than the chunk
                    step += TAIL_STEP
                    continue
                data, start = data[cut + 1:], start + cut + 1
            self.records[:0] = json_lines(data)
            self.begin = start
            return True
        return False


def as_text(value):
    return value if isinstance(value, str) else parts_text(value)


def parts_text(content):
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return "\n".join(p["text"] for p in content
                     if isinstance(p, dict) and isinstance(p.get("text"), str))


def clip(text, cap):
    flat = re.sub(r"\s+", " ", text or "").strip()
    return flat if len(flat) <= cap else flat[:cap - 1].rstrip() + "…"


def own_words(text):
    """Drop quoted lines (an answer quoting the agent's question) before keyword checks."""
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(">"))


def human_text(text):
    if not isinstance(text, str):
        return None
    text = AMBIENT_RE.sub("", text).strip()
    if not text or text.startswith(NOT_HUMAN):
        return None
    return text


class Session:
    def __init__(self, agent, path):
        self.agent, self.path = agent, Path(path)
        self.session_id = self.cwd = self.goal = self.goal_state = None
        self.status, self.reason = "ok", ""
        self.events = []  # (kind, timestamp, text, turn_id) with kind user | agent
        self.turn_open, self.turn_start = False, None
        self.start_before_tail = self.unresolved = False
        self.turns = {}
        self.limits = self.billing = self.model = None
        self.mtime = self.first_seen = self.last_seen = None

    def seen(self, moment):
        if moment:
            self.first_seen = min(self.first_seen or moment, moment)
            self.last_seen = max(self.last_seen or moment, moment)
        return moment

    def add(self, kind, moment, text, turn=None):
        if not isinstance(text, str) or not text.strip():
            return
        text = text.strip()
        for prev in self.events[-6:]:
            if prev[0] != kind or prev[2] != text:
                continue
            if turn and prev[3] == turn:
                return
            if moment and prev[1] and abs((moment - prev[1]).total_seconds()) <= DUP_SECONDS:
                return  # one message logged by several record types
        self.events.append((kind, moment, text, turn))

    def add_human(self, moment, text, turn=None):
        text = human_text(text)
        if text:
            self.add("user", moment, text, turn)

    def users(self):
        return [e for e in self.events if e[0] == "user"]

    def agents(self):
        return [e for e in self.events if e[0] == "agent"]


def wants_more(session, deep):
    if session.unresolved:
        return True
    if not (deep or session.turn_open):
        return False
    if len(session.users()) < 3:
        return True
    minutes, basis = goal_age(session, session.last_seen) if session.last_seen else (None, None)
    return basis == GOAL_SEEN and minutes < GOAL_LONG_MIN  # older goal turns may sit before the window


def load(path, first, read, deep):
    window = Window(path, first)
    while True:
        session = read(path, window)
        if not (window.truncated and wants_more(session, deep) and window.grow()):
            return session


def codex_meta(path):
    with open(path, "rb") as stream:
        head = stream.read(CODEX_HEAD)
    first = head.split(b"\n", 1)[0]
    try:
        record = json.loads(first)
        if isinstance(record, dict) and record.get("type") == "session_meta":
            payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
            return {k: payload.get(k) for k in ("id", "cwd", "forked_from_id", "thread_source")}
    except ValueError:
        pass
    found = {}
    for key in ("id", "cwd", "forked_from_id", "thread_source"):
        match = re.search(rb'"%s"\s*:\s*"((?:[^"\\]|\\.)*)"' % key.encode(), head)
        if match:
            try:
                found[key] = json.loads(b'"' + match.group(1) + b'"')
            except ValueError:
                found[key] = match.group(1).decode("utf-8", "replace")
    return found


def norm(text):
    return re.sub(r"\s+", " ", text or "").strip()


def goal_from_update(goal, data, moment):
    objective = norm(data.get("objective")) if isinstance(data.get("objective"), str) else ""
    same = goal is not None and (not objective or goal["objective"] == objective)
    return {"objective": objective or (goal or {}).get("objective") or "", "status": data.get("status"),
            "used": number(data.get("timeUsedSeconds")), "created": from_epoch(data.get("createdAt")),
            "updated": from_epoch(data.get("updatedAt")) or moment, "turns": goal["turns"] if same else set()}


def goal_from_block(goal, text, objective, moment, turn):
    objective = norm(objective)
    if goal is None or goal["objective"] != objective:
        goal = {"objective": objective, "used": None, "created": None, "updated": None, "turns": set()}
    goal["status"] = "active"  # a goal continuation turn only runs for an active goal
    for key, value in GOAL_HINT_RE.findall(text):
        if key == "timeUsedSeconds":
            goal["used"], goal["updated"] = float(value), moment
        else:
            goal["created"] = from_epoch(value)
    if turn:
        goal["turns"].add(turn)
    return goal


def read_codex(path, window, info):
    session = Session("codex", path)
    session.session_id, session.cwd = info.get("id"), info.get("cwd")
    turns, latest, goal = {}, None, None
    for record in window.records:
        kind, payload = record.get("type"), record.get("payload")
        if not isinstance(payload, dict):
            continue
        moment = session.seen(stamp_of(record))
        ptype, turn = payload.get("type"), payload.get("turn_id")
        turn = turn if isinstance(turn, str) else None
        if kind == "event_msg" and ptype == "task_started":
            turns[turn] = {"start": from_epoch(payload.get("started_at")) or moment, "end": None}
            latest = turn
            continue
        if kind == "event_msg" and ptype in ("task_complete", "turn_aborted"):
            turns.setdefault(turn, {"start": None, "end": None})["end"] = moment or True
            continue
        if turn and turn not in turns:
            turns[turn] = {"start": None, "end": None}  # began before the window
        if kind == "event_msg":
            if ptype == "user_message":
                session.add_human(moment, as_text(payload.get("message")), turn)
            elif ptype == "agent_message":
                session.add("agent", moment, as_text(payload.get("message")), turn)
            elif ptype == "item_completed":
                item = payload.get("item") if isinstance(payload.get("item"), dict) else {}
                if item.get("type") == "UserMessage":
                    session.add_human(moment, parts_text(item.get("content")), turn)
                elif item.get("type") == "AgentMessage":
                    session.add("agent", moment, parts_text(item.get("content")), turn)
            elif ptype == "token_count" and isinstance(payload.get("rate_limits"), dict):
                session.limits = payload["rate_limits"]
            elif ptype == "thread_goal_updated" and isinstance(payload.get("goal"), dict):
                goal = goal_from_update(goal, payload["goal"], moment)
        elif kind == "response_item" and ptype == "message":
            text = parts_text(payload.get("content"))
            if payload.get("role") == "user":
                block = GOAL_BLOCK_RE.search(text)
                if block:
                    goal = goal_from_block(goal, text, block.group(1), moment, latest)
                else:
                    session.add_human(moment, text)
            elif payload.get("role") == "assistant":
                session.add("agent", moment, text)
    still_open = [t for t in turns.values() if t["end"] is None]
    starts = [t["start"] for t in still_open if t["start"]]
    startless = window.truncated and any(t["start"] is None for t in still_open)
    session.turn_open = bool(starts) or startless
    session.unresolved = window.truncated and (startless or not turns)
    if startless:
        session.start_before_tail, session.turn_start = True, session.first_seen
    elif starts:
        session.turn_start = min(starts)
    session.turns, session.goal_state = turns, goal
    if goal and goal["objective"]:
        session.goal = goal["objective"]
    elif session.users():
        session.goal = session.users()[-1][2]
    return session


def parse_codex(path, deep=False):
    info = codex_meta(path)
    if info.get("forked_from_id") or info.get("thread_source") == "subagent":
        session = Session("codex", path)
        session.session_id, session.cwd = info.get("id"), info.get("cwd")
        session.status, session.reason = "unknown", "fork or subagent session (parent owns the turn)"
        return session
    return load(path, CODEX_TAIL, lambda p, w: read_codex(p, w, info), deep)


def read_claude(path, window):
    session = Session("claude", path)
    title, start, known, prompt_at = None, None, False, None
    opened = ended = False
    for record in window.records:
        if record.get("isSidechain"):
            continue
        if isinstance(record.get("sessionId"), str):
            session.session_id = record["sessionId"]
        if isinstance(record.get("cwd"), str):
            session.cwd = record["cwd"]
        kind = record.get("type")
        moment = session.seen(stamp_of(record))
        message = record.get("message") if isinstance(record.get("message"), dict) else {}
        if kind == "ai-title":
            title = record.get("aiTitle") if isinstance(record.get("aiTitle"), str) else title
        elif kind == "system" and record.get("subtype") == "turn_duration":
            opened, ended, prompt_at = False, True, None
        elif kind == "assistant":
            if not opened and (prompt_at or (window.truncated and not ended)):
                opened, start, known = True, prompt_at, ended or not window.truncated
            prompt_at = None
            if message.get("stop_reason") not in (None, "tool_use"):
                opened, ended = False, True
            session.add("agent", moment, parts_text(message.get("content")))
        elif kind == "attachment":
            item = record.get("attachment") if isinstance(record.get("attachment"), dict) else {}
            origin = item.get("origin") if isinstance(item.get("origin"), dict) else {}
            if item.get("type") == "queued_command" and origin.get("kind") == "human":
                session.add_human(moment, item.get("prompt"))  # typed while the turn was running
        elif kind == "user" and not record.get("isCompactSummary"):
            content = message.get("content")
            if isinstance(content, list) and any(isinstance(p, dict) and p.get("type") == "tool_result"
                                                 for p in content):
                continue
            text = parts_text(content).strip()
            if not text or text.startswith("<local-command"):
                continue
            if text.startswith(INTERRUPTED):
                opened, ended, prompt_at = False, True, None
                continue
            if record.get("isMeta") or text.startswith(("<command-", "<bash-")):
                if not opened:
                    prompt_at = prompt_at or moment  # opens a turn only if the model answers
                continue
            if not opened:
                opened, start, known, prompt_at = True, moment, ended or not window.truncated, None
            session.add_human(moment, text)
    session.turn_open = opened
    if opened and not known:
        session.unresolved = session.start_before_tail = True
        session.turn_start = session.first_seen
    elif opened:
        session.turn_start = start
    session.goal = title or (session.users()[-1][2] if session.users() else None)
    return session


def parse_claude(path, deep=False):
    return load(path, CLAUDE_TAIL, read_claude, deep)


_SIDE_CACHE = {}


def side_lines(path):
    """Bounded tail of a small side file (billing log, prompt history), re-read only when it changes."""
    path = Path(path)
    try:
        info = path.stat()
    except OSError:
        return []
    key = (info.st_mtime_ns, info.st_size)
    cached = _SIDE_CACHE.get(str(path))
    if cached and cached[0] == key:
        return cached[1]
    with open(path, "rb") as stream:
        stream.seek(max(0, info.st_size - SIDE_TAIL))
        data = stream.read(SIDE_TAIL)
    if info.st_size > SIDE_TAIL:
        data = data.split(b"\n", 1)[-1]  # drop the partial first line
    lines = data.split(b"\n")
    _SIDE_CACHE[str(path)] = (key, lines)
    return lines


def grok_billing():
    """Latest Grok 'billing: fetched credits config' line: used percent and period end, or None."""
    home = Path(os.environ.get("GROK_HOME") or Path.home() / ".grok")
    log = Path(os.environ.get("AI_DEBATE_GROK_LOG") or home / "logs" / "unified.jsonl")
    for line in reversed(side_lines(log)):
        if b"billing: fetched credits config" not in line:
            continue
        try:
            record = json.loads(line)
            config = record["ctx"]["config"]
            used = float(config["creditUsagePercent"])
        except (ValueError, KeyError, TypeError):
            continue
        end = (config.get("currentPeriod") or {}).get("end") or config.get("billingPeriodEnd")
        try:
            reset = parse_iso(end) if end else None
        except (TypeError, ValueError):
            reset = None
        return {"used_percent": used, "reset": reset, "observed": record.get("ts"), "source": log.as_posix()}
    return None


def grok_info(path):
    folder = Path(path).parent
    try:
        with open(folder / "summary.json", "rb") as stream:
            summary = json.loads(stream.read(256 * 1024))
    except (OSError, ValueError):
        summary = {}
    summary = summary if isinstance(summary, dict) else {}
    info = summary.get("info") if isinstance(summary.get("info"), dict) else {}
    title = next((summary[k] for k in ("generated_title", "session_summary")
                  if isinstance(summary.get(k), str) and summary[k].strip()), None)
    model = " · ".join(str(summary[k]) for k in ("current_model_id", "reasoning_effort") if summary.get(k))
    return {"id": info.get("id") or folder.name, "cwd": info.get("cwd") or unquote(folder.parent.name),
            "title": title, "model": model or None}


def grok_moment(record, meta):
    stamp_ms = number(meta.get("agentTimestampMs"))
    return from_epoch(stamp_ms / 1000.0) if stamp_ms else from_epoch(number(record.get("timestamp")))


def read_grok(path, window, info):
    """Grok updates.jsonl: user_message_chunk opens a turn, turn_completed (or a stop/session_end hook) ends it."""
    session = Session("grok", path)
    session.session_id, session.cwd, session.model = info.get("id"), info.get("cwd"), info.get("model")
    opened = ended = known = False
    start = prompt = None
    begun = {}  # promptId -> earliest turnStartMs, which survives when the opening record is cut off
    user_parts, agent_parts = [], []

    def flush(parts, kind):
        if parts:
            if kind == "user":
                session.add_human(parts[0][0], "".join(t for _m, t in parts))
            else:
                session.add("agent", parts[0][0], "".join(t for _m, t in parts))
            parts.clear()

    for record in window.records:
        params = record.get("params") if isinstance(record.get("params"), dict) else {}
        update = params.get("update") if isinstance(params.get("update"), dict) else {}
        meta = params.get("_meta") if isinstance(params.get("_meta"), dict) else {}
        kind = update.get("sessionUpdate")
        if not isinstance(kind, str):
            continue
        if kind == "hook_execution":
            kind = "hook:%s" % update.get("event_name")
        moment = session.seen(grok_moment(record, meta))
        pid = meta.get("promptId") or update.get("prompt_id")
        pid = pid if isinstance(pid, str) else None
        turn_ms = number(meta.get("turnStartMs"))
        if pid and turn_ms:
            begun[pid] = min(begun.get(pid, turn_ms), turn_ms)
        content = update.get("content") if isinstance(update.get("content"), dict) else {}
        text = content.get("text") if isinstance(content.get("text"), str) else None
        if kind != "user_message_chunk":
            flush(user_parts, "user")
        if kind not in ("agent_message_chunk", "agent_thought_chunk"):
            flush(agent_parts, "agent")
        if kind == "user_message_chunk":
            if not opened:
                opened, start, known, prompt = True, moment, True, None
            if text:
                user_parts.append((moment, text))
        elif kind in GROK_TURN_END:
            opened, ended, start, prompt = False, True, None, None
        elif kind in GROK_ACTIVITY:
            if not opened:  # woken by a background task, or the turn began before the window
                opened, known = True, ended or not window.truncated
                start = moment if known else None
            if kind == "agent_message_chunk" and text:
                agent_parts.append((moment, text))
        if opened and pid:
            prompt = pid
    flush(user_parts, "user")
    flush(agent_parts, "agent")
    session.turn_open = opened
    if opened and not known and begun.get(prompt):
        start, known = from_epoch(begun[prompt] / 1000.0), True
    if opened and known and start:
        session.turn_start = start
    elif opened:
        session.unresolved = session.start_before_tail = True
        session.turn_start = session.first_seen
    session.goal = info.get("title") or (session.users()[-1][2] if session.users() else None)
    return session


def parse_grok(path, deep=False):
    info = grok_info(path)
    session = load(path, GROK_TAIL, lambda p, w: read_grok(p, w, info), deep)
    session.billing = grok_billing()
    return session


def agy_workspace(history, conversation):
    """Latest workspace that agy's prompt history recorded for this conversation, or None."""
    for line in reversed(side_lines(history)):
        if conversation.encode("utf-8") not in line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if not isinstance(record, dict) or record.get("conversationId") != conversation:
            continue
        if isinstance(record.get("workspace"), str):
            return record["workspace"]
    return None


def agy_info(path):
    path = Path(path)  # <brain>/<conversation>/.system_generated/logs/transcript.jsonl
    full = path.absolute()
    parents = full.parents
    if len(parents) >= 4 and parents[0].name == "logs" and parents[1].name == ".system_generated":
        conversation, brain = parents[2].name, parents[3]
        return {"id": conversation, "cwd": agy_workspace(brain.parent / "history.jsonl", conversation)}
    # A copied or shallow transcript: no brain layout, so no workspace lookup.
    return {"id": full.parent.name or None, "cwd": None}


def created_at(record):
    try:
        return parse_iso(record.get("created_at"))
    except (TypeError, ValueError):
        return None


def agy_request(text):
    if not isinstance(text, str):
        return None
    match = USER_REQUEST_RE.search(text)
    return match.group(1) if match else text


def read_agy(path, window, info):
    """agy steps: USER_INPUT opens a turn; a DONE PLANNER_RESPONSE without tool calls is the final answer."""
    session = Session("agy", path)
    session.session_id, session.cwd = info.get("id"), info.get("cwd")
    opened = ended = known = False
    start = None
    for record in window.records:
        kind, status = record.get("type"), record.get("status")
        moment = session.seen(created_at(record))
        content = record.get("content") if isinstance(record.get("content"), str) else None
        if kind == "USER_INPUT":
            if not opened:
                opened, start, known = True, moment, True
            session.add_human(moment, agy_request(content))
            continue
        final = kind == "PLANNER_RESPONSE" and status == "DONE" and not record.get("tool_calls")
        if not opened and not final:  # a system message (task notice) or a turn begun before the window
            opened, known = True, ended or not window.truncated
            start = moment if known else None
        if kind == "PLANNER_RESPONSE" and content:
            session.add("agent", moment, content)
        if final:
            opened, ended = False, True
    session.turn_open = opened
    if opened and known and start:
        session.turn_start = start
    elif opened:
        session.unresolved = session.start_before_tail = True
        session.turn_start = session.first_seen
    session.goal = session.users()[-1][2] if session.users() else None
    return session


def parse_agy(path, deep=False):
    info = agy_info(path)
    return load(path, AGY_TAIL, lambda p, w: read_agy(p, w, info), deep)


def quota_windows(limits, current):
    rows = []
    for name in ("primary", "secondary"):
        window = (limits or {}).get(name)
        if isinstance(window, dict) and isinstance(window.get("used_percent"), (int, float)):
            reset = from_epoch(window.get("resets_at"))
            if reset is None or reset > current:
                rows.append((name, float(window["used_percent"]), reset))
    return rows


def spent_quota(session, current):
    """Windows at 100% with a future reset: Codex rate limits or the Grok billing line (no evidence elsewhere)."""
    if session.agent == "codex":
        return [w for w in quota_windows(session.limits, current) if w[1] >= 100]
    billing = session.billing if session.agent == "grok" else None
    if billing and billing["used_percent"] >= 100 and (billing["reset"] is None or billing["reset"] > current):
        return [("credits", billing["used_percent"], billing["reset"])]
    return []


def covered_seconds(spans, since=None):
    total, reach = 0.0, since
    for start, end in sorted(spans):
        start = max(start, reach) if reach else start
        if end > start:
            total += (end - start).total_seconds()
            reach = end
    return total


def goal_age(session, current):
    """Minutes an active Codex thread goal has been worked on, and the evidence used."""
    goal = session.goal_state
    if not goal or goal.get("status") != "active":
        return None, None
    spans = []
    for turn in goal["turns"]:
        info = session.turns.get(turn) or {}
        end = current if info.get("end") is None else info.get("end")
        if info.get("start") and isinstance(end, datetime):
            spans.append((info["start"], end))
    if goal["used"] is not None:
        return (goal["used"] + covered_seconds(spans, goal["updated"])) / 60, "timeUsedSeconds"
    if goal["created"]:
        return (current - goal["created"]).total_seconds() / 60, "createdAt"
    if spans:
        return covered_seconds(spans) / 60, GOAL_SEEN
    return None, None


def evaluate(session, current, threshold):
    try:
        session.mtime = datetime.fromtimestamp(session.path.stat().st_mtime, timezone.utc)
    except OSError:
        session.mtime = None
    latest = max([m for m in (session.mtime, session.last_seen) if m], default=None)
    idle = (current - latest).total_seconds() / 60 if latest else None
    status, reason = session.status, session.reason
    if status == "ok" and session.turn_open and idle is not None and idle >= STALE_MIN:
        status = "stale"
        reason = "no records for %d min with a turn open (dead, interrupted or waiting)" % idle
    elapsed = None
    if session.turn_open and session.turn_start:
        elapsed = (current - session.turn_start).total_seconds() / 60
    humans = session.users()
    last = humans[-1] if humans else None
    stopped = bool(last and STOP_RE.search(own_words(last[2])))
    opened_at = session.turn_start + timedelta(seconds=MID_TURN_SECONDS) if session.turn_start else None
    goal_minutes, goal_basis = goal_age(session, current) if session.agent == "codex" else (None, None)
    triggers, detail, note = [], {}, ""
    if status == "ok" and session.turn_open:
        if elapsed is not None and elapsed >= threshold:
            triggers.append("T1_LONG_TURN")
        since = current - timedelta(minutes=LOOP_WINDOW_MIN)
        since = max(since, session.turn_start) if session.turn_start else since
        loops = [e for e in session.agents() if e[1] and e[1] >= since and LOOP_RE.search(e[2])]
        if len(loops) >= LOOP_MIN_MESSAGES:
            triggers.append("T2_LOOP")
            detail["loop_matches"] = len(loops)
        mid_turn = [e for e in humans[-3:] if e[1] and opened_at and e[1] > opened_at
                    and current - e[1] <= timedelta(hours=RECENT_HOURS)]
        if stopped:
            waited = (current - last[1]).total_seconds() / 60 if last[1] else None
            if last in mid_turn and waited is not None and waited >= STOP_GRACE_MIN:
                triggers.append("T4_IGNORED_STOP")
                detail["stop_ignored_min"] = round(waited, 1)
        elif any(FRUSTRATION_RE.search(own_words(e[2])) for e in mid_turn):
            triggers.append("T3_USER_FRUSTRATION")
        spent = spent_quota(session, current)
        if spent:
            triggers.append("T5_QUOTA")
            detail["quota"] = {w[0]: {"used_percent": w[1], "resets_kst": kst(w[2])} for w in spent}
        if goal_minutes is not None and goal_minutes >= GOAL_LONG_MIN:
            triggers.append("T6_GOAL_LONG")
    if stopped and (not session.turn_open or status == "stale"):
        note = "user already stopped it"
    goal, hidden_goal = redact(session.goal or "")
    last_text, hidden_last = redact(last[2] if last else "")
    return {"agent": session.agent, "file": session.path.as_posix(), "session_id": session.session_id,
            "cwd": session.cwd, "status": status, "reason": reason,
            "goal": clip(goal, 160) if session.goal else None,
            "turn_open": session.turn_open,
            "elapsed_min": round(elapsed, 1) if elapsed is not None else None,
            "elapsed_lower_bound": session.start_before_tail and elapsed is not None,
            "start_before_tail": session.start_before_tail,
            "idle_min": round(idle, 1) if idle is not None else None,
            "goal_minutes": round(goal_minutes, 1) if goal_minutes is not None else None,
            "goal_basis": goal_basis,
            "triggers": triggers, "detail": detail, "note": note,
            "last_user_text": clip(last_text, 120), "redacted": hidden_goal + hidden_last,
            "recommendation": "ai-debate interject" if triggers else ""}


def recent_files(root, pattern_ok, hours, current):
    cutoff = (current - timedelta(hours=hours)).timestamp()
    found = []
    if not root or not Path(root).is_dir():
        return found
    for dirpath, _dirs, names in os.walk(root):
        if "subagents" in Path(dirpath).parts:
            continue
        for name in names:
            path = Path(dirpath) / name
            if not pattern_ok(path, root):
                continue
            try:
                if path.stat().st_mtime >= cutoff:
                    found.append(path)
            except OSError:
                continue
    return sorted(found)


def codex_ok(path, _root):
    return path.name.startswith("rollout-") and path.suffix == ".jsonl"


def claude_ok(path, root):
    # ~/.claude/projects/<project>/<session>.jsonl only; deeper files are subagents.
    return path.suffix == ".jsonl" and path.parent.parent == Path(root)


def recent_matches(root, pattern, hours, current):
    """Files at a fixed depth under root (Grok and agy layouts) modified in the last `hours`."""
    cutoff = (current - timedelta(hours=hours)).timestamp()
    if not root or not Path(root).is_dir():
        return []
    found = []
    for path in Path(root).glob(pattern):
        try:
            if path.is_file() and path.stat().st_mtime >= cutoff:
                found.append(path)
        except OSError:
            continue
    return sorted(found)


def default_roots():
    """codex, claude, grok, agy session roots; AI_DEBATE_* overrides match debate.py's host-session proof."""
    home = Path.home()
    codex = Path(os.environ.get("CODEX_HOME") or home / ".codex") / "sessions"
    claude = Path(os.environ.get("CLAUDE_CONFIG_DIR") or home / ".claude") / "projects"
    grok = Path(os.environ.get("GROK_HOME") or home / ".grok") / "sessions"
    agy = home / ".gemini" / "antigravity-cli" / "brain"
    return (Path(os.environ.get("AI_DEBATE_CODEX_SESSIONS") or codex),
            Path(os.environ.get("AI_DEBATE_CLAUDE_PROJECTS") or claude),
            Path(os.environ.get("AI_DEBATE_GROK_SESSIONS") or grok),
            Path(os.environ.get("AI_DEBATE_AGY_BRAIN") or agy))


def elapsed_label(row):
    if row.get("elapsed_min") is None:
        return "-"
    return (">=" if row.get("elapsed_lower_bound") else "") + "%s" % row["elapsed_min"]


def scan(args):
    current = now()
    _SIDE_CACHE.clear()
    defaults = dict(zip(("codex", "claude", "grok", "agy"), default_roots()))
    roots = {agent: Path(getattr(args, agent + "_root") or defaults[agent]) for agent in defaults}
    sources = (("codex", lambda r: recent_files(r, codex_ok, args.hours, current), parse_codex),
               ("claude", lambda r: recent_files(r, claude_ok, args.hours, current), parse_claude),
               ("grok", lambda r: recent_matches(r, GROK_GLOB, args.hours, current), parse_grok),
               ("agy", lambda r: recent_matches(r, AGY_GLOB, args.hours, current), parse_agy))
    rows = []
    for agent, find, parse in sources:
        for path in find(roots[agent]):
            try:
                rows.append(evaluate(parse(path), current, args.threshold_min))
            except Exception as exc:  # one unreadable or drifted transcript must not hide the rest
                rows.append({"agent": agent, "file": path.as_posix(), "status": "unknown",
                             "reason": "unreadable", "error": redact("%s: %s" % (type(exc).__name__, exc))[0][:300],
                             "triggers": [], "recommendation": ""})
    triggered = [r for r in rows if r.get("triggers")]
    result = {"scanned_at": current.astimezone(KST).isoformat(timespec="seconds"),
              "hours": args.hours, "threshold_min": args.threshold_min,
              "roots": {agent: root.as_posix() for agent, root in roots.items()},
              "sessions": rows, "triggered": len(triggered)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        errors = sum(1 for r in rows if r.get("error"))
        print("scanned %d sessions (last %gh), %d triggered%s" % (
            len(rows), args.hours, len(triggered), ", %d unreadable" % errors if errors else ""))
        for row in rows:
            if not row.get("triggers") and not (row.get("status") == "ok" and row.get("turn_open")):
                continue
            print("- %s %s open=%s elapsed=%s min %s" % (
                row["agent"], row.get("session_id"), row.get("turn_open"), elapsed_label(row),
                ",".join(row.get("triggers") or []) or "-"))
            print("    goal: %s" % (row.get("goal") or "-"))
            print("    last user: %s" % (row.get("last_user_text") or "-"))
            if row.get("recommendation"):
                print("    -> %s (snapshot --file \"%s\")" % (row["recommendation"], row["file"]))
    return 10 if args.fail_on_trigger and triggered else 0


def fit_snapshot(text):
    if len(text) <= SNAPSHOT_CHARS and len(text.encode("utf-8")) <= SNAPSHOT_BYTES:
        return text
    keep = min(len(text), SNAPSHOT_CHARS - 40)
    while keep > 0 and len(text[:keep].encode("utf-8")) > SNAPSHOT_BYTES - 80:
        keep -= 200
    keep = max(0, keep)
    return text[:keep].rstrip() + "\n[... %d자 생략]\n" % (len(text) - keep)


def snapshot_text(session, row, current, user_cap, agent_cap):
    """Snapshot markdown with secrets masked before clipping; returns (text, masked count)."""
    hidden = [0]

    def safe(text, cap):
        masked, count = redact(text or "")
        hidden[0] += count
        return clip(masked, cap)

    lines = ["# 작업 중 에이전트 스냅숏",
             "- 에이전트: %s · 세션: %s · cwd: %s" % (session.agent, session.session_id or "?",
                                                  session.cwd or "?"),
             "- 파일: %s" % session.path.as_posix(),
             "- 목표: %s" % (safe(session.goal, 400) if session.goal else "(확인 불가)")]
    if session.model:
        lines.append("- 모델: %s" % session.model)
    if session.turn_open:
        lines.append("- 진행: 턴 열림 · %s분 경과%s · 마지막 기록 %s분 전" % (
            elapsed_label(row), " (시작 기록이 읽은 범위 밖, 하한값)" if row["elapsed_lower_bound"] else "",
            row["idle_min"]))
    else:
        lines.append("- 진행: 열린 턴 없음 · 마지막 기록 %s분 전" % row["idle_min"])
    if row["status"] != "ok":
        lines.append("- 상태: %s · %s" % (row["status"], row["reason"]))
    if row["note"]:
        lines.append("- 참고: 마지막 사용자 메시지가 중지 요청 (%s)" % row["note"])
    if row["goal_minutes"] is not None:
        lines.append("- 목표 진행: %s분 (%s)" % (row["goal_minutes"], row["goal_basis"]))
    if session.agent == "codex" and session.limits:
        windows = quota_windows(session.limits, current)
        credits = (session.limits.get("credits") or {}).get("has_credits") is True
        quota = ", ".join("%s %g%% (~%s 리셋)" % (n, u, kst(r)) for n, u, r in windows) or "근거 없음"
        lines.append("- 쿼터: %s%s" % (quota, " · 구매 크레딧 보유(소진 후 과금 위험)" if credits else ""))
    elif session.agent == "grok" and session.billing:
        lines.append("- 쿼터: Grok credits %g%% (~%s 리셋, %s)" % (
            session.billing["used_percent"], kst(session.billing["reset"]), session.billing["source"]))
    lines.append("- 트리거: %s" % (", ".join(row["triggers"]) or "없음"))
    lines.append("- 스냅숏 시각: %s" % kst(current))
    lines += ["", "## 최근 사용자 메시지 (최대 3)"]
    users = session.users()[-3:]
    lines += ["%d. [%s] %s" % (i, kst(e[1], True), safe(e[2], user_cap)) for i, e in enumerate(users, 1)] \
        or ["(없음)"]
    lines += ["", "## 최근 에이전트 메시지 (최대 8, 요약)"]
    agents = session.agents()[-8:]
    lines += ["%d. [%s] %s" % (i, kst(e[1], True), safe(e[2], agent_cap)) for i, e in enumerate(agents, 1)] \
        or ["(없음)"]
    text, count = redact("\n".join(lines) + "\n")
    return text, hidden[0] + count


def snapshot(args):
    path = Path(args.file)
    _SIDE_CACHE.clear()
    with open(path, "rb") as stream:
        head = stream.read(4096)
    if path.name == "updates.jsonl":
        session = parse_grok(path, deep=True)
    elif path.name == "transcript.jsonl":
        session = parse_agy(path, deep=True)
    elif path.name.startswith("rollout-") or b'"type":"session_meta"' in head:
        session = parse_codex(path, deep=True)
    else:
        session = parse_claude(path, deep=True)
    current = now()
    row = evaluate(session, current, args.threshold_min)
    text, hidden = "", 0
    for user_cap, agent_cap in ((600, 450), (300, 220), (160, 110)):
        text, hidden = snapshot_text(session, row, current, user_cap, agent_cap)
        if len(text) <= SNAPSHOT_CHARS and len(text.encode("utf-8")) <= SNAPSHOT_BYTES:
            break
    text = fit_snapshot(text)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(text.encode("utf-8"))
        print(json.dumps({"out": out.as_posix(), "chars": len(text), "bytes": len(text.encode("utf-8")),
                          "triggers": row["triggers"], "status": row["status"], "redacted": hidden},
                         ensure_ascii=False))
    else:
        print(text, end="")
        if hidden:
            print(json.dumps({"redacted": hidden}), file=sys.stderr)
    return 0


def parser():
    top = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = top.add_subparsers(dest="command", required=True)
    p = sub.add_parser("scan", help="list long-running agent turns and triggers")
    p.add_argument("--hours", type=float, default=12)
    p.add_argument("--threshold-min", type=float, default=45)
    p.add_argument("--json", action="store_true")
    p.add_argument("--codex-root")
    p.add_argument("--claude-root")
    p.add_argument("--grok-root", help="Grok CLI sessions folder (default ~/.grok/sessions)")
    p.add_argument("--agy-root", help="agy brain folder (default ~/.gemini/antigravity-cli/brain)")
    p.add_argument("--fail-on-trigger", action="store_true")
    p = sub.add_parser("snapshot", help="write interject evidence for one session")
    p.add_argument("--file", required=True, help="Codex rollout, Claude transcript, Grok updates.jsonl "
                                                 "or agy transcript.jsonl")
    p.add_argument("--out")
    p.add_argument("--threshold-min", type=float, default=45)
    return top


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        return scan(args) if args.command == "scan" else snapshot(args)
    except OSError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
