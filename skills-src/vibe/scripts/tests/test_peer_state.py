"""Offline tests for peer_state.py (record-first peer session state).

Synthetic fixtures under tests/fixtures/peer/ mirror the STRUCTURE of real codex-tui 0.155.0 /
Codex Desktop rollouts and Claude Code main-session JSONL. No real records, processes, network,
sleeping or writes outside a temporary directory.
"""
import ast
import contextlib
import functools
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "peer"
sys.path.insert(0, str(SCRIPTS))
import peer_state  # noqa: E402

KST_1956 = "2026-09-28 10:56:26 KST"
ASSESS_KEYS = {"agent", "path", "state", "sendable", "reasons", "open_turns", "question",
               "last_event", "quota", "context", "record"}


class FakeTime:
    """Injectable clock/sleep: sleeping only advances the fake clock."""

    def __init__(self, now, advance=True):
        self.now, self.advance, self.sleeps = float(now), advance, []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        if self.advance:
            self.now += seconds


def fixture_lines(name):
    data = (FIXTURES / name).read_bytes()
    assert data.endswith(b"\n"), name
    return data.split(b"\n")[:-1]


def fixture_records(name, upto=None):
    records, errors = peer_state.read_records(FIXTURES / name)
    assert not errors, errors
    return [(n, r) for n, r in records if upto is None or n <= upto]


def codex_meta(**extra):
    payload = {"id": "thread-x", "originator": "codex-tui", "cli_version": "0.155.0",
               "thread_source": "user", "cwd": "X:/Shared Project"}
    payload.update(extra)
    return {"timestamp": "2026-09-28T01:50:00.000Z", "type": "session_meta", "payload": payload}


def codex_event(kind, ts="2026-09-28T01:50:10.000Z", **payload):
    return {"timestamp": ts, "type": "event_msg", "payload": dict(type=kind, **payload)}


def codex_item(kind, ts="2026-09-28T01:50:10.000Z", **payload):
    return {"timestamp": ts, "type": "response_item", "payload": dict(type=kind, **payload)}


def user_message(turn):
    return codex_event("item_completed", turn_id=turn, thread_id="thread-x",
                       item={"type": "UserMessage", "id": "item-" + turn, "content": []})


def numbered(*records):
    return list(enumerate(records, 1))


def token_count(rate_limits=None, info=None, ts="2026-09-28T01:55:00.000Z"):
    payload = {}
    if rate_limits is not None:
        payload["rate_limits"] = rate_limits
    if info is not None:
        payload["info"] = info
    return codex_event("token_count", ts=ts, **payload)


def claude(kind, uuid, content=None, *, msg_id=None, stop=None, usage=None, **extra):
    record = {"type": kind, "uuid": uuid, "isSidechain": False, "sessionId": "sess-fixture-0002",
              "timestamp": "2026-09-28T01:52:00.000Z"}
    if kind == "assistant":
        record["message"] = {"id": msg_id, "type": "message", "role": "assistant", "content": content,
                             "stop_reason": stop, "usage": usage or {}}
    elif kind == "user":
        record["message"] = {"role": "user", "content": content}
    record.update(extra)
    return record


def tool_result(uuid, tool_use_id):
    return claude("user", uuid, [{"type": "tool_result", "tool_use_id": tool_use_id, "content": "ok"}],
                  toolUseResult={"answers": {}})


def turn_duration(uuid):
    return {"type": "system", "subtype": "turn_duration", "uuid": uuid, "isSidechain": False,
            "timestamp": "2026-09-28T01:53:00.000Z", "durationMs": 1000, "messageCount": 4}


class PeerStateCase(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="vibe-peer-state-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for target in ("subprocess.Popen", "socket.socket"):
            guard = patch(target, side_effect=AssertionError("offline test: " + target))
            guard.start()
            self.addCleanup(guard.stop)

    def make(self, name, source=None, upto=None, extra=(), raw=None):
        lines = fixture_lines(source)[:upto] if source else []
        lines += [json.dumps(r, ensure_ascii=False).encode("utf-8") for r in extra]
        data = raw if raw is not None else (b"\n".join(lines) + b"\n" if lines else b"")
        path = self.root / name
        path.write_bytes(data)
        return path

    def assess(self, agent, path, age=100.0, **kwargs):
        fake = FakeTime(os.stat(path).st_mtime_ns / 1e9 + age)
        result = peer_state.assess(agent, path, clock=fake.clock, sleep=fake.sleep, **kwargs)
        json.dumps(result, ensure_ascii=False, allow_nan=False)  # must stay plain JSON
        self.assertEqual(set(result), ASSESS_KEYS)
        return result, fake


class CodexStateTests(PeerStateCase):
    def test_codex_task_started_only_is_working(self):
        result, _ = self.assess("codex", self.make("a.jsonl", "codex_started_only.jsonl"))
        self.assertEqual(result["state"], "working")
        self.assertFalse(result["sendable"])
        self.assertEqual(result["open_turns"], ["turn-a"])
        self.assertIn("open_turn", result["reasons"])

    def test_codex_task_complete_is_idle_and_sendable(self):
        result, fake = self.assess("codex", self.make("b.jsonl", "codex_complete.jsonl"))
        self.assertEqual((result["state"], result["sendable"]), ("idle", True), result["reasons"])
        self.assertEqual(result["open_turns"], [])
        self.assertTrue(result["record"]["quiet"]["ok"])
        self.assertTrue(result["record"]["quiet"]["stable"])
        self.assertEqual(fake.sleeps, [2])
        self.assertEqual(result["last_event"], {"type": "event_msg/task_complete", "line": 10,
                                                "utc": "2026-09-28T01:56:26Z", "kst": KST_1956})
        self.assertEqual(result["question"], {"open": False, "line": None, "name": None})

    def test_codex_bad_middle_line_is_unknown(self):
        path = self.make("c.jsonl", "codex_bad_middle.jsonl")
        records, errors = peer_state.read_records(path)
        self.assertEqual([n for n, _ in records], [1, 2, 4])
        self.assertEqual(errors, ["line 3: invalid JSON"])
        result, _ = self.assess("codex", path)
        self.assertEqual((result["state"], result["sendable"]), ("unknown", False))
        self.assertIn("parse_error", result["reasons"])

    def test_codex_trailing_partial_line_is_unknown(self):
        whole = (FIXTURES / "codex_complete.jsonl").read_bytes()
        for label, data in (("cut", whole[:-40]), ("no_newline", whole[:-1])):
            with self.subTest(label):
                path = self.make(label + ".jsonl", raw=data)
                records, errors = peer_state.read_records(path)
                self.assertEqual(len(records), 9)
                self.assertEqual(errors, ["line 10: trailing partial line (no newline)"])
                result, _ = self.assess("codex", path)
                self.assertEqual((result["state"], result["sendable"]), ("unknown", False))

    def test_codex_overlapping_turns_pair_by_turn_id(self):
        prefix = fixture_records("codex_overlap.jsonl", upto=7)
        lifecycle = [r["payload"]["type"] for _, r in prefix if r["type"] == "event_msg"
                     and r["payload"]["type"] in peer_state.CODEX_LIFECYCLE]
        self.assertEqual(lifecycle[-1], "task_complete")  # "last event wins" would say idle
        status = peer_state.codex_status(prefix)
        self.assertEqual((status["state"], status["open_turns"]), ("working", ["turn-a"]))
        result, _ = self.assess("codex", self.make("o7.jsonl", "codex_overlap.jsonl", upto=7))
        self.assertEqual((result["state"], result["sendable"]), ("working", False))
        full, _ = self.assess("codex", self.make("o9.jsonl", "codex_overlap.jsonl"))
        self.assertEqual((full["state"], full["sendable"], full["open_turns"]), ("idle", True, []))

    def test_codex_recent_write_is_held(self):
        result, fake = self.assess("codex", self.make("r.jsonl", "codex_complete.jsonl"), age=5)
        self.assertEqual(result["state"], "idle")
        self.assertFalse(result["sendable"])
        self.assertIn("recent_write", result["reasons"])
        self.assertEqual(fake.sleeps, [])

    def test_codex_record_changing_between_stats_is_held(self):
        path = self.make("s.jsonl", "codex_complete.jsonl")
        real = os.stat(path)
        stats = iter([SimpleNamespace(st_size=real.st_size, st_mtime_ns=real.st_mtime_ns),
                      SimpleNamespace(st_size=real.st_size + 64, st_mtime_ns=real.st_mtime_ns + 10)])
        result, _ = self.assess("codex", path, stat=lambda _p: next(stats))
        self.assertEqual(result["state"], "idle")
        self.assertFalse(result["sendable"])
        self.assertIn("record_changed", result["reasons"])
        self.assertFalse(result["record"]["quiet"]["stable"])

    def test_codex_request_user_input_text_is_not_a_question(self):
        prefix = fixture_records("codex_question.jsonl", upto=14)
        raw = fixture_lines("codex_question.jsonl")[:14]
        self.assertGreaterEqual(sum(b"request_user_input" in line for line in raw), 10)
        status = peer_state.codex_status(prefix)
        self.assertEqual(status["state"], "idle")
        self.assertFalse(status["question"]["open"])

    def test_codex_request_user_input_call_opens_question(self):
        working = peer_state.codex_status(fixture_records("codex_question.jsonl", upto=18))
        self.assertEqual(working["state"], "working")
        self.assertEqual(working["question"], {"open": True, "line": 18,
                                               "name": "request_user_input_async"})
        result, _ = self.assess("codex", self.make("q21.jsonl", "codex_question.jsonl", upto=21))
        self.assertEqual((result["state"], result["sendable"]), ("question", False))
        self.assertEqual(result["question"]["line"], 18)
        self.assertIn("question_open", result["reasons"])

    def test_codex_later_user_input_closes_question(self):
        status = peer_state.codex_status(fixture_records("codex_question.jsonl", upto=24))
        self.assertEqual((status["state"], status["question"]["open"]), ("working", False))
        result, _ = self.assess("codex", self.make("q.jsonl", "codex_question.jsonl"))
        self.assertEqual((result["state"], result["sendable"]), ("idle", True))

    def test_codex_turn_aborted_closes_question(self):
        base = [codex_meta(), codex_event("task_started", turn_id="t1"), user_message("t1"),
                codex_item("function_call", name="request_user_input_async", arguments="{}")]
        opened = peer_state.codex_status(numbered(*base, codex_event("task_complete", turn_id="t1")))
        self.assertEqual(opened["state"], "question")
        aborted = peer_state.codex_status(numbered(*base, codex_event(
            "turn_aborted", turn_id="t1", reason="interrupted")))
        self.assertEqual((aborted["state"], aborted["question"]["open"]), ("idle", False))

    def test_codex_custom_tool_call_named_request_user_input_counts(self):
        status = peer_state.codex_status(numbered(
            codex_meta(), codex_event("task_started", turn_id="t1"), user_message("t1"),
            codex_item("custom_tool_call", name="request_user_input", input="{}"),
            codex_event("task_complete", turn_id="t1")))
        self.assertEqual((status["state"], status["question"]["name"]), ("question", "request_user_input"))

    def test_codex_fork_file_is_unknown(self):
        result, _ = self.assess("codex", self.make("f.jsonl", "codex_fork.jsonl"))
        self.assertEqual((result["state"], result["sendable"]), ("unknown", False))
        self.assertIn("fork_file", result["reasons"])
        self.assertIn("unmatched_complete", result["reasons"])
        subagent_only = peer_state.codex_status(numbered(
            codex_meta(thread_source="subagent"), codex_event("task_started", turn_id="t1"),
            codex_event("task_complete", turn_id="t1")))
        self.assertEqual(subagent_only["state"], "unknown")

    def test_codex_stale_open_turn_is_unknown(self):
        path = self.make("st.jsonl", "codex_started_only.jsonl")
        stale, _ = self.assess("codex", path, age=700)
        self.assertEqual((stale["state"], stale["sendable"]), ("unknown", False))
        self.assertIn("open_turn_stale", stale["reasons"])
        patient, _ = self.assess("codex", path, age=700, stale_open_turn_seconds=1000)
        self.assertEqual(patient["state"], "working")

    def test_codex_duplicate_turn_start_is_unknown(self):
        result, _ = self.assess("codex", self.make("d.jsonl", "codex_duplicate_start.jsonl"))
        self.assertEqual((result["state"], result["sendable"]), ("unknown", False))
        self.assertIn("duplicate_turn_start", result["reasons"])

    def test_codex_unmatched_complete_is_noted_not_fatal(self):
        status = peer_state.codex_status(numbered(
            codex_meta(), codex_event("task_complete", turn_id="ghost"),
            codex_event("task_started", turn_id="t1"), codex_event("task_complete", turn_id="t1")))
        self.assertEqual(status["state"], "idle")
        self.assertIn("unmatched_complete", status["reasons"])

    def test_codex_without_lifecycle_is_unknown(self):
        status = peer_state.codex_status(numbered(codex_meta(), user_message("t1")))
        self.assertEqual(status["state"], "unknown")
        self.assertIn("no_lifecycle_events", status["reasons"])
        missing_id = peer_state.codex_status(numbered(codex_meta(), codex_event("task_started")))
        self.assertEqual(missing_id["state"], "unknown")

    def test_codex_quota_comes_from_last_token_count(self):
        quota = peer_state.codex_status(fixture_records("codex_complete.jsonl"))["quota"]
        self.assertEqual(quota["source"], "codex-record")
        self.assertEqual((quota["observed_utc"], quota["observed_kst"]),
                         ("2026-09-28T01:56:25Z", "2026-09-28 10:56:25 KST"))
        self.assertEqual(quota["primary"], {"used_percent": 20.0, "window_minutes": 300,
                                            "resets_at_utc": "2026-09-28T05:00:00Z",
                                            "resets_at_kst": "2026-09-28 14:00:00 KST"})
        self.assertEqual(quota["secondary"]["used_percent"], 40.0)
        self.assertEqual(quota["secondary"]["resets_at_kst"], "2026-10-02 09:00:00 KST")
        self.assertIs(quota["limit_reached"], False)

    def test_codex_quota_omitted_fields_do_not_crash(self):
        variants = [
            ({"primary": {"window_minutes": 300}}, (None, 300, None), None, None),
            ({"primary": None, "secondary": None, "rate_limit_reached_type": None}, None, None, False),
            ({}, None, None, None),
            ({"primary": {"used_percent": True, "resets_at": "garbage"}}, (None, None, None), None, None),
        ]
        for limits, primary, secondary, reached in variants:
            with self.subTest(limits=limits):
                status = peer_state.codex_status(numbered(
                    codex_meta(), codex_event("task_started", turn_id="t1"),
                    token_count(rate_limits=limits), codex_event("task_complete", turn_id="t1")))
                quota = status["quota"]
                got = quota["primary"] and (quota["primary"]["used_percent"],
                                            quota["primary"]["window_minutes"],
                                            quota["primary"]["resets_at_utc"])
                self.assertEqual((got, quota["secondary"], quota["limit_reached"]),
                                 (primary, secondary, reached))
        no_quota = peer_state.codex_status(numbered(codex_meta(), token_count(info={})))
        self.assertIsNone(no_quota["quota"])
        self.assertEqual(no_quota["context"], {"source": "codex-record", "used_tokens": None,
                                               "window_tokens": None, "percent": None})

    def test_codex_quota_limit_reached_flags(self):
        for limits in ({"rate_limit_reached_type": "primary"}, {"spend_control_reached": True}):
            with self.subTest(limits=limits):
                status = peer_state.codex_status(numbered(codex_meta(), token_count(rate_limits=limits)))
                self.assertIs(status["quota"]["limit_reached"], True)

    def test_codex_context_uses_last_request_not_cumulative_usage(self):
        path = self.make("ctx.jsonl", "codex_complete.jsonl")
        result, _ = self.assess("codex", path, context_window=999999)
        self.assertEqual(result["context"], {"source": "codex-record", "used_tokens": 60000,
                                             "window_tokens": 200000, "percent": 30.0})
        info = {"last_token_usage": {"input_tokens": 45000, "output_tokens": 5000}}
        fallback = self.make("ctx2.jsonl", extra=[codex_meta(), token_count(info=info)])
        result, _ = self.assess("codex", fallback, context_window=100000)
        self.assertEqual(result["context"], {"source": "codex-record+window-arg", "used_tokens": 50000,
                                             "window_tokens": 100000, "percent": 50.0})


class TimeTests(unittest.TestCase):
    def test_to_kst_converts_utc_and_epochs(self):
        for value in ("2026-09-28T01:56:26.123Z", "2026-09-28T01:56:26Z", "2026-09-28T10:56:26+09:00",
                      1790560586, 1790560586.9, 1790560586123, "1790560586", "1790560586123"):
            with self.subTest(value=value):
                self.assertEqual(peer_state.to_kst(value), KST_1956)
        self.assertEqual(peer_state.to_kst("2026-09-28T15:30:00Z"), "2026-09-29 00:30:00 KST")

    def test_to_kst_rejects_naive_and_garbage(self):
        for value in ("2026-09-28T01:56:26", "", "yesterday", None, True, float("nan"), [1]):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    peer_state.to_kst(value)


class QuietCheckTests(PeerStateCase):
    def setUp(self):
        super().setUp()
        self.path = self.make("quiet.jsonl", "codex_complete.jsonl")
        self.mtime = os.stat(self.path).st_mtime_ns

    def test_quiet_check_ok_after_quiet_period_and_identical_stats(self):
        fake = FakeTime(self.mtime / 1e9 + 45)
        result = peer_state.quiet_check(self.path, clock=fake.clock, sleep=fake.sleep)
        self.assertEqual((result["ok"], result["stable"], result["reasons"]), (True, True, []))
        self.assertAlmostEqual(result["age_seconds"], 45, places=2)
        self.assertEqual((result["size"], result["mtime_ns"]), (os.stat(self.path).st_size, self.mtime))

    def test_quiet_check_requires_real_recheck_interval(self):
        fake = FakeTime(self.mtime / 1e9 + 45, advance=False)
        result = peer_state.quiet_check(self.path, clock=fake.clock, sleep=fake.sleep)
        self.assertFalse(result["ok"])
        self.assertIn("recheck_interval_short", result["reasons"])
        self.assertEqual(len(fake.sleeps), 3)

    def test_quiet_check_differing_stats_are_not_stable(self):
        fake = FakeTime(100.0)
        stats = iter([SimpleNamespace(st_size=10, st_mtime_ns=10 * 10**9),
                      SimpleNamespace(st_size=10, st_mtime_ns=99 * 10**9)])
        result = peer_state.quiet_check("any", stat=lambda _p: next(stats), clock=fake.clock,
                                        sleep=fake.sleep)
        self.assertEqual((result["ok"], result["stable"]), (False, False))
        self.assertIn("record_changed", result["reasons"])

    def test_quiet_check_missing_file_is_not_ok(self):
        result = peer_state.quiet_check(self.root / "missing.jsonl", sleep=FakeTime(0).sleep)
        self.assertEqual((result["ok"], result["reasons"]), (False, ["record_missing"]))
        assessed = peer_state.assess("codex", self.root / "missing.jsonl", sleep=FakeTime(0).sleep)
        self.assertEqual((assessed["state"], assessed["sendable"]), ("unknown", False))
        self.assertIn("record_missing", assessed["reasons"])


class ClaudeStateTests(PeerStateCase):
    def test_claude_turn_duration_last_is_idle_by_line_order(self):
        path = self.make("ci.jsonl", "claude_idle.jsonl")
        result, _ = self.assess("claude", path)
        self.assertEqual((result["state"], result["sendable"]), ("idle", True), result["reasons"])
        # line 11 is stamped earlier than line 8: order is by line, never by timestamp
        self.assertEqual(result["last_event"], {"type": "system/turn_duration", "line": 11,
                                                "utc": "2026-09-28T01:51:00Z",
                                                "kst": "2026-09-28 10:51:00 KST"})
        self.assertIsNone(result["quota"])
        self.assertEqual(result["context"], {"source": "claude-record", "used_tokens": 50000,
                                             "window_tokens": None, "percent": None})
        windowed, _ = self.assess("claude", path, context_window=200000)
        self.assertEqual(windowed["context"]["percent"], 25.0)
        self.assertEqual(windowed["context"]["source"], "claude-record+window-arg")

    def test_claude_turn_in_progress_is_working(self):
        cases = {3: "user_prompt_last", 6: "tool_pending", 7: "user_tool_result_last",
                 8: "end_turn_without_turn_duration", 10: "end_turn_without_turn_duration"}
        for upto, reason in cases.items():
            with self.subTest(upto=upto):
                status = peer_state.claude_status(fixture_records("claude_idle.jsonl", upto=upto))
                self.assertEqual(status["state"], "working")
                self.assertIn(reason, status["reasons"])
        result, _ = self.assess("claude", self.make("c8.jsonl", "claude_idle.jsonl", upto=8))
        self.assertEqual((result["state"], result["sendable"]), ("working", False))

    def test_claude_stop_reason_is_read_from_last_record_of_group(self):
        thinking_only = peer_state.claude_status(fixture_records("claude_idle.jsonl", upto=5))
        self.assertEqual(thinking_only["state"], "unknown")
        self.assertIn("assistant_stop_null", thinking_only["reasons"])
        group = peer_state.claude_status(numbered(
            claude("user", "u1", "Synthetic."),
            claude("assistant", "a1", [{"type": "thinking", "thinking": ""}], msg_id="m1", stop=None),
            claude("assistant", "a2", [{"type": "text", "text": "done"}], msg_id="m1", stop="end_turn")))
        self.assertEqual(group["state"], "working")
        self.assertIn("end_turn_without_turn_duration", group["reasons"])

    def test_claude_pending_ask_user_question_is_question(self):
        result, _ = self.assess("claude", self.make("cq.jsonl", "claude_question.jsonl"))
        self.assertEqual((result["state"], result["sendable"]), ("question", False))
        self.assertEqual(result["question"], {"open": True, "line": 4, "name": "AskUserQuestion"})

    def test_claude_answered_question_then_turn_end_is_idle(self):
        answered = [tool_result("u2", "toolu_ask_01")]
        status = peer_state.claude_status(peer_state._parse_lines(
            self.make("qa.jsonl", "claude_question.jsonl", extra=answered).read_bytes())[0])
        self.assertEqual((status["state"], status["question"]["open"]), ("working", False))
        finished = answered + [claude("assistant", "a9", [{"type": "text", "text": "ok"}],
                                      msg_id="m9", stop="end_turn"), turn_duration("s9")]
        result, _ = self.assess("claude", self.make("qb.jsonl", "claude_question.jsonl", extra=finished))
        self.assertEqual((result["state"], result["sendable"]), ("idle", True))

    def test_claude_ask_pending_at_turn_duration_is_question(self):
        path = self.make("qd.jsonl", "claude_question.jsonl", extra=[turn_duration("s1")])
        result, _ = self.assess("claude", path)
        self.assertEqual((result["state"], result["sendable"]), ("question", False))

    def test_claude_abandoned_ask_is_not_question(self):
        later = [claude("user", "u5", "A new synthetic prompt.", promptSource="typed")]
        status = peer_state.claude_status(peer_state._parse_lines(
            self.make("qx.jsonl", "claude_question.jsonl", extra=later).read_bytes())[0])
        self.assertEqual((status["state"], status["question"]["open"]), ("working", False))

    def test_claude_interrupt_marker_is_unknown(self):
        for marker in peer_state.CLAUDE_INTERRUPT_MARKERS:
            with self.subTest(marker=marker):
                status = peer_state.claude_status(numbered(
                    claude("user", "u1", "Synthetic."),
                    claude("assistant", "a1", [{"type": "tool_use", "id": "t1", "name": "Bash",
                                                "input": {}}], msg_id="m1", stop="tool_use"),
                    tool_result("u2", "t1"),
                    claude("user", "u3", [{"type": "text", "text": marker}])))
                self.assertEqual(status["state"], "unknown")
                self.assertIn("interrupt_marker", status["reasons"])

    def test_claude_empty_or_unparsable_record_is_unknown(self):
        empty, _ = self.assess("claude", self.make("e.jsonl", raw=b""))
        self.assertEqual((empty["state"], empty["sendable"]), ("unknown", False))
        self.assertIn("no_valid_records", empty["reasons"])
        lines = fixture_lines("claude_idle.jsonl")
        broken = self.make("b.jsonl", raw=b"\n".join(lines[:5] + [b"{not json"] + lines[5:]) + b"\n")
        result, _ = self.assess("claude", broken)
        self.assertEqual((result["state"], result["sendable"]), ("unknown", False))
        self.assertIn("parse_error", result["reasons"])

    def test_claude_unrecognized_stop_reason_is_unknown(self):
        status = peer_state.claude_status(numbered(
            claude("user", "u1", "Synthetic."),
            claude("assistant", "a1", [{"type": "text", "text": "..."}], msg_id="m1", stop="max_tokens")))
        self.assertEqual(status["state"], "unknown")
        self.assertIn("assistant_stop_max_tokens", status["reasons"])

    def test_claude_meta_and_sidechain_records_are_ignored(self):
        extra = [{"type": "pr-link", "sessionId": "s"}, {"type": "system", "subtype": "away_summary",
                                                          "timestamp": "2026-09-28T01:59:00.000Z"},
                 claude("user", "side1", "Sidechain prompt.", isSidechain=True)]
        status = peer_state.claude_status(peer_state._parse_lines(
            self.make("m.jsonl", "claude_idle.jsonl", extra=extra).read_bytes())[0])
        self.assertEqual(status["state"], "idle")


class ScreenTests(unittest.TestCase):
    IDLE = {"agent": "claude", "state": "idle", "sendable": True, "reasons": []}

    def test_combine_screen_downgrades_idle_on_screen_conflict(self):
        combined = peer_state.combine_screen(self.IDLE, False)
        self.assertEqual((combined["state"], combined["sendable"]), ("unknown", False))
        self.assertIn("screen_conflict", combined["reasons"])
        self.assertEqual((self.IDLE["state"], self.IDLE["reasons"]), ("idle", []))  # not mutated

    def test_combine_screen_never_upgrades(self):
        self.assertEqual(peer_state.combine_screen(self.IDLE, True)["sendable"], True)
        self.assertEqual(peer_state.combine_screen(self.IDLE, None)["state"], "idle")
        for state in ("working", "question", "unknown"):
            with self.subTest(state=state):
                held = {"state": state, "sendable": False, "reasons": []}
                combined = peer_state.combine_screen(held, True)
                self.assertEqual((combined["state"], combined["sendable"]), (state, False))
                self.assertNotIn("screen_conflict", combined["reasons"])


class CliTests(PeerStateCase):
    def run_cli(self, *argv, age=100.0, path=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        fake = FakeTime(os.stat(path).st_mtime_ns / 1e9 + age) if path and path.exists() else FakeTime(0)
        wrapped = functools.partial(peer_state.assess, clock=fake.clock, sleep=fake.sleep)
        with patch.object(peer_state, "assess", wrapped), contextlib.redirect_stdout(stdout), \
                contextlib.redirect_stderr(stderr):
            code = peer_state.main(list(argv))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_cli_exit_codes(self):
        idle = self.make("기록.jsonl", "codex_complete.jsonl")
        code, out, _ = self.run_cli("--agent", "codex", "--record", str(idle), path=idle)
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertTrue(payload["sendable"])
        self.assertIn("기록.jsonl", out)  # ensure_ascii=False
        busy = self.make("busy.jsonl", "codex_started_only.jsonl")
        self.assertEqual(self.run_cli("--agent", "codex", "--record", str(busy), path=busy)[0], 3)
        self.assertEqual(self.run_cli("--agent", "codex", "--record", str(idle), "--quiet-seconds",
                                      "500", path=idle)[0], 3)
        missing = self.root / "missing.jsonl"
        self.assertEqual(self.run_cli("--agent", "claude", "--record", str(missing))[0], 3)
        for bad in (["--agent", "grok", "--record", str(idle)], ["--agent", "codex"],
                    ["--agent", "codex", "--record", str(idle), "--context-window", "0"],
                    ["--agent", "codex", "--record", str(idle), "--quiet-seconds", "-1"], []):
            with self.subTest(argv=bad):
                code, out, err = self.run_cli(*bad)
                self.assertEqual((code, out), (2, ""))
                self.assertIn("usage error", err)
        self.assertEqual(self.run_cli("--help")[0], 0)

    def test_cli_context_window_argument_reaches_claude(self):
        path = self.make("claude.jsonl", "claude_idle.jsonl")
        code, out, _ = self.run_cli("--agent", "claude", "--record", str(path), "--context-window",
                                    "200000", path=path)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["context"]["percent"], 25.0)


class ReviewRegressionTests(PeerStateCase):
    """One regression test per defect found in the adversarial review."""

    def test_codex_non_root_thread_metadata_is_unknown(self):
        # Real child threads without forked_from_id exist (thread_source guardian_review with
        # parent_thread_id; SubAgent source serialized as a dict). They must never read idle.
        variants = {
            "guardian": dict(thread_source="guardian_review", parent_thread_id="p"),
            "parent_only": dict(parent_thread_id="p"),
            "dict_source": dict(source={"subagent": {"other": "x"}}),
            "future_source_kind": dict(thread_source="something_new"),
        }
        turn = [codex_event("task_started", turn_id="t1"), user_message("t1"),
                codex_event("task_complete", turn_id="t1")]
        for label, extra in variants.items():
            with self.subTest(label):
                path = self.make(label + ".jsonl", extra=[codex_meta(**extra)] + turn)
                result, _ = self.assess("codex", path)
                self.assertEqual((result["state"], result["sendable"]), ("unknown", False))
                self.assertIn("non_root_thread", result["reasons"])
        legacy = codex_meta()
        del legacy["payload"]["thread_source"]  # older root files have no thread_source
        self.assertEqual(peer_state.codex_status(numbered(legacy, *turn))["state"], "idle")

    def test_codex_first_record_must_be_session_meta(self):
        turn = [codex_event("task_started", turn_id="t1"), codex_event("task_complete", turn_id="t1")]
        for label, records in (("none", turn), ("late", turn + [codex_meta()])):
            with self.subTest(label):
                status = peer_state.codex_status(numbered(*records))
                self.assertEqual(status["state"], "unknown")
                self.assertIn("no_session_meta", status["reasons"])

    def test_codex_abort_of_another_turn_keeps_question_open(self):
        asked = [codex_meta(), codex_event("task_started", turn_id="A"), user_message("A"),
                 codex_item("function_call", name="request_user_input_async", arguments="{}")]
        # B starts without human input (automation) and is aborted; A's question is untouched.
        other = asked + [codex_event("task_started", turn_id="B"),
                         codex_event("turn_aborted", turn_id="B", reason="interrupted"),
                         codex_event("task_complete", turn_id="A")]
        result, _ = self.assess("codex", self.make("abort_b.jsonl", extra=other))
        self.assertEqual((result["state"], result["sendable"]), ("question", False))
        self.assertEqual(result["question"]["line"], 4)
        # Aborting the asking turn itself still closes it (unchanged rule).
        own = asked + [codex_event("turn_aborted", turn_id="A", reason="interrupted")]
        self.assertEqual(peer_state.codex_status(numbered(*own))["state"], "idle")

    def test_claude_unconsumed_enqueue_after_turn_duration_is_unknown(self):
        base = fixture_lines("claude_idle.jsonl")[:11]  # ends with turn_duration
        def queue(operation):
            return {"type": "queue-operation", "operation": operation,
                    "timestamp": "2026-09-28T01:52:00.000Z", "sessionId": "sess-fixture-0001"}
        cases = {("enqueue",): "unknown", ("enqueue", "enqueue", "dequeue"): "unknown",
                 ("enqueue", "remove"): "idle", ("enqueue", "dequeue"): "idle",
                 ("enqueue", "enqueue", "popAll"): "idle", ("dequeue", "enqueue", "remove"): "idle"}
        for ops, expected in cases.items():
            with self.subTest(ops=ops):
                lines = base + [json.dumps(queue(op)).encode("utf-8") for op in ops]
                path = self.make("q_%d.jsonl" % len(lines), raw=b"\n".join(lines) + b"\n")
                result, _ = self.assess("claude", path)
                self.assertEqual(result["state"], expected, result["reasons"])
                self.assertEqual(result["sendable"], expected == "idle")
                if expected == "unknown":
                    self.assertIn("queued_input_pending", result["reasons"])
        # An enqueue before turn_duration (absorbed later) does not hold the idle verdict.
        early = fixture_lines("claude_idle.jsonl")[:10] + [json.dumps(queue("enqueue")).encode()] + \
            fixture_lines("claude_idle.jsonl")[10:11]
        result, _ = self.assess("claude", self.make("q_early.jsonl", raw=b"\n".join(early) + b"\n"))
        self.assertEqual(result["state"], "idle")

    def test_non_finite_or_negative_quiet_parameters_are_not_ok(self):
        path = self.make("nan.jsonl", "codex_complete.jsonl")
        for kwargs in ({"quiet_seconds": float("nan")}, {"quiet_seconds": -1},
                       {"recheck_seconds": float("nan")}, {"recheck_seconds": float("-inf")},
                       {"quiet_seconds": "30"}):
            with self.subTest(kwargs=kwargs):
                result, fake = self.assess("codex", path, age=0.5, **kwargs)
                self.assertFalse(result["sendable"])
                self.assertIn("invalid_quiet_parameters", result["reasons"])
                self.assertNotIn("changed_during_read", result["reasons"])
                self.assertEqual(fake.sleeps, [])
        zero, _ = self.assess("codex", path, age=0.5, quiet_seconds=0, recheck_seconds=0)
        self.assertTrue(zero["sendable"], zero["reasons"])  # peer_link's self-record call shape

    def test_deeply_nested_line_is_a_parse_error_not_a_crash(self):
        deep = b'{"a":' + b"[" * 200000 + b"]" * 200000 + b"}"
        lines = fixture_lines("codex_complete.jsonl")
        path = self.make("deep.jsonl", raw=b"\n".join(lines[:5] + [deep] + lines[5:]) + b"\n")
        result, _ = self.assess("codex", path)
        self.assertEqual((result["state"], result["sendable"]), ("unknown", False))
        self.assertEqual(peer_state.read_records(path)[1], ["line 6: invalid JSON"])

    def test_assess_streams_instead_of_loading_the_whole_record(self):
        import tracemalloc
        filler = codex_item("message", role="assistant",
                            content=[{"type": "output_text", "text": "x" * 480}])
        head = [codex_meta(), codex_event("task_started", turn_id="t1"), user_message("t1")]
        body = json.dumps(filler).encode("utf-8") + b"\n"
        path = self.root / "big.jsonl"
        with open(path, "wb") as handle:
            handle.write(b"".join(json.dumps(r).encode("utf-8") + b"\n" for r in head))
            handle.write(body * 12000)
            handle.write(json.dumps(codex_event("task_complete", turn_id="t1")).encode() + b"\n")
        size = os.stat(path).st_size
        self.assertGreater(size, 6_000_000)
        tracemalloc.start()
        try:
            result, _ = self.assess("codex", path)
            peak = tracemalloc.get_traced_memory()[1]
        finally:
            tracemalloc.stop()
        self.assertEqual((result["state"], result["sendable"]), ("idle", True), result["reasons"])
        self.assertLess(peak, size // 6)  # whole-file reads peaked above 2x the file size

    def test_status_functions_take_one_shot_iterators(self):
        for agent, name in (("codex", "codex_overlap.jsonl"), ("claude", "claude_idle.jsonl")):
            with self.subTest(agent=agent):
                records = fixture_records(name)
                judge = peer_state.codex_status if agent == "codex" else peer_state.claude_status
                self.assertEqual(judge(iter(records)), judge(records))

    def test_bom_crlf_and_non_utf8_bytes(self):
        lines = fixture_lines("codex_complete.jsonl")
        crlf = self.make("crlf.jsonl", raw=b"\xef\xbb\xbf" + b"\r\n".join(lines) + b"\r\n")
        result, _ = self.assess("codex", crlf)
        self.assertEqual((result["state"], result["sendable"]), ("idle", True), result["reasons"])
        late_bom = self.make("bom2.jsonl", raw=b"\n".join(lines[:1] + [b"\xef\xbb\xbf" + lines[1]]
                                                        + lines[2:]) + b"\n")
        self.assertEqual(peer_state.read_records(late_bom)[1], ["line 2: invalid JSON"])
        latin = self.make("latin.jsonl", raw=b"\n".join(lines[:3] + [lines[3].replace(
            b"Synthetic", b"Synth\xe9tic")] + lines[4:]) + b"\n")
        self.assertEqual(peer_state.read_records(latin)[1], ["line 4: not UTF-8"])
        result, _ = self.assess("codex", latin)
        self.assertEqual((result["state"], result["sendable"]), ("unknown", False))

    def test_sendable_only_when_idle_closed_and_quiet_for_every_fixture_prefix(self):
        for fixture in sorted(FIXTURES.glob("*.jsonl")):
            agent = "codex" if fixture.name.startswith("codex") else "claude"
            lines = fixture_lines(fixture.name)
            for upto in range(len(lines) + 1):
                with self.subTest(fixture=fixture.name, upto=upto):
                    path = self.make("p.jsonl", fixture.name, upto=upto)
                    result, _ = self.assess(agent, path)
                    if result["sendable"]:
                        self.assertEqual(result["state"], "idle")
                        self.assertEqual(result["open_turns"], [])
                        self.assertFalse(result["question"]["open"])
                        self.assertTrue(result["record"]["quiet"]["ok"])
                        self.assertNotIn("parse_error", result["reasons"])


class HygieneTests(unittest.TestCase):
    def test_sources_parse_with_python_311_grammar(self):
        for path in (SCRIPTS / "peer_state.py", Path(__file__)):
            with self.subTest(path=path.name):
                ast.parse(path.read_text(encoding="utf-8"), feature_version=(3, 11))

    def test_module_imports_no_process_or_network_modules(self):
        tree = ast.parse((SCRIPTS / "peer_state.py").read_text(encoding="utf-8"))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add((node.module or "").split(".")[0])
        self.assertIn("json", names)
        self.assertFalse(names & {"subprocess", "socket", "urllib", "http", "asyncio", "multiprocessing"})

    def test_fixtures_are_synthetic(self):
        # Only the synthetic drive "X:" may appear; no real drive paths, no e-mail addresses,
        # no real user profile or project folder names.
        forbidden = re.compile(r"(?<![A-Za-z])(?![Xx]:)[A-Za-z]:[\\/]|[\w.+-]+@[\w-]+\.[A-Za-z]{2,}")
        files = sorted(FIXTURES.glob("*.jsonl")) + [SCRIPTS / "peer_state.py", Path(__file__)]
        self.assertGreaterEqual(len(files), 10)
        for path in files:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertIsNone(forbidden.search(text))
                self.assertIsNone(re.search(r"(?i)[\\/]users[\\/]|p[a]rry|2nd[b]", text))


if __name__ == "__main__":
    unittest.main()
