"""Offline interject_scan.py regressions on synthetic Codex and Claude transcripts."""
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import quote

import debate
import interject_scan

NOW = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
# Synthetic fixtures, joined at runtime so no token-shaped literal sits in the source.
SECRETS = ("sk" + "-proj-" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcd",
           "gh" + "p_" + "0123456789abcdefghijABCDEFGHIJ012345",
           "abcdefghijklmnopqrstuvwxyz0123", "xa" + "i-" + "ABCDEFGHIJKLMNOPQRSTUVWX",
           "AI" + "za" + "SyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456",
           "hunter2", "plainvalue123")


def iso(moment):
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def rec(minutes_ago, kind, payload):
    return {"timestamp": iso(NOW - timedelta(minutes=minutes_ago)), "type": kind, "payload": payload}


def session_meta(session_id="s-main", fork=False, padding=0):
    payload = {"session_id": session_id, "id": session_id}
    if fork:
        payload["forked_from_id"] = "s-parent"  # real rollouts put it before the long instructions
    payload.update({"cwd": "E:\\work", "thread_source": "user",
                    "base_instructions": {"text": "x" * padding}})
    return {"timestamp": iso(NOW - timedelta(hours=3)), "type": "session_meta", "payload": payload}


def started(minutes_ago, turn):
    return rec(minutes_ago, "event_msg", {"type": "task_started", "turn_id": turn,
                                          "started_at": int((NOW - timedelta(minutes=minutes_ago)).timestamp())})


def finished(minutes_ago, turn, kind="task_complete"):
    return rec(minutes_ago, "event_msg", {"type": kind, "turn_id": turn, "last_agent_message": "끝"})


def completed(turn, item):
    payload = {"type": "item_completed", "item": item}
    if turn:
        payload["turn_id"] = turn
    return payload


def user(minutes_ago, text, turn=None):
    return [rec(minutes_ago, "response_item", {"type": "message", "role": "user",
                                               "content": [{"type": "input_text", "text": text}]}),
            rec(minutes_ago, "event_msg", completed(turn, {"type": "UserMessage",
                                                           "content": [{"type": "text", "text": text}]}))]


def agent(minutes_ago, text, turn=None):
    return [rec(minutes_ago, "event_msg", completed(turn, {"type": "AgentMessage",
                                                           "content": [{"type": "Text", "text": text}]})),
            rec(minutes_ago, "response_item", {"type": "message", "role": "assistant",
                                               "content": [{"type": "output_text", "text": text}]})]


def goal_block(minutes_ago, objective):
    text = ('<codex_internal_context source="goal">\nContinue working toward the active thread goal.\n\n'
            "<objective>\n%s\n</objective>\n\nBudget:\n- Tokens used: 15\n</codex_internal_context>" % objective)
    return rec(minutes_ago, "response_item", {"type": "message", "role": "user",
                                              "content": [{"type": "input_text", "text": text}]})


def goal_update(minutes_ago, objective, status="active", used=None, created_min=None):
    goal = {"threadId": "s-main", "objective": objective, "status": status,
            "updatedAt": int((NOW - timedelta(minutes=minutes_ago)).timestamp())}
    if used is not None:
        goal["timeUsedSeconds"] = used
    if created_min is not None:
        goal["createdAt"] = int((NOW - timedelta(minutes=created_min)).timestamp())
    return rec(minutes_ago, "event_msg", {"type": "thread_goal_updated", "threadId": "s-main", "goal": goal})


def command(minutes_ago, turn, size=500):
    return rec(minutes_ago, "event_msg", {"type": "item_completed", "turn_id": turn,
                                          "item": {"type": "CommandExecution", "output": "x" * size}})


def quota(minutes_ago, used):
    return rec(minutes_ago, "event_msg", {"type": "token_count", "info": {}, "rate_limits": {
        "primary": {"used_percent": float(used), "window_minutes": 10080,
                    "resets_at": int((NOW + timedelta(days=5)).timestamp())},
        "secondary": None, "credits": {"has_credits": True}}})


def flatten(rows):
    out = []
    for row in rows:
        out.extend(row if isinstance(row, list) else [row])
    return out


def cl(minutes_ago, sid="c-1", **fields):
    return dict(sessionId=sid, cwd="E:\\work", timestamp=iso(NOW - timedelta(minutes=minutes_ago)), **fields)


def said(minutes_ago, text, sid="c-1", **extra):
    return cl(minutes_ago, sid, type="user", message={"role": "user", "content": text}, **extra)


def replied(minutes_ago, stop="end_turn", text="답", sid="c-1"):
    return cl(minutes_ago, sid, type="assistant", message={"role": "assistant", "stop_reason": stop,
                                                           "content": [{"type": "text", "text": text}]})


def tiny_tail(first=4096, step=4096, cap=1 << 20):
    return patch.multiple(interject_scan, CODEX_TAIL=first, CLAUDE_TAIL=first, GROK_TAIL=first, AGY_TAIL=first,
                          TAIL_STEP=step, TAIL_CAP=cap)


# Grok CLI: ~/.grok/sessions/<urlencoded cwd>/<session id>/updates.jsonl (+ summary.json)
def ms(minutes_ago):
    return int((NOW - timedelta(minutes=minutes_ago)).timestamp() * 1000)


def gk(minutes_ago, kind, prompt=None, start_min=None, sid="g-1", **update):
    meta = {"eventId": sid + "-e", "agentTimestampMs": ms(minutes_ago)}
    if prompt:
        meta["promptId"] = prompt
    if start_min is not None:
        meta["turnStartMs"] = ms(start_min)
    method = "_x.ai/session/update" if kind in ("hook_execution", "turn_completed", "retry_state") \
        else "session/update"
    return {"timestamp": ms(minutes_ago) // 1000, "method": method,
            "params": {"sessionId": sid, "update": dict(sessionUpdate=kind, **update), "_meta": meta}}


def g_user(minutes_ago, text):
    return gk(minutes_ago, "user_message_chunk", content={"type": "text", "text": text},
              _meta={"modelId": "grok-4.7", "promptIndex": 0})


def g_agent(minutes_ago, text, prompt="p-1", start_min=None):
    return gk(minutes_ago, "agent_message_chunk", prompt, start_min, content={"type": "text", "text": text})


def g_tool(minutes_ago, prompt="p-1", start_min=None, size=40):
    return gk(minutes_ago, "tool_call", prompt, start_min, toolCallId="t", title="x" * size)


def g_hook(minutes_ago, event):
    return gk(minutes_ago, "hook_execution", event_name=event, runs=[])


def g_done(minutes_ago, prompt="p-1"):
    return gk(minutes_ago, "turn_completed", prompt_id=prompt, stop_reason="end_turn", elapsed_ms=1000)


# agy: ~/.gemini/antigravity-cli/brain/<conversation>/.system_generated/logs/transcript.jsonl
def step(minutes_ago, kind, source="MODEL", status="DONE", content=None, tools=None):
    row = {"step_index": 0, "source": source, "type": kind, "status": status,
           "created_at": (NOW - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")}
    if content is not None:
        row["content"] = content
    if tools:
        row["tool_calls"] = tools
    return row


def a_user(minutes_ago, text):
    return step(minutes_ago, "USER_INPUT", "USER_EXPLICIT", content=(
        "<USER_REQUEST>\n%s\n</USER_REQUEST>\n<ADDITIONAL_METADATA>\nThe current local time is: x.\n"
        "</ADDITIONAL_METADATA>" % text))


def a_tool(minutes_ago, text=None):
    return step(minutes_ago, "PLANNER_RESPONSE", content=text, tools=[{"name": "run_command", "args": {}}])


def a_result(minutes_ago, status="DONE"):
    return step(minutes_ago, "GENERIC", status=status, content="Created At: x")


def a_final(minutes_ago, text="완료"):
    return step(minutes_ago, "PLANNER_RESPONSE", content=text)


def a_system(minutes_ago, text):
    return step(minutes_ago, "SYSTEM_MESSAGE", "SYSTEM", content=(
        "The following is a <SYSTEM_MESSAGE> not actually sent by the user.\n<SYSTEM_MESSAGE>\n%s\n"
        "</SYSTEM_MESSAGE>" % text))


class InterjectScanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ai-debate-scan-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.codex = self.root / "codex"
        self.claude = self.root / "claude"
        self.grok = self.root / "grok"
        self.agy = self.root / "agy" / "brain"
        for folder in (self.codex, self.claude, self.grok, self.agy):
            folder.mkdir(parents=True)
        env = {"AI_DEBATE_NOW": NOW.isoformat(), "AI_DEBATE_HOME": str(self.root / "home"),
               "AI_DEBATE_CODEX_SESSIONS": str(self.root / "none"),
               "AI_DEBATE_CLAUDE_PROJECTS": str(self.root / "none"),
               "AI_DEBATE_GROK_SESSIONS": str(self.root / "none"),
               "AI_DEBATE_AGY_BRAIN": str(self.root / "none"),
               "AI_DEBATE_GROK_LOG": str(self.root / "none.jsonl"),
               "AI_DEBATE_CLAUDE_BRIDGE": str(self.root / "none")}
        for key in ("OPENAI", "XAI", "GOOGLE", "ANTHROPIC", "ORCA"):
            env["AI_DEBATE_CMD_" + key] = "[]"
        patcher = patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, path, records, idle_min=0):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
                        encoding="utf-8")
        moment = (NOW - timedelta(minutes=idle_min)).timestamp()
        os.utime(path, (moment, moment))
        return path

    def rollout(self, name, records, idle_min=0):
        return self.write(self.codex / "2026" / "10" / "01" / ("rollout-" + name + ".jsonl"),
                          flatten(records), idle_min)

    def transcript(self, name, records, idle_min=0):
        return self.write(self.claude / "E--work" / (name + ".jsonl"), records, idle_min)

    def grok_session(self, sid, records, idle_min=0, title="", cwd="E:\\work", kind=None):
        folder = self.grok / quote(cwd, safe="") / sid
        folder.mkdir(parents=True, exist_ok=True)
        summary = {"info": {"id": sid, "cwd": cwd}, "generated_title": title, "session_summary": title,
                   "current_model_id": "grok-4.7", "reasoning_effort": "xhigh",
                   "created_at": iso(NOW - timedelta(hours=3)), "last_active_at": iso(NOW)}
        if kind:
            summary["session_kind"] = kind
        (folder / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
        (folder / "chat_history.jsonl").write_text('{"type": "system", "content": "x"}\n', encoding="utf-8")
        return self.write(folder / "updates.jsonl", records, idle_min)

    def agy_session(self, cid, records, idle_min=0, workspace=None):
        if workspace:
            with open(self.agy.parent / "history.jsonl", "a", encoding="utf-8") as stream:
                stream.write(json.dumps({"display": "요청", "timestamp": ms(100), "workspace": workspace,
                                         "conversationId": cid}, ensure_ascii=False) + "\n")
        return self.write(self.agy / cid / ".system_generated" / "logs" / "transcript.jsonl", records, idle_min)

    def grok_billing(self, pct, end):
        record = {"ts": "2026-10-01T09:00:00.000Z", "msg": "billing: fetched credits config",
                  "ctx": {"config": {"creditUsagePercent": float(pct), "currentPeriod": {"end": end.isoformat()},
                                     "onDemandCap": {"val": 0}, "prepaidBalance": {"val": 0}}}}
        (self.root / "none.jsonl").write_text('{"msg": "other"}\n' + json.dumps(record) + "\n", encoding="utf-8")

    def scan(self, *extra):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = interject_scan.main(["scan", "--json", "--codex-root", str(self.codex),
                                      "--claude-root", str(self.claude), "--grok-root", str(self.grok),
                                      "--agy-root", str(self.agy), *extra])
        return rc, json.loads(out.getvalue())

    def rows(self, *extra):
        _rc, result = self.scan(*extra)
        return {r["session_id"] or Path(r["file"]).stem: r for r in result["sessions"]}

    def only(self, result, agent_name="codex"):
        rows = [r for r in result["sessions"] if r["agent"] == agent_name]
        self.assertEqual(len(rows), 1, rows)
        return rows[0]

    def snapshot(self, path):
        out_path = self.root / ("snap-%s.md" % path.stem)
        out = io.StringIO()
        with redirect_stdout(out):
            rc = interject_scan.main(["snapshot", "--file", str(path), "--out", str(out_path)])
        self.assertEqual(rc, 0)
        return out_path.read_text(encoding="utf-8"), json.loads(out.getvalue())

    def stuck_codex(self):
        return self.rollout("stuck", [
            session_meta(), started(90, "turn-a"), goal_block(88, "캐시 계층 리팩터링"),
            user(88, "시작해"), agent(60, "진행 중"),
            user(10, "왜 이렇게 오래 걸려? 언제 끝나?"),
            user(9, "<environment_context>cwd</environment_context>"),
            agent(8, "판정 HOLD — 증거 부족"), agent(6, "다시 HOLD 유지"), agent(4, "여전히 HOLD"),
            quota(3, 100)])

    def test_stuck_codex_turn_fires_all_triggers(self):
        self.stuck_codex()
        rc, result = self.scan()
        self.assertEqual(rc, 0)
        row = self.only(result)
        self.assertEqual(row["status"], "ok")
        self.assertTrue(row["turn_open"])
        self.assertAlmostEqual(row["elapsed_min"], 90, delta=0.5)
        self.assertFalse(row["elapsed_lower_bound"])
        self.assertEqual(row["triggers"], ["T1_LONG_TURN", "T2_LOOP", "T3_USER_FRUSTRATION", "T5_QUOTA"])
        self.assertEqual(row["detail"]["loop_matches"], 3)
        self.assertEqual(row["goal"], "캐시 계층 리팩터링")
        self.assertEqual(row["last_user_text"], "왜 이렇게 오래 걸려? 언제 끝나?")
        self.assertEqual(row["recommendation"], "ai-debate interject")
        self.assertEqual(row["session_id"], "s-main")
        rc, _result = self.scan("--fail-on-trigger")
        self.assertEqual(rc, 10)

    def test_closed_turn_has_no_long_turn_trigger(self):
        self.rollout("closed", [session_meta(), started(120, "turn-a"), user(119, "작업해"),
                                agent(30, "완료"), finished(29, "turn-a"), quota(28, 100)])
        rc, result = self.scan("--fail-on-trigger")
        row = self.only(result)
        self.assertFalse(row["turn_open"])
        self.assertEqual(row["triggers"], [])
        self.assertEqual(rc, 0)

    def test_overlapping_turns_pair_by_turn_id(self):
        self.rollout("overlap-closed", [session_meta("s1"), started(100, "A"), started(50, "B"),
                                        finished(40, "B"), finished(30, "A", "turn_aborted")])
        self.rollout("overlap-open", [session_meta("s2"), started(100, "A"), started(50, "B"),
                                      finished(40, "A")])
        _rc, result = self.scan()
        rows = {r["session_id"]: r for r in result["sessions"]}
        self.assertFalse(rows["s1"]["turn_open"])
        self.assertTrue(rows["s2"]["turn_open"])
        self.assertAlmostEqual(rows["s2"]["elapsed_min"], 50, delta=0.5)
        self.assertEqual(rows["s2"]["triggers"], ["T1_LONG_TURN"])

    def test_fork_session_is_unknown_even_when_meta_exceeds_head(self):
        self.rollout("fork", [session_meta("s-fork", fork=True, padding=70000), started(200, "A")])
        _rc, result = self.scan()
        row = self.only(result)
        self.assertEqual(row["status"], "unknown")
        self.assertEqual(row["session_id"], "s-fork")
        self.assertEqual(row["triggers"], [])

    def test_claude_turn_in_progress_fires_long_turn(self):
        project = self.claude / "E--work"
        self.write(project / "c-1.jsonl", [
            {"type": "ai-title", "aiTitle": "결제 모듈 정리", "sessionId": "c-1"},
            said(200, "이전 작업"), replied(190, text="끝"),
            cl(189, type="system", subtype="turn_duration", durationMs=60000),
            said(60, [{"type": "text", "text": "리팩터링 해줘"}]),
            cl(59, type="assistant", message={"role": "assistant", "stop_reason": "tool_use",
                                               "content": [{"type": "tool_use", "id": "t1", "name": "Bash"}]}),
            said(58, [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]),
            said(57, "skill text", isMeta=True),
            replied(2, stop=None, text="아직 보류")])
        self.write(project / "c-1" / "subagents" / "agent-x.jsonl", [said(100, "sub")])
        self.write(project / "c-2.jsonl", [said(30, "짧은 질문", "c-2"), replied(29, sid="c-2")])
        _rc, result = self.scan()
        rows = {r["session_id"]: r for r in result["sessions"] if r["agent"] == "claude"}
        self.assertEqual(sorted(rows), ["c-1", "c-2"])
        self.assertTrue(rows["c-1"]["turn_open"])
        self.assertAlmostEqual(rows["c-1"]["elapsed_min"], 60, delta=0.5)
        self.assertEqual(rows["c-1"]["triggers"], ["T1_LONG_TURN"])
        self.assertEqual(rows["c-1"]["goal"], "결제 모듈 정리")
        self.assertEqual(rows["c-1"]["last_user_text"], "리팩터링 해줘")
        self.assertFalse(rows["c-2"]["turn_open"])
        self.assertEqual(rows["c-2"]["triggers"], [])

    def test_old_files_are_skipped(self):
        path = self.stuck_codex()
        old = (NOW - timedelta(hours=20)).timestamp()
        os.utime(path, (old, old))
        _rc, result = self.scan("--hours", "12")
        self.assertEqual(result["sessions"], [])

    def test_snapshot_is_capped_and_feeds_interject_debate(self):
        rows = [session_meta(), started(95, "A"), goal_block(94, "대형 이관")]
        for i in range(12):
            rows += [user(90 - i * 7, "요청 %d " % i + "가" * 5000),
                     agent(89 - i * 7, "보고 %d " % i + "나" * 4000)]
        rows.append(quota(1, 100))
        path = self.rollout("big", rows)
        text, meta = self.snapshot(path)
        self.assertLessEqual(len(text), interject_scan.SNAPSHOT_CHARS)
        self.assertLessEqual(len(text.encode("utf-8")), interject_scan.SNAPSHOT_BYTES)
        for item in ("# 작업 중 에이전트 스냅숏", "대형 이관", "T1_LONG_TURN", "## 최근 사용자 메시지",
                     "## 최근 에이전트 메시지", "구매 크레딧"):
            self.assertIn(item, text)
        self.assertEqual(meta["chars"], len(text))
        self.assertEqual(meta["redacted"], 0)
        out_path = self.root / ("snap-%s.md" % path.stem)
        quiet = io.StringIO()
        with redirect_stdout(quiet), redirect_stderr(io.StringIO()):
            rc = debate.main(["new", "--id", "dbt-int", "--title", "겐세이", "--question",
                              "지금 무엇을 하라고 할까?", "--mode", "interject", "--evidence-file",
                              str(out_path), "--no-probe", "--orchestrator", "anthropic"])
        self.assertEqual(rc, 0)
        agenda = json.loads((self.root / "home" / "debates" / "dbt-int" / "agenda.json")
                            .read_text(encoding="utf-8"))
        self.assertEqual(agenda["evidence"], text.strip())

    # 1. secrets never reach the evidence or the scan output
    def test_secrets_are_masked_in_snapshot_and_scan(self):
        path = self.rollout("secret", [
            session_meta("s-sec"), started(90, "A"),
            user(80, "이 키로 배포해: %s %s" % SECRETS[:2]),
            agent(70, "OPENAI_API_KEY=%s 설정, Authorization: Bearer %s, %s, %s, password: %s, subtask-%s" % (
                SECRETS[0], SECRETS[2], SECRETS[3], SECRETS[4], SECRETS[5], "abcdefghijklmnopqrstuvwxyz")),
            user(5, "토큰은 token=%s 이야. Tokens used: 15, max_tokens: 3" % SECRETS[6])])
        text, meta = self.snapshot(path)
        for secret in SECRETS:
            self.assertNotIn(secret, text)
        self.assertIn("[REDACTED]", text)
        self.assertIn("Tokens used: 15, max_tokens: 3", text)
        self.assertIn("subtask-abcdefghijklmnopqrstuvwxyz", text)
        self.assertGreaterEqual(meta["redacted"], 8)
        row = self.rows()["s-sec"]
        self.assertEqual(row["last_user_text"], "토큰은 token=[REDACTED] 이야. Tokens used: 15, max_tokens: 3")
        self.assertNotIn(SECRETS[6], row["goal"])
        self.assertEqual(row["redacted"], 2)

    # 2. the open turn's start and the last human messages are found beyond the first tail chunk
    def long_codex(self, name="long"):
        rows = [session_meta("s-" + name), started(110, "A"), user(109, "캐시 리팩터링 해줘"),
                user(100, "왜 이렇게 오래 걸려?")]
        rows += [command(99 - i, "A") for i in range(80)]
        return self.rollout(name, rows + agent(5, "진행 중"))

    def test_tail_grows_backwards_to_find_the_open_turn(self):
        self.long_codex()
        with tiny_tail():
            row = self.rows()["s-long"]
        self.assertTrue(row["turn_open"])
        self.assertAlmostEqual(row["elapsed_min"], 110, delta=0.5)
        self.assertFalse(row["start_before_tail"])
        self.assertEqual(row["triggers"], ["T1_LONG_TURN", "T3_USER_FRUSTRATION"])
        self.assertEqual(row["last_user_text"], "왜 이렇게 오래 걸려?")

    def test_turn_start_beyond_the_cap_is_a_lower_bound(self):
        path = self.long_codex()
        with tiny_tail(cap=12288):
            row = self.rows()["s-long"]
            window = interject_scan.Window(path, interject_scan.CODEX_TAIL)
            while window.grow():
                pass
        self.assertGreaterEqual(window.begin, path.stat().st_size - 12288)
        self.assertTrue(row["turn_open"])
        self.assertTrue(row["start_before_tail"])
        self.assertTrue(row["elapsed_lower_bound"])
        self.assertGreater(row["elapsed_min"], 5)
        self.assertLess(row["elapsed_min"], 99)
        self.assertEqual(row["status"], "ok")

    def test_line_longer_than_a_chunk_does_not_stall_growth(self):
        self.rollout("wide", [session_meta("s-wide"), started(110, "A"), user(109, "요청"),
                              command(100, "A", size=10000), agent(5, "진행 중", "A")])
        with tiny_tail():
            row = self.rows()["s-wide"]
        self.assertAlmostEqual(row["elapsed_min"], 110, delta=0.5)
        self.assertFalse(row["start_before_tail"])

    def test_claude_compact_summary_is_not_a_turn_start(self):
        filler = [cl(119 - i, type="assistant", message={
            "role": "assistant", "stop_reason": "tool_use",
            "content": [{"type": "tool_use", "id": "t%d" % i, "name": "Bash", "input": {"c": "x" * 500}}]})
            for i in range(80)]
        records = [said(130, "이전"), replied(125), cl(124, type="system", subtype="turn_duration"),
                   said(120, "리팩터링 해줘")] + filler + [
            said(30, "This session is being continued from a previous conversation. 왜 이렇게 오래 걸려",
                 isCompactSummary=True),
            cl(29, type="assistant", message={"role": "assistant", "stop_reason": "tool_use",
                                               "content": [{"type": "tool_use", "id": "z", "name": "Bash"}]}),
            replied(1, stop=None, text="작업 중")]
        self.transcript("c-long", records)
        with tiny_tail():
            row = self.rows()["c-1"]
        self.assertAlmostEqual(row["elapsed_min"], 120, delta=0.5)
        self.assertFalse(row["start_before_tail"])
        self.assertEqual(row["last_user_text"], "리팩터링 해줘")
        self.assertEqual(row["triggers"], ["T1_LONG_TURN"])
        with tiny_tail(cap=12288):
            row = self.rows()["c-1"]
        self.assertTrue(row["start_before_tail"])
        self.assertGreater(row["elapsed_min"], 30)
        self.assertLess(row["elapsed_min"], 120)

    def test_snapshot_recovers_human_messages_beyond_the_tail(self):
        rows = [session_meta("s-snap"), started(110, "A"), user(109, "첫째 요청"), user(108, "둘째 요청"),
                user(107, "셋째 요청")]
        rows += [command(100 - i, "A") for i in range(80)]
        path = self.rollout("snap", rows + agent(5, "진행 중"))
        with tiny_tail():
            text, _meta = self.snapshot(path)
        for item in ("첫째 요청", "둘째 요청", "셋째 요청"):
            self.assertIn(item, text)

    # 3. T2/T3 only while the turn is open; stop requests are STOP, not frustration
    def test_closed_turns_get_no_t2_t3_or_recommendation(self):
        self.rollout("stop-obeyed", [session_meta("s-stop"), started(60, "A"), user(59, "작업해"),
                                     user(20, "멈추고 그만해. 그리고 /simon-handoff"),
                                     agent(15, "핸드오프 완료"), finished(14, "A")])
        self.rollout("vented", [session_meta("s-vent"), started(60, "A"), user(59, "작업해"),
                                user(30, "왜 이렇게 오래 걸려"), agent(20, "완료"), finished(10, "A")])
        self.rollout("loop-closed", [session_meta("s-loop"), started(200, "A"), user(199, "작업해")]
                     + [agent(50 - i * 5, "단계 %d 완료, 배포는 보류 유지" % i) for i in range(4)]
                     + [finished(25, "A")])
        rc, result = self.scan("--fail-on-trigger")
        self.assertEqual(rc, 0)
        rows = {r["session_id"]: r for r in result["sessions"]}
        for sid in ("s-stop", "s-vent", "s-loop"):
            self.assertEqual(rows[sid]["triggers"], [], sid)
            self.assertEqual(rows[sid]["recommendation"], "", sid)
        self.assertEqual(rows["s-stop"]["note"], "user already stopped it")
        self.assertEqual(rows["s-vent"]["note"], "")

    def test_stop_request_ignored_for_five_minutes_triggers_t4(self):
        self.rollout("ignored", [session_meta("s-ign"), started(30, "A"), user(29, "작업해"),
                                 agent(20, "진행"), user(12, "멈춰"), agent(3, "계속 진행")])
        self.rollout("fresh", [session_meta("s-fresh"), started(30, "A"), user(29, "작업해"),
                               user(10, "답답해 진짜"), user(2, "> 결제할까요? 중단할까요?\n\n그만해"),
                               agent(1, "멈추는 중")])
        self.rollout("quoted", [session_meta("s-quote"), started(30, "A"), user(29, "작업해"),
                                user(10, "> 계속할까요, 중단할까요?\n\n계속해. 근데 답답하네"), agent(1, "진행")])
        rows = self.rows()
        self.assertEqual(rows["s-ign"]["triggers"], ["T4_IGNORED_STOP"])
        self.assertEqual(rows["s-ign"]["detail"]["stop_ignored_min"], 12)
        self.assertEqual(rows["s-ign"]["recommendation"], "ai-debate interject")
        self.assertEqual(rows["s-fresh"]["triggers"], [])
        self.assertEqual(rows["s-quote"]["triggers"], ["T3_USER_FRUSTRATION"])

    def test_message_that_opened_the_turn_is_not_feedback_on_it(self):
        self.transcript("orchestrator", [
            said(50, "codex가 작업을 진행하고 있었는데, 작업이 너무 오래 걸려서 너한테 전달해줄께."),
            cl(49, type="assistant", message={"role": "assistant", "stop_reason": "tool_use",
                                               "content": [{"type": "tool_use", "id": "a", "name": "Bash"}]}),
            replied(1, stop=None, text="확인 중")])
        self.rollout("orca", [session_meta("s-orca"), started(10, "A"),
                              user(10 - 1 / 60, "You are a dispatched worker. 코디네이터가 패치를 멈추고 경계를 "
                                                "재배치했다. 리뷰해."), agent(3, "리뷰 시작")])
        rows = self.rows()
        self.assertEqual(rows["c-1"]["triggers"], ["T1_LONG_TURN"])
        self.assertEqual(rows["s-orca"]["triggers"], [])

    def test_claude_queued_human_messages_count_as_mid_turn_feedback(self):
        def queued(minutes_ago, prompt, kind="human"):
            return cl(minutes_ago, type="attachment", attachment={
                "type": "queued_command", "prompt": prompt, "commandMode": "prompt", "origin": {"kind": kind}})

        self.transcript("c-q", [said(40, "작업해"), replied(39, stop="tool_use"),
                                queued(20, "왜 이렇게 오래 걸려?"), queued(15, "<cross-session-message>멈춰", "peer"),
                                replied(1, stop=None)])
        self.transcript("c-s", [said(40, "작업해", "c-s"), replied(39, stop="tool_use", sid="c-s"),
                                dict(queued(10, "멈춰"), sessionId="c-s"), replied(1, stop=None, sid="c-s")])
        rows = self.rows()
        self.assertEqual(rows["c-1"]["triggers"], ["T3_USER_FRUSTRATION"])
        self.assertEqual(rows["c-s"]["triggers"], ["T4_IGNORED_STOP"])

    # 4. dead, interrupted and stop_sequence turns do not stay open
    def test_dead_and_interrupted_turns_are_not_long_turns(self):
        self.transcript("c-int", [said(180, "리팩터링 해줘", "c-int"), replied(179, "tool_use", sid="c-int"),
                                  said(178, [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}], "c-int"),
                                  said(177, [{"type": "text", "text": "[Request interrupted by user]"}], "c-int")])
        self.transcript("c-seq", [said(120, "review PR", "c-seq", entrypoint="sdk-cli"),
                                  replied(120, "stop_sequence", "Not logged in", "c-seq")])
        self.transcript("c-idle", [said(100, "작업해", "c-idle"), replied(40, "tool_use", sid="c-idle")],
                        idle_min=40)
        self.transcript("c-cont", [said(100, "작업해", "c-cont"), replied(60, "max_tokens", sid="c-cont"),
                                   said(59, "Output token limit hit. Resume.", "c-cont", isMeta=True),
                                   replied(2, None, sid="c-cont")])
        self.rollout("dead", [dict(session_meta("s-dead"), timestamp=iso(NOW - timedelta(minutes=401))),
                              started(400, "A"), user(399, "업데이트 해줘"),
                              agent(360, "진행 중")], idle_min=360)
        rows = self.rows("--fail-on-trigger")
        for sid in ("c-int", "c-seq"):
            self.assertFalse(rows[sid]["turn_open"], sid)
            self.assertEqual(rows[sid]["triggers"], [], sid)
        for sid, idle in (("c-idle", 40), ("s-dead", 360)):
            self.assertEqual(rows[sid]["status"], "stale", sid)
            self.assertTrue(rows[sid]["turn_open"], sid)
            self.assertEqual(rows[sid]["idle_min"], idle, sid)
            self.assertEqual(rows[sid]["triggers"], [], sid)
            self.assertEqual(rows[sid]["recommendation"], "", sid)
        self.assertTrue(rows["c-cont"]["turn_open"])
        self.assertAlmostEqual(rows["c-cont"]["elapsed_min"], 59, delta=0.5)

    # 5. only same-message copies are deduplicated
    def test_identical_repeats_still_count(self):
        self.rollout("loop", [session_meta("s-loop"), started(70, "A"), user(65, "판정해")]
                     + [agent(60 - i * 10, "판정: HOLD — 증거 부족") for i in range(5)])
        self.rollout("copies", [session_meta("s-copy"), started(70, "A"), user(65, "판정해"),
                                agent(30, "HOLD"), agent(30 - 1 / 120, "HOLD"), agent(20, "HOLD 유지")])
        self.rollout("repeat", [session_meta("s-rep"), started(250, "A"), user(240, "왜 이렇게 오래 걸려?"),
                                agent(200, "확인 중"), user(10, "왜 이렇게 오래 걸려?")])
        rows = self.rows()
        self.assertEqual(rows["s-loop"]["triggers"], ["T1_LONG_TURN", "T2_LOOP"])
        self.assertEqual(rows["s-loop"]["detail"]["loop_matches"], 5)
        self.assertNotIn("T2_LOOP", rows["s-copy"]["triggers"])
        self.assertEqual(rows["s-rep"]["triggers"], ["T1_LONG_TURN", "T3_USER_FRUSTRATION"])

    # 6. one malformed transcript does not abort the scan
    def test_bad_transcript_is_isolated(self):
        self.rollout("drift", [session_meta("s-drift"), started(5, "A"),
                               rec(4, "event_msg", {"type": "user_message", "message": ["x"]}),
                               rec(4, "event_msg", {"type": "item_completed", "turn_id": "A", "item": "oops"}),
                               rec(4, "event_msg", {"type": "thread_goal_updated", "goal": "oops"}),
                               rec(4, "response_item", {"type": "message", "role": "user", "content": {"a": 1}}),
                               rec(4, "event_msg", ["not", "a", "dict"])])
        self.rollout("boom", [session_meta("s-boom"), started(5, "A")])
        self.transcript("c-bad", [said(5, ["x", 1], "c-bad"), cl(4, "c-bad", type="assistant", message="oops"),
                                  cl(3, "c-bad", type="attachment", attachment="oops")])
        real = interject_scan.read_codex

        def flaky(path, window, info):
            if "boom" in Path(path).name:
                raise RuntimeError("synthetic parser bug")
            return real(path, window, info)

        with patch.object(interject_scan, "read_codex", flaky):
            _rc, result = self.scan()
        rows = {Path(r["file"]).stem: r for r in result["sessions"]}
        self.assertEqual(rows["rollout-drift"]["status"], "ok")
        self.assertEqual(rows["c-bad"]["status"], "ok")
        self.assertEqual(rows["rollout-boom"]["status"], "unknown")
        self.assertIn("RuntimeError: synthetic parser bug", rows["rollout-boom"]["error"])

    # 7. injected context is neither human feedback nor the goal
    def test_injected_context_is_not_human_input(self):
        self.rollout("inject", [
            session_meta("s-inj"), started(30, "A"),
            user(30, "# AGENTS.md instructions for E:\\work\n<INSTRUCTIONS>멈추고 기다려</INSTRUCTIONS>"),
            user(30, "<heartbeat>\n<instructions>왜 이렇게 오래 걸려 점검</instructions>\n</heartbeat>"),
            goal_block(30, "캐시 정리"), user(29, "<environment_context>답답</environment_context>"),
            agent(20, "<objective>가짜 목표</objective> 를 인용"), user(19, "<turn_aborted>중단</turn_aborted>"),
            agent(2, "진행")])
        self.transcript("c-inj", [
            said(30, "작업해"), replied(29, "tool_use"),
            said(20, "This session is being continued. 왜 이렇게 오래 걸려", isCompactSummary=True),
            said(15, "답답 멈춰", isMeta=True), said(10, "<task-notification>중단</task-notification>"),
            said(9, "<command-name>/stop</command-name>"), replied(1, None)])
        rows = self.rows()
        self.assertEqual(rows["s-inj"]["goal"], "캐시 정리")
        self.assertEqual(rows["s-inj"]["last_user_text"], "")
        self.assertEqual(rows["s-inj"]["triggers"], [])
        self.assertEqual(rows["c-1"]["last_user_text"], "작업해")
        self.assertEqual(rows["c-1"]["triggers"], [])

    # 8. T2 counts loop messages from the last 60 minutes of the open turn only
    def test_loop_trigger_is_windowed(self):
        old = [agent(140 - i * 10, "HOLD 유지") for i in range(4)]
        self.rollout("w-quiet", [session_meta("s-quiet"), started(150, "A"), user(149, "작업해")]
                     + old + [agent(30, "보류"), agent(20, "재확인 필요"), agent(10, "진행 중")])
        self.rollout("w-loud", [session_meta("s-loud"), started(150, "A"), user(149, "작업해")]
                     + old + [agent(30, "보류"), agent(20, "재확인 필요"), agent(10, "NO-GO")])
        rows = self.rows()
        self.assertEqual(rows["s-quiet"]["triggers"], ["T1_LONG_TURN"])
        self.assertEqual(rows["s-loud"]["triggers"], ["T1_LONG_TURN", "T2_LOOP"])
        self.assertEqual(rows["s-loud"]["detail"]["loop_matches"], 3)

    # 9. a long-running Codex thread goal fires T6 while a turn is open
    def test_goal_long_trigger(self):
        self.rollout("g-used", [session_meta("s-used"), goal_update(40, "장기 목표", used=6000),
                                started(30, "G"), goal_block(30, "장기 목표"), agent(1, "진행")])
        self.rollout("g-created", [session_meta("s-created"), goal_update(40, "생성 목표", created_min=150),
                                   started(20, "G"), agent(1, "진행")])
        turns = [started(200, "G1"), goal_block(200, "관찰 목표"), finished(150, "G1"),
                 started(149, "G2"), goal_block(149, "관찰 목표"), finished(100, "G2"),
                 started(30, "G3"), goal_block(30, "관찰 목표"), agent(1, "진행")]
        self.rollout("g-seen", [session_meta("s-seen")] + turns)
        self.rollout("g-paused", [session_meta("s-paused")] + turns + [goal_update(1, "관찰 목표", "paused")])
        self.rollout("g-closed", [session_meta("s-closed")] + turns + [finished(0.5, "G3")])
        rows = self.rows()
        self.assertEqual(rows["s-used"]["triggers"], ["T6_GOAL_LONG"])
        self.assertAlmostEqual(rows["s-used"]["goal_minutes"], 130, delta=0.5)
        self.assertEqual(rows["s-used"]["goal_basis"], "timeUsedSeconds")
        self.assertEqual(rows["s-created"]["triggers"], ["T6_GOAL_LONG"])
        self.assertAlmostEqual(rows["s-created"]["goal_minutes"], 150, delta=0.5)
        self.assertEqual(rows["s-seen"]["triggers"], ["T6_GOAL_LONG"])
        self.assertAlmostEqual(rows["s-seen"]["goal_minutes"], 129, delta=0.5)
        self.assertEqual(rows["s-seen"]["goal"], "관찰 목표")
        self.assertEqual(rows["s-paused"]["triggers"], [])
        self.assertIsNone(rows["s-paused"]["goal_minutes"])
        self.assertEqual(rows["s-closed"]["triggers"], [])

    def test_goal_turns_before_the_tail_are_found(self):
        rows = [session_meta("s-far")]
        for turn, begin, end in (("G1", 200, 150), ("G2", 149, 100)):
            rows += [started(begin, turn), goal_block(begin, "관찰 목표")]
            rows += [command(begin - 1 - i / 10, turn) for i in range(10)] + [finished(end, turn)]
        rows += [started(30, "G3"), goal_block(30, "관찰 목표"), user(25, "가", "G3"), user(20, "나", "G3"),
                 user(15, "다", "G3"), agent(1, "진행", "G3")]
        self.rollout("far", rows)
        with tiny_tail():
            row = self.rows()["s-far"]
        self.assertAlmostEqual(row["goal_minutes"], 129, delta=0.5)
        self.assertEqual(row["triggers"], ["T6_GOAL_LONG"])

    # 10. Grok CLI sessions
    def stuck_grok(self):
        return self.grok_session("g-1", [
            g_hook(91, "session_start"), g_hook(90, "user_prompt_submit"), g_user(90, "캐시 리팩터링 해줘"),
            g_agent(60, "진행 중", start_min=90), g_tool(59), g_user(10, "왜 이렇게 오래 걸려?"),
            g_agent(8, "판정 HOLD — 증거 부족"), g_tool(7), g_agent(6, "다시 HOLD 유지"), g_tool(5),
            gk(5, "agent_thought_chunk", "p-1", content={"type": "text", "text": "HOLD?"}),
            g_agent(4, "여전히 HOLD"), g_tool(3)], title="캐시 계층 리팩터링")

    def test_grok_open_turn_fires_triggers(self):
        self.stuck_grok()
        self.grok_billing(100, NOW + timedelta(days=2))
        rc, result = self.scan("--fail-on-trigger")
        self.assertEqual(rc, 10)
        self.assertIn("grok", result["roots"])
        row = self.only(result, "grok")
        self.assertEqual((row["agent"], row["session_id"], row["cwd"], row["status"]), ("grok", "g-1", "E:\\work", "ok"))
        self.assertTrue(row["turn_open"])
        self.assertAlmostEqual(row["elapsed_min"], 90, delta=0.5)
        self.assertEqual(row["triggers"], ["T1_LONG_TURN", "T2_LOOP", "T3_USER_FRUSTRATION", "T5_QUOTA"])
        self.assertEqual(row["detail"]["loop_matches"], 3)
        self.assertEqual(row["detail"]["quota"]["credits"]["used_percent"], 100.0)
        self.assertEqual(row["goal"], "캐시 계층 리팩터링")
        self.assertEqual(row["last_user_text"], "왜 이렇게 오래 걸려?")
        self.grok_billing(78, NOW + timedelta(days=2))
        self.assertNotIn("T5_QUOTA", self.only(self.scan()[1], "grok")["triggers"])
        self.grok_billing(100, NOW - timedelta(minutes=1))
        self.assertNotIn("T5_QUOTA", self.only(self.scan()[1], "grok")["triggers"])

    def test_grok_closed_ended_and_stale_turns_do_not_trigger(self):
        self.grok_session("g-done", [g_user(120, "작업해"), g_agent(60, "HOLD"), g_tool(59), g_agent(58, "HOLD"),
                                     g_tool(57), g_agent(56, "HOLD"), g_hook(31, "stop"), g_done(30)])
        self.grok_session("g-end", [g_user(100, "작업해"), g_agent(99, "진행"), g_hook(98, "session_end")])
        self.grok_session("g-idle", [g_user(100, "작업해"), g_agent(40, "진행")], idle_min=40)
        self.grok_session("g-next", [g_user(200, "첫 요청"), g_done(150), g_user(20, "둘째 요청"),
                                     g_agent(2, "진행", prompt="p-2", start_min=20)])
        self.grok_billing(100, NOW + timedelta(days=2))
        rows = self.rows("--fail-on-trigger")
        for sid in ("g-done", "g-end"):
            self.assertFalse(rows[sid]["turn_open"], sid)
            self.assertEqual(rows[sid]["triggers"], [], sid)
        self.assertEqual((rows["g-idle"]["status"], rows["g-idle"]["triggers"]), ("stale", []))
        self.assertTrue(rows["g-next"]["turn_open"])
        self.assertAlmostEqual(rows["g-next"]["elapsed_min"], 20, delta=0.5)
        self.assertEqual(rows["g-next"]["triggers"], ["T5_QUOTA"])

    def test_grok_turn_start_beyond_the_tail_comes_from_turn_start_ms(self):
        records = [g_user(110, "긴 작업 해줘")] + [g_tool(100 - i / 10, size=500) for i in range(80)]
        self.grok_session("g-long", records + [g_agent(5, "진행 중", start_min=110)])
        with tiny_tail(cap=12288):
            row = self.rows()["g-long"]
        self.assertTrue(row["turn_open"])
        self.assertAlmostEqual(row["elapsed_min"], 110, delta=0.5)
        self.assertFalse(row["start_before_tail"])
        self.assertEqual(row["triggers"], ["T1_LONG_TURN"])

    # 11. agy (Antigravity CLI) sessions
    def stuck_agy(self):
        return self.agy_session("a-1", [
            a_user(70, "번역 파일 정리해줘"), a_tool(69), a_result(68), a_tool(8, "판정 HOLD 유지"), a_result(7),
            a_tool(6, "다시 보류"), a_result(5), a_tool(4, "여전히 HOLD"), a_result(3, "RUNNING")],
            workspace="D:\\proj")

    def test_agy_open_turn_fires_triggers(self):
        self.stuck_agy()
        _rc, result = self.scan()
        self.assertIn("agy", result["roots"])
        row = self.only(result, "agy")
        self.assertEqual((row["agent"], row["session_id"], row["cwd"], row["status"]), ("agy", "a-1", "D:\\proj", "ok"))
        self.assertTrue(row["turn_open"])
        self.assertAlmostEqual(row["elapsed_min"], 70, delta=0.5)
        self.assertEqual(row["triggers"], ["T1_LONG_TURN", "T2_LOOP"])
        self.assertEqual(row["last_user_text"], "번역 파일 정리해줘")
        self.assertEqual(row["goal"], "번역 파일 정리해줘")

    def test_agy_final_answer_closes_and_system_messages_are_not_human(self):
        self.agy_session("a-done", [a_user(100, "작업해"), a_tool(99, "HOLD"), a_result(98), a_final(90)])
        self.agy_session("a-sys", [a_user(200, "작업해"), a_final(150), a_system(50, "Task done. 멈춰 답답"),
                                   a_tool(49), a_result(2, "RUNNING")])
        self.agy_session("a-idle", [a_user(100, "작업해"), a_tool(40)], idle_min=40)
        self.agy_session("a-stop", [a_user(30, "작업해"), a_tool(29), a_user(12, "멈춰"), a_tool(3)])
        clipped = dict(step(20, "USER_INPUT", "USER_EXPLICIT", content="<USER_REQUEST>\n/plan 잘린 긴 요청 본문"),
                       truncated_fields=["content"])  # agy cuts long prompts before the closing tag
        self.agy_session("a-clip", [clipped, a_final(19)])
        rows = self.rows()
        self.assertEqual(rows["a-clip"]["last_user_text"], "/plan 잘린 긴 요청 본문")
        self.assertEqual(rows["a-clip"]["goal"], "/plan 잘린 긴 요청 본문")
        self.assertFalse(rows["a-done"]["turn_open"])
        self.assertEqual(rows["a-done"]["triggers"], [])
        self.assertIsNone(rows["a-done"]["cwd"])
        self.assertTrue(rows["a-sys"]["turn_open"])
        self.assertAlmostEqual(rows["a-sys"]["elapsed_min"], 50, delta=0.5)
        self.assertEqual(rows["a-sys"]["triggers"], ["T1_LONG_TURN"])
        self.assertEqual(rows["a-sys"]["last_user_text"], "작업해")
        self.assertEqual((rows["a-idle"]["status"], rows["a-idle"]["triggers"]), ("stale", []))
        self.assertEqual(rows["a-stop"]["triggers"], ["T4_IGNORED_STOP"])

    def test_grok_and_agy_snapshots(self):
        grok = self.stuck_grok()
        agy = self.stuck_agy()
        text, meta = self.snapshot(grok)
        for item in ("# 작업 중 에이전트 스냅숏", "에이전트: grok", "세션: g-1", "E:\\work", "캐시 계층 리팩터링",
                     "모델: grok-4.7 · xhigh", "T1_LONG_TURN", "왜 이렇게 오래 걸려?", "여전히 HOLD"):
            self.assertIn(item, text)
        self.assertEqual(meta["status"], "ok")
        text, meta = self.snapshot(agy)
        for item in ("에이전트: agy", "세션: a-1", "D:\\proj", "번역 파일 정리해줘", "T2_LOOP"):
            self.assertIn(item, text)
        self.assertNotIn("USER_REQUEST", text)

    def test_snapshot_takes_a_shallow_or_relative_agy_path(self):
        """P2-4: a copied transcript.jsonl outside brain/<id>/.system_generated/logs raised IndexError."""
        shallow = self.root / "shallow"
        self.write(shallow / "transcript.jsonl", [a_user(70, "번역 파일 정리해줘"), a_tool(69), a_result(68)])
        cwd = os.getcwd()
        os.chdir(shallow)
        self.addCleanup(os.chdir, cwd)
        for name in ("transcript.jsonl", str(shallow / "transcript.jsonl")):
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = interject_scan.main(["snapshot", "--file", name])
            self.assertEqual(rc, 0, err.getvalue())
            self.assertIn("에이전트: agy", out.getvalue())
            self.assertIn("번역 파일 정리해줘", out.getvalue())


if __name__ == "__main__":
    unittest.main()
