"""Persistent run/budget contracts. Fake providers only; real local processes race."""
import copy
import hashlib
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import orchestrate
from test_orchestrate import candidate, fixture_registry, step, NOW

SCRIPT = Path(__file__).with_name("run_state.py")
LATER = (datetime.fromisoformat(NOW) + timedelta(seconds=2)).isoformat()
STALE = (datetime.fromisoformat(NOW) + timedelta(minutes=16)).isoformat()
HANDLE = {"kind": "cli", "id": "fixture-job", "identity": "fixture-process-start"}


def plan(run="run-one", cost=0, nodes=None, now=NOW, account="fixture-account", cap=10):
    c = candidate(billing={"mode": "api", "verified": True, "account_ref": account},
                  upper_usd_per_attempt=cost, observed_at=now,
                  quota={"used_pct": 10, "observed_at": now, "bucket": "fixture-weekly"})
    data = {"run_id": run, "budget": {"approved_usd": cap}, "steps": nodes or [step()]}
    return orchestrate.make_plan(data, {"explain": {"path": "/fixture/SKILL.md"}},
        {"candidates": [c], "tools": [], "observed_at": now}, now, fixture_registry([c]))


class RunStateTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "Persistent run state is not implemented")
        spec = importlib.util.spec_from_file_location("run_state", SCRIPT)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.tmp = tempfile.TemporaryDirectory(prefix="vibe-state-test-")
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "state.sqlite3"
        self.store = self.m.Store(self.path)

    def init(self, cap=10):
        self.store.initialize(cap, approval_ref="fixture-user-approval")

    def register_claim(self, p=None):
        p = p or plan()
        self.store.register(p, now=NOW)
        return self.store.claim(p["run_id"], "read", "request-one", p["plan_digest"], now=NOW)

    def finish(self, attempt, actual="0", success=True):
        dispatch = attempt["dispatch_id"]
        self.store.bind(dispatch, HANDLE, now=NOW)
        self.store.observe(dispatch, {"state": "succeeded" if success else "failed", "handle": HANDLE,
            "observed_at": NOW, "evidence": ["fixture-provider-terminal"],
            "resolved_model": "fixture-small", "effective_effort": "low"}, now=NOW)
        if actual is not None:
            self.store.settle(dispatch, actual, ["fixture-final-receipt"], now=NOW)
        if success:
            self.store.verify(dispatch, ["fixture-output-checked"], now=NOW)

    def test_uninitialized_store_does_not_create_or_reset_database(self):
        with self.assertRaises(self.m.StateError):
            self.store.snapshot()
        self.assertFalse(self.path.exists())

    def test_zero_is_default_and_initial_grant_is_immutable(self):
        self.store.initialize()
        with self.assertRaises(self.m.StateError):
            self.store.register(plan(cost="0.01"), now=NOW)
        self.assertEqual(self.store.snapshot()["runs"], [])
        with self.assertRaises(self.m.StateError):
            self.store.initialize(10, approval_ref="changed")

    def test_whole_run_reserves_all_nodes_and_attempts_atomically(self):
        self.init(1)
        p = plan(cost="0.3", nodes=[step("a"), step("b")])
        with self.assertRaises(self.m.StateError):
            self.store.register(p, now=NOW)
        self.assertEqual(self.store.snapshot()["runs"], [])
        self.assertEqual(self.store.snapshot()["budget"]["held_usd"], "0")

    def test_same_plan_registration_is_idempotent_but_changed_intent_is_not(self):
        self.init()
        p = plan(cost="0.2")
        self.store.register(p, now=NOW)
        self.store.register(p, now=NOW)
        self.assertEqual(self.store.snapshot()["budget"]["held_usd"], "0.4")
        changed = plan(nodes=[step(task="Different task")])
        with self.assertRaises(self.m.StateError):
            self.store.register(changed, now=NOW)

    def test_claim_replay_never_authorizes_a_second_send(self):
        self.init()
        p = plan()
        first = self.register_claim(p)
        repeat = self.store.claim("run-one", "read", "request-one", p["plan_digest"], now=NOW)
        self.assertTrue(first["dispatch_allowed"])
        self.assertFalse(repeat["dispatch_allowed"])
        self.assertEqual(first["dispatch_id"], repeat["dispatch_id"])
        with self.assertRaises(self.m.StateError):
            self.store.claim("run-one", "read", "different-request", p["plan_digest"], now=NOW)

    def test_same_request_key_cannot_be_rebound_to_another_task(self):
        self.init()
        p = plan(nodes=[step("a"), step("b")])
        self.store.register(p, now=NOW)
        self.store.claim("run-one", "a", "same", p["plan_digest"], now=NOW)
        with self.assertRaises(self.m.StateError):
            self.store.claim("run-one", "b", "same", p["plan_digest"], now=NOW)

    def test_plan_and_runtime_expiry_are_rechecked_on_claim(self):
        self.init()
        p = plan()
        self.store.register(p, now=NOW)
        with self.assertRaises(self.m.StateError):
            self.store.claim("run-one", "read", "stale", p["plan_digest"], now=STALE)
        self.assertEqual(self.store.snapshot()["attempts"], [])

    def test_timeout_and_restart_keep_handle_reservation_and_no_retry(self):
        self.init()
        p = plan(cost="0.2")
        a = self.register_claim(p)
        self.store.bind(a["dispatch_id"], HANDLE, now=NOW)
        self.store.observe(a["dispatch_id"], {"state": "unknown", "handle": HANDLE,
            "observed_at": LATER, "evidence": ["observer-timeout"]}, now=LATER)
        reopened = self.m.Store(self.path)
        s = reopened.snapshot()
        self.assertEqual(s["attempts"][0]["state"], "uncertain")
        self.assertEqual(s["attempts"][0]["handle"], HANDLE)
        self.assertEqual(s["budget"]["held_usd"], "0.4")
        with self.assertRaises(self.m.StateError):
            reopened.claim("run-one", "read", "retry", p["plan_digest"], now=LATER)
        with self.assertRaises(self.m.StateError):
            reopened.cancel("run-one", ["not-termination-proof"], now=LATER)

    def test_handle_is_immutable_and_mismatched_observation_is_rejected(self):
        self.init()
        a = self.register_claim()
        self.store.bind(a["dispatch_id"], HANDLE, now=NOW)
        wrong = {**HANDLE, "identity": "different-start"}
        with self.assertRaises(self.m.StateError):
            self.store.bind(a["dispatch_id"], wrong, now=NOW)
        with self.assertRaises(self.m.StateError):
            self.store.observe(a["dispatch_id"], {"state": "failed", "handle": wrong,
                "observed_at": NOW, "evidence": ["wrong-process"]}, now=NOW)

    def test_terminal_is_not_verified_output_or_cost_settlement(self):
        self.init()
        p = plan(cost="0.2", nodes=[step(), step("next", depends_on=["read"])])
        a = self.register_claim(p)
        self.store.bind(a["dispatch_id"], HANDLE, now=NOW)
        self.store.observe(a["dispatch_id"], {"state": "succeeded", "handle": HANDLE,
            "observed_at": NOW, "evidence": ["provider-exit-0"],
            "resolved_model": "fixture-small", "effective_effort": "low"}, now=NOW)
        s = self.store.snapshot()
        self.assertIsNone(s["budget"]["actual_total_usd"])
        self.assertEqual(s["budget"]["held_usd"], "0.8")
        self.assertEqual(self.store.ready("run-one", now=NOW), [])
        self.store.settle(a["dispatch_id"], "0.15", ["receipt"], now=NOW)
        self.assertEqual(self.store.ready("run-one", now=NOW), [])
        self.store.verify(a["dispatch_id"], ["acceptance-checked"], now=NOW)
        self.assertEqual(self.store.ready("run-one", now=NOW), ["next"])

    def test_unknown_actual_is_not_zero_or_released_on_cancel(self):
        self.init()
        a = self.register_claim(plan(cost="0.2"))
        self.finish(a, actual=None, success=False)
        s = self.store.snapshot()
        self.assertIsNone(s["attempts"][0]["actual_usd"])
        self.assertEqual(s["budget"]["held_usd"], "0.4")
        with self.assertRaises(self.m.StateError):
            self.store.cancel("run-one", ["cancel-request"], now=NOW)

    def test_overspend_is_recorded_and_blocks_next_dispatch(self):
        self.init("0.5")
        a = self.register_claim(plan(cost="0.2", cap="0.5"))
        self.finish(a, actual="0.6", success=False)
        s = self.store.snapshot()
        self.assertEqual(s["budget"]["known_spent_usd"], "0.6")
        self.assertTrue(s["budget"]["halted"])
        with self.assertRaises(self.m.StateError):
            self.store.register(plan("another", cap=0), now=NOW)

    def test_cost_receipt_replay_is_idempotent_and_conflicting_receipt_rejected(self):
        self.init()
        a = self.register_claim(plan(cost="0.2"))
        self.finish(a, actual="0.1")
        self.store.settle(a["dispatch_id"], "0.1", ["receipt-again"], now=NOW)
        self.assertEqual(self.store.snapshot()["budget"]["known_spent_usd"], "0.1")
        with self.assertRaises(self.m.StateError):
            self.store.settle(a["dispatch_id"], "0", ["conflicting-receipt"], now=NOW)

    def test_retry_requires_terminal_receipt_and_fresh_revalidated_plan(self):
        self.init()
        p = plan(cost="0.2")
        a = self.register_claim(p)
        self.finish(a, actual="0.1", success=False)
        with self.assertRaises(self.m.StateError):
            self.store.claim("run-one", "read", "retry", p["plan_digest"], now=NOW)
        refreshed = plan(cost="0.3", now=LATER, account="fallback-account")
        self.store.refresh(refreshed, now=LATER)
        b = self.store.claim("run-one", "read", "retry", refreshed["plan_digest"], now=LATER)
        self.assertEqual(b["attempt"], 2)
        self.assertNotEqual(a["dispatch_id"], b["dispatch_id"])
        self.assertEqual(self.store.snapshot()["budget"]["held_usd"], "0.3")
        self.assertEqual(self.store.snapshot()["budget"]["known_spent_usd"], "0.1")

    def test_shadow_task_fit_refresh_is_not_new_task_intent(self):
        self.init()
        first = plan()
        first["steps"][0]["shadow_task_fit"] = {"status": "ranked", "suggested_model": "fixture-a"}
        first["plan_digest"] = orchestrate.digest({k: v for k, v in first.items() if k != "plan_digest"})
        refreshed = plan(now=LATER)
        refreshed["steps"][0]["shadow_task_fit"] = {"status": "expired"}
        refreshed["plan_digest"] = orchestrate.digest({k: v for k, v in refreshed.items() if k != "plan_digest"})

        self.store.register(first, now=NOW)
        self.store.refresh(refreshed, now=LATER)
        self.assertEqual(self.store.snapshot()["runs"][0]["plan_digest"], refreshed["plan_digest"])
        self.assertEqual(self.m.spec_digest(first), self.m.spec_digest(refreshed))
        self.assertEqual(self.m.task_spec(first["steps"][0]), self.m.task_spec(refreshed["steps"][0]))

    def test_refresh_cannot_forget_an_uncertain_dispatch(self):
        self.init()
        self.register_claim()
        with self.assertRaises(self.m.StateError):
            self.store.refresh(plan(now=LATER), now=LATER)

    def test_late_observation_cannot_overwrite_terminal_or_verified_result(self):
        self.init()
        a = self.register_claim()
        self.finish(a)
        with self.assertRaises(self.m.StateError):
            self.store.observe(a["dispatch_id"], {"state": "running", "handle": HANDLE,
                "observed_at": LATER, "evidence": ["late-message"]}, now=LATER)
        self.assertTrue(self.store.snapshot()["attempts"][0]["verified"])

    def test_actual_effort_mismatch_cannot_be_verified(self):
        self.init()
        a = self.register_claim()
        self.store.bind(a["dispatch_id"], HANDLE, now=NOW)
        self.store.observe(a["dispatch_id"], {"state": "succeeded", "handle": HANDLE,
            "observed_at": NOW, "evidence": ["output"],
            "resolved_model": "fixture-small", "effective_effort": "high"}, now=NOW)
        with self.assertRaises(self.m.StateError):
            self.store.verify(a["dispatch_id"], ["not-matching"], now=NOW)

    def test_nan_boolean_negative_and_tiny_money(self):
        for value in (True, -1, "NaN", "Infinity", None):
            with self.subTest(value=value), self.assertRaises(self.m.StateError):
                self.m.nano(value)
        self.assertEqual(self.m.nano("0.00000000001"), 1)

    def test_raw_secrets_rejected_before_persistence(self):
        self.init()
        p = plan(nodes=[step(task='password="do-not-store-this-value"')])
        with self.assertRaises(self.m.StateError) as err:
            self.store.register(p, now=NOW)
        self.assertNotIn("do-not-store", str(err.exception))
        self.assertEqual(self.store.snapshot()["runs"], [])

    def test_tampered_or_blocked_plan_rejected(self):
        self.init()
        for change in ({"status": "blocked"}, {"plan_digest": "bad"}):
            p = plan()
            p.update(change)
            with self.subTest(change=change), self.assertRaises(self.m.StateError):
                self.store.register(p, now=NOW)

    def test_multiple_process_reservations_cannot_oversubscribe(self):
        self.init(1)
        program = ('import sys,json; sys.path.insert(0,sys.argv[1]); from run_state import Store,StateError; '
                   's=Store(sys.argv[2]); p=json.loads(sys.stdin.read());\n'
                   'try: s.register(p,now=sys.argv[3]); print("ok")\n'
                   'except StateError as e: print(e.code)\n')
        children = [subprocess.Popen([sys.executable, "-c", program, str(SCRIPT.parent), str(self.path), NOW],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    for _ in range(2)]
        for i, child in enumerate(children):
            child.stdin.write(json.dumps(plan("race-" + str(i), cost="0.3")))
            child.stdin.close()
            child.stdin = None
        outputs = [c.communicate(timeout=10) for c in children]
        self.assertEqual(sum(out.strip() == "ok" for out, err in outputs), 1, outputs)
        self.assertEqual(self.store.snapshot()["budget"]["held_usd"], "0.6")
        self.assertEqual(len(self.store.snapshot()["runs"]), 1)

    def test_corrupt_or_foreign_database_is_not_reinitialized(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("CREATE TABLE unrelated(data TEXT)")
            db.commit()
        with self.assertRaises(self.m.StateError):
            self.store.initialize()
        with closing(sqlite3.connect(self.path)) as db:
            self.assertIsNotNone(db.execute("SELECT name FROM sqlite_master WHERE name='unrelated'").fetchone())

    def test_missing_observation_time_cannot_be_made_fresh(self):
        self.init()
        a = self.register_claim()
        self.store.bind(a["dispatch_id"], HANDLE, now=NOW)
        with self.assertRaises(self.m.StateError):
            self.store.observe(a["dispatch_id"], {"state": "succeeded", "handle": HANDLE,
                "evidence": ["old-unknown-time"]})

    def test_run_overrun_is_visible_even_when_global_cap_has_room(self):
        self.init(10)
        a = self.register_claim(plan(cost="0.1", cap="0.2"))
        self.finish(a, actual="0.3")
        self.assertTrue(self.store.snapshot()["budget"]["halted"])

    def test_cross_run_parallel_limit_counts_uncertain_intents(self):
        self.init()
        for i in range(3):
            self.store.register(plan("parallel-" + str(i)), now=NOW)
        for i in range(2):
            p = plan("parallel-" + str(i))
            self.store.claim(p["run_id"], "read", "request", p["plan_digest"], now=NOW)
        self.assertEqual(self.store.ready("parallel-2", now=NOW), [])

    def test_concurrent_claims_issue_only_one_send_permission(self):
        self.init()
        p = plan()
        self.store.register(p, now=NOW)
        code = ('import sys,json; sys.path.insert(0,sys.argv[1]); from run_state import Store; '
                'print(json.dumps(Store(sys.argv[2]).claim("run-one","read","same",sys.argv[3],now=sys.argv[4])))')
        children = [subprocess.Popen([sys.executable, "-c", code, str(SCRIPT.parent), str(self.path),
            p["plan_digest"], NOW], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(4)]
        responses = [c.communicate(timeout=10) for c in children]
        values = [json.loads(out) for out, err in responses]
        self.assertEqual(sum(v["dispatch_allowed"] for v in values), 1)
        self.assertEqual(len({v["dispatch_id"] for v in values}), 1)
        self.assertEqual(len(self.store.snapshot()["attempts"]), 1)

    def test_crash_before_commit_rolls_back_reservation(self):
        self.init()
        code = ('import sys,os; sys.path.insert(0,sys.argv[1]); from run_state import Store; '
                'from test_run_state import plan,NOW; s=Store(sys.argv[2]);\n'
                's._event=lambda *args: os._exit(91)\n'
                's.register(plan(cost="0.2"),now=NOW)\n')
        child = subprocess.run([sys.executable, "-c", code, str(SCRIPT.parent), str(self.path)],
                               capture_output=True, timeout=10)
        self.assertEqual(child.returncode, 91)
        self.assertEqual(self.store.snapshot()["runs"], [])
        self.assertEqual(self.store.snapshot()["budget"]["held_usd"], "0")

    def test_crash_after_claim_keeps_intent_and_forbids_resend(self):
        self.init()
        p = plan(cost="0.2")
        self.store.register(p, now=NOW)
        code = ('import sys,os; sys.path.insert(0,sys.argv[1]); from run_state import Store; '
                'Store(sys.argv[2]).claim("run-one","read","crashed",sys.argv[3],now=sys.argv[4]); os._exit(92)')
        child = subprocess.run([sys.executable, "-c", code, str(SCRIPT.parent), str(self.path),
                                p["plan_digest"], NOW], capture_output=True, timeout=10)
        self.assertEqual(child.returncode, 92)
        replay = self.store.claim("run-one", "read", "crashed", p["plan_digest"], now=LATER)
        self.assertFalse(replay["dispatch_allowed"])
        self.assertEqual(replay["state"], "intent")
        self.assertIsNone(replay["handle"])
        self.assertEqual(self.store.snapshot()["budget"]["held_usd"], "0.4")

    def test_database_busy_fails_closed_and_does_not_reserve(self):
        self.init()
        with closing(sqlite3.connect(self.path, isolation_level=None)) as db:
            db.execute("BEGIN IMMEDIATE")
            with self.assertRaises(self.m.StateError):
                self.m.Store(self.path, timeout=0.01).register(plan(), now=NOW)
            db.rollback()
        self.assertEqual(self.store.snapshot()["runs"], [])

    def test_writer_output_waits_for_independent_review(self):
        self.init()
        candidates = [candidate(), candidate("critic", "claude", resource_rank=2)]
        nodes = [step("write", writes=True), step("review", verify_of="write", depends_on=["write"]),
                 step("consume", depends_on=["write"])]
        p = orchestrate.make_plan({"run_id": "review-run", "steps": nodes},
            {"explain": {"path": "/fixture/SKILL.md"}}, {"candidates": candidates, "tools": [], "observed_at": NOW},
            NOW, fixture_registry(candidates))
        self.assertEqual(p["status"], "ready")
        self.store.register(p, now=NOW)
        a = self.store.claim("review-run", "write", "write-request", p["plan_digest"], now=NOW)
        self.finish(a)
        self.assertEqual(self.store.ready("review-run", now=NOW), ["review"])

    def test_proven_not_started_still_needs_receipt_before_refund(self):
        self.init()
        a = self.register_claim(plan(cost="0.2"))
        self.store.observe(a["dispatch_id"], {"state": "not_started", "handle": None,
            "observed_at": NOW, "evidence": ["adapter-confirmed-before-send-failure"],
            "proof_kind": "transport-not-accepted"}, now=NOW)
        with self.assertRaises(self.m.StateError):
            self.store.cancel("run-one", ["cancel"], now=NOW)
        self.store.settle(a["dispatch_id"], 0, ["no-request-sent"], now=NOW)
        self.store.cancel("run-one", ["cancel"], now=NOW)
        self.assertEqual(self.store.snapshot()["budget"]["held_usd"], "0")

    def test_deep_sensitive_keys_and_oversized_embedded_json_fail_closed(self):
        hidden = {"dbPassword": "fixture-short"}
        for _ in range(12):
            hidden = {"nested": hidden}
        variants = [hidden, json.dumps({"dbPassword": "fixture-short", "padding": "x" * 70000})]
        for payload in variants:
            with self.subTest(kind=type(payload).__name__), self.assertRaises(self.m.StateError):
                self.m.safe_json({"metadata": payload})

    def test_embedded_duplicate_keys_cannot_hide_sensitive_values(self):
        variants = ['{"metadata":{"dbPassword":"fixture-short"},"metadata":{}}',
                    '{"overflow":1e9999}',
                    '{"underflow":1e-1000000}', '{"underflow":-1e-1000000}',
                    '{"rounding":1.00000000000000000000000000000000001}',
                    '{"untrusted":NaN}', '{"bad":Infinity}']
        for payload in variants:
            with self.subTest(payload=payload), self.assertRaises(self.m.StateError):
                self.m.safe_json({"note": payload})

    def test_grant_rounding_never_increases_authorized_money(self):
        self.store.initialize("0.00000000001", approval_ref="fixture-tiny-grant")
        self.assertEqual(self.store.snapshot()["budget"]["approved_usd"], "0")
        self.assertEqual(self.m.nano("1e-1000000"), 1)
        self.assertEqual(self.m.nano("1.00000000000000000000000000000000001"), 1000000001)

    def test_excessive_structure_is_rejected_even_without_a_known_secret(self):
        deep = {"normal": "value"}
        for _ in range(30):
            deep = {"nested": deep}
        with self.assertRaises(self.m.StateError):
            self.m.safe_json(deep)

    def test_successful_but_rejected_output_can_retry_after_settlement_and_refresh(self):
        self.init()
        p = plan(cost="0.2")
        a = self.register_claim(p)
        self.store.bind(a["dispatch_id"], HANDLE, now=NOW)
        self.store.observe(a["dispatch_id"], {"state": "succeeded", "handle": HANDLE,
            "observed_at": NOW, "evidence": ["provider-terminal"],
            "resolved_model": "fixture-small", "effective_effort": "high"}, now=NOW)
        with self.assertRaises(self.m.StateError):
            self.store.verify(a["dispatch_id"], ["wrong-effort"], now=NOW)
        self.store.reject(a["dispatch_id"], ["acceptance-effort-mismatch"], now=NOW)
        self.store.settle(a["dispatch_id"], "0.1", ["receipt"], now=NOW)
        refreshed = plan(cost="0.2", now=LATER)
        self.store.refresh(refreshed, now=LATER)
        self.assertEqual(self.store.ready("run-one", now=LATER), ["read"])
        b = self.store.claim("run-one", "read", "retry", refreshed["plan_digest"], now=LATER)
        self.assertEqual(b["attempt"], 2)

    def test_verified_result_cannot_be_rejected_and_rebound(self):
        self.init()
        a = self.register_claim()
        self.finish(a)
        with self.assertRaises(self.m.StateError):
            self.store.reject(a["dispatch_id"], ["late-rejection"], now=LATER)

    def test_complete_requires_every_node_verified_and_every_cost_settled(self):
        self.init()
        a = self.register_claim()
        with self.assertRaises(self.m.StateError):
            self.store.complete("run-one", ["incomplete"], now=NOW)
        self.finish(a)
        self.store.complete("run-one", ["all-acceptance-criteria"], now=NOW)
        self.assertEqual(self.store.snapshot()["runs"][0]["status"], "completed")
        self.assertEqual(self.store.snapshot()["budget"]["held_usd"], "0")

    def test_crash_after_fake_provider_acceptance_does_not_repeat_side_effect(self):
        self.init()
        p = plan(cost="0.2")
        self.store.register(p, now=NOW)
        marker = Path(self.tmp.name) / "fake-provider-acceptances.txt"
        code = ('import sys,os; from pathlib import Path; sys.path.insert(0,sys.argv[1]); '
                'from run_state import Store; a=Store(sys.argv[2]).claim("run-one","read","accepted",sys.argv[3],now=sys.argv[4]);\n'
                'if a["dispatch_allowed"]:\n'
                ' with open(sys.argv[5],"a") as receipt:\n'
                '  receipt.write(a["dispatch_id"]+"\\n"); receipt.flush(); os.fsync(receipt.fileno())\n'
                ' os._exit(93)\n')
        argv = [sys.executable, "-c", code, str(SCRIPT.parent), str(self.path), p["plan_digest"], NOW, str(marker)]
        self.assertEqual(subprocess.run(argv, capture_output=True, timeout=10).returncode, 93)
        self.assertEqual(subprocess.run(argv, capture_output=True, timeout=10).returncode, 0)
        self.assertEqual(len(marker.read_text().splitlines()), 1)
        pending = self.store.snapshot()["attempts"][0]
        self.assertIsNone(pending["handle"])
        self.assertIsNone(pending["actual_usd"])
        with self.assertRaises(self.m.StateError):
            self.store.refresh(plan(cost="0.2", now=LATER), now=LATER)
        # Simulated provider lookup returns the original job, not a new send.
        self.finish(pending, actual="0.1")
        self.store.complete("run-one", ["recovered-original-job"], now=LATER)

    def test_cli_local_stub_handoff_survives_replay_and_finishes(self):
        def cli(*args):
            result = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPT), "--db", str(self.path), *args],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return json.loads(result.stdout)
        def data(name, value):
            path = Path(self.tmp.name) / name
            path.write_text(json.dumps(value), encoding="utf-8")
            return str(path)
        cli("init")
        now = datetime.now().astimezone().isoformat()
        argv = [sys.executable, "-c", "print('local-fixture-ok')"]
        p = orchestrate.make_plan({"run_id": "local-cli", "steps": [{"id": "local", "kind": "local",
            "skills": [], "writes": False, "argv": argv, "software": [sys.executable]}]}, {},
            {"observed_at": now, "tools": [sys.executable], "candidates": [], "tool_costs": [{
                "argv_sha256": orchestrate.digest(argv), "observed_at": now, "verified": True,
                "evidence": "inspected-fixed-offline-fixture", "upper_usd_per_attempt": 0,
                "transitive_effects_audited": True, "billing_mode": "nonmetered"}]}, now)
        cli("register", "--plan", data("plan.json", p))
        a = cli("claim", "--run", "local-cli", "--node", "local", "--request", "local-once", "--plan-digest", p["plan_digest"])
        self.assertTrue(a["dispatch_allowed"])
        child = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        handle = {"kind": "local-fixture", "id": str(child.pid), "identity": str(time.monotonic_ns())}
        cli("bind", "--dispatch", a["dispatch_id"], "--input", data("handle.json", handle))
        out, err = child.communicate(timeout=5)
        self.assertEqual((child.returncode, out.strip(), err), (0, "local-fixture-ok", ""))
        again = cli("claim", "--run", "local-cli", "--node", "local", "--request", "local-once", "--plan-digest", p["plan_digest"])
        self.assertFalse(again["dispatch_allowed"])
        cli("observe", "--dispatch", a["dispatch_id"], "--input", data("observed.json", {
            "state": "succeeded", "handle": handle, "observed_at": datetime.now().astimezone().isoformat(),
            "evidence": ["owned-child-exit-0", "stdout-local-fixture-ok"]}))
        cli("settle", "--dispatch", a["dispatch_id"], "--input", data("receipt.json", {
            "actual_usd": 0, "evidence": ["fixed-python-print-no-network-or-billed-service"]}))
        cli("verify", "--dispatch", a["dispatch_id"], "--input", data("acceptance.json", {"evidence": ["expected-stdout-checked"]}))
        done = cli("complete", "--run", "local-cli", "--input", data("complete.json", {"evidence": ["local-fixture-criteria-passed"]}))
        self.assertEqual(done["runs"][0]["status"], "completed")
        self.assertEqual(done["budget"]["actual_total_usd"], "0")


class GstackIsolationTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("run_state", SCRIPT)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.tmp = tempfile.TemporaryDirectory(prefix="vibe-gstack-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def home(self, run):
        return self.root.resolve() / "gstack-runs" / hashlib.sha256(run.encode("utf-8")).hexdigest()[:32]

    def test_gstack_env_isolates_state_without_home_reads(self):
        def forbidden(*_args, **_kwargs):
            raise AssertionError("personal home must not be read")
        with patch.object(Path, "home", side_effect=forbidden), \
                patch("os.path.expanduser", side_effect=forbidden):
            env = self.m.gstack_state("run-one", self.root)
        home = self.home("run-one")
        self.assertEqual(env["GSTACK_HOME"], home.as_posix())
        self.assertTrue(home.is_relative_to(self.root.resolve()))
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["gstack-runs"])
        self.assertEqual(sorted(p.name for p in home.iterdir()),
                         sorted(["config.yaml", *self.m.GSTACK_MARKERS]))

    def test_gstack_env_sets_all_three_dir_vars_identically(self):
        env = self.m.gstack_state("run-one", self.root)
        self.assertEqual(set(env), {"GSTACK_HOME", "GSTACK_STATE_DIR", "GSTACK_STATE_ROOT", "GSTACK_TELEMETRY_OFF"})
        self.assertEqual(env["GSTACK_HOME"], env["GSTACK_STATE_DIR"])
        self.assertEqual(env["GSTACK_HOME"], env["GSTACK_STATE_ROOT"])
        self.assertEqual(env["GSTACK_TELEMETRY_OFF"], "1")
        self.assertNotIn("\\", env["GSTACK_HOME"])
        self.assertTrue(Path(env["GSTACK_HOME"]).is_dir())

    def test_gstack_env_config_turns_off_telemetry_and_update_check(self):
        self.m.gstack_state("run-one", self.root)
        raw = (self.home("run-one") / "config.yaml").read_bytes()
        self.assertNotIn(b"\r", raw)
        config = dict(line.split(": ", 1) for line in raw.decode("utf-8").splitlines())
        self.assertEqual(config, {"telemetry": "off", "update_check": "false", "auto_upgrade": "false",
                                  "routing_declined": "true", "artifacts_sync_mode": "off",
                                  "artifacts_sync_mode_prompted": "true",
                                  "cross_project_learnings": "false", "repo_mode": "unknown"})
        self.assertEqual(list(self.home("run-one").glob("*.tmp")), [])

    def test_gstack_env_seeds_onboarding_markers(self):
        self.m.gstack_state("run-one", self.root)
        for marker in (".telemetry-prompted", ".completeness-intro-seen", ".proactive-prompted",
                       ".activated", ".first-loop-tip-shown", ".feature-prompted-model-overlay"):
            with self.subTest(marker=marker):
                self.assertTrue((self.home("run-one") / marker).is_file())

    def test_gstack_env_reentry_detects_flipped_telemetry(self):
        first = self.m.gstack_state("run-one", self.root)
        config = self.home("run-one") / "config.yaml"
        original = config.read_bytes()
        self.assertEqual(self.m.gstack_state("run-one", self.root), first)
        self.assertEqual(config.read_bytes(), original)
        for flipped in ("telemetry: community\n", "update_check: true\n", "telemetry: 'community'\n"):
            with self.subTest(flipped=flipped):
                config.write_bytes(original + flipped.encode("utf-8"))
                with self.assertRaises(self.m.StateError) as caught:
                    self.m.gstack_state("run-one", self.root)
                self.assertEqual(caught.exception.code, "GSTACK_ISOLATION_CHANGED")
                self.assertEqual(config.read_bytes(), original + flipped.encode("utf-8"))
        config.write_bytes(original.replace(b"telemetry: off\n", b""))
        with self.assertRaises(self.m.StateError):
            self.m.gstack_state("run-one", self.root)

    def test_gstack_env_reentry_reads_values_like_gstack_config(self):
        # gstack-config: grep "^key:" | tail -1, "\n" lines only, quotes kept, exact compare.
        self.m.gstack_state("run-one", self.root)
        config = self.home("run-one") / "config.yaml"
        original = config.read_bytes()
        for flipped in (b"update_check: 'false'\n", b'telemetry: "off"\n',
                        b"update_check: true\rupdate_check: false\n",
                        "telemetry: community\u0085telemetry: off\n".encode("utf-8"),
                        "update_check: false \n".encode("utf-8")):  # Stricter than Gstack: fail closed.
            with self.subTest(flipped=flipped):
                config.write_bytes(original + flipped)
                with self.assertRaises(self.m.StateError) as caught:
                    self.m.gstack_state("run-one", self.root)
                self.assertEqual(caught.exception.code, "GSTACK_ISOLATION_CHANGED")
        config.write_bytes(original + b"telemetry:\toff \r\nupdate_check:false\x0b\x0c\n  update_check: true\n")
        self.assertEqual(self.m.gstack_state("run-one", self.root)["GSTACK_HOME"], self.home("run-one").as_posix())

    def test_gstack_env_distinct_runs_distinct_homes_no_colon(self):
        first = self.m.gstack_state("run:one", self.root)["GSTACK_HOME"]
        second = self.m.gstack_state("run:two", self.root)["GSTACK_HOME"]
        self.assertNotEqual(first, second)
        for value in (first, second):
            name = value.rsplit("/", 1)[1]
            self.assertRegex(name, r"\A[0-9a-f]{32}\Z")
            self.assertNotIn(":", value.split(":", 1)[1] if os.name == "nt" else value)

    def test_gstack_env_rejects_invalid_run_id(self):
        for bad in ("", "../escape", "a b", "-leading", "x" * 161, None, 7):
            with self.subTest(bad=bad), self.assertRaises(self.m.StateError) as caught:
                self.m.gstack_state(bad, self.root)
            self.assertEqual(caught.exception.code, "INVALID_IDENTIFIER")
        self.assertEqual(list(self.root.iterdir()), [])

    def test_gstack_env_refuses_linked_run_folder(self):
        personal = self.root / "personal-gstack"
        personal.mkdir()
        link = self.root / "state" / "gstack-runs"
        link.parent.mkdir()
        if os.name == "nt":
            import _winapi
            _winapi.CreateJunction(str(personal), str(link))  # No symlink privilege needed.
            self.addCleanup(os.rmdir, link)  # Remove only the junction, never its target.
        else:
            os.symlink(personal, link, target_is_directory=True)
            self.addCleanup(os.unlink, link)
        with self.assertRaises(self.m.StateError) as caught:
            self.m.gstack_state("run-one", link.parent)
        self.assertEqual(caught.exception.code, "GSTACK_HOME_REDIRECTED")
        self.assertEqual(list(personal.iterdir()), [])

    def test_gstack_env_cli_does_not_create_db(self):
        db = self.root / "nested" / "state.sqlite3"
        result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(SCRIPT), "gstack-env",
                                 "--run", "run:one", "--db", str(db)],
                                capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        out = json.loads(result.stdout)
        self.assertFalse(db.exists())
        self.assertEqual(sorted(p.name for p in db.parent.iterdir()), ["gstack-runs"])
        home = out["env"]["GSTACK_HOME"]
        self.assertEqual(home, (db.parent.resolve() / "gstack-runs" /
                                hashlib.sha256(b"run:one").hexdigest()[:32]).as_posix())
        self.assertEqual(out["export"], f"export GSTACK_HOME='{home}'; export GSTACK_STATE_DIR='{home}'; "
                         f"export GSTACK_STATE_ROOT='{home}'; export GSTACK_TELEMETRY_OFF=1")
        self.assertEqual(out["powershell"], f"$env:GSTACK_HOME='{home}'; $env:GSTACK_STATE_DIR='{home}'; "
                         f"$env:GSTACK_STATE_ROOT='{home}'; $env:GSTACK_TELEMETRY_OFF='1'")
        bad = subprocess.run([sys.executable, "-B", "-X", "utf8", str(SCRIPT), "--db", str(db),
                                 "gstack-env", "--run", "bad id"], capture_output=True, text=True,
                                encoding="utf-8", timeout=20)
        self.assertEqual((bad.returncode, json.loads(bad.stdout)), (2, {"error": "INVALID_IDENTIFIER"}))
        self.assertFalse(db.exists())

    def test_gstack_exports_quote_shell_metacharacters(self):
        env = {"GSTACK_HOME": "C:/it's $x", "GSTACK_STATE_DIR": "C:/it's $x",
               "GSTACK_STATE_ROOT": "C:/it's $x", "GSTACK_TELEMETRY_OFF": "1"}
        out = self.m.gstack_exports(env)
        self.assertTrue(out["export"].startswith("export GSTACK_HOME='C:/it'\\''s $x';"))
        self.assertTrue(out["powershell"].startswith("$env:GSTACK_HOME='C:/it''s $x';"))

    def test_gstack_handoff_flags_do_not_change_spec_digest(self):
        catalog = {"review": {"name": "review", "path": "/fixture/review/SKILL.md",
                              "description": "Pre-landing PR review. (gstack)"}}
        c = candidate(transport="orca")
        p = orchestrate.make_plan({"run_id": "gstack-run", "steps": [step(skills=["review"])]},
                                  catalog, {"candidates": [c], "tools": [], "observed_at": NOW},
                                  NOW, fixture_registry([c]))
        node = p["steps"][0]
        self.assertEqual(node["handoff"]["gstack_isolation"], "best-effort")
        # The handoff is part of the native Orca Task spec, so the brief reaches the worker.
        self.assertIn("gstack-env --run 'gstack-run'", self.m.task_spec(node))
        plain = copy.deepcopy(p)
        for key in ("gstack_isolation", "gstack_brief"):
            plain["steps"][0]["handoff"].pop(key)
        self.assertEqual(self.m.spec_digest(plain), self.m.spec_digest(p))


if __name__ == "__main__":
    unittest.main()
