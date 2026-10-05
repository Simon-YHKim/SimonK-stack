"""Synthetic owned-session protocol tests. Never import/run a native bridge."""
import copy
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
with patch("subprocess.Popen", side_effect=AssertionError("No process during imports")):
    import orchestrate
    import run_state
    import test_prepare_state as fixture_module
    from test_orchestrate import NOW
    from test_run_state import STALE
    core = __import__("prepare_orca") if importlib.util.find_spec("prepare_orca") else None


class Session:
    """Lying is possible here: synthetic assertions are NOT host evidence."""
    def __init__(self, plan, store):
        self.plan, self.store = plan, store
        b = plan["steps"][0]["orca"]
        self.context = {k: b[k] for k in ("runtime_id", "app_version", "executable",
            "executable_sha256", "worktree_id", "worktree_path", "workspace_instance")}
        self.context.update(handle="fixture-coordinator", pane_key="fixture-pane",
            process_incarnation="fixture-process", transport_id="fixture-local-transport",
            target="local", loaded_server_sha256="c" * 64, inspected_server_sha256="c" * 64)
        self.scope_id = "fixture-session"
        self.attestation = {"scope_id": self.scope_id, "context": self.context,
            "draft_digest": plan["plan_digest"], "observed_at": NOW, "valid_until": STALE,
            "verified": True, "owned": True, "exclusive": True, "startup_reviewed": True,
            "non_generating": True, "actual_usd": "0", "first_use_uuid": True,
            "contract": "owned-local-orca-preparation-v1", "evidence": ["synthetic only"]}
        self.attestation["request_identity"] = {
            "contract": "caller-chosen-uuid-first-run-task-create-v1",
            "methods": ["orchestration.runCreate", "orchestration.taskCreate", "orchestration.requestShow"],
            "runtime_id": b["runtime_id"], "app_version": b["app_version"],
            "server_sha256": self.context["loaded_server_sha256"], "evidence": ["synthetic exact-method review"]}
        self.worker_caps = ["orchestration.worker-launch-preferences.v1"]
        self.calls, self.receipts, self.tasks = [], {}, {}
        self.run, self.workers = None, []
        self.lose_response, self.before_effect = False, False
        self.reply_scope, self.reply_runtime = self.scope_id, b["runtime_id"]

    def attest(self):
        return copy.deepcopy(self.attestation)

    def wrap(self, result):
        return {"scope_id": self.reply_scope, "context_sha256": orchestrate.digest(self.context),
            "envelope": {"ok": True, "result": copy.deepcopy(result),
                         "_meta": {"runtimeId": self.reply_runtime}}}

    def read_exact(self, argv):
        self.calls.append(("read", argv))
        self.assert_json(argv)
        args, b = list(argv[:-1]), self.plan["steps"][0]["orca"]
        if args == ["status"]:
            return self.wrap({"runtime": {"runtimeId": b["runtime_id"], "appVersion": b["app_version"],
                "state": "ready", "capabilities": self.worker_caps}})
        if args[:2] == ["worktree", "show"]:
            return self.wrap({"worktree": {"id": b["worktree_id"], "path": b["worktree_path"],
                "hostId": "local", "instanceId": b["workspace_instance"], "identity": {"executionHostId": "local"}}})
        verb = args[1]
        if verb in {"run-current", "run-show"}:
            return self.wrap({"run": self.run})
        if verb == "request-show":
            request = args[args.index("--request") + 1]
            return self.wrap(self.receipts.get(request, {"requestId": request, "state": "absent"}))
        if verb == "task-list":
            return self.wrap({"runId": self.run["id"], "legacyReadOnly": False,
                "tasks": list(self.tasks.values()), "count": len(self.tasks)})
        if verb == "worker-list":
            return self.wrap({"scope": {"run": self.run["id"]}, "workers": self.workers,
                "page": {"hasMore": False}})
        raise AssertionError("Unexpected read verb")

    @staticmethod
    def assert_json(argv):
        assert isinstance(argv, tuple) and argv[-1] == "--json" and argv.count("--json") == 1

    def mutate_exact(self, argv):
        self.calls.append(("mutate", argv))
        self.assert_json(argv)
        ops = self.store.preparation(self.plan["run_id"])["operations"]
        assert any(tuple(op["argv"]) == argv for op in ops.values()), "Send before durable intent"
        if self.before_effect:
            raise TimeoutError("fixture before effect")
        fields = dict(zip(argv[2:-1:2], argv[3:-1:2]))
        request = fields["--retry-request"]
        assert request not in self.receipts, "Duplicate send"
        if argv[1] == "run-create":
            self.run = {"id": "native-run", "objective": fields["--objective"], "legacy": 0,
                "coordinator_handle": self.context["handle"], "consumer_generation": 1}
            result, method = {"run": self.run}, "orchestration.runCreate"
        elif argv[1] == "task-create":
            tid = "native-" + fields["--task-title"].rsplit(":", 1)[1]
            task = {"id": tid, "run_id": self.run["id"], "spec": fields["--spec"],
                "task_title": fields["--task-title"], "deps": fields["--deps"], "parent_id": None,
                "created_by_terminal_handle": self.context["handle"], "created_by_pane_key": self.context["pane_key"],
                "created_by_process_incarnation": self.context["process_incarnation"],
                "created_by_run_generation": self.run["consumer_generation"],
                "status": "pending" if run_state.strict_loads(fields["--deps"]) else "ready"}
            self.tasks[tid] = task
            result, method = {"task": task}, "orchestration.taskCreate"
        else:
            raise AssertionError("Forbidden mutation")
        result["mutation"] = {"requestId": request, "replayed": False}
        self.receipts[request] = copy.deepcopy({"requestId": request, "state": "completed",
                                               "method": method, "receipt": result})
        if self.lose_response:
            raise TimeoutError("fixture after effect")
        return self.wrap(result)


class Host:
    def __init__(self, session):
        self.session = session

    def open(self, expected):
        assert expected["draft_digest"] == self.session.plan["plan_digest"]
        return self.session


class PreparationAdapterTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture_module.PreparationTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.init()
        self.plan, self.store = self.fixture.draft(), self.fixture.store
        self.session = Session(self.plan, self.store)

    def adapter(self, session=None, now=NOW):
        self.assertIsNotNone(core, "Host-injected preparation core is missing")
        return core.PreparationAdapter(self.store, Host(session or self.session), clock=lambda: now)

    def begin(self):
        adapter = self.adapter()
        adapter.begin(self.plan)
        return adapter

    def bind_all(self):
        adapter = self.begin()
        for key in ("run", "task:a", "task:b"):
            self.assertNotEqual(adapter.prepare_one(self.plan, key)["status"], "uncertain")
        return adapter

    def test_exact_metadata_only_order_and_atomic_finalization(self):
        adapter = self.bind_all()
        final = adapter.finalize(self.plan)
        self.assertEqual(final["steps"][1]["orca"]["task_id"], "native-b")
        mutations = [argv[1] for kind, argv in self.session.calls if kind == "mutate"]
        self.assertEqual(mutations, ["run-create", "task-create", "task-create"])
        self.assertEqual(self.store.snapshot()["attempts"], [])
        self.assertEqual(self.store.preparation(self.plan["run_id"])["state"], "registered")
        self.assertFalse(hasattr(core, "main"), "No operational CLI until a real bridge exists")

    def test_missing_or_false_attestation_blocks_before_any_native_read(self):
        for key, value in (("verified", False), ("actual_usd", "0.01"), ("actual_usd", None),
                           ("owned", False), ("exclusive", False), ("startup_reviewed", False),
                           ("first_use_uuid", False), ("valid_until", NOW)):
            with self.subTest(key=key, value=value):
                session = Session(self.plan, self.store)
                session.attestation[key] = value
                with self.assertRaises(run_state.StateError):
                    self.adapter(session).begin(self.plan)
                self.assertEqual(session.calls, [])
        self.assertEqual(self.store.snapshot()["preparations"], [])

    def test_lost_mutation_response_recovers_without_second_send(self):
        adapter = self.begin()
        self.session.lose_response = True
        self.assertEqual(adapter.prepare_one(self.plan, "run")["status"], "uncertain")
        self.session.lose_response = False
        result = self.adapter().prepare_one(self.plan, "run")
        self.assertNotEqual(result["status"], "uncertain")
        self.assertEqual(sum(kind == "mutate" for kind, _ in self.session.calls), 1)

    def test_absent_pending_or_pruned_receipt_never_resends_or_advances(self):
        adapter = self.begin()
        self.session.before_effect = True
        self.assertEqual(adapter.prepare_one(self.plan, "run")["status"], "uncertain")
        self.session.before_effect = False
        for key in ("run", "task:a"):
            self.assertEqual(self.adapter().prepare_one(self.plan, key)["status"], "uncertain")
        self.assertEqual(sum(kind == "mutate" for kind, _ in self.session.calls), 1)
        self.assertIsNone(self.store.snapshot()["budget"]["actual_total_usd"])

    def test_receipt_and_resource_both_required(self):
        adapter = self.begin()
        adapter.prepare_one(self.plan, "run")
        self.session.lose_response = True
        adapter.prepare_one(self.plan, "task:a")
        op = self.store.preparation(self.plan["run_id"])["operations"]["task:a"]
        receipt = self.session.receipts[op["request_id"]]
        receipt["method"] = "orchestration.runCreate"
        self.assertEqual(self.adapter().reconcile(self.plan)["status"], "uncertain")
        receipt["method"] = "orchestration.taskCreate"
        self.session.tasks["native-a"]["deps"] = '["foreign-task"]'
        self.assertEqual(self.adapter().reconcile(self.plan)["status"], "uncertain")
        self.assertIsNone(self.store.preparation(self.plan["run_id"])["operations"]["task:a"]["native_id"])

    def test_unrelated_current_run_blocks_before_intent(self):
        adapter = self.begin()
        self.session.run = {"id": "other-run", "objective": "other"}
        with self.assertRaises(run_state.StateError):
            adapter.prepare_one(self.plan, "run")
        self.assertEqual(self.store.preparation(self.plan["run_id"])["operations"], {})
        self.assertFalse(any(kind == "mutate" for kind, _ in self.session.calls))

    def test_changed_scope_runtime_or_loaded_source_never_mutates(self):
        adapter = self.begin()
        self.session.reply_scope = "foreign-session"
        with self.assertRaises(run_state.StateError):
            adapter.prepare_one(self.plan, "run")
        self.session.reply_scope = self.session.scope_id
        self.session.context["loaded_server_sha256"] = "d" * 64
        with self.assertRaises(run_state.StateError):
            adapter.prepare_one(self.plan, "run")
        self.assertFalse(any(kind == "mutate" for kind, _ in self.session.calls))

    def test_finalization_rechecks_all_tasks_and_no_workers(self):
        adapter = self.bind_all()
        self.session.workers = [{"dispatchId": "foreign-dispatch"}]
        with self.assertRaises(run_state.StateError):
            adapter.finalize(self.plan)
        self.session.workers = []
        self.session.tasks["native-a"]["spec"] = "changed"
        with self.assertRaises(run_state.StateError):
            adapter.finalize(self.plan)
        self.assertEqual(self.store.snapshot()["runs"], [])

    def test_current_run_changed_after_intent_never_rebinds_it(self):
        adapter = self.begin()
        original = self.store.preparation_intent
        def claim(*args, **kwargs):
            op = original(*args, **kwargs)
            self.session.run = {"id": "other-run", "objective": "user changed current Run"}
            return op
        with patch.object(self.store, "preparation_intent", side_effect=claim):
            self.assertEqual(adapter.prepare_one(self.plan, "run")["status"], "uncertain")
        self.assertFalse(any(kind == "mutate" for kind, _ in self.session.calls))
        self.assertEqual(self.session.run["id"], "other-run")

    def test_pending_receipt_and_null_provenance_are_not_positive_proof(self):
        adapter = self.begin()
        adapter.prepare_one(self.plan, "run")
        self.session.lose_response = True
        adapter.prepare_one(self.plan, "task:a")
        op = self.store.preparation(self.plan["run_id"])["operations"]["task:a"]
        receipt = self.session.receipts[op["request_id"]]
        receipt["state"] = "pending"
        self.assertEqual(self.adapter().reconcile(self.plan)["status"], "uncertain")
        receipt["state"] = "completed"
        self.session.tasks["native-a"]["created_by_process_incarnation"] = None
        self.assertEqual(self.adapter().reconcile(self.plan)["status"], "uncertain")
        self.assertIsNone(self.store.preparation(self.plan["run_id"])["operations"]["task:a"]["native_id"])

    def test_read_allowlist_never_forwards_worker_or_mutation_verbs(self):
        adapter = self.begin()
        for args in (("orchestration", "worker-start"), ("orchestration", "worker-stop"),
                     ("orchestration", "run-use"), ("orchestration", "task-update"),
                     ("terminal", "send"), ("orchestration", "request-show", "--request", "foreign")):
            with self.subTest(args=args), self.assertRaises(run_state.StateError):
                adapter.call(*args)
        self.assertEqual(self.session.calls, [])

    def test_wrong_runtime_and_context_response_block_before_mutation(self):
        adapter = self.begin()
        self.session.reply_runtime = "foreign-runtime"
        with self.assertRaises(run_state.StateError):
            adapter.prepare_one(self.plan, "run")
        self.assertFalse(any(kind == "mutate" for kind, _ in self.session.calls))

    def test_expiry_between_read_and_mutation_preserves_intent_without_send(self):
        adapter = self.begin()
        original = self.store.preparation_intent
        def claim(*args, **kwargs):
            op = original(*args, **kwargs)
            self.session.attestation["valid_until"] = NOW
            return op
        with patch.object(self.store, "preparation_intent", side_effect=claim):
            self.assertEqual(adapter.prepare_one(self.plan, "run")["status"], "uncertain")
        self.assertFalse(any(kind == "mutate" for kind, _ in self.session.calls))

    def test_reconciliation_of_stale_plan_never_renews_or_mutates_it(self):
        adapter = self.bind_all()
        original_mutations = sum(kind == "mutate" for kind, _ in self.session.calls)
        self.session.attestation.update(observed_at=STALE, valid_until="2027-01-01T00:00:00+00:00")
        later = self.adapter(now=STALE)
        self.assertEqual(later.reconcile(self.plan)["status"], "bound")
        with self.assertRaises(run_state.StateError):
            later.finalize(self.plan)
        self.assertEqual(sum(kind == "mutate" for kind, _ in self.session.calls), original_mutations)
        self.assertEqual(self.store.snapshot()["runs"], [])

    def test_pruned_previously_complete_receipt_blocks_later_mutation(self):
        adapter = self.begin()
        adapter.prepare_one(self.plan, "run")
        self.session.receipts.clear()
        self.assertEqual(adapter.reconcile(self.plan)["status"], "uncertain")
        self.assertEqual(self.adapter().prepare_one(self.plan, "task:a")["status"], "uncertain")
        self.assertEqual(sum(kind == "mutate" for kind, _ in self.session.calls), 1)
        self.assertNotIn("task:a", self.store.preparation(self.plan["run_id"])["operations"])

    def test_worker_only_uuid_evidence_cannot_authorize_preparation(self):
        self.session.attestation["request_identity"]["contract"] = "caller-chosen-uuid-first-worker-start-v1"
        with self.assertRaises(run_state.StateError):
            self.adapter().begin(self.plan)
        self.assertEqual(self.session.calls, [])
        self.assertEqual(self.store.snapshot()["preparations"], [])

    def test_method_proof_requires_task_and_exact_loaded_runtime(self):
        for key, value in (("methods", ["orchestration.runCreate", "orchestration.requestShow"]),
                           ("runtime_id", "foreign-runtime"), ("server_sha256", "e" * 64)):
            with self.subTest(key=key):
                session = Session(self.plan, self.store)
                session.attestation["request_identity"][key] = value
                with self.assertRaises(run_state.StateError):
                    self.adapter(session).begin(self.plan)
                self.assertEqual(session.calls, [])

    def test_metadata_preparation_does_not_require_worker_launch_capability(self):
        self.session.worker_caps = []
        adapter = self.bind_all()
        self.assertEqual(adapter.finalize(self.plan)["steps"][0]["orca"]["run_id"], "native-run")

    def test_missing_current_run_field_is_not_positive_empty_binding(self):
        adapter = self.begin()
        original = self.session.read_exact
        def read(argv):
            result = original(argv)
            if argv[:2] == ("orchestration", "run-current"):
                result["envelope"]["result"] = {}
            return result
        with patch.object(self.session, "read_exact", side_effect=read):
            with self.assertRaises(run_state.StateError):
                adapter.prepare_one(self.plan, "run")
        self.assertFalse(any(kind == "mutate" for kind, _ in self.session.calls))

    def test_missing_task_parent_field_is_not_positive_null_parent(self):
        adapter = self.begin()
        adapter.prepare_one(self.plan, "run")
        self.session.lose_response = True
        adapter.prepare_one(self.plan, "task:a")
        self.session.tasks["native-a"].pop("parent_id")
        self.assertEqual(adapter.reconcile(self.plan)["status"], "uncertain")
        self.assertIsNone(self.store.preparation(self.plan["run_id"])["operations"]["task:a"]["native_id"])


if __name__ == "__main__":
    unittest.main()
