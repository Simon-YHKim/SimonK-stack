"""D-126 Gemini 4 Neon Korean prose runner: offline fixtures only, no agy or model calls."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import execute_agy_prose as m  # noqa: E402
import runtime_collect  # noqa: E402

NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
BRIEF = "다음 사실만 써서 서버 점검 공지를 써 줘: 11월 20일 02:00~04:00, 로그인 불가.\n"


def agy_raw(neon_remaining=0.97):
    return {"_agy_models": [m.MODEL], "status": "SUCCESS", "num_turns": 0,
            "usage": {"input_tokens": 0, "output_tokens": 0, "thinking_tokens": 0,
                      "cache_read_tokens": 0, "total_tokens": 0},
            "command": {"name": "usage", "data": {"groups": [
                {"name": "Gemini Models", "buckets": [
                    {"id": "gemini-weekly", "window": "weekly", "remaining_fraction": 1.0,
                     "reset_time": "2099-01-01T00:00:00Z"}]},
                {"name": "Gemini 4 Neon", "buckets": [
                    {"id": "gemini-neon-wtu-weekly", "window": "weekly",
                     "remaining_fraction": neon_remaining, "reset_time": "2099-01-01T00:00:00Z"}]}]}}}


def observation(neon_remaining=0.97, at=None):
    return runtime_collect.normalize("antigravity", agy_raw(neon_remaining), at or NOW, "/fixture/agy")


def print_result(response="## 서버 점검 안내\n\n11월 20일 02:00~04:00 에는 로그인할 수 없습니다.",
                 status="SUCCESS"):
    return json.dumps({"conversation_id": "conv-1", "status": status, "response": response,
                       "duration_seconds": 4.2, "num_turns": 1,
                       "usage": {"input_tokens": 26000, "output_tokens": 300, "thinking_tokens": 200,
                                 "cache_read_tokens": 0, "total_tokens": 26500}})


class Recorder:
    def __init__(self, rc=0, stdout=None, error=None):
        self.rc, self.stdout, self.error, self.calls = rc, stdout if stdout is not None else print_result(), error, []

    def __call__(self, argv, workdir, env):
        self.calls.append({"argv": argv, "brief": (Path(workdir) / m.BRIEF_NAME).read_text(encoding="utf-8"),
                           "env": env})
        if self.error:
            raise self.error
        return self.rc, self.stdout


class ArgvTests(unittest.TestCase):
    def test_argv_pins_neon_medium_read_only_sandbox_and_no_slash_expansion(self):
        argv = m.build_argv(["agy"])
        self.assertEqual(argv[:2], ["agy", "--print"])
        self.assertEqual(argv[argv.index("--model") + 1], "gemini-4-neon-medium")
        self.assertEqual(argv[argv.index("--mode") + 1], "plan")
        self.assertIn("--sandbox", argv)
        self.assertIn("--disable-slash-commands", argv)
        self.assertEqual(argv[argv.index("--output-format") + 1], "json")
        self.assertEqual(argv[2], m.PROMPT)  # The request itself never rides on the command line.
        self.assertIn(m.BRIEF_NAME, m.PROMPT)

    def test_parse_result_reads_status_and_response(self):
        parsed = m.parse_result(print_result())
        self.assertEqual(parsed["status"], "SUCCESS")
        self.assertTrue(parsed["response"].startswith("## "))
        self.assertIsNone(m.parse_result("not json"))


class DraftTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / "notice.md"

    def run_draft(self, run=None, collect=None, brief=BRIEF, not_confidential=True, out=None):
        observations = iter([observation(), observation(neon_remaining=0.96)])
        return m.draft(brief, str(out or self.out), not_confidential,
                       collect=collect or (lambda: next(observations)), run=run or Recorder(),
                       command=["agy"])

    def test_advisory_handoff_pins_task_model_profile_and_receipt(self):
        import agy_lanes
        for slug, tasks in agy_lanes.ADVISORY_MODELS.items():
            with self.subTest(slug=slug):
                obs = dict(observation(), agy_model_slugs=[slug])
                run = Recorder()
                out = self.out.with_name(slug + ".md")
                code, receipt = m.draft(BRIEF, str(out), True, model=slug, task_type=tasks[0],
                                        expected_profile=obs["profile_ref"], collect=lambda: obs,
                                        run=run, command=["agy"])
                self.assertEqual(code, 0, receipt)
                argv = run.calls[0]["argv"]
                self.assertEqual(argv[argv.index("--model") + 1], slug)
                self.assertEqual(argv[2], m.ADVISORY_PROMPT)
                self.assertEqual((receipt["model"], receipt["task_type"]), (slug, tasks[0]))
        run = Recorder()
        code, _ = m.draft(BRIEF, str(self.out), True, expected_profile="changed",
                          collect=observation, run=run, command=["agy"])
        self.assertEqual((code, run.calls), (3, []))

    def test_success_writes_the_draft_receipt_and_usage_before_and_after(self):
        run = Recorder()
        code, receipt = self.run_draft(run=run)
        self.assertEqual(code, 0, receipt)
        self.assertEqual(receipt["status"], "succeeded")
        self.assertTrue(self.out.read_text(encoding="utf-8").startswith("## 서버 점검 안내"))
        saved = json.loads(m.receipt_path(self.out).read_text(encoding="utf-8"))
        self.assertEqual((saved["schema"], saved["decision"], saved["model"]),
                         ("vibe-agy-prose-v1", "D-131", "gemini-4-neon-medium"))
        self.assertEqual(saved["fact_check_required"], m.FACT_CHECK)
        self.assertAlmostEqual(saved["usage_before"]["used_pct"], 3, places=3)
        self.assertAlmostEqual(saved["usage_after"]["used_pct"], 4, places=3)
        self.assertEqual(saved["agy"]["conversation_id"], "conv-1")
        self.assertNotIn("response", saved["agy"])
        self.assertEqual(len(run.calls), 1)  # One send, no retry.
        self.assertEqual(run.calls[0]["brief"], BRIEF)
        self.assertEqual(run.calls[0]["env"]["AGY_CLI_DISABLE_AUTO_UPDATE"], "true")

    def test_usage_gate_refuses_before_sending_and_writes_nothing(self):
        for remaining in (0.15, 0.0):
            with self.subTest(remaining=remaining):
                run = Recorder()
                code, receipt = m.draft(BRIEF, str(self.out), True,
                                        collect=lambda: observation(neon_remaining=remaining),
                                        run=run, command=["agy"])
                self.assertEqual(code, 3)
                self.assertEqual(receipt["status"], "refused")
                self.assertIn("PROSE_QUOTA_UNVERIFIED", receipt["reasons"])
                self.assertEqual(run.calls, [])
                self.assertFalse(self.out.exists())
                self.assertFalse(m.receipt_path(self.out).exists())
        stale = (datetime.fromisoformat(NOW) - timedelta(hours=1)).isoformat()
        code, receipt = m.draft(BRIEF, str(self.out), True, collect=lambda: observation(at=stale),
                                run=Recorder(), command=["agy"])
        self.assertEqual(code, 3)
        broken = observation()
        broken["collection"]["zero_token_verified"] = None
        code, receipt = m.draft(BRIEF, str(self.out), True, collect=lambda: broken,
                                run=Recorder(), command=["agy"])
        self.assertEqual((code, receipt["reasons"]), (3, ["PROSE_AGY_SUBSCRIPTION_UNVERIFIED"]))

    def test_bad_arguments_stop_before_collecting(self):
        def never():
            raise AssertionError("collected")
        cases = [("CONFIDENTIALITY_UNCONFIRMED", {"not_confidential": False}),
                 ("BRIEF_REQUIRED", {"brief": "  "}),
                 ("BRIEF_TOO_LARGE", {"brief": "가" * 30000}),
                 ("SENSITIVE_PAYLOAD", {"brief": BRIEF + "OPENAI_API_KEY=sk-proj-" + "a" * 40}),
                 ("OUTPUT_PATH_INVALID", {"out": Path(self.temp.name) / "notice.png"})]
        for code_name, change in cases:
            with self.subTest(case=code_name):
                with self.assertRaises(m.ProseError) as ctx:
                    self.run_draft(collect=never, **change)
                self.assertEqual((ctx.exception.code, ctx.exception.exit_code), (code_name, 2))
        self.out.write_text("old", encoding="utf-8")
        with self.assertRaises(m.ProseError) as ctx:
            self.run_draft(collect=never)
        self.assertEqual(ctx.exception.code, "OUTPUT_PATH_INVALID")

    def test_failed_or_unknown_sends_are_reported_without_retry(self):
        for name, run, reason in (
                ("nonzero", Recorder(rc=1), "AGY_PRINT_FAILED"),
                ("status", Recorder(stdout=print_result(status="ERROR")), "AGY_PRINT_FAILED"),
                ("empty", Recorder(stdout=print_result(response="  ")), "AGY_PRINT_FAILED"),
                ("garbage", Recorder(stdout="not json"), "AGY_PRINT_FAILED"),
                ("timeout", Recorder(error=m.SendInterrupted("timeout")), "AGY_SEND_OUTCOME_UNKNOWN:timeout")):
            with self.subTest(case=name):
                out = Path(self.temp.name) / (name + ".md")
                code, receipt = self.run_draft(run=run, out=out)
                self.assertEqual(code, 4)
                self.assertIn(reason, receipt["reasons"])
                self.assertEqual(len(run.calls), 1)
                self.assertFalse(out.exists())
                self.assertTrue(m.receipt_path(out).exists())

    def test_cli_requires_the_confidentiality_flag(self):
        brief = Path(self.temp.name) / "brief.md"
        brief.write_text(BRIEF, encoding="utf-8")
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            code = m.main(["--brief-file", str(brief), "--out", str(self.out)])
        self.assertEqual(code, 2)
        self.assertIn("CONFIDENTIALITY_UNCONFIRMED", printed.getvalue())
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
