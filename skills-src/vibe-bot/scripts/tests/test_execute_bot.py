"""Offline Bot publication tests: no provider, real bus, process or network."""
import sys


def deny_effects(event, args):
    if event.startswith(("subprocess.", "socket.", "os.exec", "os.spawn")) or event in {
            "os.system", "os.kill", "os.killpg"}:
        raise AssertionError("External effects forbidden in Bot fixtures")


sys.addaudithook(deny_effects)

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import marshal
from pathlib import Path
import tempfile
import threading
import struct
import unittest
from unittest.mock import patch

BOT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = BOT_ROOT.parent / "vibe/scripts"
sys.path.insert(0, str(SCRIPTS))
import orchestrate
from run_state import Store, StateError
from test_orchestrate import NOW, candidate, fixture_registry


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


builder = module("bot_fixture_builder", BOT_ROOT / "scripts/make_bot_spec.py")


class LegacyDeliveryTests(unittest.TestCase):
    def test_hub_without_central_claim_has_no_file_effect(self):
        with tempfile.TemporaryDirectory() as root, contextlib.redirect_stdout(io.StringIO()):
            rc = builder.main(["--mode", "console", "--target", "Fixture Console",
                "--task", "Read the fixture screen and report its displayed status", "--bot", "relay",
                "--deliver", "hub", "--hub", root, "--out", root])
            self.assertNotEqual(rc, 0)
            self.assertEqual(list(Path(root).iterdir()), [])

    def test_manual_draft_cannot_write_into_declared_watched_bus(self):
        with tempfile.TemporaryDirectory() as root, contextlib.redirect_stdout(io.StringIO()):
            rc = builder.main(["--mode", "console", "--target", "Fixture Console",
                "--task", "Read the fixture screen and report its displayed status", "--bot", "relay",
                "--hub", root, "--out", str(Path(root) / "bots/relay/inbox")])
            self.assertNotEqual(rc, 0)
            self.assertEqual(list(Path(root).iterdir()), [])

    def test_send_flag_and_direct_webhook_cannot_restore_legacy_delivery(self):
        with tempfile.TemporaryDirectory() as root, contextlib.redirect_stdout(io.StringIO()):
            rc = builder.main(["--task", "Read the fixture screen and report its displayed status",
                "--send", "--hub", root, "--out", root])
            self.assertNotEqual(rc, 0)
            self.assertEqual(list(Path(root).iterdir()), [])
        with patch.object(builder, "TRANSPORT_VERIFIED", True):
            with patch.dict("os.environ", {builder.WEBHOOK_URL_ENV: "https://invalid.example",
                    builder.WEBHOOK_KEY_ENV: "fixture-not-an-operational-key"}):
                self.assertFalse(builder.send_webhook({"nonce": "vb-00000001"})[0])


class BotAdapterTests(unittest.TestCase):
    def setUp(self):
        path = SCRIPTS / "execute_bot.py"
        self.assertTrue(path.is_file(), "Shared durable Bot publication adapter is missing")
        self.m = module("execute_bot_fixture", path)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.bot_root = self.root / "bot"
        (self.bot_root / "scripts").mkdir(parents=True)
        helper = self.bot_root / "scripts/make_bot_spec.py"
        helper.write_bytes((BOT_ROOT / "scripts/make_bot_spec.py").read_bytes())
        (self.bot_root / "bots.json").write_text(json.dumps({"bots": [
            {"id": "relay", "name": "Fixture Relay", "status": "active", "keywords": []}]}))
        self.bus = self.root / "bus"
        self.bus.mkdir()
        self.nonce = "vb-00000001"
        self.task = "Read the fixture screen and report its displayed status"
        self.target = "Fixture Console"
        meta = {"nonce": self.nonce, "bot": "relay", "mode": "console", "target": self.target,
                "task": self.task, "deliver": "manual", "project": None}
        spec = builder.build_console_spec(self.task, self.nonce, target=self.target,
            return_to=str(self.bus / "relay/outbox" / (self.nonce + ".result.md")))
        self.spec = self.root / "draft.md"
        self.meta = self.root / "draft.meta.json"
        self.spec.write_text(spec, encoding="utf-8")
        self.meta.write_text(json.dumps(meta), encoding="utf-8")
        self.binding = {"nonce": self.nonce, "bot_root": str(self.bot_root), "bus_root": str(self.bus),
            "spec_path": str(self.spec), "meta_path": str(self.meta),
            "spec_sha256": self.sha(self.spec), "meta_sha256": self.sha(self.meta),
            "helper_sha256": self.sha(helper), "roster_sha256": self.sha(self.bot_root / "bots.json")}
        c = candidate("bot", "grok-bot", transport="bot", model=None, bot_id="relay",
                      bot_status="active", capabilities=["gui"])
        request = {"run_id": "bot-fixture", "steps": [{"id": "screen", "kind": "gui",
            "task": self.task, "target": self.target, "skills": ["vibe-bot"], "needs": ["gui"],
            "gui_reason": "fixture screen only", "tool_route_available": False,
            "writes": False, "bot_delivery": self.binding}]}
        self.plan = orchestrate.make_plan(request, {"vibe-bot": {"name": "vibe-bot",
            "path": str(BOT_ROOT / "SKILL.md"), "description": "fixture"}},
            {"candidates": [c], "observed_at": NOW}, NOW, fixture_registry([c]))
        self.assertEqual(self.plan["status"], "ready", self.plan)
        self.store = Store(self.root / "runs.sqlite3")
        self.store.initialize()
        self.store.register(self.plan, now=NOW)
        route = self.plan["steps"][0]["route"]
        self.proof = {"verified": True, "binding_sha256": self.m.binding_digest(self.plan, "screen"),
            "account_ref": route["billing"]["account_ref"], "billing": route["billing"],
            "relay_account_ref": route["billing"]["account_ref"],
            "quota": route["quota"], "bot_id": "relay", "bus_root": str(self.bus),
            "delivery_authorized": True, "approval_ref": "fixture-only-approval",
            "relay_verified": True, "all_delivery_costs_included": True,
            "observed_at": NOW, "valid_until": "2026-09-23T10:10:00+00:00",
            "evidence": ["synthetic test only; not operational authorization"]}
        self.adapter = self.m.Adapter(self.store, clock=lambda: NOW)
        self.inbox = self.bus / "relay/inbox"

    @staticmethod
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def dispatch(self):
        return self.adapter.dispatch(self.plan, "screen", self.proof)

    def test_publication_is_complete_and_replay_is_read_only(self):
        result = self.dispatch()
        self.assertEqual(result["status"], "waiting_external")
        self.assertFalse(result["bot_acceptance_verified"])
        self.assertIsNone(result["actual_usd"])
        self.assertEqual((self.inbox / (self.nonce + ".md")).read_bytes(), self.spec.read_bytes())
        published = json.loads((self.inbox / (self.nonce + ".meta.json")).read_bytes())
        self.assertEqual(published["vibe"]["run_id"], self.plan["run_id"])
        self.assertEqual(published["vibe"]["dispatch_id"], result["dispatch_id"])
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.bus.rglob("*") if p.is_file()}
        with patch.object(self.m, "publish", side_effect=AssertionError("No replay writes")):
            again = self.dispatch()
        self.assertEqual(again["dispatch_id"], result["dispatch_id"])
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns)
                                 for p in self.bus.rglob("*") if p.is_file()})
        self.assertEqual(len(self.store.snapshot()["attempts"]), 1)
        self.assertIsNone(self.store.snapshot()["budget"]["actual_total_usd"])

    def test_md_is_last_commit_marker(self):
        original = self.m.publish
        seen = []
        def watched(path, data):
            if path.suffix == ".md":
                published = json.loads((self.inbox / (self.nonce + ".meta.json")).read_bytes())
                self.assertEqual(published["nonce"], self.nonce)
                self.assertEqual(published["vibe"]["node_id"], "screen")
                self.assertFalse(path.exists())
            original(path, data)
            seen.append(path.name)
        with patch.object(self.m, "publish", side_effect=watched):
            self.dispatch()
        self.assertEqual(seen, [self.nonce + ".meta.json", self.nonce + ".md"])

    def test_meta_only_crash_never_resends(self):
        original = self.m.publish
        def fail_md(path, data):
            if path.suffix == ".md":
                raise OSError("fixture interruption")
            original(path, data)
        with patch.object(self.m, "publish", side_effect=fail_md):
            result = self.dispatch()
        self.assertEqual(result["status"], "uncertain")
        with patch.object(self.m, "publish", side_effect=AssertionError("No resumed send")):
            self.assertEqual(self.dispatch()["status"], "uncertain")
        self.assertFalse((self.inbox / (self.nonce + ".md")).exists())

    def test_crash_after_publish_recovers_binding_without_publish(self):
        with patch.object(self.store, "bind", side_effect=OSError("fixture crash")):
            with self.assertRaises(OSError):
                self.dispatch()
        self.assertIsNone(self.store.snapshot()["attempts"][0]["handle"])
        with patch.object(self.m, "publish", side_effect=AssertionError("No duplicate send")):
            self.assertEqual(self.dispatch()["status"], "waiting_external")

    def test_unknown_unbound_publication_stays_uncertain_after_binding(self):
        with patch.object(self.store, "bind", side_effect=OSError("fixture crash")):
            with self.assertRaises(OSError):
                self.dispatch()
        attempt = self.store.snapshot()["attempts"][0]
        self.store.observe(attempt["dispatch_id"], {"state": "unknown", "handle": None,
            "observed_at": NOW, "evidence": ["fixture crash before binding"]}, now=NOW)
        result = self.adapter.reconcile(self.plan, "screen")
        self.assertEqual(result["store_state"], "uncertain")
        self.assertFalse(result["bot_acceptance_verified"])

    def test_bad_proof_stops_before_claim_and_bus_write(self):
        for key, value in (("verified", False), ("account_ref", "other-account"),
                ("relay_account_ref", "other-relay-account"),
                ("relay_verified", False), ("all_delivery_costs_included", False),
                ("delivery_authorized", False), ("observed_at", "2026-09-22T00:00:00Z")):
            with self.subTest(key=key):
                proof = {**self.proof, key: value}
                with self.assertRaises(StateError):
                    self.adapter.dispatch(self.plan, "screen", proof)
        self.assertEqual(self.store.snapshot()["attempts"], [])
        self.assertEqual(list(self.bus.iterdir()), [])

    def test_drift_and_collision_are_not_overwritten(self):
        self.inbox.mkdir(parents=True)
        collision = self.inbox / (self.nonce + ".md")
        collision.write_text("another task", encoding="utf-8")
        with self.assertRaises(StateError):
            self.dispatch()
        self.assertEqual(collision.read_text(), "another task")
        self.assertEqual(self.store.snapshot()["attempts"], [])

    def test_recovery_does_not_need_generation_authorization(self):
        self.dispatch()
        result = self.adapter.reconcile(self.plan, "screen")
        self.assertEqual(result["status"], "waiting_external")
        self.assertFalse(result["bot_acceptance_verified"])

    def test_inactive_roster_is_rejected_even_with_matching_hash(self):
        for status in ("ON HOLD", "WITHDRAWN", "to create", "inactive"):
            with self.subTest(status=status):
                changed = copy.deepcopy(self.plan)
                roster = self.bot_root / "bots.json"
                roster.write_text(json.dumps({"bots": [{"id": "relay", "status": status}]}))
                changed["steps"][0]["bot_delivery"]["roster_sha256"] = self.sha(roster)
                changed["plan_digest"] = orchestrate.digest({k: v for k, v in changed.items() if k != "plan_digest"})
                store = Store(self.root / (status.replace(" ", "-") + ".sqlite3"))
                store.initialize()
                store.register(changed, now=NOW)
                proof = {**self.proof, "binding_sha256": self.m.binding_digest(changed, "screen")}
                with self.assertRaises(StateError):
                    self.m.Adapter(store, lambda: NOW).dispatch(changed, "screen", proof)
                self.assertEqual(store.snapshot()["attempts"], [])

    def test_draft_drift_and_metadata_disagreement_stop_before_claim(self):
        self.spec.write_text(self.spec.read_text(encoding="utf-8") + "changed", encoding="utf-8")
        with self.assertRaises(StateError):
            self.dispatch()
        self.assertEqual(self.store.snapshot()["attempts"], [])
        self.assertEqual(list(self.bus.iterdir()), [])

    def test_publication_collision_does_not_overwrite_bytes(self):
        target = self.root / "existing.md"
        target.write_bytes(b"original")
        with self.assertRaises(FileExistsError):
            self.m.publish(target, b"replacement")
        self.assertEqual(target.read_bytes(), b"original")
        self.assertEqual(list(self.root.glob(".vibe-*.tmp")), [])

    def test_authority_revoked_after_claim_never_publishes_md(self):
        original = self.adapter.gate
        calls = []
        def gate(*args):
            calls.append(1)
            if len(calls) == 3:
                raise StateError("revoked-before-marker")
            return original(*args)
        with patch.object(self.adapter, "gate", side_effect=gate):
            self.assertEqual(self.dispatch()["status"], "uncertain")
        self.assertFalse((self.inbox / (self.nonce + ".md")).exists())
        self.assertEqual(len(self.store.snapshot()["attempts"]), 1)

    def test_concurrent_claims_publish_once(self):
        barrier = threading.Barrier(2)
        original = self.store.claim
        results, failures, published = [], [], []
        def claim(*args, **kwargs):
            barrier.wait(timeout=5)
            return original(*args, **kwargs)
        publish = self.m.publish
        def watched(path, data):
            publish(path, data)
            published.append(path.name)
        def run():
            try:
                results.append(self.dispatch())
            except Exception as exc:
                failures.append(type(exc).__name__)
        with patch.object(self.store, "claim", side_effect=claim), patch.object(self.m, "publish", side_effect=watched):
            threads = [threading.Thread(target=run) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)
            self.assertFalse(any(t.is_alive() for t in threads))
        self.assertEqual(failures, [])
        self.assertEqual(len(self.store.snapshot()["attempts"]), 1)
        self.assertEqual(len({r["dispatch_id"] for r in results}), 1)
        self.assertEqual(published, [self.nonce + ".meta.json", self.nonce + ".md"])

    def test_lookup_after_missing_marker_retains_existing_handle_and_hold(self):
        self.dispatch()
        marker = self.inbox / (self.nonce + ".md")
        marker.rename(marker.with_suffix(".fixture-removed"))
        result = self.adapter.reconcile(self.plan, "screen")
        self.assertEqual(result["status"], "uncertain")
        self.assertIsNotNone(self.store.snapshot()["attempts"][0]["handle"])
        self.assertIsNone(self.store.snapshot()["attempts"][0]["actual_usd"])

    def result_fixture(self, prefix=""):
        out = self.bus / "relay/outbox"
        (out / "screen.png").write_bytes(b"\x89PNG\r\n\x1a\nfixture-not-a-decoded-image")
        (out / (self.nonce + ".result.md")).write_text(
            prefix + self.nonce + "\nScreen path: Home > Status\nscreen.png\n", encoding="utf-8")
        evidence = out / "screens.json"
        evidence.write_text(json.dumps({"nonce": self.nonce, "target": self.target, "images": ["screen.png"]}))
        return evidence

    def test_result_checks_do_not_accept_embedded_nonce(self):
        self.assertTrue(callable(getattr(self.adapter, "check_result", None)), "Exact Bot result checking is missing")
        self.dispatch()
        result = self.adapter.check_result(self.plan, "screen", self.result_fixture("unrelated "))
        self.assertEqual(result["status"], "result_checks_failed")
        self.assertIn("BOT_FIRST_LINE_NONCE_MISMATCH", result["findings"])

    def test_result_checks_do_not_claim_pixel_acceptance_or_settle_cost(self):
        self.assertTrue(callable(getattr(self.adapter, "check_result", None)), "Exact Bot result checking is missing")
        self.dispatch()
        result = self.adapter.check_result(self.plan, "screen", self.result_fixture())
        self.assertEqual(result["status"], "result_checks_passed")
        self.assertTrue(result["requires_screen_inspection"])
        attempt = self.store.snapshot()["attempts"][0]
        self.assertFalse(attempt["verified"])
        self.assertEqual(attempt["state"], "uncertain")
        self.assertIsNone(attempt["actual_usd"])

    def test_result_uses_pinned_source_not_timestamp_valid_bytecode(self):
        self.dispatch()
        proof = self.result_fixture()
        helper = self.bot_root / "scripts/make_bot_spec.py"
        info = helper.stat()
        cache = Path(importlib.util.cache_from_source(str(helper)))
        cache.parent.mkdir()
        payload = compile("raise RuntimeError('STALE_BYTECODE_EXECUTED')", str(helper), "exec")
        cache.write_bytes(importlib.util.MAGIC_NUMBER + struct.pack("<III", 0, int(info.st_mtime), info.st_size)
                          + marshal.dumps(payload))
        self.assertEqual(self.sha(helper), self.binding["helper_sha256"])
        self.assertEqual(self.adapter.check_result(self.plan, "screen", proof)["status"], "result_checks_passed")


if __name__ == "__main__":
    unittest.main()
