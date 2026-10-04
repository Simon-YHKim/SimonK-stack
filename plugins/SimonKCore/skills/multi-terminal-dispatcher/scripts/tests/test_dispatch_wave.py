"""Offline wave/PowerShell integration. Real state + adapter, fake native Orca."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

SCRIPT = Path(__file__).resolve().parents[1] / "dispatch_wave.py"
ROOT = Path(__file__).resolve().parents[4]
CORE = ROOT / "skills-src/vibe/scripts"
sys.path.insert(0, str(CORE))
with patch("subprocess.Popen", side_effect=AssertionError("Process launch during test import")):
    import execute_orca
    import orchestrate
    import run_state
    from test_execute_orca import FakeOrca
    from test_orchestrate import candidate, fixture_registry, step


class TaggedOrca(FakeOrca):
    def __init__(self, node_id, path):
        super().__init__()
        self.tag = node_id
        self.path = str(path)
        self.executable = "/fixture/" + node_id + ".exe"

    def call(self, *args):
        value = super().call(*args)
        def rename(item):
            if isinstance(item, str):
                return item.replace("task-fixture", "task-" + self.tag).replace("ctx-fixture", "ctx-" + self.tag)
            if isinstance(item, list):
                return [rename(x) for x in item]
            if isinstance(item, dict):
                return {k: rename(v) for k, v in item.items()}
            return item
        return rename(value)


class WaveTests(unittest.TestCase):
    def setUp(self):
        # Shell integration has its own explicit opt-in below; ordinary unit
        # cases never launch any child, even after an accidental real import.
        if self._testMethodName != "test_actual_powershell_preview_and_rejected_dispatch":
            process_guard = patch("subprocess.Popen", side_effect=AssertionError("Offline wave: no process launch"))
            process_guard.start()
            self.addCleanup(process_guard.stop)
        self.assertTrue(SCRIPT.exists(), "A bounded wave consumer of the canonical state/adapter is missing")
        spec = importlib.util.spec_from_file_location("dispatch_wave", SCRIPT)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.temp = tempfile.TemporaryDirectory(prefix="wave-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        now = datetime.now(timezone.utc)
        self.now = now.isoformat()
        self.later = (now + timedelta(minutes=15)).isoformat()
        self.db = self.root / "state.sqlite3"
        self.store = run_state.Store(self.db)
        self.store.initialize()
        self.transports = {name: TaggedOrca(name, self.root) for name in ("one", "two", "after")}
        self.factory_calls = []
        c = candidate(model="gpt-5.6-luna", transport="orca", observed_at=self.now,
                      quota={"used_pct": 10, "observed_at": self.now})
        guards = {"quota_checked_vendors": ["claude", "codex", "grok", "gemini"]}
        nodes = []
        for name, transport in self.transports.items():
            binding = {"run_id": "run-fixture", "task_id": "task-" + name,
                       "worktree_id": "workspace-fixture", "worktree_path": str(self.root),
                       "workspace_instance": "instance-fixture", "executable": transport.executable,
                       "executable_sha256": transport.sha256, "app_version": "1.4.206",
                       "runtime_id": "runtime-fixture", "account_ref": "test-account",
                       "profile_ref": "profile-fixture", "guards": guards}
            nodes.append(step(name, proc="inventory-schema", **{"class": "A"}, orca=binding,
                              depends_on=["one", "two"] if name == "after" else []))
        registry = fixture_registry([c])
        registry["checked_at"] = self.now
        self.plan = orchestrate.make_plan({"run_id": "wave-run", "ancestor_skills": ["vibe"], "steps": nodes},
                                          {"explain": {"path": "/fixture/SKILL.md"}},
                                          {"candidates": [c], **guards}, self.now, registry)
        self.assertEqual(self.plan["status"], "ready", self.plan)
        self.store.register(self.plan, now=self.now)
        self.certificates = {}
        for node in self.plan["steps"]:
            self.transports[node["id"]].spec = execute_orca.render_spec(node)
            self.certificates[node["id"]] = {
                "verified": True, "binding_sha256": execute_orca.binding_digest(self.plan, node["id"]),
                "account_ref": "test-account", "profile_ref": "profile-fixture", "observed_at": self.now,
                "valid_until": self.later, "billing": copy.deepcopy(c["billing"]), "evidence": ["fixture-only"]}
            self.certificates[node["id"]]["request_identity"] = {
                "contract": "caller-chosen-uuid-first-worker-start-v1", "supported": True,
                "binding_sha256": execute_orca.binding_digest(self.plan, node["id"]),
                "runtime_id": "runtime-fixture", "app_version": "1.4.206",
                "executable_sha256": self.transports[node["id"]].sha256,
                "observed_at": self.now, "valid_until": self.later,
                "evidence": ["synthetic fixture; not native support evidence"]}

    def factory(self, executable, sha):
        self.factory_calls.append(executable)
        return next(t for t in self.transports.values() if t.executable == executable)

    def run_wave(self, action="dispatch", nodes=None, certificates=None):
        return self.m.run_wave(action, self.plan, self.store,
                               self.certificates if certificates is None else certificates,
                               nodes, transport_factory=self.factory, clock=lambda: self.now)

    def starts(self, node=None):
        transports = [self.transports[node]] if node else self.transports.values()
        return sum(len(a) > 1 and a[1] == "worker-start" for t in transports for a in t.calls)

    def test_preview_uses_shared_readiness_without_native_or_state_mutation(self):
        before = self.db.read_bytes()
        result = self.run_wave("preview")
        self.assertEqual(result["ready"], ["one", "two"])
        self.assertEqual(result["status"], "preview")
        self.assertEqual(self.factory_calls, [])
        self.assertEqual(before, self.db.read_bytes())

    def test_two_native_workers_start_but_dependent_node_waits(self):
        result = self.run_wave()
        self.assertEqual(result["status"], "dispatched")
        self.assertEqual([r["node_id"] for r in result["results"]], ["one", "two"])
        self.assertEqual(self.starts(), 2)
        self.assertEqual(self.starts("after"), 0)
        self.assertEqual(len(self.store.snapshot()["attempts"]), 2)
        self.assertTrue(all(r["actual_usd"] is None and not r["verified"] for r in result["results"]))

    def test_reentry_is_reconcile_only_with_no_fresh_certificate(self):
        self.run_wave()
        result = self.run_wave(certificates={})
        self.assertEqual(result["status"], "reconciled")
        self.assertEqual(self.starts(), 2)
        self.assertEqual(result["new_dispatches"], [])

    def test_legacy_pending_is_visible_and_reconciled_without_refill_or_certificate(self):
        legacy = "vibe-orca-" + execute_orca.binding_digest(self.plan, "one")
        old = self.store.claim("wave-run", "one", legacy, self.plan["plan_digest"], now=self.now)
        preview = self.run_wave("preview")
        self.assertEqual(preview["next_action"], "reconcile")
        self.assertEqual(preview["unresolved"][0]["request_id"], legacy)
        result = self.run_wave(nodes=["two"], certificates={})
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["results"][0]["dispatch_id"], old["dispatch_id"])
        self.assertEqual(result["results"][0]["request_id"], legacy)
        self.assertEqual(result["results"][0]["state"], "uncertain")
        self.assertEqual(result["new_dispatches"], [])
        self.assertEqual(result["deferred"], ["two"])
        self.assertEqual(self.starts(), 0)

    def test_foreign_or_ambiguous_identity_blocks_before_transport(self):
        self.store.claim("wave-run", "one", execute_orca.request_id(self.plan, "one"),
                         self.plan["plan_digest"], now=self.now)
        snapshot = self.store.snapshot()
        for mode in ("foreign", "ambiguous"):
            changed = copy.deepcopy(snapshot)
            if mode == "foreign":
                changed["attempts"][0]["request_id"] = "vibe-orca-wrong-binding"
            else:
                changed["attempts"].append(dict(changed["attempts"][0], dispatch_id="conflict",
                    request_id="vibe-orca-" + execute_orca.binding_digest(self.plan, "one")))
            with patch.object(self.store, "snapshot", return_value=changed):
                self.assertEqual(self.run_wave()["status"], "blocked")
            self.assertEqual(self.factory_calls, [])

    def test_one_missing_first_use_contract_blocks_whole_wave_before_claim(self):
        del self.certificates["two"]["request_identity"]
        self.assertEqual(self.run_wave()["status"], "blocked")
        self.assertEqual(self.starts(), 0)
        self.assertEqual(self.store.snapshot()["attempts"], [])

    def test_one_bad_certificate_blocks_entire_fresh_wave(self):
        self.certificates["two"]["verified"] = False
        result = self.run_wave()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(self.starts(), 0)
        self.assertEqual(self.store.snapshot()["attempts"], [])

    def test_invalid_selection_cannot_partially_dispatch(self):
        for nodes in (["one", "missing"], ["one", "one"], ["one", "after"]):
            with self.subTest(nodes=nodes):
                result = self.run_wave(nodes=nodes)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(self.starts(), 0)

    def test_uncertain_first_send_stops_remaining_wave(self):
        self.transports["one"].effective = None
        result = self.run_wave()
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["deferred"], ["two"])
        self.assertEqual(self.starts(), 1)
        self.assertEqual(result["results"][0]["state"], "uncertain")
        resumed = self.run_wave()
        self.assertEqual(resumed["status"], "blocked")
        self.assertEqual(self.starts(), 1)

    def test_crash_after_acceptance_is_not_resent_and_does_not_refill(self):
        def crash():
            raise KeyboardInterrupt()
        self.transports["one"].after_start = crash
        with self.assertRaises(KeyboardInterrupt):
            self.run_wave()
        self.transports["one"].after_start = None
        result = self.run_wave()
        self.assertEqual(result["status"], "reconciled")
        self.assertEqual(self.starts(), 1)
        self.assertEqual(self.starts("two"), 0)

    def test_state_unavailable_after_acceptance_does_not_claim_no_intent(self):
        snapshot = self.store.snapshot
        def unavailable():
            raise run_state.StateError("STATE_DB_UNAVAILABLE")
        def accepted():
            self.store.snapshot = unavailable
        self.transports["one"].after_start = accepted
        try:
            result = self.run_wave()
        finally:
            self.store.snapshot = snapshot
        self.assertEqual(self.starts(), 1)
        self.assertEqual(self.store.snapshot()["attempts"][0]["state"], "intent")
        self.assertEqual(result["new_dispatches"], [])
        self.assertEqual(result["deferred"], ["two"])
        self.assertEqual(result["admission_unknown"], ["one"])
        self.assertFalse(result["state_available"])
        self.assertIsNone(result["budget_halted"])
        self.assertEqual(self.run_wave()["status"], "reconciled")
        self.assertEqual(self.starts(), 1)

    def test_terminal_unknown_cost_stops_new_starts(self):
        self.transports["one"].terminal = True
        result = self.run_wave()
        self.assertEqual(result["status"], "partial")
        self.assertEqual(self.starts(), 1)
        self.assertTrue(self.store.snapshot()["budget"]["halted"])
        self.assertTrue(result["budget_halted"])
        self.assertEqual(result["halt_reason"], "COST_UNRESOLVED")
        self.assertIsNone(result["results"][0]["actual_usd"])

    def test_selected_node_cannot_hide_pending_sibling(self):
        self.run_wave(nodes=["one"])
        result = self.run_wave(nodes=["two"])
        self.assertEqual(result["status"], "reconciled")
        self.assertEqual(result["deferred"], ["two"])
        self.assertEqual(self.starts(), 1)

    def test_expiry_after_whole_wave_preflight_stops_later_start(self):
        def expire():
            self.now = self.later
        self.transports["one"].after_start = expire
        result = self.run_wave()
        self.assertEqual(result["status"], "partial")
        self.assertEqual(self.starts(), 1)
        self.assertEqual(result["deferred"], ["two"])

    def test_unverified_success_waits_then_accepted_settled_nodes_allow_next_wave(self):
        self.run_wave()
        for transport in self.transports.values():
            transport.terminal = True
        reconciled = self.run_wave()
        for row in reconciled["results"]:
            self.store.settle(row["dispatch_id"], 0, ["fixture receipt"], now=self.now)
        waiting = self.run_wave()
        self.assertEqual(waiting["ready"], [])
        self.assertEqual(self.starts(), 2)
        self.assertTrue(all(not r["verified"] for r in waiting["results"]))
        for row in waiting["results"]:
            self.store.verify(row["dispatch_id"], ["fixture acceptance"], now=self.now)
        self.transports["after"].terminal = False
        next_wave = self.run_wave()
        self.assertEqual(next_wave["status"], "dispatched")
        self.assertEqual(next_wave["new_dispatches"], ["after"])
        self.assertEqual(self.starts(), 3)

    def test_changed_plan_or_unregistered_database_is_blocked_without_native_reads(self):
        for change in ("tamper", "empty_store"):
            with self.subTest(change=change):
                plan, store = copy.deepcopy(self.plan), self.store
                if change == "tamper":
                    plan["steps"][0]["task"] = "different"
                else:
                    store = run_state.Store(self.root / "empty.sqlite3")
                    store.initialize()
                result = self.m.run_wave("dispatch", plan, store, self.certificates,
                                         transport_factory=self.factory, clock=lambda: self.now)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(self.factory_calls, [])

    def test_missing_store_is_not_implicitly_created(self):
        missing = self.root / "missing.sqlite3"
        result = self.m.run_wave("preview", self.plan, run_state.Store(missing), {},
                                 transport_factory=self.factory, clock=lambda: self.now)
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(missing.exists())
        self.assertEqual(self.factory_calls, [])

    def test_later_preflight_native_read_failure_blocks_first_start(self):
        self.transports["two"].runtime = "wrong-runtime"
        result = self.run_wave()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(self.starts(), 0)
        self.assertEqual(self.store.snapshot()["attempts"], [])

    def mixed_local_predecessor(self, finished):
        c = candidate(model="gpt-5.6-luna", transport="orca", observed_at=self.now,
                      quota={"used_pct": 10, "observed_at": self.now})
        registry = fixture_registry([c])
        registry["checked_at"] = self.now
        nodes = copy.deepcopy(self.plan["steps"])
        argv = ["python", "--version"]
        nodes[0] = {"id": "one", "kind": "local", "task": "Read local version", "skills": ["explain"],
                    "needs": [], "writes": False, "depends_on": [], "argv": argv, "software": ["python"]}
        nodes[1]["depends_on"] = ["one"]
        runtime = {"candidates": [c], "quota_checked_vendors": ["claude", "codex", "grok", "gemini"],
                   "observed_at": self.now, "tools": ["python"], "tool_costs": [{
                       "argv_sha256": orchestrate.digest(argv), "verified": True, "evidence": ["local fixture"],
                       "observed_at": self.now, "upper_usd_per_attempt": 0}]}
        self.plan = orchestrate.make_plan({"run_id": "mixed-run", "steps": nodes},
            {"explain": {"path": "/fixture/SKILL.md"}}, runtime, self.now, registry)
        self.store = run_state.Store(self.root / "mixed.sqlite3")
        self.store.initialize()
        self.store.register(self.plan, now=self.now)
        attempt = self.store.claim("mixed-run", "one", "local-one", self.plan["plan_digest"], now=self.now)
        if finished:
            handle = {"kind": "tool", "id": "local-fixture", "identity": "local-identity"}
            self.store.bind(attempt["dispatch_id"], handle, now=self.now)
            self.store.observe(attempt["dispatch_id"], {"state": "succeeded", "handle": handle,
                "observed_at": self.now, "evidence": ["local output"]}, now=self.now)
            self.store.settle(attempt["dispatch_id"], 0, ["local receipt"], now=self.now)
            self.store.verify(attempt["dispatch_id"], ["local acceptance"], now=self.now)
        for node in self.plan["steps"][1:]:
            self.certificates[node["id"]]["binding_sha256"] = execute_orca.binding_digest(self.plan, node["id"])
            self.certificates[node["id"]]["request_identity"]["binding_sha256"] = execute_orca.binding_digest(self.plan, node["id"])
            self.transports[node["id"]].spec = execute_orca.render_spec(node)

    def test_finalized_local_predecessor_does_not_block_orca_wave(self):
        self.mixed_local_predecessor(finished=True)
        self.assertEqual(self.store.ready("mixed-run", now=self.now), ["two"])
        self.assertEqual(self.run_wave("preview")["status"], "preview")
        result = self.run_wave()
        self.assertEqual(result["status"], "dispatched")
        self.assertEqual(result["new_dispatches"], ["two"])
        self.assertEqual(self.starts(), 1)

    def test_unresolved_other_transport_is_visible_but_never_replayed(self):
        self.mixed_local_predecessor(finished=False)
        preview = self.run_wave("preview")
        self.assertEqual(preview["status"], "preview")
        self.assertEqual([a["node_id"] for a in preview["unresolved"]], ["one"])
        for action in ("dispatch", "reconcile"):
            result = self.run_wave(action)
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["unsupported_nodes"], ["one"])
            self.assertTrue(result["state_available"])
            self.assertEqual(self.factory_calls, [])

    def test_reconcile_never_dispatches_fresh_nodes(self):
        result = self.run_wave("reconcile")
        self.assertEqual(result["status"], "waiting")
        self.assertEqual(self.starts(), 0)

    def test_expired_certificate_cannot_start(self):
        self.certificates["two"]["valid_until"] = self.now
        result = self.run_wave()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(self.starts(), 0)

    @unittest.skipUnless(os.environ.get("VIBE_REVIEWED_SHELL_INTEGRATION") == "1",
                         "Native shell integration requires separately reviewed isolation; not a unit test")
    def test_actual_powershell_preview_and_rejected_dispatch(self):
        pwsh = shutil.which("pwsh")
        if not pwsh:
            self.skipTest("PowerShell 7 required for executable shim tests")
        plan = self.root / "plan's 경로.json"
        plan.write_text(json.dumps(self.plan), encoding="utf-8")
        for action in (None, "preview", "dispatch"):
            arguments = [] if action is None else ["-Action", action]
            result = subprocess.run([pwsh, "-NoProfile", "-NonInteractive", "-File",
                                     str(ROOT / "scripts/multi-terminal-launch.ps1"),
                                     *arguments, "-PlanPath", str(plan), "-DbPath", str(self.db)],
                                    capture_output=True, text=True, encoding="utf-8", timeout=20,
                                    env={**os.environ, "PYTHONUTF8": "1"})
            self.assertEqual(result.returncode, 2 if action == "dispatch" else 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data["status"], "blocked" if action == "dispatch" else "preview")
        self.assertEqual(self.store.snapshot()["attempts"], [])


@unittest.skipUnless(os.environ.get("VIBE_REVIEWED_SHELL_INTEGRATION") == "1",
                     "Native shell integration requires separately reviewed isolation; not a unit test")
class LegacyShellTests(unittest.TestCase):
    def test_empty_legacy_args_and_conflicting_dry_run_fail_closed(self):
        pwsh = shutil.which("pwsh")
        if not pwsh:
            self.skipTest("PowerShell 7 required")
        for args in (["-ConfigPath", ""], ["-CostThreshold", "0"],
                     ["-DryRun", "-Action", "dispatch"], ["-Node", ""]):
            with self.subTest(args=args):
                result = subprocess.run([pwsh, "-NoProfile", "-NonInteractive", "-File",
                                         str(ROOT / "scripts/multi-terminal-launch.ps1"),
                                         "-PlanPath", "absent.json", "-DbPath", "absent.sqlite3", *args],
                                        capture_output=True, text=True, encoding="utf-8", timeout=15)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(json.loads(result.stdout)["error"], "WAVE_INPUT_REQUIRED")

    def test_legacy_dry_run_no_longer_accepts_unpriced_task_config(self):
        pwsh = shutil.which("pwsh")
        if not pwsh:
            self.skipTest("PowerShell 7 required")
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "legacy.json"
            config.write_text(json.dumps({"tasks": [{"id": "one", "model": "unknown-model-fixture",
                                                      "type": "RESEARCH", "prompt": "private-fixture-text"}]}))
            # DryRun makes the old unsafe implementation non-mutating for RED.
            result = subprocess.run([pwsh, "-NoProfile", "-NonInteractive", "-File",
                                     str(ROOT / "scripts/multi-terminal-launch.ps1"),
                                     "-ConfigPath", str(config), "-DryRun"],
                                    capture_output=True, text=True, encoding="utf-8", timeout=15)
            self.assertEqual(result.returncode, 2, result.stdout)
            self.assertNotIn("private-fixture-text", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
