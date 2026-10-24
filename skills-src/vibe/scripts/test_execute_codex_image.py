"""D-121 Codex image runner: offline fixtures only, no Codex or model calls."""
import base64
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import execute_codex_image as m  # noqa: E402
import runtime_collect  # noqa: E402

NOW = "2026-09-23T13:00:00+00:00"
PNG = m.PNG_SIGNATURE + b"fixture image bytes"
THREAD = "01a16ccb-5f10-7ae0-9ac8-720c2e276888"


def codex_raw(used=42, limit=None):
    bucket = {"limitId": "codex", "primary": {"usedPercent": used, "windowDurationMins": 10080,
                                               "resetsAt": 1790400000},
              "credits": {"hasCredits": True, "unlimited": False, "balance": "100"},
              "spendControlReached": False, "rateLimitReachedType": limit}
    return {"initialize": {"codexHome": "/fixture/profile"},
            "account": {"account": {"type": "chatgpt", "planType": "pro",
                                    "email": "fixture@example.invalid"}},
            "models": {"data": []}, "limits": {"rateLimitsByLimitId": {"codex": bucket}}}


def observation(**changes):
    return runtime_collect.normalize("codex", codex_raw(**changes), NOW, "/fixture/profile")


def stream(thread=THREAD, errors=(), completed=True):
    events = [{"type": "thread.started", "thread_id": thread}, {"type": "turn.started"}]
    events += [{"type": "item.completed", "item": {"id": "e", "type": "error", "message": text}}
               for text in errors]
    events.append({"type": "item.completed", "item": {"id": "m", "type": "agent_message",
                                                      "text": "DONE"}})
    if completed:
        events.append({"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 2}})
    return "\n".join(json.dumps(event) for event in events) + "\n"


def rollout_lines(images=(PNG,), status="completed"):
    lines = [{"type": "session_meta", "payload": {"id": THREAD}}]
    for raw in images:
        b64 = base64.b64encode(raw).decode()
        lines.append({"type": "event_msg", "payload": {"type": "item_completed", "item": {
            "type": "Extension", "kind": "image_gen.generation", "id": "exec-1", "status": status,
            "revisedPrompt": "A blue circle", "result": b64, "savedPath": "C:/untrusted.png"}}})
        # The same bytes return to the model as a data URL; they are not a second image.
        lines.append({"type": "response_item", "payload": {"type": "custom_tool_call_output",
            "output": [{"type": "input_image", "image_url": "data:image/png;base64," + b64}]}})
    return "\n".join(json.dumps(line) for line in lines) + "\n"


class ParsingTests(unittest.TestCase):
    def test_argv_pins_astra_xhigh_and_a_writable_private_sandbox(self):
        argv = m.build_argv(["codex"], Path("/tmp/work"))
        self.assertEqual(argv[:2], ["codex", "exec"])
        self.assertIn("--json", argv)
        self.assertEqual(argv[argv.index("--sandbox") + 1], "workspace-write")
        self.assertEqual(argv[argv.index("-m") + 1], "gpt-6-astra")
        self.assertIn('model_reasoning_effort="xhigh"', argv)
        self.assertNotIn("--ephemeral", argv)  # The rollout carries the image bytes.
        self.assertEqual(argv[-1], "-")

    def test_prompt_asks_for_one_call_and_optional_alpha(self):
        plain = m.build_prompt("a fox")
        self.assertIn("exactly once", plain)
        self.assertNotIn("transparent background", plain)
        self.assertIn("transparent background", m.build_prompt("a fox", transparent=True))

    def test_stream_reads_thread_usage_and_errors(self):
        parsed = m.parse_stream("not json\n" + stream(errors=["clamping hook"]))
        self.assertEqual(parsed["thread_id"], THREAD)
        self.assertTrue(parsed["completed"])
        self.assertEqual(parsed["usage"]["input_tokens"], 10)
        self.assertEqual(parsed["errors"], ["clamping hook"])

    def test_usage_limit_messages_match_both_apostrophes(self):
        for text in ("You've hit your usage limit. Try again later.",
                     "You\u2019ve hit your usage limit.", "Your workspace is out of credits."):
            with self.subTest(text=text):
                self.assertEqual(m.usage_limit_message(["other", text]), text)
        self.assertIsNone(m.usage_limit_message(["Exceeded skills context budget."]))

    def test_rollout_images_are_deduplicated_and_failures_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rollout.jsonl"
            path.write_text(rollout_lines(images=(PNG, PNG + b"2")), encoding="utf-8")
            images, failures = m.extract_images(path)
            self.assertEqual(len(images), 2)
            self.assertEqual(base64.b64decode(images[0]["b64"]), PNG)
            self.assertEqual(images[0]["revised_prompt"], "A blue circle")
            self.assertEqual(failures, [])
            path.write_text(rollout_lines(status="failed"), encoding="utf-8")
            self.assertEqual(m.extract_images(path), ([], ["failed"]))
            legacy = {"type": "response_item", "payload": {"type": "image_generation_call",
                      "status": "completed", "result": base64.b64encode(PNG).decode()}}
            path.write_text(json.dumps(legacy) + "\n", encoding="utf-8")
            self.assertEqual(len(m.extract_images(path)[0]), 1)

    def test_decode_requires_png(self):
        self.assertEqual(m.decode_png(base64.b64encode(PNG).decode()), PNG)
        for bad in ("@@@", base64.b64encode(b"GIF89a").decode()):
            with self.subTest(bad=bad), self.assertRaises(m.ImageError):
                m.decode_png(bad)


class GateTests(unittest.TestCase):
    def test_open_under_the_ceiling(self):
        reasons, tool = m.gate(observation(), NOW)
        self.assertEqual(reasons, [])
        self.assertEqual(tool["quota"]["used_pct"], 42)

    def test_d74_conditions_close_the_gate(self):
        self.assertIn("IMAGE_QUOTA_UNVERIFIED", m.gate(observation(used=85), NOW)[0])
        self.assertIn("IMAGE_USAGE_LIMIT_REACHED",
                      m.gate(observation(limit="primary"), NOW)[0])
        later = "2026-09-23T13:30:00+00:00"
        self.assertIn("IMAGE_QUOTA_UNVERIFIED", m.gate(observation(), later)[0])
        api_key = runtime_collect.normalize("codex", {**codex_raw(), "account": {"account": {
            "type": "apiKey"}}}, NOW, "/fixture/profile")
        self.assertEqual(m.gate(api_key, NOW), (["IMAGE_CODEX_SUBSCRIPTION_UNVERIFIED"], None))
        broken = copy.deepcopy(observation())
        broken["state"] = "error"
        self.assertEqual(m.gate(broken, NOW)[1], None)


class GenerateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.home = self.root / "codex-home"
        (self.home / "sessions" / "2026").mkdir(parents=True)
        self.out = self.root / "art" / "circle.png"
        self.out.parent.mkdir()
        self.calls = []

    def tearDown(self):
        self.tmp.cleanup()

    def fake_run(self, stdout, rollout=None, rc=0):
        def run(argv, prompt, workdir, env):
            self.calls.append({"argv": argv, "prompt": prompt, "env": env})
            if rollout is not None:
                name = "rollout-2026-09-23T13-00-00-" + THREAD + ".jsonl"
                (self.home / "sessions" / "2026" / name).write_text(rollout, encoding="utf-8")
            return rc, stdout
        return run

    def generate(self, run, collect=observation, **kwargs):
        return m.generate("a blue circle", str(self.out), collect=collect, run=run,
                          command=["codex"], home=self.home, now=NOW, **kwargs)

    def test_success_writes_png_and_receipt_once(self):
        code, receipt = self.generate(self.fake_run(stream(), rollout_lines()))
        self.assertEqual(code, 0, receipt)
        self.assertEqual(self.out.read_bytes(), PNG)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(receipt["images"][0]["bytes"], len(PNG))
        self.assertEqual(receipt["usage_before"]["used_pct"], 42)
        self.assertEqual(receipt["codex"]["thread_id"], THREAD)
        saved = json.loads((self.out.parent / "circle.receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["status"], "succeeded")
        self.assertNotIn("OPENAI_API_KEY", self.calls[0]["env"])

    def test_refused_gate_never_sends(self):
        code, receipt = self.generate(self.fake_run(stream()),
                                      collect=lambda: observation(used=90))
        self.assertEqual((code, receipt["status"]), (3, "refused"))
        self.assertEqual(self.calls, [])
        self.assertFalse((self.out.parent / "circle.receipt.json").exists())

    def test_codex_usage_limit_is_a_refusal_not_a_failure(self):
        code, receipt = self.generate(self.fake_run(
            stream(errors=["You've hit your usage limit."], completed=False), rc=1))
        self.assertEqual((code, receipt["status"]), (3, "usage_limit"))
        self.assertFalse(self.out.exists())

    def test_no_image_record_fails_without_resend(self):
        empty = json.dumps({"type": "session_meta", "payload": {"id": THREAD}}) + "\n"
        code, receipt = self.generate(self.fake_run(stream(), empty))
        self.assertEqual(code, 4)
        self.assertEqual(receipt["reasons"], ["IMAGE_GEN_NOT_RUN"])
        self.assertEqual(len(self.calls), 1)

    def test_existing_output_or_secret_stops_before_any_call(self):
        self.out.write_bytes(b"keep me")
        with self.assertRaises(m.ImageError) as caught:
            self.generate(self.fake_run(stream()))
        self.assertEqual(caught.exception.exit_code, 2)
        self.assertEqual(self.out.read_bytes(), b"keep me")
        self.out.unlink()
        with self.assertRaises(m.ImageError) as caught:
            m.generate("key sk-ant-api03-" + "A" * 90, str(self.out), collect=observation,
                       run=self.fake_run(stream()), command=["codex"], home=self.home, now=NOW)
        self.assertEqual(caught.exception.code, "SENSITIVE_PAYLOAD")
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
