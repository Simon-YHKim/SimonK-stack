"""Offline bus watcher tests: disposable bus only, no process or network."""
import sys


def deny_effects(event, args):
    if event.startswith(("subprocess.", "socket.", "os.exec", "os.spawn")) or event in {
            "os.system", "os.kill", "os.killpg"}:
        raise AssertionError("External effects forbidden in bus watcher fixtures")


sys.addaudithook(deny_effects)

import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

BOT_ROOT = Path(__file__).resolve().parents[2]


def load_watcher(bus: Path, drafts: Path, hub: Path):
    env = {"VIBE_BOT_BUS": str(bus), "VIBE_BOT_DRAFTS": str(drafts), "VIBE_BOT_HUB_STATUS": str(hub)}
    with patch.dict(os.environ, env):
        spec = importlib.util.spec_from_file_location("bus_watch_fixture", BOT_ROOT / "scripts/bus_watch.py")
        value = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(value)
    return value


def write(path: Path, text: str, age_seconds: float = 0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if age_seconds:
        past = time.time() - age_seconds
        os.utime(path, (past, past))
    return path


def tree_digest(root: Path) -> dict:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


class BusWatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.bus = base / "bus"
        self.drafts = base / "drafts"
        self.hub = base / "hub" / "STATUS.md"
        self.state = base / "state" / "bus_watch.json"
        for d in ("relay/inbox", "relay/outbox", "keys/inbox", "keys/outbox"):
            (self.bus / d).mkdir(parents=True)
        self.drafts.mkdir()
        write(self.hub, "nonce|task\n")
        write(self.bus / "relay/STATUS.md", "# Relay STATUS\n")
        self.w = load_watcher(self.bus, self.drafts, self.hub)

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, *args):
        out = io.StringIO()
        argv = ["bus_watch.py", "--state", str(self.state), *args]
        with patch.object(sys, "argv", argv), contextlib.redirect_stdout(out):
            self.w.main()
        return out.getvalue()

    def test_classification_separates_production_changes_and_org_noise(self):
        self.assertEqual(self.w.classify("x/keys/outbox/vb-simon-go-enabled-1.result.md"), "ALERT")
        self.assertEqual(self.w.classify("x/relay/outbox/vb-0123abcd.result.md"), "CODING")
        self.assertEqual(self.w.classify("x/relay/inbox/ping-relay-vb-0123abcd.md"), "CODING")
        for noise in ("x/drafts/hr-kpi.md", "x/relay/outbox/_tmp-hr-draft.md", "x/drafts/_relay-copy.md"):
            self.assertEqual(self.w.classify(noise), "NOISE", noise)

    def test_reply_is_found_in_any_outbox_with_any_suffix(self):
        write(self.bus / "relay/inbox/vb-11111111.claim", "Relay\n")
        write(self.bus / "keys/outbox/vb-11111111-adunit-label.result.md", "vb-11111111\n")
        status, paths = self.w.outbound_status("vb-11111111", {"pinged": False})
        self.assertEqual(status, "ANSWERED")
        self.assertTrue(paths[0].endswith("vb-11111111-adunit-label.result.md"))

    def test_one_reminder_only_after_claim_ttl(self):
        self.assertEqual(self.w.outbound_status("vb-22222222", {})[0], "UNCLAIMED")
        claim = write(self.bus / "relay/inbox/vb-22222222.claim", "Relay\n")
        self.assertTrue(self.w.outbound_status("vb-22222222", {"pinged": False})[0].startswith("CLAIMED"))
        past = time.time() - (self.w.PING_AFTER_MIN + 5) * 60
        os.utime(claim, (past, past))
        self.assertTrue(self.w.outbound_status("vb-22222222", {"pinged": False})[0].startswith("PING-DUE"))
        self.assertTrue(self.w.outbound_status("vb-22222222", {"pinged": True})[0].startswith("CLAIMED"))

    def test_coding_task_detection_ignores_own_outbound_tasks(self):
        write(self.bus / "relay/inbox/vb-33333333.md", "# 과제\n담당 봇: Coding LLM (via relay pointer)\n")
        write(self.bus / "relay/inbox/vb-44444444.md", "# 과제서\n작성 · 발행 Claude Code · 담당 봇: Coding LLM\n")
        out = self.run_main()
        self.assertIn("OPEN-CODING-TASK vb-33333333", out)
        self.assertNotIn("vb-44444444", out.split("OPEN-CODING-TASK", 1)[-1])

    def test_heading_task_stays_open_until_the_coding_session_answers(self):
        nonce = "vb-1865-date-q5-fix"
        write(self.bus / f"relay/inbox/{nonce}.md", "# Task — Coding · #1865 date 09-26\n\n- From: Relay\n")
        self.assertIn(f"OPEN-CODING-TASK {nonce}", self.run_main())
        # Relay's own dispatch note reuses the nonce and names the Coding LLM.
        write(self.bus / f"relay/outbox/{nonce}.result.md",
              "# Result — dispatch\n- **Bot:** `aurelius`\n1. Coding LLM (file bus) will update the PR.\n")
        self.assertIn(f"OPEN-CODING-TASK {nonce}", self.run_main())
        write(self.bus / f"relay/outbox/{nonce}.coding.result.md",
              f"{nonce}\n# Result\n- **Bot:** Claude Code (코딩 LLM)\n")
        self.assertNotIn(f"OPEN-CODING-TASK {nonce}", self.run_main())

    def run_watch(self):
        out = io.StringIO()
        argv = ["bus_watch.py", "--state", str(self.state), "--watch", "--once"]
        with patch.object(sys, "argv", argv), contextlib.redirect_stdout(out):
            self.w.main()
        return out.getvalue()

    def test_watch_reports_an_answer_that_landed_before_the_monitor_started(self):
        # 2026-09-26 22:18: the review result arrived, then a monitor armed at
        # 22:19 took it as already present. The baseline must be the saved state.
        self.run_main("--track", "vb-b36e42bf")
        write(self.bus / "relay/outbox/vb-b36e42bf.result.md", "vb-b36e42bf\n# Result\n")
        out = self.run_watch()
        self.assertIn("ANSWER vb-b36e42bf:", out)

    def test_watch_orders_by_urgency_and_drops_org_noise(self):
        self.run_main("--track", "vb-88888888")
        write(self.drafts / "hr-kpi.md", "# HR\n")
        write(self.bus / "relay/outbox/_tmp-copy.md", "# tmp\n")
        write(self.bus / "relay/inbox/vb-99999999.md", "# Task — Coding · fix the copy\n")
        write(self.bus / "keys/outbox/vb-simon-go-x.result.md", "# Simon GO\n")
        write(self.bus / "keys/outbox/vb-88888888.result.md", "vb-88888888\n")
        lines = [l for l in self.run_watch().splitlines() if l]
        self.assertEqual([l.split(" ", 1)[0] for l in lines], ["ANSWER", "ALERT", "CODING"])
        self.assertFalse(any("hr-kpi" in l or "_tmp-copy" in l for l in lines))

    def test_watch_never_writes_state(self):
        self.run_main()
        before = self.state.read_bytes()
        write(self.bus / "relay/outbox/vb-12121212.result.md", "vb-12121212\n")
        self.assertIn("NEW bus file:", self.run_watch())
        self.assertEqual(self.state.read_bytes(), before)

    def test_scan_never_writes_to_the_bus_and_keeps_state_outside(self):
        write(self.bus / "keys/outbox/vb-simon-go-x.result.md", "# Simon GO\n")
        write(self.drafts / "hr-org.md", "# HR\n")
        before = tree_digest(self.bus)
        out = self.run_main("--track", "vb-55555555")
        self.assertEqual(tree_digest(self.bus), before)
        self.assertIn("[ALERT]", out)
        self.assertIn("[NOISE] 1 file(s) skipped", out)
        self.assertIn("OUTBOUND vb-55555555: UNCLAIMED", out)
        state = json.loads(self.state.read_text(encoding="utf-8"))
        self.assertIn("vb-55555555", state["outbound"])
        self.assertFalse(Path(self.w.DEFAULT_STATE).resolve().is_relative_to(BOT_ROOT.resolve()))

    def test_second_scan_reports_only_changes(self):
        self.run_main()
        write(self.bus / "relay/outbox/vb-66666666.result.md", "vb-66666666\n")
        out = self.run_main()
        self.assertIn("vb-66666666.result.md", out)
        self.assertNotIn("STATUS.md", out.split("RELAY STATUS", 1)[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
