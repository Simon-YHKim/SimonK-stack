"""Observable-PC trust contract: synthetic transport, no native side effects."""
import copy
import inspect
import sys
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch


def deny_external(event, args):
    if event.startswith(("subprocess.", "os.system", "os.exec", "os.spawn",
                         "os.posix_spawn", "socket.connect", "socket.__new__", "os.kill")):
        raise RuntimeError("PROCESS_NETWORK_OR_SIGNAL_FORBIDDEN")


sys.addaudithook(deny_external)
sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]
import test_prepare_orca as f
from test_orchestrate import NOW
from test_run_state import STALE

CONTRACT = "observable-local-orca-preparation-v2"
READS = ["status", "worktree.show", "orchestration.runCurrent", "orchestration.runShow",
         "orchestration.taskList", "orchestration.workerList", "orchestration.requestShow"]
MUTATIONS = ["orchestration.runCreate", "orchestration.taskCreate"]
EFFECTS = ["orca_db_open_or_create", "schema_migration", "federation_relay_start",
           "restored_message_repoint_schedule", "repository_status_probes"]
PROVENANCE = ("created_by_pane_key", "created_by_process_incarnation", "created_by_run_generation")


class Session(f.Session):
    def __init__(self, plan, store):
        super().__init__(plan, store)
        self.context.update(contract=CONTRACT, approval_ref="fixture-trust-decision",
                            loaded_server_sha256=None, pane_key=None, process_incarnation=None)
        self.attestation.update(contract=CONTRACT, local_runtime_trusted=True, coordinator_serialized=True)
        self.attestation.pop("owned")
        self.attestation.pop("exclusive")
        identity = self.attestation["request_identity"]
        identity.pop("server_sha256")
        identity.update(basis="at-rest-unloaded", reviewed_package_sha256=self.context["inspected_server_sha256"])
        self.authorize_effects()

    def authorize_effects(self):
        self.attestation["effects_grant"] = {
            "approval_ref": "fixture-effects-separate-approval", "authorized": True,
            "draft_digest": self.plan["plan_digest"], "context_sha256": f.orchestrate.digest(self.context),
            "observed_at": NOW, "valid_until": STALE, "read_methods": READS[:],
            "mutation_methods": MUTATIONS[:], "accepted_effects": EFFECTS[:],
            "external_transmission": False, "generation": False, "installation": False,
            "evidence": ["synthetic reviewed effects, not live permission"]}

    def mutate_exact(self, argv):
        result = super().mutate_exact(argv)
        if argv[1] == "task-create":
            tid = result["envelope"]["result"]["task"]["id"]
            request = argv[argv.index("--retry-request") + 1]
            for row in (self.tasks[tid], self.receipts[request]["receipt"]["task"],
                        result["envelope"]["result"]["task"]):
                for field in PROVENANCE:
                    row[field] = None
        return result


class ObservablePreparationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = f.fixture_module.PreparationTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.init()
        self.plan, self.store = self.fixture.draft(), self.fixture.store
        self.session = Session(self.plan, self.store)

    def adapter(self, session=None, **kwargs):
        self.assertIn("contract", inspect.signature(f.core.PreparationAdapter).parameters,
                      "Explicit observable contract integration is missing")
        return f.core.PreparationAdapter(self.store, f.Host(session or self.session), clock=lambda: NOW,
            contract=CONTRACT, approval_ref="fixture-trust-decision", **kwargs)

    def begin(self):
        adapter = self.adapter()
        adapter.begin(self.plan)
        return adapter

    def bind(self):
        adapter = self.begin()
        for key in ("run", "task:a", "task:b"):
            self.assertNotEqual(adapter.prepare_one(self.plan, key)["status"], "uncertain")
        return adapter

    def test_null_provenance_uses_explicit_contract_and_preserves_full_dag(self):
        adapter = self.bind()
        state = self.store.preparation(self.plan["run_id"])
        self.assertEqual(state["caller"]["contract"], CONTRACT)
        self.assertEqual(state["caller"]["approval_ref"], "fixture-trust-decision")
        for op in state["operations"].values():
            self.assertNotIn("--from", op["argv"])
            self.assertTrue(any(CONTRACT in item for item in op["proof"]["evidence"]))
            self.assertIn("effects-approval:fixture-effects-separate-approval", op["proof"]["evidence"])
            self.assertFalse(any("owned-session:" in item for item in op["proof"]["evidence"]))
        for kind, argv in self.session.calls:
            if kind == "read" and argv[:2] in (("orchestration", "run-current"), ("orchestration", "task-list")):
                self.assertEqual(len(argv), 3)  # verb + command + --json only
        self.assertEqual(adapter.finalize(self.plan)["steps"][1]["orca"]["task_id"], "native-b")
        self.assertEqual(self.store.snapshot()["attempts"], [])

    def test_trust_approval_alone_never_authorizes_effects(self):
        self.session.attestation.pop("effects_grant")
        with self.assertRaises(f.run_state.StateError):
            self.adapter().begin(self.plan)
        self.assertEqual(self.session.calls, [])
        self.assertEqual(self.store.snapshot()["preparations"], [])

    def test_exact_effect_scope_and_negative_permissions(self):
        cases = [("authorized", False), ("approval_ref", "fixture-trust-decision"),
            ("context_sha256", "f" * 64), ("draft_digest", "f" * 64), ("valid_until", NOW),
            ("read_methods", READS[:-1]), ("mutation_methods", MUTATIONS + ["orchestration.workerStart"]),
            ("accepted_effects", EFFECTS[:-1]), ("external_transmission", True),
            ("generation", True), ("installation", True)]
        for key, value in cases:
            with self.subTest(key=key):
                session = Session(self.plan, self.store)
                session.attestation["effects_grant"][key] = value
                with self.assertRaises(f.run_state.StateError):
                    self.adapter(session).begin(self.plan)
                self.assertEqual(session.calls, [])

    def test_missing_approval_unknown_contract_and_wrong_proof_do_not_fallback(self):
        self.assertIn("contract", inspect.signature(f.core.PreparationAdapter).parameters)
        for kwargs in ({"contract": CONTRACT}, {"contract": "unknown", "approval_ref": "decision"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(f.run_state.StateError):
                f.core.PreparationAdapter(self.store, f.Host(self.session), **kwargs).begin(self.plan)
        with self.assertRaises(f.run_state.StateError):
            f.core.PreparationAdapter(self.store, f.Host(self.session), clock=lambda: NOW).begin(self.plan)
        with self.assertRaises(f.run_state.StateError):
            self.adapter(f.Session(self.plan, self.store)).begin(self.plan)
        self.assertEqual(self.session.calls, [])

    def test_at_rest_hash_never_becomes_loaded_code_proof(self):
        for change in (lambda s: s.context.update(loaded_server_sha256="c" * 64),
                       lambda s: s.attestation["request_identity"].update(basis="loaded"),
                       lambda s: s.attestation["request_identity"].update(reviewed_package_sha256="d" * 64)):
            session = Session(self.plan, self.store)
            change(session)
            session.authorize_effects()
            with self.assertRaises(f.run_state.StateError):
                self.adapter(session).begin(self.plan)
            self.assertEqual(session.calls, [])

    def test_v2_uuid_is_stable_and_in_its_own_namespace(self):
        adapter = self.begin()
        adapter.prepare_one(self.plan, "run")
        before = self.store.preparation(self.plan["run_id"])
        op = before["operations"]["run"]
        identity = f.orchestrate.digest({"draft": self.plan["plan_digest"], "caller": before["caller"],
                                        "key": "run", "argv": op["argv"][:-3]})
        expected = str(uuid.uuid5(uuid.NAMESPACE_URL, "simonk:vibe:orca:preparation:v2:" + identity))
        self.assertEqual(op["request_id"], expected)
        self.adapter().prepare_one(self.plan, "run")
        self.assertEqual(self.store.preparation(self.plan["run_id"])["operations"], before["operations"])
        self.assertEqual(sum(k == "mutate" for k, _ in self.session.calls), 1)

    def test_v1_canonical_uuid_is_unchanged_and_cannot_be_reinterpreted(self):
        strong = f.Session(self.plan, self.store)
        adapter = f.core.PreparationAdapter(self.store, f.Host(strong), clock=lambda: NOW)
        adapter.begin(self.plan)
        op = self.store.preparation_intent(self.plan["run_id"], "run", adapter.caller, now=NOW)
        self.assertIn("--from", op["argv"])
        identity = f.orchestrate.digest({"draft": self.plan["plan_digest"], "caller": adapter.caller,
                                        "key": "run", "argv": op["argv"][:-3]})
        self.assertEqual(op["request_id"], str(uuid.uuid5(uuid.NAMESPACE_URL,
                         "simonk:vibe:orca:preparation:v1:" + identity)))
        with self.assertRaises(f.run_state.StateError):
            self.adapter().begin(self.plan)
        with self.assertRaises(f.run_state.StateError):
            self.adapter().reconcile(self.plan)
        self.assertEqual(self.session.calls, [])

    def test_revoked_effect_grant_blocks_lookup_without_changing_intent(self):
        adapter = self.begin()
        self.session.before_effect = True
        self.assertEqual(adapter.prepare_one(self.plan, "run")["status"], "uncertain")
        before = copy.deepcopy(self.store.preparation(self.plan["run_id"]))
        calls = len(self.session.calls)
        self.session.attestation["effects_grant"]["authorized"] = False
        with self.assertRaises(f.run_state.StateError):
            self.adapter().reconcile(self.plan)
        self.assertEqual(self.store.preparation(self.plan["run_id"]), before)
        self.assertEqual(len(self.session.calls), calls)

    def test_lost_response_is_lookup_only_with_original_uuid(self):
        adapter = self.begin()
        self.session.lose_response = True
        adapter.prepare_one(self.plan, "run")
        self.session.lose_response = False
        self.assertNotEqual(self.adapter().prepare_one(self.plan, "run")["status"], "uncertain")
        self.assertEqual(sum(k == "mutate" for k, _ in self.session.calls), 1)

    def test_nullable_provenance_must_agree_between_receipt_and_resource(self):
        adapter = self.bind()
        op = self.store.preparation(self.plan["run_id"])["operations"]["task:a"]
        receipt = self.session.receipts[op["request_id"]]["receipt"]["task"]
        row = self.session.tasks["native-a"]
        for field in PROVENANCE:
            for changed in (receipt, row):
                changed[field] = 1 if field.endswith("generation") else "foreign"
                self.assertEqual(adapter.reconcile(self.plan)["status"], "uncertain")
                changed[field] = None

    def test_nonnull_provenance_cannot_match_an_unknown_context(self):
        adapter = self.bind()
        op = self.store.preparation(self.plan["run_id"])["operations"]["task:a"]
        for row in (self.session.tasks["native-a"], self.session.receipts[op["request_id"]]["receipt"]["task"]):
            row["created_by_pane_key"] = "unobserved-pane"
        self.assertEqual(adapter.reconcile(self.plan)["status"], "uncertain")

    def test_run_change_and_any_worker_block_finalization(self):
        adapter = self.bind()
        self.session.run["consumer_generation"] = 2
        with self.assertRaises(f.run_state.StateError):
            adapter.finalize(self.plan)
        self.session.run["consumer_generation"] = 1
        self.session.workers = [{"dispatchId": "another-dispatch"}]
        with self.assertRaises(f.run_state.StateError):
            adapter.finalize(self.plan)
        self.assertEqual(self.store.snapshot()["runs"], [])

    def test_foreign_current_run_blocks_before_intent(self):
        adapter = self.begin()
        self.session.run = {"id": "unrelated-run"}
        with self.assertRaises(f.run_state.StateError):
            adapter.prepare_one(self.plan, "run")
        self.assertEqual(self.store.preparation(self.plan["run_id"])["operations"], {})
        self.assertFalse(any(k == "mutate" for k, _ in self.session.calls))

    def test_effect_revocation_after_intent_never_sends(self):
        adapter = self.begin()
        original = self.store.preparation_intent
        def claim(*args, **kwargs):
            op = original(*args, **kwargs)
            self.session.attestation["effects_grant"]["authorized"] = False
            return op
        with patch.object(self.store, "preparation_intent", side_effect=claim):
            self.assertEqual(adapter.prepare_one(self.plan, "run")["status"], "uncertain")
        self.assertFalse(any(k == "mutate" for k, _ in self.session.calls))
        self.assertIsNone(self.store.snapshot()["budget"]["actual_total_usd"])

    def test_nullable_fields_must_exist_and_reject_boolean_generation(self):
        adapter = self.bind()
        row = self.session.tasks["native-a"]
        for field in PROVENANCE:
            row.pop(field)
            self.assertEqual(adapter.reconcile(self.plan)["status"], "uncertain")
            row[field] = None
        row["created_by_run_generation"] = True
        self.assertEqual(adapter.reconcile(self.plan)["status"], "uncertain")

    def test_matching_nonnull_observations_are_supported(self):
        self.session.context.update(pane_key="observed-pane", process_incarnation="observed-process")
        self.session.authorize_effects()
        adapter = self.bind()
        for op in self.store.preparation(self.plan["run_id"])["operations"].values():
            if op["native_id"] == "native-run":
                continue
            for row in (self.session.tasks[op["native_id"]], self.session.receipts[op["request_id"]]["receipt"]["task"]):
                row.update(created_by_pane_key="observed-pane", created_by_process_incarnation="observed-process",
                           created_by_run_generation=1)
        self.assertEqual(adapter.reconcile(self.plan)["status"], "bound")

    def test_v2_existing_state_cannot_switch_to_v1(self):
        self.begin()
        strong = f.Session(self.plan, self.store)
        adapter = f.core.PreparationAdapter(self.store, f.Host(strong), clock=lambda: NOW)
        with self.assertRaises(f.run_state.StateError):
            adapter.reconcile(self.plan)
        self.assertEqual(strong.calls, [])

    def test_explicit_context_bypass_reads_are_not_forwarded(self):
        adapter = self.bind()
        calls = len(self.session.calls)
        for args in (("orchestration", "run-current", "--from", self.session.context["handle"]),
                     ("orchestration", "task-list", "--run", "native-run"),
                     ("orchestration", "worker-start"), ("orchestration", "run-use")):
            with self.assertRaises(f.run_state.StateError):
                adapter.call(*args)
        self.assertEqual(len(self.session.calls), calls)

    def test_observable_required_context_still_fails_closed(self):
        for field, value in (("target", "remote"), ("runtime_id", "other"), ("worktree_id", "other"),
                             ("handle", None), ("transport_id", None), ("approval_ref", "other")):
            session = Session(self.plan, self.store)
            session.context[field] = value
            session.authorize_effects()
            with self.assertRaises(f.run_state.StateError):
                self.adapter(session).begin(self.plan)
            self.assertEqual(session.calls, [])

    def test_read_only_grant_can_recover_but_never_create_next_intent(self):
        adapter = self.begin()
        self.session.lose_response = True
        adapter.prepare_one(self.plan, "run")
        self.session.lose_response = False
        state = self.store.preparation(self.plan["run_id"])
        request = state["operations"]["run"]["request_id"]
        self.session.attestation["effects_grant"]["mutation_methods"] = []
        recovered = self.adapter()
        self.assertNotEqual(recovered.prepare_one(self.plan, "run")["status"], "uncertain")
        with self.assertRaises(f.run_state.StateError):
            recovered.prepare_one(self.plan, "task:a")
        after = self.store.preparation(self.plan["run_id"])
        self.assertEqual(set(after["operations"]), {"run"})
        self.assertEqual(after["operations"]["run"]["request_id"], request)
        self.assertEqual(sum(k == "mutate" for k, _ in self.session.calls), 1)

    def test_read_only_grant_on_new_preparation_makes_no_intent_or_native_call(self):
        self.session.attestation["effects_grant"]["mutation_methods"] = []
        adapter = self.begin()
        with self.assertRaises(f.run_state.StateError):
            adapter.prepare_one(self.plan, "run")
        self.assertEqual(self.store.preparation(self.plan["run_id"])["operations"], {})
        self.assertEqual(self.session.calls, [])

    def test_mutation_permission_removed_after_intent_keeps_hold_without_send(self):
        adapter = self.begin()
        original = self.store.preparation_intent
        def claim(*args, **kwargs):
            op = original(*args, **kwargs)
            self.session.attestation["effects_grant"]["mutation_methods"] = []
            return op
        with patch.object(self.store, "preparation_intent", side_effect=claim):
            self.assertEqual(adapter.prepare_one(self.plan, "run")["status"], "uncertain")
        self.assertFalse(any(k == "mutate" for k, _ in self.session.calls))
        self.assertIsNone(self.store.snapshot()["budget"]["actual_total_usd"])

    def test_read_only_grant_can_finalize_an_already_bound_graph(self):
        adapter = self.bind()
        count = sum(k == "mutate" for k, _ in self.session.calls)
        self.session.attestation["effects_grant"]["mutation_methods"] = []
        self.assertEqual(adapter.finalize(self.plan)["steps"][1]["orca"]["task_id"], "native-b")
        self.assertEqual(sum(k == "mutate" for k, _ in self.session.calls), count)

    def test_mutation_permission_removed_during_pre_intent_read_makes_no_intent(self):
        adapter = self.begin()
        original = self.session.read_exact
        def read(argv):
            result = original(argv)
            if argv[:2] == ("orchestration", "run-current"):
                self.session.attestation["effects_grant"]["mutation_methods"] = []
            return result
        with patch.object(self.session, "read_exact", side_effect=read):
            with self.assertRaises(f.run_state.StateError):
                adapter.prepare_one(self.plan, "run")
        self.assertEqual(self.store.preparation(self.plan["run_id"])["operations"], {})
        self.assertFalse(any(k == "mutate" for k, _ in self.session.calls))


if __name__ == "__main__":
    unittest.main()
