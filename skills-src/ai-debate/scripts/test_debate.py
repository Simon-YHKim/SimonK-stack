"""Offline debate.py regressions; every vendor CLI is a fake Python script."""
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import debate

NOW = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
MARK = {v: "MARK-%d" % i for i, v in enumerate(("anthropic", "openai", "xai", "google"))}
VENDOR_WORDS = re.compile(r"claude|codex|grok|gemini|anthropic|openai|xai|google|antigravity", re.I)

FAKE_CLI = r'''
import json, os, subprocess, sys, time
from pathlib import Path

vendor, state, argv = sys.argv[1], Path(sys.argv[2]), sys.argv[3:]
state.mkdir(parents=True, exist_ok=True)


def setting(name, default=""):
    path = state / name
    return path.read_text(encoding="utf-8") if path.exists() else default


def out(text, stream=None):
    (stream or sys.stdout).buffer.write(text.encode("utf-8"))
    (stream or sys.stdout).flush()


stdin_text = sys.stdin.buffer.read().decode("utf-8")
with open(state / ("calls-" + vendor + ".jsonl"), "a", encoding="utf-8") as log:
    log.write(json.dumps({"argv": argv, "stdin": stdin_text, "cwd": os.getcwd(),
                          "agy_no_update": os.environ.get("AGY_CLI_DISABLE_AUTO_UPDATE"),
                          "api_key": os.environ.get("OPENAI_API_KEY")}, ensure_ascii=False) + "\n")
if vendor == "google" and "/usage" in argv:
    if (state / "usage-json").exists():
        out(setting("usage-json"))
        sys.exit(0)
    usage = setting("usage", "1")
    if usage == "fail":
        out("AGY_ERROR: probe broke\n", sys.stderr)
        sys.exit(3)
    bucket = lambda i, w, t: {"id": i, "window": w, "remaining_fraction": float(usage), "reset_time": t}
    out(json.dumps({"conversation_id": "", "status": "SUCCESS", "response": "usage", "num_turns": 0,
                    "command": {"name": "usage", "data": {"groups": [
                        {"name": "Gemini Models", "buckets": [
                            bucket("gemini-weekly", "weekly", "2026-10-08T09:46:30Z"),
                            bucket("gemini-5h", "5h", "2026-10-01T14:46:30Z")]},
                        {"name": "Claude and GPT models", "buckets": []}]}}}))
    sys.exit(0)
mode = setting("mode-" + vendor, "ok")
answer = setting("answer-" + vendor, "## 입장\n선택지 1 — 확신도 70\n## 핵심 근거\n- fake\n")
if mode == "hang":
    survivor = state / ("survivor-" + vendor)
    kid = subprocess.Popen([sys.executable, "-c",
                            "import sys, time; time.sleep(3); open(sys.argv[1], 'w').write('alive')",
                            str(survivor)])
    (state / ("grandchild-" + vendor)).write_text(str(kid.pid))
    (state / ("spawned-" + vendor)).write_text(str(os.getpid()))
    time.sleep(60)
    sys.exit(0)
if mode == "402":
    out("API error (status 402 Payment Required): Grok Build usage balance exhausted\n", sys.stderr)
    sys.exit(1)
if mode == "429":
    out("HTTP 429 Too Many Requests: rate_limit_exceeded\n", sys.stderr)
    sys.exit(1)
if mode == "agy_error":
    out("AGY_ERROR: internal failure\n", sys.stderr)
    sys.exit(3)
if vendor == "openai":
    Path(argv[argv.index("-o") + 1]).write_text(answer, encoding="utf-8")
    out("session id: 11111111-2222-3333-4444-555555555555\n", sys.stderr)
    out(answer)
elif vendor == "xai":
    out(answer)
elif vendor == "google":
    out(json.dumps({"conversation_id": "conv-1", "status": "SUCCESS", "response": answer,
                    "num_turns": 1}, ensure_ascii=False))
elif vendor == "anthropic":
    out(json.dumps({"type": "result", "is_error": False, "result": answer, "session_id": "sess-1"},
                   ensure_ascii=False))
else:
    out(json.dumps({"ok": True}))
'''


def r1_answer(marker, option=1, confidence=70):
    return ("## 입장\n선택지 %d — 확신도 %d\n## 핵심 근거\n- %s 근거\n## 내 입장의 가장 강한 반론\n반론\n"
            "## 조건·전제\n전제\n## 기준별 평가\n| 기준 | 1 | 2 |\n" % (option, confidence, marker))


JUDGE_ANSWER = ("VERDICT: 선택지 1 채택\nCONFIDENCE: 80\n## 기준별 채점\n표\n## 판정 근거\n근거가 강하다\n"
                "## 패자가 진 이유\n- P2 근거 부족\n## 소수의견(보존)\n되돌림 비용을 과소평가했다는 반론\n"
                "## 후속 조치\n카나리 먼저\n")
INTERJECT_JUDGE = ("CALL: RESCOPE\nCONFIDENCE: 75\n## 다음 한 걸음\n테스트 하나만 고치고 보고한다\n"
                   "## 지금 자를 것\n문서 재작성\n## 시간 상자\n20\n## 판정 근거\n90분째 같은 보류 반복\n"
                   "## 소수의견(보존)\n지금 멈추자는 의견\n")


class DebateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ai-debate-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.fake = self.root / "fake_cli.py"
        self.fake.write_text(FAKE_CLI, encoding="utf-8")
        self.state = self.root / "fake-state"
        self.state.mkdir()
        env = {"AI_DEBATE_HOME": str(self.root / "home"),
               "AI_DEBATE_CODEX_SESSIONS": str(self.root / "codex"),
               "AI_DEBATE_GROK_LOG": str(self.root / "grok.jsonl"),
               "AI_DEBATE_CLAUDE_BRIDGE": str(self.root / "bridge"),
               "AI_DEBATE_TEST": "1", "AI_DEBATE_NOW": NOW.isoformat(),
               "OPENAI_API_KEY": "sk-should-not-leak"}
        for key in ("openai", "xai", "google", "anthropic", "orca"):
            env["AI_DEBATE_CMD_" + key.upper()] = json.dumps(
                [sys.executable, "-B", str(self.fake), key, str(self.state)])
        patcher = patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("AI_DEBATE_MAX_USED", None)
        (self.root / "bridge").mkdir()
        self.write_codex(10, NOW + timedelta(days=5), True)
        self.write_grok(10, NOW + timedelta(days=2))

    # ------------------------------------------------------------ fixtures
    def write_codex(self, used, reset, has_credits):
        folder = self.root / "codex" / "2026" / "10" / "01"
        folder.mkdir(parents=True, exist_ok=True)
        record = {"timestamp": "2026-10-01T09:00:00.000Z", "type": "event_msg",
                  "payload": {"type": "token_count", "info": {}, "rate_limits": {
                      "primary": {"used_percent": float(used), "window_minutes": 10080,
                                  "resets_at": int(reset.timestamp())},
                      "secondary": None, "credits": {"has_credits": has_credits, "balance": "5"},
                      "plan_type": "pro"}}}
        noise = {"timestamp": "2026-10-01T08:00:00.000Z", "type": "response_item", "payload": {}}
        (folder / "rollout-2026-10-01T08-00-00-x.jsonl").write_text(
            json.dumps(noise) + "\n" + json.dumps(record) + "\n", encoding="utf-8")

    def write_grok(self, pct, end):
        record = {"ts": "2026-10-01T02:23:00.475Z", "msg": "billing: fetched credits config",
                  "ctx": {"config": {"creditUsagePercent": float(pct), "currentPeriod": {
                      "type": "USAGE_PERIOD_TYPE_WEEKLY", "start": "2026-09-26T14:12:19+00:00",
                      "end": end.isoformat()}, "onDemandCap": {"val": 0}, "onDemandUsed": {"val": 0},
                      "prepaidBalance": {"val": 0}}, "onDemandEnabled": None,
                      "subscriptionTier": "SuperGrok Heavy"}}
        (self.root / "grok.jsonl").write_text('{"msg":"other"}\n' + json.dumps(record) + "\n",
                                              encoding="utf-8")

    def write_bridge(self, five, seven, captured=None, name="abc.json"):
        data = {"rate_limits": {
            "five_hour": {"used_percentage": five, "resets_at": int((NOW + timedelta(hours=2)).timestamp())},
            "seven_day": {"used_percentage": seven, "resets_at": int((NOW + timedelta(days=1)).timestamp())}},
            "model": {"id": "claude-opus-5-5"}}
        if captured is not None:
            data["capturedAt"] = int(captured.timestamp() * 1000)
        (self.root / "bridge" / name).write_text(json.dumps(data), encoding="utf-8")

    def setting(self, name, value):
        (self.state / name).write_text(value, encoding="utf-8")

    def calls(self, vendor):
        path = self.state / ("calls-" + vendor + ".jsonl")
        if not path.exists():
            return []
        return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = debate.main([str(a) for a in argv])
        return rc, out.getvalue(), err.getvalue()

    def new(self, debate_id="dbt-test", mode="full", orchestrator="anthropic", evidence=None, extra=()):
        argv = ["new", "--id", debate_id, "--title", "캐시 전략 결정", "--question", "어느 캐시 전략을 쓸까?",
                "--option", "메모리 캐시", "--option", "디스크 캐시", "--criterion", "되돌림 비용",
                "--criterion", "속도", "--mode", mode, "--orchestrator", orchestrator, "--no-probe", *extra]
        if evidence is not None:
            path = self.root / ("evidence-%s.md" % debate_id)
            path.write_text(evidence, encoding="utf-8")
            argv += ["--evidence-file", path]
        rc, out, err = self.run_cli(*argv)
        self.assertEqual(rc, 0, err)
        return json.loads(out)

    def agenda(self, debate_id="dbt-test"):
        return json.loads((self.folder(debate_id) / "agenda.json").read_text(encoding="utf-8"))

    def answer(self, debate_id, rnd, vendor, text, *extra):
        """Answer the way the real flow does: in-session submit for the orchestrator, a call otherwise."""
        if vendor == self.agenda(debate_id)["orchestrator"]:
            rc, _out, err = self.run_cli("prompt", "--id", debate_id, "--round", rnd, "--vendor", vendor)
            self.assertEqual(rc, 0, err)
            path = self.root / ("answer-%s-%s-%s.md" % (debate_id, rnd, vendor))
            path.write_text(text, encoding="utf-8")
            rc, _out, err = self.run_cli("submit", "--id", debate_id, "--round", rnd, "--vendor", vendor,
                                         "--file", path)
        else:
            self.setting("answer-" + vendor, text)
            rc, _out, err = self.run_cli("call", "--id", debate_id, "--round", rnd, "--vendor", vendor, *extra)
        self.assertEqual(rc, 0, err)

    def status(self, debate_id="dbt-test"):
        rc, out, err = self.run_cli("status", "--id", debate_id, "--json")
        self.assertEqual(rc, 0, err)
        return json.loads(out)

    def folder(self, debate_id="dbt-test"):
        return self.root / "home" / "debates" / debate_id

    def meta(self, rnd, vendor, debate_id="dbt-test"):
        return json.loads((self.folder(debate_id) / "rounds" / rnd / (vendor + ".meta.json"))
                          .read_text(encoding="utf-8"))

    def write_meta(self, rnd, vendor, row, debate_id="dbt-test"):
        (self.folder(debate_id) / "rounds" / rnd / (vendor + ".meta.json")).write_text(
            json.dumps(row), encoding="utf-8")

    def reap(self, pid):
        if debate.pid_alive(pid):
            if os.name == "nt":
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True)
            else:
                os.kill(pid, signal.SIGKILL)

    def wait_for(self, predicate, seconds=20.0):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if predicate():
                return True
            time.sleep(0.1)
        return predicate()

    # ------------------------------------------------------------ seats
    def test_codex_spent_with_credits_is_absent(self):
        self.write_codex(100, NOW + timedelta(days=5), True)
        seat = debate.seat_for("openai", "anthropic")
        self.assertEqual(seat["status"], "ABSENT")
        self.assertIn("further calls would bill purchased credits", seat["reason"])
        self.assertEqual(seat["reset_kst"], debate.kst(NOW + timedelta(days=5)))
        self.assertIn("구매 크레딧", seat["short"])

    def test_codex_window_reset_since_snapshot_is_ready(self):
        self.write_codex(100, NOW - timedelta(hours=1), True)
        seat = debate.seat_for("openai", "anthropic")
        self.assertEqual((seat["status"], seat["reason"]), ("READY", "window reset since snapshot"))

    def test_codex_without_evidence_is_unknown(self):
        os.environ["AI_DEBATE_CODEX_SESSIONS"] = str(self.root / "missing")
        self.assertEqual(debate.seat_for("openai", "anthropic")["status"], "UNKNOWN")

    def test_grok_spent_until_period_end_is_absent(self):
        self.write_grok(100, NOW + timedelta(days=2))
        seat = debate.seat_for("xai", "anthropic")
        self.assertEqual(seat["status"], "ABSENT")
        self.assertIn("HTTP 402 expected until " + debate.kst(NOW + timedelta(days=2)), seat["reason"])

    def test_grok_period_ended_is_ready(self):
        self.write_grok(100, NOW - timedelta(minutes=5))
        self.assertEqual(debate.seat_for("xai", "anthropic")["status"], "READY")

    def test_agy_probe_states(self):
        self.setting("usage", "1")
        self.assertEqual(debate.seat_for("google", "anthropic")["status"], "READY")
        self.setting("usage", "0")
        seat = debate.seat_for("google", "anthropic")
        self.assertEqual(seat["status"], "ABSENT")
        self.assertIn("2026-10-08", seat["reset_kst"])
        self.setting("usage", "fail")
        self.assertEqual(debate.seat_for("google", "anthropic")["status"], "UNKNOWN")
        self.assertEqual(debate.seat_for("google", "anthropic", probe=False)["status"], "UNKNOWN")
        probes = self.calls("google")
        self.assertEqual(len(probes), 3)
        self.assertTrue(all("/usage" in c["argv"] and "--disable-slash-commands" not in c["argv"]
                            and c["agy_no_update"] == "1" for c in probes))

    def test_gemini_probe_counts_a_missing_fraction_as_spent(self):
        def usage(buckets, turns=0):
            return json.dumps({"status": "SUCCESS", "num_turns": turns, "command": {"data": {"groups": [
                {"name": "Gemini Models", "buckets": buckets}]}}})
        weekly = {"id": "gemini-weekly", "window": "weekly", "reset_time": "2026-10-08T09:46:30Z"}
        five = {"id": "gemini-5h", "window": "5h", "remaining_fraction": 0.5,
                "reset_time": "2026-10-01T14:46:30Z"}
        self.setting("usage-json", usage([weekly, five]))
        seat = debate.seat_for("google", "anthropic")
        self.assertEqual(seat["status"], "ABSENT")
        self.assertIn("gemini-weekly", seat["reason"])
        self.assertIn("2026-10-08", seat["reset_kst"])
        self.setting("usage-json", usage([dict(weekly, remaining_fraction=0.9), five], turns=2))
        seat = debate.seat_for("google", "anthropic")
        self.assertEqual(seat["status"], "UNKNOWN")
        self.assertIn("num_turns", seat["reason"])
        self.setting("usage-json", usage([five]))
        seat = debate.seat_for("google", "anthropic")
        self.assertEqual(seat["status"], "UNKNOWN")
        self.assertIn("weekly", seat["reason"])

    def test_anthropic_seat_in_session_and_spent(self):
        seat = debate.seat_for("anthropic", "anthropic")
        self.assertEqual(seat["status"], "READY")
        self.assertTrue(seat["in_session"])
        self.assertIn("submit", seat["reason"])
        self.write_bridge(4, 100)
        (self.root / "bridge" / "abc.wrap.json").write_text("{}", encoding="utf-8")
        self.assertEqual(debate.seat_for("anthropic", "openai")["status"], "ABSENT")
        os.environ["AI_DEBATE_CMD_ANTHROPIC"] = "[]"
        self.assertEqual(debate.seat_for("anthropic", "openai")["reason"], "claude CLI not found")

    def test_headless_claude_is_unknown_never_ready(self):
        self.new(orchestrator="openai")
        seat = debate.seat_for("anthropic", "openai")
        self.assertEqual(seat["status"], "UNKNOWN")
        self.assertIn("headless", seat["reason"])
        rc, _out, _err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "anthropic")
        self.assertEqual(rc, 3)
        self.assertEqual(self.calls("anthropic"), [])
        self.write_bridge(10, 10, NOW - timedelta(hours=1))
        seat = debate.seat_for("anthropic", "openai")
        self.assertEqual(seat["status"], "UNKNOWN")
        self.assertIn("interactive windows below 95%", seat["reason"])
        self.write_bridge(96, 10, NOW - timedelta(hours=1))
        self.assertEqual(debate.seat_for("anthropic", "openai")["status"], "ABSENT")
        self.write_bridge(10, 10, NOW - timedelta(hours=7))
        seat = debate.seat_for("anthropic", "openai")
        self.assertEqual(seat["status"], "UNKNOWN")
        self.assertIn("older than 6h", seat["reason"])
        self.write_codex(100, NOW + timedelta(days=5), True)
        self.write_grok(100, NOW + timedelta(days=2))
        self.setting("usage", "0")
        picked = json.loads(self.run_cli("judge-pick", "--id", "dbt-test")[1])
        self.assertEqual(picked, {"vendor": "openai", "independence": "same-vendor", "in_session": False})
        picked = json.loads(self.run_cli("judge-pick", "--id", "dbt-test", "--accept-unknown")[1])
        self.assertEqual(picked["vendor"], "anthropic")
        self.write_bridge(10, 10, NOW - timedelta(hours=1))
        rc, _out, err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "anthropic",
                                     "--accept-unknown")
        self.assertEqual(rc, 0, err)
        self.assertTrue(self.meta("r1", "anthropic")["accepted_unknown"])
        self.assertIn("-p", self.calls("anthropic")[0]["argv"])

    def test_max_used_rejects_non_finite_and_clock_needs_test_flag(self):
        for raw, expected in (("nan", 95.0), ("inf", 95.0), ("-5", 95.0), ("0", 95.0), ("abc", 95.0),
                              ("150", 100.0), ("80", 80.0)):
            os.environ["AI_DEBATE_MAX_USED"] = raw
            self.assertEqual(debate.max_used(), expected, raw)
        os.environ["AI_DEBATE_MAX_USED"] = "nan"
        self.write_codex(100, NOW + timedelta(days=5), True)
        self.assertEqual(debate.seat_for("openai", "anthropic")["status"], "ABSENT")
        os.environ.pop("AI_DEBATE_TEST")
        self.assertGreater(abs(debate.now() - NOW), timedelta(seconds=1))

    def test_child_env_scrubs_billing_switches(self):
        names = ("CLAUDE_CODE_USE_FOUNDRY", "ANTHROPIC_FOUNDRY_API_KEY", "CLAUDE_CODE_USE_GATEWAY",
                 "CLAUDE_API_KEY", "GROK_CODE_XAI_API_KEY", "GATEWAY_API_KEY", "XAI_API_KEY",
                 "GOOGLE_GENAI_USE_ENTERPRISE", "GOOGLE_CLOUD_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS",
                 "AWS_PROFILE", "AZURE_OPENAI_ENDPOINT", "OPENAI_BASE_URL", "MY_ACCESS_TOKEN",
                 "SOME_AUTH_TOKEN", "GEMINI_API_KEY", "GOOGLE_API_KEY")
        for name in names:
            os.environ[name] = "dummy"
        os.environ["CODEX_HOME"] = str(self.root / "codex-home")
        os.environ["GROK_HOME"] = str(self.root / "grok-home")
        env = debate.child_env("google")
        kept = {k.upper() for k in env}
        for name in names + ("OPENAI_API_KEY",):
            self.assertNotIn(name, kept)
        self.assertEqual(env["CODEX_HOME"], str(self.root / "codex-home"))
        self.assertEqual(env["GROK_HOME"], str(self.root / "grok-home"))
        self.assertEqual((env["NO_COLOR"], env["AGY_CLI_DISABLE_AUTO_UPDATE"]), ("1", "1"))
        self.assertIn("PATH", kept)

    # ------------------------------------------------------------ new / lenses / inputs
    def test_lens_rotation_is_a_permutation_and_varies_by_id(self):
        seen = set()
        for i in range(12):
            lenses = debate.lenses_for("dbt-%02d" % i)
            self.assertEqual(sorted(lenses.values()), sorted(debate.LENSES))
            offset = int(hashlib.sha256(("dbt-%02d" % i).encode()).hexdigest()[:8], 16) % 4
            self.assertEqual(lenses["anthropic"], debate.LENSES[offset])
            seen.add(tuple(lenses[v] for v in debate.VENDORS))
        self.assertGreater(len(seen), 1)

    def test_new_rejects_oversized_evidence(self):
        path = self.root / "big.md"
        path.write_text("가" * 6000, encoding="utf-8")
        rc, _out, err = self.run_cli("new", "--title", "t", "--question", "q", "--evidence-file", path,
                                     "--no-probe")
        self.assertEqual(rc, 2)
        self.assertIn("16384", err)

    def test_new_defaults_to_kst_id_quick_mode_and_snapshots_seats(self):
        rc, out, _err = self.run_cli("new", "--title", "t", "--question", "q", "--no-probe")
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data["id"], "dbt-261001-190000")
        self.assertEqual(data["mode"], "quick")
        self.assertEqual(self.agenda(data["id"])["mode"], "quick")
        self.assertEqual(data["seats"]["google"]["status"], "UNKNOWN")
        self.assertTrue((Path(data["dir"]) / "seats.json").is_file())
        self.assertEqual(data["summary"], "Claude ✓(세션 내) · Codex ✓(쿼터 10%) · Grok ✓(쿼터 10%) · "
                                          "Gemini ?(확인 생략)")

    def test_inputs_are_validated(self):
        for bad in ("abc\n", "dot.", "NUL", "con", "COM1", "lpt9.txt", "a b", ""):
            rc, _out, err = self.run_cli("new", "--id", bad, "--title", "t", "--question", "q", "--no-probe")
            self.assertEqual(rc, 2, repr(bad))
            self.assertIn("invalid debate id", err)
        cases = {"ev16.md": ("근거: 적중률".encode("utf-16"), "UTF-16"),
                 "evnul.md": ("a\x00b".encode("utf-8"), "NUL"),
                 "latin.md": (b"caf\xe9", "not valid UTF-8")}
        for name, (data, message) in cases.items():
            (self.root / name).write_bytes(data)
            rc, _out, err = self.run_cli("new", "--title", "t", "--question", "q", "--no-probe",
                                         "--evidence-file", self.root / name)
            self.assertEqual(rc, 2, name)
            self.assertIn(message, err)
        rc, _out, err = self.run_cli("new", "--title", "t", "--question", "q", "--no-probe",
                                     "--evidence-file", self.root / "missing.md")
        self.assertEqual(rc, 2)
        self.assertIn("not found", err)
        for extra in (("--question", "질" * 2001), ("--option", "o" * 301), ("--criterion", "c" * 301),
                      tuple(x for i in range(11) for x in ("--option", "o%d" % i))):
            argv = ["new", "--title", "t", "--no-probe"] + list(extra)
            if extra[0] != "--question":
                argv += ["--question", "q"]
            rc, _out, err = self.run_cli(*argv)
            self.assertEqual(rc, 2, extra[0])
        self.new()
        self.run_cli("prompt", "--id", "dbt-test", "--round", "r1", "--vendor", "anthropic")
        rc, _out, err = self.run_cli("submit", "--id", "dbt-test", "--round", "r1", "--vendor", "anthropic",
                                     "--file", self.root / "missing.md")
        self.assertEqual(rc, 2)
        self.assertIn("not found", err)

    def test_evidence_secrets_are_redacted(self):
        secrets = ["sk-" + "ant-" + "a" * 30, "gh" + "p_" + "b" * 36, "xai-" + "c" * 24,
                   "AI" + "za" + "d" * 35, "Bearer " + "e" * 30]
        evidence = "\n".join(["값 %s" % s for s in secrets] + ["api_key = plainvalue123", "password: hunter2"])
        data = self.new(evidence=evidence)
        agenda = self.agenda()
        raw = (self.folder() / "agenda.json").read_text(encoding="utf-8")
        for secret in secrets + ["plainvalue123", "hunter2"]:
            self.assertNotIn(secret, raw)
        self.assertEqual((agenda["redacted"], data["redacted"]), (7, 7))
        self.assertIn("api_key = [REDACTED]", agenda["evidence"])

    # ------------------------------------------------------------ calls
    def test_call_on_absent_vendor_spawns_nothing(self):
        self.new()
        self.write_codex(100, NOW + timedelta(days=5), True)
        rc, out, _err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "openai")
        self.assertEqual(rc, 3)
        self.assertEqual(json.loads(out)["status"], "absent")
        self.assertEqual(self.calls("openai"), [])
        meta = self.meta("r1", "openai")
        self.assertEqual(meta["status"], "absent")
        self.assertIn("purchased credits", meta["reason"])

    def test_unknown_readiness_needs_accept_unknown(self):
        self.new()
        os.environ["AI_DEBATE_CODEX_SESSIONS"] = str(self.root / "missing")
        rc, _out, _err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "openai")
        self.assertEqual(rc, 3)
        self.assertEqual(self.calls("openai"), [])
        rc, _out, err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "openai",
                                     "--accept-unknown")
        self.assertEqual(rc, 0, err)
        self.assertTrue(self.meta("r1", "openai")["accepted_unknown"])

    def test_call_ok_writes_answer_and_redacts_prompt_argv(self):
        self.new()
        self.setting("answer-google", r1_answer("GEM"))
        rc, _out, err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "google")
        self.assertEqual(rc, 0, err)
        folder = self.folder() / "rounds" / "r1"
        self.assertIn("GEM 근거", (folder / "google.md").read_text(encoding="utf-8"))
        meta = self.meta("r1", "google")
        prompt = (folder / "google.prompt.md").read_text(encoding="utf-8")
        self.assertEqual(meta["status"], "ok")
        self.assertEqual(meta["session_id"], "conv-1")
        self.assertIn("<prompt:%d chars>" % len(prompt), meta["argv"])
        self.assertNotIn(prompt, meta["argv"])
        self.assertEqual(meta["format_warnings"], [])
        generation = [c for c in self.calls("google") if "/usage" not in c["argv"]][0]
        self.assertEqual(generation["argv"][generation["argv"].index("--print") + 1], prompt)
        for flag in ("--mode", "plan", "--sandbox", "--output-format", "json"):
            self.assertIn(flag, generation["argv"])
        self.assertNotIn("--disable-slash-commands", generation["argv"])

    def test_codex_call_uses_stdin_last_message_and_drops_api_keys(self):
        self.new()
        self.setting("answer-openai", r1_answer("CDX"))
        rc, _out, err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "openai")
        self.assertEqual(rc, 0, err)
        call = self.calls("openai")[0]
        prompt = (self.folder() / "rounds" / "r1" / "openai.prompt.md").read_text(encoding="utf-8")
        self.assertEqual(call["stdin"], prompt)
        self.assertIsNone(call["api_key"])
        for flag in ("exec", "--ephemeral", "--ignore-user-config", "--skip-git-repo-check",
                     'model_reasoning_effort="xhigh"', "gpt-6.1-sol"):
            self.assertIn(flag, call["argv"])
        self.assertEqual(call["argv"][-1], "-")
        meta = self.meta("r1", "openai")
        self.assertEqual(meta["session_id"], "11111111-2222-3333-4444-555555555555")

    def test_seat_cwd_is_an_empty_dir_outside_the_debate_folder(self):
        self.new()
        self.answer("dbt-test", "r1", "openai", r1_answer("C"))
        cwd = Path(self.calls("openai")[0]["cwd"]).resolve()
        folder = self.folder().resolve()
        self.assertNotEqual(cwd, folder)
        self.assertNotIn(folder, cwd.parents)
        self.assertEqual(cwd, (self.root / "home" / "work" / "dbt-test" / "r1-openai").resolve())
        self.assertFalse((cwd.parent / "rounds").exists())
        self.assertEqual(list(cwd.iterdir()), [])

    def test_grok_402_is_absent(self):
        self.new()
        self.setting("mode-xai", "402")
        rc, _out, _err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "xai")
        self.assertEqual(rc, 3)
        meta = self.meta("r1", "xai")
        self.assertEqual(meta["status"], "absent")
        self.assertIn("quota", meta["reason"])
        argv = self.calls("xai")[0]["argv"]
        self.assertEqual(argv[argv.index("--tools") + 1], "")
        self.assertNotIn("-p", argv)
        self.assertNotIn("--single", argv)

    def test_rate_limit_429_is_absent_not_failed(self):
        self.new()
        self.setting("mode-openai", "429")
        rc, _out, _err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "openai")
        self.assertEqual(rc, 3)
        meta = self.meta("r1", "openai")
        self.assertEqual(meta["status"], "absent")
        self.assertIn("quota", meta["reason"])

    def test_agy_error_is_failed(self):
        self.new()
        self.setting("mode-google", "agy_error")
        rc, _out, _err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "google")
        self.assertEqual(rc, 4)
        meta = self.meta("r1", "google")
        self.assertEqual(meta["status"], "failed")
        self.assertIn("AGY_ERROR", meta["reason"])

    def test_agy_command_line_fits_the_windows_limit(self):
        self.new(evidence='"' * 16000)
        self.setting("answer-google", r1_answer("Q"))
        rc, _out, err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "google")
        self.assertEqual(rc, 0, err)
        generation = [c for c in self.calls("google") if "/usage" not in c["argv"]][-1]
        full = json.loads(os.environ["AI_DEBATE_CMD_GOOGLE"]) + generation["argv"]
        self.assertLessEqual(debate.cmdline_units(full), debate.CMDLINE_CAP)
        meta = self.meta("r1", "google")
        self.assertLessEqual(meta["cmdline_chars"], debate.CMDLINE_CAP)
        self.assertIn("evidence", [t["block"] for t in meta["truncated"]])

    def test_cmd_shims_are_resolved_or_refused(self):
        shims = self.root / "shims"
        shims.mkdir()
        bare = shims / "agy.cmd"
        bare.write_text("@echo off\r\necho %*\r\n", encoding="ascii")
        os.environ["AI_DEBATE_CMD_GOOGLE"] = json.dumps([str(bare)])
        seat = debate.seat_for("google", "anthropic")
        self.assertEqual(seat["status"], "UNKNOWN")
        self.assertTrue(seat.get("shim"))
        self.new()
        rc, _out, _err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "google",
                                      "--accept-unknown")
        self.assertEqual(rc, 4)
        meta = self.meta("r1", "google")
        self.assertEqual(meta["status"], "failed")
        self.assertIn("shim refused", meta["reason"])
        native = shims / "agy.exe"
        native.write_bytes(b"MZ")
        wrapper = shims / "agy-wrap.cmd"
        wrapper.write_text('@echo off\r\n"%~dp0agy.exe" %*\r\n', encoding="ascii")
        os.environ["AI_DEBATE_CMD_GOOGLE"] = json.dumps([str(wrapper)])
        self.assertEqual(Path(debate.resolve_cmd("google")[0]).resolve(), native.resolve())

    def test_timeout_fails_and_kills_process_tree(self):
        self.new()
        self.setting("mode-openai", "hang")
        rc, _out, _err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "openai",
                                      "--timeout", "2")
        self.assertEqual(rc, 4)
        meta = self.meta("r1", "openai")
        self.assertEqual(meta["status"], "failed")
        self.assertIn("timeout", meta["reason"])
        self.assertTrue((self.state / "spawned-openai").exists(), "grandchild never started")
        time.sleep(3.5)
        self.assertFalse((self.state / "survivor-openai").exists(), "grandchild outlived the kill")

    def test_running_call_is_locked_and_dies_with_its_runner(self):
        self.new()
        self.setting("mode-openai", "hang")
        runner = subprocess.Popen([sys.executable, "-B", str(Path(debate.__file__).resolve()), "call",
                                   "--id", "dbt-test", "--round", "r1", "--vendor", "openai",
                                   "--timeout", "60"], env=dict(os.environ),
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(self.reap, runner.pid)
        marker = self.state / "spawned-openai"
        self.assertTrue(self.wait_for(lambda: marker.exists() and marker.read_text().strip()))
        child = int(marker.read_text())
        grandchild = int((self.state / "grandchild-openai").read_text())
        self.addCleanup(self.reap, child)
        self.addCleanup(self.reap, grandchild)
        meta = self.meta("r1", "openai")
        real = meta["pid"]  # runner.pid can be a launcher shim
        self.addCleanup(self.reap, real)
        self.assertEqual(meta["status"], "running")
        self.assertTrue(debate.pid_alive(real))
        rc, _out, err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "openai",
                                     "--timeout", "5")
        self.assertEqual(rc, 2)
        self.assertIn("already running", err)
        self.assertEqual(len(self.calls("openai")), 1)
        os.kill(real, signal.SIGTERM if os.name == "nt" else signal.SIGKILL)
        runner.wait(timeout=30)
        self.assertTrue(self.wait_for(lambda: not debate.pid_alive(child), 10), "vendor CLI outlived its runner")
        if os.name == "nt":
            self.assertTrue(self.wait_for(lambda: not debate.pid_alive(grandchild), 10),
                            "job object left the grandchild running")
        self.setting("mode-openai", "ok")
        self.setting("answer-openai", r1_answer("RETRY"))
        rc, _out, err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "openai")
        self.assertEqual(rc, 0, err)
        self.assertEqual(self.meta("r1", "openai")["status"], "ok")

    def test_claude_seat_is_never_spawned_when_claude_orchestrates(self):
        self.new()
        rc, _out, err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "anthropic")
        self.assertEqual(rc, 2)
        self.assertIn("submit", err)
        self.assertEqual(self.calls("anthropic"), [])

    def test_answered_seat_is_not_called_twice(self):
        self.new()
        self.answer("dbt-test", "r1", "xai", r1_answer("X"))
        rc, _out, _err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "xai")
        self.assertEqual(rc, 2)
        self.assertEqual(len(self.calls("xai")), 1)

    def test_submit_is_only_for_the_orchestrator(self):
        self.new()
        self.run_cli("prompt", "--id", "dbt-test", "--round", "r1", "--vendor", "openai")
        path = self.root / "fake-openai.md"
        path.write_text(r1_answer("FAKE"), encoding="utf-8")
        rc, _out, err = self.run_cli("submit", "--id", "dbt-test", "--round", "r1", "--vendor", "openai",
                                     "--file", path)
        self.assertEqual(rc, 2)
        self.assertIn("orchestrator", err)
        self.assertFalse((self.folder() / "rounds" / "r1" / "openai.md").exists())

    # ------------------------------------------------------------ prompts
    def test_r1_prompt_shape(self):
        self.new(evidence="측정값: 캐시 적중률 62%")
        rc, out, _err = self.run_cli("prompt", "--id", "dbt-test", "--round", "r1")
        self.assertEqual(rc, 0)
        prompts = json.loads(out)["prompts"]
        self.assertEqual([p["vendor"] for p in prompts], list(debate.VENDORS))
        text = Path(prompts[0]["path"]).read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# 좌석 카드"))
        self.assertTrue(text.rstrip("\n").endswith(debate.FOOTER))
        for heading in ("## 입장", "## 핵심 근거", "## 내 입장의 가장 강한 반론", "## 조건·전제",
                        "## 기준별 평가", "캐시 적중률 62%"):
            self.assertIn(heading, text)
        self.assertIsNone(VENDOR_WORDS.search(text))

    def test_interject_r1_prompt_asks_for_a_call(self):
        self.new(debate_id="dbt-int", mode="interject", evidence="90분째 열린 턴")
        self.run_cli("prompt", "--id", "dbt-int", "--round", "r1", "--vendor", "xai")
        text = (self.folder("dbt-int") / "rounds" / "r1" / "xai.prompt.md").read_text(encoding="utf-8")
        for item in ("CALL: CONTINUE", "ASK_USER", "## 지금 자를 것", "## 다음 한 걸음", "## 시간 상자",
                     "90분째 열린 턴"):
            self.assertIn(item, text)

    def test_r2_prompt_hides_own_text_and_vendor_names(self):
        self.new()
        for vendor in ("anthropic", "openai", "google"):
            self.answer("dbt-test", "r1", vendor, r1_answer(MARK[vendor]))
        self.run_cli("prompt", "--id", "dbt-test", "--round", "r2", "--vendor", "openai")
        path = self.folder() / "rounds" / "r2" / "openai.prompt.md"
        text = path.read_text(encoding="utf-8")
        self.assertNotIn(MARK["openai"], text)
        self.assertIn(MARK["anthropic"], text)
        self.assertIn(MARK["google"], text)
        self.assertIn("### 입장 A", text)
        self.assertIn("### 입장 B", text)
        self.assertIsNone(VENDOR_WORDS.search(text))
        expected = sorted(["anthropic", "google"],
                          key=lambda v: hashlib.sha256(("dbt-test:openai:r2:" + v).encode()).hexdigest())
        self.assertEqual(self.meta("r2", "openai")["anon"], {"A": expected[0], "B": expected[1]})
        self.run_cli("prompt", "--id", "dbt-test", "--round", "r2", "--vendor", "openai")
        self.assertEqual(path.read_text(encoding="utf-8"), text)

    def test_judge_prompt_shuffle_is_deterministic(self):
        self.new()
        for vendor in debate.VENDORS:
            self.answer("dbt-test", "r1", vendor, r1_answer(MARK[vendor]))
        self.run_cli("prompt", "--id", "dbt-test", "--round", "judge", "--vendor", "xai")
        path = self.folder() / "rounds" / "judge" / "xai.prompt.md"
        first = path.read_text(encoding="utf-8")
        order = sorted(debate.VENDORS,
                       key=lambda v: hashlib.sha256(("dbt-test:judge:" + v).encode()).hexdigest())
        anon = self.meta("judge", "xai")["anon"]
        self.assertEqual([anon["P%d" % i] for i in range(1, 5)], order)
        positions = [first.index(MARK[v]) for v in order]
        self.assertEqual(positions, sorted(positions))
        self.assertIsNone(VENDOR_WORDS.search(first))
        self.assertIn("VERDICT:", first)
        self.run_cli("prompt", "--id", "dbt-test", "--round", "judge", "--vendor", "xai")
        self.assertEqual(path.read_text(encoding="utf-8"), first)

    def test_judge_prompt_admits_a_possible_own_position(self):
        self.new()
        for vendor in debate.VENDORS:
            self.answer("dbt-test", "r1", vendor, r1_answer(MARK[vendor]))
        self.run_cli("prompt", "--id", "dbt-test", "--round", "judge", "--vendor", "xai")
        text = (self.folder() / "rounds" / "judge" / "xai.prompt.md").read_text(encoding="utf-8")
        self.assertNotIn("어느 것도 쓰지 않았다", text)
        self.assertIn("같은 벤더가 썼을 수 있다", text)
        self.assertIn("작성자를 추측하지 말고", text)
        meta = self.meta("judge", "xai")
        self.assertEqual((meta["judge_wrote_position"], meta["positions_count"]), (True, 4))

    def test_prompt_is_capped_with_truncation_marker(self):
        self.new()
        for vendor in debate.VENDORS:
            self.answer("dbt-test", "r1", vendor, r1_answer(vendor[:3]) + "가" * 15000)
        rc, out, _err = self.run_cli("prompt", "--id", "dbt-test", "--round", "judge", "--vendor", "google")
        self.assertEqual(rc, 0)
        text = (self.folder() / "rounds" / "judge" / "google.prompt.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(text), debate.PROMPT_CAP)
        self.assertRegex(text, r"\[\.\.\. \d+자 생략\]")
        self.assertTrue(text.rstrip("\n").endswith(debate.FOOTER))
        self.assertTrue(json.loads(out)["prompts"][0]["truncated"])
        self.assertTrue(self.meta("judge", "google")["truncated"])

    def test_call_always_rebuilds_the_prompt(self):
        self.new()
        for vendor in ("anthropic", "xai", "google"):
            self.answer("dbt-test", "r1", vendor, r1_answer(MARK[vendor]))
        self.run_cli("prompt", "--id", "dbt-test", "--round", "judge", "--vendor", "xai")
        self.answer("dbt-test", "r1", "openai", r1_answer(MARK["openai"]))
        self.answer("dbt-test", "judge", "xai", JUDGE_ANSWER)
        sent = self.calls("xai")[-1]["argv"]
        prompt = Path(sent[sent.index("--prompt-file") + 1]).read_text(encoding="utf-8")
        self.assertIn(MARK["openai"], prompt)
        meta = self.meta("judge", "xai")
        self.assertEqual((meta["positions_count"], len(meta["anon"])), (4, 4))
        self.assertEqual(self.status()["state"], "FINAL")
        rc, _out, err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "openai")
        self.assertEqual(rc, 2)

    def test_submit_refuses_a_prompt_built_on_older_inputs(self):
        self.new()
        self.answer("dbt-test", "r1", "openai", r1_answer(MARK["openai"]))
        self.answer("dbt-test", "r1", "anthropic", r1_answer(MARK["anthropic"]))
        self.run_cli("prompt", "--id", "dbt-test", "--round", "r2", "--vendor", "anthropic")
        self.answer("dbt-test", "r1", "google", r1_answer(MARK["google"]))
        path = self.root / "r2-anthropic.md"
        path.write_text("UNCHANGED\n## 반박\nx\n", encoding="utf-8")
        argv = ("submit", "--id", "dbt-test", "--round", "r2", "--vendor", "anthropic", "--file", path)
        rc, _out, err = self.run_cli(*argv)
        self.assertEqual(rc, 2)
        self.assertIn("re-run prompt", err)
        self.run_cli("prompt", "--id", "dbt-test", "--round", "r2", "--vendor", "anthropic")
        rc, _out, err = self.run_cli(*argv)
        self.assertEqual(rc, 0, err)
        self.assertEqual(self.meta("r2", "anthropic")["inputs"]["present"], ["google", "openai"])

    # ------------------------------------------------------------ parsing
    def test_call_and_verdict_parsing_tolerates_markdown(self):
        for text, expected in (("**CALL**: RESCOPE", "RESCOPE"), ("CALL: SHIP NOW", "SHIP_NOW"),
                               ("CALL: SHIP-NOW", "SHIP_NOW"), ("CALL: ask user", "ASK_USER"),
                               ("**CALL:** STOP — 중단", "STOP"), ("CALL: don't STOP, CONTINUE", "STOP"),
                               ("Call - STOP", None)):
            self.assertEqual(debate.call_of(text + "\n"), expected, text)
        judged = "**VERDICT**: 선택지 1 채택\n**CONFIDENCE:** 70\n"
        self.assertEqual(debate.tagged(judged, "VERDICT"), "선택지 1 채택")
        self.assertEqual(debate.tagged(judged, "CONFIDENCE"), "70")

    # ------------------------------------------------------------ status, record, catch-up
    def test_status_states(self):
        self.new()
        self.answer("dbt-test", "r1", "anthropic", r1_answer("A"))
        self.assertEqual(self.status()["state"], "INVALID")
        self.answer("dbt-test", "r1", "google", r1_answer("G"))
        self.answer("dbt-test", "r1", "xai", r1_answer("X"))
        current = self.status()
        self.assertEqual((current["state"], current["attendance"]), ("PROVISIONAL", 3))
        self.assertEqual([a["vendor"] for a in current["absent"]], ["openai"])
        self.answer("dbt-test", "r1", "openai", r1_answer("O"))
        self.assertEqual(self.status()["state"], "PROVISIONAL")
        self.answer("dbt-test", "judge", "google", JUDGE_ANSWER)
        current = self.status()
        self.assertEqual(current["state"], "FINAL")
        self.assertEqual(current["verdict"]["line"], "선택지 1 채택")

    def test_judge_without_verdict_is_not_ok(self):
        self.new()
        for vendor in debate.VENDORS:
            self.answer("dbt-test", "r1", vendor, r1_answer(vendor))
        self.answer("dbt-test", "judge", "google", "I could not complete the judgement due to an error.\n")
        current = self.status()
        self.assertFalse(current["judge"]["ok"])
        self.assertIn("VERDICT", current["judge"]["issues"][0])
        self.assertEqual(current["state"], "PROVISIONAL")

    def test_judge_must_see_every_position(self):
        self.new()
        for vendor in debate.VENDORS:
            self.answer("dbt-test", "r1", vendor, r1_answer(vendor))
        self.answer("dbt-test", "judge", "google", JUDGE_ANSWER)
        self.assertEqual(self.status()["state"], "FINAL")
        row = self.meta("judge", "google")
        row["positions_count"] = 3
        self.write_meta("judge", "google", row)
        current = self.status()
        self.assertEqual(current["state"], "PROVISIONAL")
        self.assertIn("judge saw 3 of 4", current["judge"]["issues"][0])

    def test_unreadable_reviews_block_final(self):
        self.new()
        for vendor in debate.VENDORS:
            self.answer("dbt-test", "r1", vendor, r1_answer(vendor))
        self.answer("dbt-test", "judge", "google", JUDGE_ANSWER)
        rc, out, _err = self.run_cli("prompt", "--id", "dbt-test", "--round", "ratify")
        self.assertEqual([p["vendor"] for p in json.loads(out)["prompts"]], list(debate.VENDORS))
        self.answer("dbt-test", "ratify", "anthropic", "ACCEPT\n## 근거\nok\n")
        self.answer("dbt-test", "ratify", "google", "ACCEPT\n")
        self.answer("dbt-test", "ratify", "xai", "I object: the verdict ignores rollback cost.\n")
        self.answer("dbt-test", "ratify", "openai", "**OBJECT**: 사실 오류\n")
        current = self.status()
        self.assertEqual([u["vendor"] for u in current["unresolved"]], ["xai"])
        self.assertEqual([o["vendor"] for o in current["objections"]], ["openai"])
        self.assertTrue(current["blocked"])
        self.assertEqual(current["state"], "PROVISIONAL")

    def test_catchup_lists_debate_once_absent_vendor_is_ready(self):
        self.new()
        for vendor in ("anthropic", "xai", "google"):
            self.answer("dbt-test", "r1", vendor, r1_answer(vendor))
        self.write_codex(100, NOW + timedelta(days=5), True)
        self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "openai")
        self.answer("dbt-test", "judge", "xai", JUDGE_ANSWER)
        result = json.loads(self.run_cli("catchup", "--json", "--no-probe")[1])
        self.assertEqual(result["ready"], [])
        self.assertEqual([w["vendor"] for w in result["waiting"]], ["openai"])
        self.write_codex(5, NOW + timedelta(days=7), True)
        result = json.loads(self.run_cli("catchup", "--json", "--no-probe")[1])
        self.assertEqual([(r["id"], r["vendor"]) for r in result["ready"]], [("dbt-test", "openai")])
        commands = result["ready"][0]["commands"]
        self.assertIn("prompt --id dbt-test --round catchup --vendor openai", commands[0])
        self.assertIn("call --id dbt-test --round catchup --vendor openai", commands[1])
        rc, _out, err = self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "openai")
        self.assertEqual(rc, 2)
        self.assertIn("catchup", err)
        self.answer("dbt-test", "catchup", "openai", "ACCEPT\n## 내 독립 입장\n선택지 1\n")
        self.assertEqual(json.loads(self.run_cli("catchup", "--json", "--no-probe")[1])["ready"], [])
        current = self.status()
        self.assertEqual((current["state"], current["via"], current["attendance"]), ("FINAL", "catch-up", 3))

    def test_tiebreak_resolves_one_objection_and_two_reopen(self):
        self.new(mode="quick")
        for vendor in ("anthropic", "xai", "google"):
            self.answer("dbt-test", "r1", vendor, r1_answer(vendor))
        self.write_codex(100, NOW + timedelta(days=5), True)
        self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "openai")
        self.answer("dbt-test", "judge", "xai", JUDGE_ANSWER)
        self.write_codex(5, NOW + timedelta(days=7), True)
        self.answer("dbt-test", "catchup", "openai", "OBJECT: 되돌림 비용 과소평가\n")
        self.assertTrue(self.status()["blocked"])
        rc, out, err = self.run_cli("record", "--id", "dbt-test", "--tiebreak", "카나리로 되돌림 위험이 통제된다")
        self.assertEqual(rc, 0, err)
        self.assertIn("**타이브레이크**: Claude — 카나리로 되돌림 위험이 통제된다", out)
        current = self.status()
        self.assertFalse(current["blocked"])
        self.assertEqual((current["state"], current["via"]), ("FINAL", "catch-up"))
        rc, _out, err = self.run_cli("record", "--id", "dbt-test", "--tiebreak", "again")
        self.assertEqual(rc, 2)
        self.new(debate_id="dbt-two", mode="quick", evidence="가" * 5400)
        for vendor in ("anthropic", "google"):
            self.answer("dbt-two", "r1", vendor, r1_answer(vendor))
        self.write_codex(100, NOW + timedelta(days=5), True)
        self.write_grok(100, NOW + timedelta(days=2))
        self.run_cli("call", "--id", "dbt-two", "--round", "r1", "--vendor", "openai")
        self.run_cli("call", "--id", "dbt-two", "--round", "r1", "--vendor", "xai")
        self.answer("dbt-two", "judge", "google", JUDGE_ANSWER)
        self.write_codex(5, NOW + timedelta(days=7), True)
        self.write_grok(5, NOW + timedelta(days=2))
        self.answer("dbt-two", "catchup", "openai", "OBJECT: 사실 오류\n")
        self.answer("dbt-two", "catchup", "xai", "OBJECT: 기준 누락\n")
        rc, _out, err = self.run_cli("record", "--id", "dbt-two", "--tiebreak", "x")
        self.assertEqual(rc, 2)
        self.assertIn("--reopen-of dbt-two", err)
        rc, out, err = self.run_cli("new", "--reopen-of", "dbt-two", "--id", "dbt-two-re", "--no-probe")
        self.assertEqual(rc, 0, err)
        old, new = self.agenda("dbt-two"), self.agenda("dbt-two-re")
        for key in ("title", "question", "options", "criteria", "mode"):
            self.assertEqual(new[key], old[key], key)
        self.assertEqual(new["reopen_of"], "dbt-two")
        self.assertIn("## 이전 토론 기록", new["evidence"])
        self.assertIn("OBJECT: 기준 누락", new["evidence"])
        self.assertIn("[... 근거 자료 일부 생략]", new["evidence"])
        self.assertLessEqual(len(new["evidence"].encode("utf-8")), debate.EVIDENCE_CAP)

    def test_record_once_then_amend_with_catchup(self):
        self.new(mode="quick")
        self.answer("dbt-test", "r1", "anthropic", r1_answer("A", 1, 70))
        self.answer("dbt-test", "r1", "google", r1_answer("G", 2, 60))
        self.write_codex(100, NOW + timedelta(days=5), True)
        self.write_grok(100, NOW + timedelta(days=2))
        self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "openai")
        self.run_cli("call", "--id", "dbt-test", "--round", "r1", "--vendor", "xai")
        self.answer("dbt-test", "judge", "google", JUDGE_ANSWER)
        decisions = self.root / "DECISIONS.md"
        original = ("# 결정\r\n\r\n- 2026-09-30 | DECIDE | **D-51 a**\r\n\r\n### D-52 — b\r\n"
                    "- 참고 D-260904-01 · D-999 언급\r\n").encode("utf-8")
        decisions.write_bytes(original)
        rc, _out, err = self.run_cli("record", "--id", "dbt-test", "--decisions", decisions, "--append")
        self.assertEqual(rc, 0, err)
        data = decisions.read_bytes()
        self.assertTrue(data.startswith(original))
        added = data[len(original):]
        self.assertNotIn(b"\n", added.replace(b"\r\n", b""))
        text = added.decode("utf-8")
        self.assertRegex(text, r"- 2026-10-01 19:00:00 KST \| DECIDE \| \*\*D-53 캐시 전략 결정\*\* "
                               r"\(§35 4벤더 토론 · PROVISIONAL 2/4\) \| claude\r\n")
        for label in ("**안건**:", "**참석**:", "**입장**:", "**교차검증**: quick 모드 생략", "**심판**:",
                      "**소수의견**: 되돌림 비용", "**후속**:", "**원문**:"):
            self.assertIn(label, text)
        self.assertIn("Claude ✓(claude-opus-5-5, 세션 내)", text)
        self.assertIn("Codex ✗(쿼터 100% ~", text)
        self.assertIn("구매 크레딧 과금 위험", text)
        self.assertRegex(text, r"\*\*입장\*\*: Claude\[(찬성|회의|대안|사용자 이익)\]: 선택지 1 — 확신도 70 · "
                               r"Gemini\[(찬성|회의|대안|사용자 이익)\]: ")
        self.assertIn("catchup", text)
        saved = json.loads((self.folder() / "record.json").read_text(encoding="utf-8"))
        self.assertEqual((saved["label"], saved["decisions_path"]), ("D-53", decisions.resolve().as_posix()))
        self.assertTrue(saved["appended_at"])
        before = decisions.read_bytes()
        rc, _out, err = self.run_cli("record", "--id", "dbt-test", "--decisions", decisions, "--append")
        self.assertEqual(rc, 2)
        self.assertIn("--amend", err)
        rc, _out, err = self.run_cli("record", "--id", "dbt-test", "--amend")
        self.assertEqual(rc, 2)
        self.assertIn("nothing changed", err)
        self.assertEqual(decisions.read_bytes(), before)
        self.write_codex(5, NOW + timedelta(days=7), True)
        self.answer("dbt-test", "catchup", "openai", "ACCEPT\n## 내 독립 입장\n선택지 1\n")
        rc, _out, err = self.run_cli("record", "--id", "dbt-test", "--amend")
        self.assertEqual(rc, 0, err)
        data = decisions.read_bytes()
        self.assertTrue(data.startswith(before))
        amend = data[len(before):].decode("utf-8")
        self.assertEqual(len(re.findall(r"^- ", amend, re.M)), 1)
        self.assertRegex(amend, r"- 2026-10-01 19:00:00 KST \| AMEND \| \*\*D-53 캐시 전략 결정\*\* — "
                                r"catch-up: Codex ACCEPT · 상태 PROVISIONAL 2/4 \| claude\r\n")
        self.write_grok(5, NOW + timedelta(days=2))
        self.answer("dbt-test", "catchup", "xai", "OBJECT: 되돌림 비용 과소평가\n")
        rc, out, err = self.run_cli("record", "--id", "dbt-test", "--amend")
        self.assertEqual(rc, 0, err)
        self.assertIn("Grok OBJECT: 되돌림 비용 과소평가", out)
        self.assertIn("차단(OBJECT 1건)", out)
        rc, out, _err = self.run_cli("record", "--id", "dbt-test")
        self.assertIn("**D-53 ", out)
        self.assertIn("**catch-up**: Codex ACCEPT · Grok OBJECT: 되돌림 비용 과소평가", out)
        self.new(debate_id="dbt-lf", mode="quick")
        self.answer("dbt-lf", "r1", "anthropic", r1_answer("A"))
        self.answer("dbt-lf", "r1", "google", r1_answer("G"))
        self.answer("dbt-lf", "judge", "google", JUDGE_ANSWER)
        rc, out, _err = self.run_cli("record", "--id", "dbt-lf")
        self.assertIn("**D-?? ", out)
        lf = self.root / "LF.md"
        lf.write_bytes(b"- 2026-09-01 | DECIDE | **D-7 x**\n")
        rc, _out, err = self.run_cli("record", "--id", "dbt-lf", "--decisions", lf, "--append")
        self.assertEqual(rc, 0, err)
        self.assertNotIn(b"\r\n", lf.read_bytes())
        self.assertIn("**D-8 ", lf.read_text(encoding="utf-8"))

    def test_record_refuses_invalid_or_judgeless_unless_forced(self):
        self.new()
        self.answer("dbt-test", "r1", "anthropic", r1_answer("A"))
        decisions = self.root / "DEC.md"
        decisions.write_bytes(b"- 2026-09-01 | DECIDE | **D-52 x**\n")
        rc, _out, err = self.run_cli("record", "--id", "dbt-test", "--decisions", decisions, "--append")
        self.assertEqual(rc, 2)
        self.assertIn("INVALID", err)
        self.assertEqual(decisions.read_bytes(), b"- 2026-09-01 | DECIDE | **D-52 x**\n")
        rc, _out, err = self.run_cli("record", "--id", "dbt-test", "--decisions", decisions, "--append", "--force")
        self.assertEqual(rc, 0, err)
        self.assertIn("⚠ 강제 기록: INVALID 1/4", decisions.read_text(encoding="utf-8"))
        self.new(debate_id="dbt-nj", mode="quick")
        self.answer("dbt-nj", "r1", "anthropic", r1_answer("A"))
        self.answer("dbt-nj", "r1", "google", r1_answer("G"))
        rc, _out, err = self.run_cli("record", "--id", "dbt-nj")
        self.assertEqual(rc, 2)
        self.assertIn("심판 없음", err)

    def test_next_d_number_counts_only_entry_headers(self):
        path = self.root / "D.md"
        path.write_text("- 2026-09-30 | DECIDE | **D-51 a**\n\n### D-52 — b\n- 참고 D-260904-01 · D-999 언급\n",
                        encoding="utf-8")
        self.assertEqual(debate.next_d_number(path), "D-53")

    def test_judge_pick(self):
        self.new()
        self.setting("usage", "1")
        rc, out, _err = self.run_cli("judge-pick", "--id", "dbt-test")
        picked = json.loads(out)
        self.assertNotEqual(picked["vendor"], "anthropic")
        self.assertEqual((picked["independence"], picked["in_session"]), ("independent", False))
        self.write_codex(100, NOW + timedelta(days=5), True)
        self.write_grok(100, NOW + timedelta(days=2))
        self.setting("usage", "0")
        picked = json.loads(self.run_cli("judge-pick", "--id", "dbt-test")[1])
        self.assertEqual(picked, {"vendor": "anthropic", "independence": "same-vendor", "in_session": True})

    def test_judge_pick_rotates_and_skips_orchestrator_and_subject(self):
        def rotation(debate_id):
            offset = int(hashlib.sha256((debate_id + ":judge").encode()).hexdigest()[:8], 16) % 4
            return [debate.VENDORS[(i + offset) % 4] for i in range(4)]
        self.new()
        self.setting("usage", "1")
        eligible = [v for v in rotation("dbt-test") if v != "anthropic"]
        for vendor in eligible[1:]:
            self.answer("dbt-test", "r1", vendor, r1_answer(vendor))
        self.assertEqual(json.loads(self.run_cli("judge-pick", "--id", "dbt-test")[1])["vendor"], eligible[0])
        order = [v for v in rotation("dbt-int") if v != "anthropic"]
        self.new(debate_id="dbt-int", mode="interject", extra=("--subject-vendor", order[0]))
        self.assertEqual(self.agenda("dbt-int")["subject_vendor"], order[0])
        self.assertEqual(json.loads(self.run_cli("judge-pick", "--id", "dbt-int")[1])["vendor"], order[1])
        rc, _out, err = self.run_cli("new", "--id", "dbt-bad", "--title", "t", "--question", "q",
                                     "--subject-vendor", "openai", "--no-probe")
        self.assertEqual(rc, 2)
        self.assertIn("interject", err)

    def test_deliver_dry_run_and_send(self):
        self.new(debate_id="dbt-int", mode="interject", evidence="스냅숏")
        self.answer("dbt-int", "r1", "anthropic", "CALL: STOP\n## 근거\n오래 걸림\n")
        self.answer("dbt-int", "r1", "google", "CALL: RESCOPE\n## 근거\n범위 축소\n")
        self.answer("dbt-int", "judge", "google", INTERJECT_JUDGE)
        rc, out, _err = self.run_cli("deliver", "--id", "dbt-int", "--orca-terminal", "term-1")
        dry = json.loads(out)
        self.assertEqual(rc, 0)
        self.assertTrue(dry["dry_run"])
        self.assertEqual(self.calls("orca"), [])
        card = (self.folder("dbt-int") / "card.md").read_text(encoding="utf-8").splitlines()
        self.assertLessEqual(len(card), 12)
        self.assertIn("CALL: RESCOPE (확신도 75)", card)
        self.assertIn("위원 권고: Claude STOP · Gemini RESCOPE", card)
        self.assertIn("시간 상자: 20분", card)
        self.assertFalse(any(line.startswith("⚠ STOP") for line in card))
        rc, _out, _err = self.run_cli("deliver", "--id", "dbt-int", "--send")
        self.assertEqual(rc, 2)
        self.assertEqual(self.calls("orca"), [])
        rc, _out, err = self.run_cli("deliver", "--id", "dbt-int", "--orca-terminal", "term-1", "--send")
        self.assertEqual(rc, 0, err)
        argv = self.calls("orca")[0]["argv"]
        self.assertEqual(argv[:4], ["terminal", "send", "--terminal", "term-1"])
        self.assertEqual(argv[-2:], ["--enter", "--json"])
        self.assertTrue(argv[5].startswith("[겐세이 dbt-int] RESCOPE: 테스트 하나만 고치고 보고한다"))
        self.assertNotIn("\n", argv[5])
        self.assertEqual(json.loads((self.folder("dbt-int") / "deliver.json")
                                    .read_text(encoding="utf-8"))["rc"], 0)
        shim = self.root / "orca.cmd"
        shim.write_text("@echo off\r\necho %*\r\n", encoding="ascii")
        os.environ["AI_DEBATE_CMD_ORCA"] = json.dumps([str(shim)])
        rc, _out, _err = self.run_cli("deliver", "--id", "dbt-int", "--orca-terminal", "term-1", "--send")
        self.assertEqual(rc, 4)
        sent = json.loads((self.folder("dbt-int") / "deliver.json").read_text(encoding="utf-8"))
        self.assertEqual(sent["status"], "failed")
        self.assertIn("shim refused", sent["reason"])

    def test_deliver_strips_control_chars_and_flags_a_stop_majority(self):
        self.new(debate_id="dbt-int", mode="interject", evidence="스냅숏")
        self.answer("dbt-int", "r1", "anthropic", "CALL: STOP\n## 근거\nx\n")
        self.answer("dbt-int", "r1", "openai", "**CALL**: STOP\n## 근거\ny\n")
        self.answer("dbt-int", "r1", "xai", "CALL: STOP\n")
        self.answer("dbt-int", "r1", "google", "CALL: RESCOPE\n")
        judge = ("CALL: STOP\nCONFIDENCE: 80\n## 다음 한 걸음\nstep\x1b[2Jone\x03two\x08\x7fthree‮end\n"
                 "## 지금 자를 것\nx\n## 시간 상자\n20분 (그 후 보고)\n## 판정 근거\nr\n")
        self.answer("dbt-int", "judge", "google", judge)
        rc, out, err = self.run_cli("deliver", "--id", "dbt-int", "--orca-terminal", "term-1")
        self.assertEqual(rc, 0, err)
        text = (self.folder("dbt-int") / "card.md").read_text(encoding="utf-8")
        card = text.splitlines()
        self.assertIn("⚠ STOP 3/4 — Simon에게 일시정지 권고", card)
        self.assertIn("시간 상자: 20분 (그 후 보고)", card)
        self.assertIsNone(debate.CTRL_RE.search(text.replace("\n", "")))
        argv = json.loads(out)["argv"]
        self.assertIsNone(debate.CTRL_RE.search(argv[argv.index("--text") + 1]))
        rc, _out, err = self.run_cli("deliver", "--id", "dbt-int", "--orca-terminal", "term-1", "--send")
        self.assertEqual(rc, 0, err)
        sent = self.calls("orca")[0]["argv"]
        self.assertIsNone(debate.CTRL_RE.search(sent[sent.index("--text") + 1]))
        self.assertIn("step[2Jonetwothreeend", sent[sent.index("--text") + 1])


if __name__ == "__main__":
    unittest.main()
