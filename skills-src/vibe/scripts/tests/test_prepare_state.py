"""Preparation journal tests: local SQLite only; no native/provider processes."""
import copy
from concurrent.futures import ThreadPoolExecutor
import tempfile
import sys
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

with patch("subprocess.Popen", side_effect=AssertionError("No process during imports")):
    import orchestrate
    import run_state
    import execute_orca
    from test_orchestrate import NOW, candidate, fixture_registry, step
    from test_run_state import STALE, plan as generic_plan


class PreparationTests(unittest.TestCase):
    def setUp(self):
        guard = patch("subprocess.Popen", side_effect=AssertionError("No external processes"))
        guard.start()
        self.addCleanup(guard.stop)
        self.tmp = tempfile.TemporaryDirectory(prefix="vibe-prepare-fixture-")
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "state.sqlite3"
        self.store = run_state.Store(self.path)
        self.caller = {"handle": "coordinator-fixture", "identity_sha256": "b" * 64}

    def draft(self, run="prep-one", cost=0, cap=0, nodes=None):
        binding = {"worktree_id": "workspace-fixture", "worktree_path": str(Path(self.tmp.name).resolve()),
            "workspace_instance": "instance-fixture", "executable": "/fixture/orca.exe",
            "executable_sha256": "a" * 64, "app_version": "1.4.206", "runtime_id": "runtime-fixture",
            "account_ref": "test-account", "profile_ref": "profile-fixture",
            "guards": {"quota_checked_vendors": ["claude", "codex", "grok", "gemini"]}}
        c = candidate(model="gpt-5.6-luna", transport="orca", upper_usd_per_attempt=cost,
            billing={"mode": "api", "verified": True, "account_ref": "test-account"})
        steps = nodes or [step("a"), step("b", depends_on=["a"])]
        steps = [{**s, "orca": copy.deepcopy(binding), "proc": "inventory-schema", "class": "A"} for s in steps]
        p = orchestrate.make_plan({"run_id": run, "budget": {"approved_usd": cap}, "steps": steps},
            {"explain": {"path": "/fixture/SKILL.md"}}, {"candidates": [c], "tools": [], **binding["guards"]},
            NOW, fixture_registry([c]))
        self.assertEqual(p["status"], "ready", p["errors"])
        return p

    def init(self, cap=0):
        self.store.initialize(cap, "fixture-only-grant" if cap else "user-zero-additional-budget")
        self.assertTrue(hasattr(self.store, "upgrade_preparations"), "Durable preparation schema is missing")
        self.store.upgrade_preparations("fixture-only-schema-approval", now=NOW)

    def start(self, p=None):
        p = p or self.draft()
        self.store.begin_preparation(p, self.caller, now=NOW)
        return p

    def finish_op(self, key, native, run="prep-one", caller=None):
        caller = caller or self.caller
        op = self.store.preparation_intent(run, key, caller, now=NOW)
        proof = {"state": "complete", "verified": True, "native_id": native,
            "operation_sha256": op["operation_sha256"], "observed_at": NOW,
            "actual_usd": "0", "non_generating": True,
            "evidence": ["synthetic exact request, resource, ownership and scope readback"]}
        self.store.observe_preparation(run, key, caller, proof, now=NOW)
        return op

    def bind_all(self):
        self.finish_op("run", "native-run")
        self.finish_op("task:a", "native-a")
        self.finish_op("task:b", "native-b")
        state = self.store.preparation("prep-one")
        return {"verified": True, "bound_sha256": state["bound_sha256"], "observed_at": NOW,
            "no_workers": True, "scope_verified": True, "non_generating": True, "actual_usd": "0",
            "evidence": ["synthetic final Run/Task/spec/deps/workspace/caller readback"]}

    def test_explicit_migration_keeps_grant_and_old_runs(self):
        self.store.initialize()
        p = self.draft()
        self.store.register(p, now=NOW)
        before = self.store.snapshot()
        self.assertTrue(hasattr(self.store, "upgrade_preparations"), "Durable preparation schema is missing")
        self.store.upgrade_preparations("fixture-only-schema-approval", now=NOW)
        self.store.upgrade_preparations("fixture-only-schema-approval", now=NOW)
        after = self.store.snapshot()
        self.assertEqual(after["schema_version"], 2)
        self.assertEqual(before["budget"], after["budget"])
        self.assertEqual(before["runs"], after["runs"])
        self.assertEqual(after["preparations"], [])
        with self.assertRaisesRegex(run_state.StateError, "GRANT_IMMUTABLE"):
            self.store.initialize(1, "different-grant")

    def test_preparation_is_not_a_dispatchable_run_and_reserves_full_plan(self):
        self.init(1)
        p = self.start(self.draft(cost="0.1", cap=1))
        s = self.store.snapshot()
        self.assertEqual(s["runs"], [])
        self.assertEqual(s["attempts"], [])
        self.assertEqual(s["budget"]["held_usd"], "0.4")
        self.assertEqual(s["preparations"][0]["state"], "preparing")
        for call in (lambda: self.store.register(p, now=NOW),
                     lambda: self.store.ready(p["run_id"], now=NOW),
                     lambda: self.store.cancel(p["run_id"], ["not cancellation proof"], now=NOW),
                     lambda: self.store.claim(p["run_id"], "a", "request", p["plan_digest"], now=NOW)):
            with self.assertRaises(run_state.StateError):
                call()

    def test_budget_and_zero_cost_slots_do_not_disappear_on_unknown(self):
        self.init(1)
        self.start(self.draft(cost="0.2", cap=1))
        with self.assertRaisesRegex(run_state.StateError, "BUDGET_EXCEEDED"):
            self.store.register(self.draft("competing", cost="0.1", cap=1), now=NOW)
        op = self.store.preparation_intent("prep-one", "run", self.caller, now=NOW)
        self.store.observe_preparation("prep-one", "run", self.caller,
            {"state": "unknown", "operation_sha256": op["operation_sha256"], "observed_at": NOW,
             "evidence": ["absent is not non-acceptance"]}, now=NOW)
        self.store.begin_preparation(self.draft("prep-two"), {"handle": "other-pane", "identity_sha256": "c" * 64}, now=NOW)
        with self.assertRaisesRegex(run_state.StateError, "PREPARATION_LIMIT"):
            self.store.begin_preparation(self.draft("prep-three"), {"handle": "third-pane", "identity_sha256": "d" * 64}, now=NOW)
        s = self.store.snapshot()
        self.assertEqual(s["budget"]["held_usd"], "0.8")
        self.assertEqual(s["preparations"][0]["state"], "uncertain")

    def test_restart_and_concurrent_intent_allow_one_send_only(self):
        self.init()
        self.start()
        def claim(_):
            return run_state.Store(self.path).preparation_intent("prep-one", "run", self.caller, now=NOW)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(claim, range(4)))
        self.assertEqual(sum(v["send_allowed"] for v in results), 1)
        self.assertEqual(len({v["request_id"] for v in results}), 1)
        self.assertEqual(str(uuid.UUID(results[0]["request_id"])), results[0]["request_id"])
        repeated = run_state.Store(self.path).preparation_intent("prep-one", "run", self.caller, now=STALE)
        self.assertFalse(repeated["send_allowed"])
        self.assertEqual(repeated["argv"], results[0]["argv"])
        with self.assertRaises(run_state.StateError):
            self.store.preparation_intent("prep-one", "run", {**self.caller, "identity_sha256": "c" * 64}, now=NOW)

    def test_task_payload_uses_exact_specs_and_bound_native_dependencies(self):
        self.init()
        p = self.start()
        with self.assertRaises(run_state.StateError):
            self.store.preparation_intent("prep-one", "task:a", self.caller, now=NOW)
        self.finish_op("run", "native-run")
        with self.assertRaises(run_state.StateError):
            self.store.preparation_intent("prep-one", "task:b", self.caller, now=NOW)
        a = self.finish_op("task:a", "native-a")
        b = self.finish_op("task:b", "native-b")
        self.assertEqual(a["argv"][a["argv"].index("--spec") + 1], execute_orca.render_spec(p["steps"][0]))
        self.assertEqual(b["argv"][b["argv"].index("--deps") + 1], '["native-a"]')
        self.assertEqual(b["argv"][b["argv"].index("--run") + 1], "native-run")

    def test_finalization_injects_only_ids_and_transfers_hold_atomically(self):
        self.init(1)
        p = self.start(self.draft(cost="0.1", cap=1))
        proof = self.bind_all()
        before = self.store.snapshot()["budget"]
        final = self.store.finalize_preparation("prep-one", self.caller, proof, now=NOW)
        expected = copy.deepcopy(p)
        for node in expected["steps"]:
            node["orca"].update(run_id="native-run", task_id="native-" + node["id"])
        expected["plan_digest"] = orchestrate.digest({k: v for k, v in expected.items() if k != "plan_digest"})
        self.assertEqual(final, expected)
        self.assertEqual(self.store.snapshot()["budget"], before)
        self.assertEqual(self.store.preparation("prep-one")["state"], "registered")
        self.assertEqual(self.store.finalize_preparation("prep-one", self.caller, proof, now=STALE), final)
        self.assertEqual(self.store.ready("prep-one", now=NOW), ["a"])
        claim = self.store.claim("prep-one", "a", execute_orca.request_id(final, "a"), final["plan_digest"], now=NOW)
        self.assertTrue(claim["dispatch_allowed"])
        self.assertEqual(self.store.snapshot()["budget"]["held_usd"], before["held_usd"])

    def test_failed_finalization_rolls_back_and_stale_draft_never_resends(self):
        self.init(1)
        self.start(self.draft(cost="0.1", cap=1))
        proof = self.bind_all()
        before = self.store.snapshot()
        with patch.object(self.store, "_node", side_effect=run_state.StateError("FIXTURE_FAILURE")):
            with self.assertRaisesRegex(run_state.StateError, "FIXTURE_FAILURE"):
                self.store.finalize_preparation("prep-one", self.caller, proof, now=NOW)
        self.assertEqual(self.store.snapshot(), before)
        with self.assertRaises(run_state.StateError):
            self.store.finalize_preparation("prep-one", self.caller, proof, now=STALE)
        self.assertEqual(self.store.snapshot(), before)

    def test_wrong_readback_or_final_evidence_cannot_bind_or_register(self):
        self.init()
        self.start()
        op = self.store.preparation_intent("prep-one", "run", self.caller, now=NOW)
        with self.assertRaises(run_state.StateError):
            self.store.observe_preparation("prep-one", "run", self.caller,
                {"state": "complete", "verified": True, "native_id": "native-run", "operation_sha256": "wrong",
                 "observed_at": NOW, "evidence": ["wrong resource"]}, now=NOW)
        proof = self.bind_all()
        for key, value in (("bound_sha256", "wrong"), ("scope_verified", False), ("no_workers", False),
                           ("non_generating", False), ("actual_usd", None), ("actual_usd", "0.1"),
                           ("observed_at", STALE), ("evidence", [])):
            with self.subTest(key=key), self.assertRaises(run_state.StateError):
                self.store.finalize_preparation("prep-one", self.caller, {**proof, key: value}, now=NOW)
        self.assertEqual(self.store.snapshot()["runs"], [])

    def test_metadata_intent_cost_is_unknown_until_zero_cost_readback(self):
        self.init()
        self.start()
        op = self.store.preparation_intent("prep-one", "run", self.caller, now=NOW)
        self.assertIsNone(self.store.snapshot()["budget"]["actual_total_usd"])
        for actual in (None, "0.01"):
            with self.subTest(actual=actual), self.assertRaises(run_state.StateError):
                self.store.observe_preparation("prep-one", "run", self.caller,
                    {"state": "complete", "verified": True, "native_id": "native-run",
                     "operation_sha256": op["operation_sha256"], "observed_at": NOW,
                     "actual_usd": actual, "non_generating": True, "evidence": ["not free"]}, now=NOW)
        self.finish_op("run", "native-run")
        self.assertEqual(self.store.snapshot()["budget"]["actual_total_usd"], "0")

    def test_existing_preparation_cannot_change_intent_caller_or_binding(self):
        self.init()
        p = self.start()
        self.start(copy.deepcopy(p))
        changed = copy.deepcopy(p)
        changed["steps"][0]["task"] = "different task"
        changed["plan_digest"] = orchestrate.digest({k: v for k, v in changed.items() if k != "plan_digest"})
        with self.assertRaisesRegex(run_state.StateError, "PREPARATION_IMMUTABLE"):
            self.start(changed)
        with self.assertRaises(run_state.StateError):
            self.store.begin_preparation(p, {**self.caller, "handle": "borrowed-pane"}, now=NOW)
        op = self.finish_op("run", "native-run")
        with self.assertRaisesRegex(run_state.StateError, "PREPARATION_BINDING_CHANGED"):
            self.store.observe_preparation("prep-one", "run", self.caller,
                {"state": "complete", "verified": True, "native_id": "replacement-run",
                 "operation_sha256": op["operation_sha256"], "observed_at": NOW,
                 "actual_usd": "0", "non_generating": True, "evidence": ["wrong identity"]}, now=NOW)

    def test_failed_or_stale_begin_leaves_no_reservation(self):
        self.init()
        with self.assertRaises(run_state.StateError):
            self.start(self.draft(cost="0.1", cap=1))
        with self.assertRaises(run_state.StateError):
            self.store.begin_preparation(self.draft(), self.caller, now=STALE)
        self.assertEqual(self.store.snapshot()["preparations"], [])
        self.assertEqual(self.store.snapshot()["budget"]["held_usd"], "0")

    def test_tiny_reservation_rounding_is_identical_before_after_registration(self):
        self.init(1)
        p = self.draft(cap=1)
        for node in p["steps"]:
            node["route"]["reserved_upper_usd"] = "0.000000001"
        p["plan_digest"] = orchestrate.digest({k: v for k, v in p.items() if k != "plan_digest"})
        self.start(p)
        before = self.store.snapshot()["budget"]["held_usd"]
        self.assertEqual(before, "0.000000004")
        self.store.finalize_preparation("prep-one", self.caller, self.bind_all(), now=NOW)
        self.assertEqual(self.store.snapshot()["budget"]["held_usd"], before)

    def test_partial_graph_missing_dependency_or_cycle_is_rejected(self):
        self.init()
        for deps in (["missing"], ["b"]):
            p = self.draft()
            p["steps"][0]["depends_on"] = deps
            p["plan_digest"] = orchestrate.digest({k: v for k, v in p.items() if k != "plan_digest"})
            with self.subTest(deps=deps), self.assertRaises(run_state.StateError):
                self.start(p)
        self.assertEqual(self.store.snapshot()["preparations"], [])

    def test_ready_root_does_not_hide_an_unreachable_cycle_or_duplicate_dependency(self):
        self.init()
        for deps in (["c"], ["a", "a"]):
            p = self.draft(nodes=[step("a"), step("b", depends_on=["a"]), step("c", depends_on=["b"])])
            p["steps"][1]["depends_on"] = deps
            p["plan_digest"] = orchestrate.digest({k: v for k, v in p.items() if k != "plan_digest"})
            with self.subTest(deps=deps), self.assertRaises(run_state.StateError):
                self.start(p)
        self.assertEqual(self.store.snapshot()["preparations"], [])

    def test_journal_capacity_is_checked_before_any_reservation_or_intent(self):
        self.init()
        p = self.draft()
        p["steps"][0]["task"] = 'x' + '"' * 280000
        p["plan_digest"] = orchestrate.digest({k: v for k, v in p.items() if k != "plan_digest"})
        self.assertLess(len(run_state.safe_json(p).encode()), 1024 * 1024)
        with self.assertRaises(run_state.StateError):
            self.start(p)
        self.assertEqual(self.store.snapshot()["preparations"], [])

    def test_oversized_proof_does_not_poison_or_enlarge_the_journal(self):
        self.init()
        self.start()
        op = self.store.preparation_intent("prep-one", "run", self.caller, now=NOW)
        before = self.store.preparation("prep-one")
        with self.assertRaises(run_state.StateError):
            self.store.observe_preparation("prep-one", "run", self.caller,
                {"state": "unknown", "operation_sha256": op["operation_sha256"], "observed_at": NOW,
                 "evidence": ["x" * 5000]}, now=NOW)
        self.assertEqual(self.store.preparation("prep-one"), before)

    def test_final_plan_size_is_checked_before_reservation(self):
        self.init()
        p = self.draft()
        # Orca metadata is excluded from Task text, but retained in final plan.
        for node in p["steps"]:
            node["orca"]["padding"] = ""
        p["plan_digest"] = orchestrate.digest({k: v for k, v in p.items() if k != "plan_digest"})
        remaining = (1024 * 1024 - 20 - len(run_state.safe_json(p).encode())) // 2
        for node in p["steps"]:
            node["orca"]["padding"] = " " * remaining
        p["plan_digest"] = orchestrate.digest({k: v for k, v in p.items() if k != "plan_digest"})
        self.assertLess(len(run_state.safe_json(p).encode()), 1024 * 1024)
        with self.assertRaises(run_state.StateError):
            self.start(p)
        self.assertEqual(self.store.snapshot()["preparations"], [])

    def test_uncertain_operation_recovers_without_new_uuid_or_hold_release(self):
        self.init(1)
        self.start(self.draft(cost="0.1", cap=1))
        op = self.store.preparation_intent("prep-one", "run", self.caller, now=NOW)
        self.store.observe_preparation("prep-one", "run", self.caller,
            {"state": "unknown", "operation_sha256": op["operation_sha256"], "observed_at": NOW,
             "evidence": ["missing receipt"]}, now=NOW)
        self.assertFalse(self.store.preparation_intent("prep-one", "run", self.caller, now=NOW)["send_allowed"])
        with self.assertRaises(run_state.StateError):
            self.store.preparation_intent("prep-one", "task:a", self.caller, now=NOW)
        recovered = self.finish_op("run", "native-run")
        self.assertEqual(recovered["request_id"], op["request_id"])
        self.assertEqual(self.store.preparation("prep-one")["state"], "preparing")
        self.assertTrue(self.store.preparation_intent("prep-one", "task:a", self.caller, now=NOW)["send_allowed"])
        self.assertEqual(self.store.snapshot()["budget"]["held_usd"], "0.4")

    def test_same_caller_identity_or_handle_cannot_prepare_a_second_run(self):
        self.init()
        self.start()
        for caller in (self.caller, {**self.caller, "handle": "changed-pane"},
                       {**self.caller, "identity_sha256": "c" * 64}):
            with self.subTest(caller=caller), self.assertRaises(run_state.StateError):
                self.store.begin_preparation(self.draft("prep-two"), caller, now=NOW)
        self.assertEqual(len(self.store.snapshot()["preparations"]), 1)

    def test_two_preparations_cannot_bind_the_same_native_run_or_task(self):
        self.init()
        self.start()
        other = {"handle": "other-pane", "identity_sha256": "c" * 64}
        self.store.begin_preparation(self.draft("prep-two"), other, now=NOW)
        self.finish_op("run", "native-run")
        self.finish_op("task:a", "native-a")
        with self.assertRaises(run_state.StateError):
            self.finish_op("run", "native-run", "prep-two", other)
        self.finish_op("run", "native-other", "prep-two", other)
        with self.assertRaises(run_state.StateError):
            self.finish_op("task:a", "native-a", "prep-two", other)

    def test_manual_registration_cannot_reuse_prepared_native_resources(self):
        self.init()
        self.start()
        self.finish_op("run", "native-run")
        self.finish_op("task:a", "native-a")
        for native_run, native_task in (("native-run", "manual-task"), ("manual-run", "native-a")):
            p = self.draft("ordinary", nodes=[step("a")])
            p["steps"][0]["orca"].update(run_id=native_run, task_id=native_task)
            p["plan_digest"] = orchestrate.digest({k: v for k, v in p.items() if k != "plan_digest"})
            with self.subTest(native_run=native_run), self.assertRaises(run_state.StateError):
                self.store.register(p, now=NOW)
        self.assertEqual(self.store.snapshot()["runs"], [])

    def test_caller_remains_busy_after_finalization_until_local_run_closes(self):
        self.init()
        self.start()
        self.store.finalize_preparation("prep-one", self.caller, self.bind_all(), now=NOW)
        with self.assertRaisesRegex(run_state.StateError, "PREPARATION_CALLER_BUSY"):
            self.start(self.draft("prep-two"))
        self.store.cancel("prep-one", ["fixture no worker started"], now=NOW)
        self.start(self.draft("prep-two"))
        # Closed history still owns native IDs; closure is not native cleanup.
        with self.assertRaisesRegex(run_state.StateError, "NATIVE_RESOURCE_ALREADY_OWNED"):
            self.finish_op("run", "native-run", "prep-two")

    def test_manual_plan_cannot_alias_tasks_inside_one_run(self):
        self.init()
        p = self.draft("ordinary")
        for n in p["steps"]:
            n["orca"].update(run_id="ordinary-native", task_id="same-task")
        p["plan_digest"] = orchestrate.digest({k: v for k, v in p.items() if k != "plan_digest"})
        with self.assertRaisesRegex(run_state.StateError, "PREPARATION_BINDING_DUPLICATE"):
            self.store.register(p, now=NOW)
        self.assertEqual(self.store.snapshot()["runs"], [])

    def test_manual_run_and_task_ownership_fences_later_preparation(self):
        self.init()
        p = self.draft("ordinary", nodes=[step("a")])
        p["steps"][0]["orca"].update(run_id="ordinary-native", task_id="ordinary-task")
        p["plan_digest"] = orchestrate.digest({k: v for k, v in p.items() if k != "plan_digest"})
        self.store.register(p, now=NOW)
        self.start()
        with self.assertRaisesRegex(run_state.StateError, "NATIVE_RESOURCE_ALREADY_OWNED"):
            self.finish_op("run", "ordinary-native")
        self.finish_op("run", "native-run")
        with self.assertRaisesRegex(run_state.StateError, "NATIVE_RESOURCE_ALREADY_OWNED"):
            self.finish_op("task:a", "ordinary-task")

    def test_generic_null_binding_does_not_block_registration_or_native_scan(self):
        self.init()
        p = generic_plan(run="generic")
        p["steps"][0]["orca"] = None
        p["plan_digest"] = orchestrate.digest({k: v for k, v in p.items() if k != "plan_digest"})
        self.store.register(p, now=NOW)
        self.start()
        self.finish_op("run", "native-run")
        self.assertEqual(self.store.preparation("prep-one")["operations"]["run"]["state"], "complete")


if __name__ == "__main__":
    unittest.main()
