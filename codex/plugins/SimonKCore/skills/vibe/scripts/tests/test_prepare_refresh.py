"""Temporary, process-denied preparation freshness tests; no live evidence."""
import copy
import sqlite3
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

with patch("subprocess.Popen", side_effect=AssertionError("No processes during imports")):
    import test_prepare_orca as adapter_fixture
    import test_prepare_state as store_fixture
    import orchestrate
    import run_state
    import prepare_orca
    from test_orchestrate import NOW
    from test_run_state import STALE


def digest(plan):
    plan["plan_digest"] = orchestrate.digest({k: v for k, v in plan.items() if k != "plan_digest"})
    return plan


def fresh_plan(plan, at=STALE):
    # Synthetic observations only. Production must rerun the central planner
    # with independently re-observed runtime, quota, alias/access and billing.
    result = copy.deepcopy(plan)
    result["planned_at"] = at
    for node in result["steps"]:
        node["route"]["runtime_observed_at"] = at
        node["route"]["quota"]["observed_at"] = at
        node["route"]["valid_until"] = (datetime.fromisoformat(at) + timedelta(minutes=15)).isoformat()
    return digest(result)


class PreparationRefreshTests(unittest.TestCase):
    def setUp(self):
        self.fixture = store_fixture.PreparationTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.init(1)
        self.store, self.caller = self.fixture.store, self.fixture.caller
        self.plan = self.fixture.start(self.fixture.draft(cost="0.1", cap=1))

    def upgrade(self):
        self.assertTrue(hasattr(self.store, "upgrade_preparation_refresh"), "Explicit refresh schema missing")
        self.store.upgrade_preparation_refresh("synthetic migration approval", now=NOW)

    def proof(self, new, at=STALE, state=None):
        state = state or self.store.preparation(self.plan["run_id"])
        return {"verified": True, "runtime_revalidated": True, "observed_at": at,
            "draft_digest": self.plan["plan_digest"],
            "previous_digest": state["validation_digest"], "previous_revision": state["validation_revision"],
            "validation_digest": new["plan_digest"], "evidence": ["synthetic complete runtime revalidation"]}

    def renew(self, new=None, at=STALE, proof=None):
        new = new or fresh_plan(self.plan, at)
        return self.store.renew_preparation(self.plan["run_id"], new, self.caller,
                                          proof or self.proof(new, at), now=at)

    def raw(self):
        with sqlite3.connect(self.fixture.path) as db:
            return db.execute("SELECT * FROM preparations").fetchall()

    def test_explicit_migration_preserves_rows_budget_and_grant(self):
        before, rows = self.store.snapshot(), self.raw()
        self.upgrade()
        self.store.upgrade_preparation_refresh("synthetic migration approval", now=NOW)
        self.store.upgrade_preparations("older schema command", now=NOW)
        self.assertEqual(self.store.snapshot()["schema_version"], 3)
        self.assertEqual(self.store.snapshot()["budget"], before["budget"])
        self.assertEqual(self.raw(), rows)
        self.assertEqual(self.store.preparation("prep-one")["validation_revision"], 0)
        with self.assertRaisesRegex(run_state.StateError, "GRANT_IMMUTABLE"):
            self.store.initialize(2, "different")

    def test_v2_never_upgrades_implicitly(self):
        self.assertTrue(hasattr(self.store, "renew_preparation"), "Renewal missing")
        with self.assertRaisesRegex(run_state.StateError, "PREPARATION_REFRESH_SCHEMA_REQUIRED"):
            self.store.renew_preparation("prep-one", fresh_plan(self.plan), self.caller, {}, now=STALE)
        self.assertEqual(self.store.snapshot()["schema_version"], 2)

    def test_partial_renewal_keeps_identity_and_all_budget(self):
        self.fixture.finish_op("run", "native-run")
        self.upgrade()
        rows, budget = self.raw(), self.store.snapshot()["budget"]
        self.renew()
        self.assertEqual(self.raw(), rows)
        self.assertEqual(self.store.snapshot()["budget"], budget)
        op = self.store.preparation_intent("prep-one", "task:a", self.caller, now=STALE)
        self.assertTrue(op["send_allowed"])
        expected = run_state.preparation_argv(self.plan, self.caller, "task:a", {"run": "native-run"})
        self.assertEqual(op["argv"], expected + ["--retry-request", op["request_id"], "--json"])
        self.assertEqual(op["validation_digest"], fresh_plan(self.plan)["plan_digest"])
        again = self.store.preparation_intent("prep-one", "task:a", self.caller, now=STALE)
        self.assertFalse(again["send_allowed"])
        self.assertEqual(again["request_id"], op["request_id"])

    def test_uncertainty_does_not_become_permission_or_zero_cost(self):
        op = self.store.preparation_intent("prep-one", "run", self.caller, now=NOW)
        self.store.observe_preparation("prep-one", "run", self.caller,
            {"state": "unknown", "operation_sha256": op["operation_sha256"], "observed_at": NOW,
             "evidence": ["synthetic unknown"]}, now=NOW)
        self.upgrade()
        before = self.store.snapshot()["budget"]
        self.renew()
        self.assertEqual(self.store.snapshot()["budget"], before)
        self.assertIsNone(before["actual_total_usd"])
        self.assertFalse(self.store.preparation_intent("prep-one", "run", self.caller, now=STALE)["send_allowed"])
        with self.assertRaisesRegex(run_state.StateError, "PREPARATION_RECONCILIATION_REQUIRED"):
            self.store.preparation_intent("prep-one", "task:a", self.caller, now=STALE)

    def test_semantic_drift_and_numeric_type_drift_are_rejected_atomically(self):
        self.upgrade()
        changes = [lambda p: p["steps"][0].update(outcome="other"),
            lambda p: p["steps"].reverse(),
            lambda p: p["steps"][1].update(depends_on=[]),
            lambda p: p["steps"][0]["handoff"].update(reuse_coordinator=True),
            lambda p: p["steps"][0]["route"].update(model="other"),
            lambda p: p["steps"][0]["route"]["billing"].update(account_ref="other"),
            lambda p: p["steps"][0]["orca"].update(profile_ref="other"),
            lambda p: p["steps"][0]["route"].update(reserved_upper_usd=0),
            lambda p: p["budget"].update(approved_usd=True),
            lambda p: p["budget"].update(approved_usd=1.0),
            lambda p: p["steps"][0]["route"]["quota"].update(used_pct=99),
            lambda p: p["model_registry"].update(sha256="e" * 64),
            lambda p: p["model_registry"].update(checked_at=STALE),
            lambda p: p.update(unrecognized="extension")]
        rows, state = self.raw(), self.store.preparation("prep-one")
        for change in changes:
            with self.subTest(change=changes.index(change)):
                new = fresh_plan(self.plan)
                change(new)
                digest(new)
                with self.assertRaises(run_state.StateError):
                    self.renew(new)
                self.assertEqual(self.raw(), rows)
                self.assertEqual(self.store.preparation("prep-one"), state)

    def test_missing_timestamp_and_unbounded_expiry_are_rejected(self):
        self.upgrade()
        for mutation in (lambda r: r.pop("runtime_observed_at"),
                         lambda r: r.update(valid_until="2099-01-01T00:00:00+00:00"),
                         lambda r: r.update(runtime_observed_at="2099-01-01T00:00:00+00:00")):
            new = fresh_plan(self.plan)
            mutation(new["steps"][0]["route"])
            digest(new)
            with self.assertRaises(run_state.StateError):
                self.renew(new)

    def test_renewal_checks_worst_id_projection_before_any_new_effect(self):
        fixture = store_fixture.PreparationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.init(1)
        plan = fixture.draft(cost="0.1", cap=1)
        plan["steps"][0]["orca"]["padding"] = ""
        digest(plan)
        plan["steps"][0]["orca"]["padding"] = " " * (1024 * 1024 - 2000 - len(run_state.safe_json(plan).encode()))
        digest(plan)
        fixture.start(plan)  # Original admission has enough worst-ID headroom.
        self.store, self.plan, self.caller = fixture.store, plan, fixture.caller
        self.upgrade()
        new = fresh_plan(plan)
        new["planned_at"] = STALE.replace("+00:00", "." + "0" * 1600 + "+00:00")
        digest(new)
        self.assertLess(len(run_state.safe_json(new).encode()), 1024 * 1024)
        before = self.store.preparation("prep-one")
        with self.assertRaises(run_state.StateError):
            self.renew(new)
        self.assertEqual(self.store.preparation("prep-one"), before)

    def test_revalidation_proof_is_required_and_not_just_fresh_timestamps(self):
        self.upgrade()
        new = fresh_plan(self.plan)
        for key, value in (("verified", False), ("runtime_revalidated", False),
                           ("previous_revision", False), ("draft_digest", "f" * 64),
                           ("evidence", []), ("observed_at", NOW)):
            proof = self.proof(new)
            proof[key] = value
            with self.subTest(key=key), self.assertRaises(run_state.StateError):
                self.renew(new, proof=proof)

    def test_expired_frozen_registry_cannot_be_laundered(self):
        self.upgrade()
        at = (datetime.fromisoformat(NOW) + timedelta(days=8)).isoformat()
        with self.assertRaisesRegex(run_state.StateError, "PREPARATION_EVIDENCE_EXPIRED"):
            self.renew(fresh_plan(self.plan, at), at)

    def test_actual_central_planner_runtime_refresh_is_compatible(self):
        self.upgrade()
        c = store_fixture.candidate(model="gpt-5.6-luna", transport="orca", upper_usd_per_attempt="0.1",
            billing={"mode": "api", "verified": True, "account_ref": "test-account"}, observed_at=STALE,
            quota={"used_pct": 10, "observed_at": STALE, "bucket": "test-weekly"})
        new = orchestrate.make_plan({"run_id": self.plan["run_id"], "budget": self.plan["budget"],
            "steps": self.plan["steps"]}, {"explain": {"path": "/fixture/SKILL.md"}},
            {"candidates": [c], "tools": [], **self.plan["steps"][0]["orca"]["guards"]},
            STALE, store_fixture.fixture_registry([c]))
        self.assertEqual(new["status"], "ready")
        self.renew(new)
        self.assertEqual(self.store.preparation_validation("prep-one", self.caller)["plan"], new)

    def test_cas_repeat_downgrade_and_wrong_caller(self):
        self.upgrade()
        new = fresh_plan(self.plan)
        proof = self.proof(new)
        self.renew(new, proof=proof)
        # Exact persisted retry is idempotent without incrementing revision.
        self.renew(new, proof=proof)
        self.assertEqual(self.store.preparation("prep-one")["validation_revision"], 1)
        later = (datetime.fromisoformat(STALE) + timedelta(seconds=1)).isoformat()
        newer = fresh_plan(self.plan, later)
        with self.assertRaisesRegex(run_state.StateError, "PREPARATION_VALIDATION_CHANGED"):
            self.renew(newer, later, {**proof, "validation_digest": newer["plan_digest"], "observed_at": later})
        self.renew(newer, later)
        with self.assertRaises(run_state.StateError):
            self.renew(new, later)
        with self.assertRaisesRegex(run_state.StateError, "PREPARATION_CALLER_CHANGED"):
            self.store.renew_preparation("prep-one", newer, {**self.caller, "handle": "other"},
                                         self.proof(newer, later), now=later)

    def test_newer_observation_can_shorten_expiry_and_then_blocks(self):
        self.upgrade()
        at = (datetime.fromisoformat(NOW) + timedelta(minutes=1)).isoformat()
        new = fresh_plan(self.plan, at)
        for node in new["steps"]:
            node["route"]["valid_until"] = (datetime.fromisoformat(NOW) + timedelta(minutes=5)).isoformat()
        digest(new)
        self.renew(new, at)
        after_expiry = (datetime.fromisoformat(NOW) + timedelta(minutes=6)).isoformat()
        with self.assertRaises(run_state.StateError):
            self.store.preparation_intent("prep-one", "run", self.caller, now=after_expiry)
        self.assertEqual(self.store.preparation("prep-one")["operations"], {})

    def test_host_skill_cannot_enter_orca_freshness_contract(self):
        plan = fresh_plan(self.plan)
        plan["steps"][0]["handoff"]["host_skills"] = [{"observed_at": NOW}]
        digest(plan)
        with self.assertRaisesRegex(run_state.StateError, "PREPARATION_HOST_SKILL_UNSUPPORTED"):
            run_state.validate_preparation_freshness(plan, STALE)

    def test_concurrent_different_renewals_have_one_cas_winner(self):
        self.upgrade()
        state = self.store.preparation("prep-one")
        new = fresh_plan(self.plan)
        other = fresh_plan(self.plan, (datetime.fromisoformat(STALE) + timedelta(seconds=1)).isoformat())
        def renew(plan):
            try:
                self.store.renew_preparation("prep-one", plan, self.caller,
                    self.proof(plan, other["planned_at"], state), now=other["planned_at"])
                return True
            except run_state.StateError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(renew, [new, other])), 1)

    def test_finalization_binds_validation_and_rolls_back_registration_failure(self):
        proof = self.fixture.bind_all()
        self.upgrade()
        self.renew()
        state = self.store.preparation("prep-one")
        proof.update(observed_at=STALE)
        with self.assertRaisesRegex(run_state.StateError, "PREPARATION_VALIDATION_CHANGED"):
            self.store.finalize_preparation("prep-one", self.caller, proof, now=STALE)
        proof.update(validation_digest=state["validation_digest"], validation_revision=state["validation_revision"])
        budget = self.store.snapshot()["budget"]
        with patch.object(self.store, "_register", side_effect=run_state.StateError("fixture rollback")):
            with self.assertRaises(run_state.StateError):
                self.store.finalize_preparation("prep-one", self.caller, proof, now=STALE)
        self.assertEqual(self.store.preparation("prep-one")["state"], "bound")
        self.assertEqual(self.store.snapshot()["budget"], budget)
        final = self.store.finalize_preparation("prep-one", self.caller, proof, now=STALE)
        self.assertEqual(final, run_state.preparation_projection(fresh_plan(self.plan),
            {"run": "native-run", "task:a": "native-a", "task:b": "native-b"}))
        self.assertEqual(self.store.snapshot()["budget"], budget)
        with self.assertRaisesRegex(run_state.StateError, "PREPARATION_ALREADY_REGISTERED"):
            self.renew()


class PreparationRefreshAdapterTests(unittest.TestCase):
    def setUp(self):
        self.fixture = adapter_fixture.PreparationAdapterTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.plan, self.store, self.session = self.fixture.plan, self.fixture.store, self.fixture.session
        self.assertTrue(hasattr(self.store, "upgrade_preparation_refresh"), "Explicit refresh schema missing")
        self.store.upgrade_preparation_refresh("synthetic migration approval", now=NOW)
        self.adapter = self.fixture.begin()

    def later(self):
        self.session.attestation.update(observed_at=STALE, valid_until="2027-01-01T00:00:00+00:00")
        return self.fixture.adapter(now=STALE)

    def renew(self, adapter):
        return adapter.renew(self.plan, fresh_plan(self.plan), ["synthetic full runtime revalidation"])

    def test_partial_restart_then_new_intents_and_finalization(self):
        self.adapter.prepare_one(self.plan, "run")
        original = self.store.preparation("prep-one")["operations"]["run"]
        later = self.later()
        before = len(self.session.calls)
        self.renew(later)
        self.assertEqual(len(self.session.calls), before, "Renewal itself must be metadata-only")
        self.assertEqual(self.store.preparation("prep-one")["operations"]["run"], original)
        for key in ("task:a", "task:b"):
            self.assertNotEqual(later.prepare_one(self.plan, key)["status"], "uncertain")
        final = later.finalize(self.plan)
        self.assertEqual(final["planned_at"], STALE)
        self.assertNotEqual(final["plan_digest"], self.plan["plan_digest"])
        self.assertEqual(sum(kind == "mutate" for kind, _ in self.session.calls), 3)
        old_final = run_state.preparation_projection(self.plan,
            {"run": "native-run", "task:a": "native-a", "task:b": "native-b"})
        transport = SimpleNamespace(executable=final["steps"][0]["orca"]["executable"],
                                    sha256=final["steps"][0]["orca"]["executable_sha256"])
        worker = store_fixture.execute_orca.Adapter(self.store, transport, clock=lambda: STALE)
        certificate = {"verified": True, "evidence": ["synthetic old-plan evidence"],
            "binding_sha256": store_fixture.execute_orca.binding_digest(old_final, "a"),
            "account_ref": final["steps"][0]["orca"]["account_ref"],
            "profile_ref": final["steps"][0]["orca"]["profile_ref"],
            "billing": final["steps"][0]["route"]["billing"]}
        with self.assertRaisesRegex(run_state.StateError, "TRANSPORT_ACCOUNT_MISMATCH"):
            worker.gate(final, "a", certificate)

    def test_renewal_never_recovers_absent_receipt_or_resends(self):
        self.session.before_effect = True
        self.adapter.prepare_one(self.plan, "run")
        self.session.before_effect = False
        later = self.later()
        self.renew(later)
        self.assertEqual(later.prepare_one(self.plan, "task:a")["status"], "uncertain")
        self.assertEqual(sum(kind == "mutate" for kind, _ in self.session.calls), 1)
        self.assertIsNone(self.store.snapshot()["budget"]["actual_total_usd"])

    def test_expired_overlay_cannot_authorize_new_send(self):
        later = self.later()
        self.renew(later)
        later.clock = lambda: (datetime.fromisoformat(STALE) + timedelta(minutes=16)).isoformat()
        self.session.attestation["observed_at"] = later.clock()
        with self.assertRaises(run_state.StateError):
            later.prepare_one(self.plan, "run")
        self.assertFalse(any(kind == "mutate" for kind, _ in self.session.calls))

    def test_changed_validation_after_claim_blocks_send(self):
        later = self.later()
        self.renew(later)
        original = self.store.preparation_intent
        def claim(*args, **kwargs):
            op = original(*args, **kwargs)
            at = (datetime.fromisoformat(STALE) + timedelta(seconds=1)).isoformat()
            later.clock = lambda: at
            later.renew(self.plan, fresh_plan(self.plan, at), ["synthetic newer observation"])
            return op
        with patch.object(self.store, "preparation_intent", side_effect=claim):
            self.assertEqual(later.prepare_one(self.plan, "run")["status"], "uncertain")
        self.assertFalse(any(kind == "mutate" for kind, _ in self.session.calls))


if __name__ == "__main__":
    unittest.main()
