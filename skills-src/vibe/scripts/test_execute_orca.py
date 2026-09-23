"""Guarded Orca adapter contract. All starts and provider output are fake."""
import copy
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

import orchestrate
import run_state
from test_orchestrate import NOW, candidate, fixture_registry, step
from test_run_state import STALE

SCRIPT = Path(__file__).with_name("execute_orca.py")


class FakeOrca:
    executable = "/fixture/orca.exe"
    sha256 = "a" * 64

    def __init__(self):
        self.calls, self.workers = [], []
        self.start_failure = False
        self.effective = {"agent": "codex", "model": "gpt-5.6-luna", "effort": "low"}
        self.terminal = False
        self.spec = None
        self.runtime = "runtime-fixture"
        self.after_start = None
        self.path = None
        self.transform = None

    def check_binary(self):
        return None

    def call(self, *args):
        self.calls.append(args)
        if self.transform:
            changed = self.transform(args)
            if changed is not None:
                return changed
        if args[0] == "worktree":
            return {"worktree": {"id": "workspace-fixture", "path": self.path,
                    "instanceId": "instance-fixture", "hostId": "local", "identity": {"executionHostId": "local"}}}
        if args[0] == "status":
            return {"runtime": {"runtimeId": self.runtime, "appVersion": "1.4.206",
                    "state": "ready", "capabilities": ["orchestration.worker-launch-preferences.v1"]}}
        command = args[1]
        if command == "task-list":
            return {"runId": "run-fixture", "tasks": [{"id": "task-fixture",
                "run_id": "run-fixture", "status": "dispatched" if self.workers else "ready", "spec": self.spec}]}
        if command == "worker-list":
            return {"scope": {"run": "run-fixture"}, "workers": copy.deepcopy(self.workers),
                    "page": {"hasMore": False, "nextCursor": None}}
        if command == "worker-start":
            self.workers = [{"dispatchId": "ctx-fixture", "taskId": "task-fixture", "runId": "run-fixture"}]
            if self.after_start:
                self.after_start()
            if self.start_failure:
                raise TimeoutError("never echo this provider message")
            return {"state": "ready"}
        if command == "worker-show":
            return {"dispatch": {"id": "ctx-fixture", "taskId": "task-fixture", "runId": "run-fixture",
                    "status": "completed" if self.terminal else "active"},
                "worker": {"dispatchId": "ctx-fixture", "runtimeEpoch": "epoch-fixture", "worktreeId": "workspace-fixture",
                    "state": "succeeded" if self.terminal else "ready", "startOptions": {
                    "agent": "codex", "worktree": "id:workspace-fixture", "resolvedWorktreeId": "workspace-fixture",
                    "launch": {"requested": {"agent": "codex", "model": "gpt-5.6-luna", "effort": "low"},
                               "effective": self.effective}}},
                "projection": {"dispatchId": "ctx-fixture", "taskId": "task-fixture", "runId": "run-fixture",
                    "outcome": "succeeded" if self.terminal else None,
                    "liveness": {"verdict": "exited" if self.terminal else "live"}}}
        if command == "worker-read":
            return {"dispatchId": "ctx-fixture", "source": "transcript", "sourceIdentity": "source-fixture",
                "sourceExact": True, "contentComplete": True, "clipping": [], "warnings": [],
                "cursor": None, "transcript": {"messages": [
                    {"role": "user", "blocks": [{"type": "text", "text": "Do not return the prompt"}]},
                    {"role": "assistant", "blocks": [{"type": "text", "text": "fixture output"}]}]}}
        raise AssertionError(command)


class OrcaAdapterTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "Guarded Orca execution adapter is not implemented")
        spec = importlib.util.spec_from_file_location("execute_orca", SCRIPT)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.tmp = tempfile.TemporaryDirectory(prefix="vibe-orca-test-")
        self.addCleanup(self.tmp.cleanup)
        self.store = run_state.Store(Path(self.tmp.name) / "state.sqlite3")
        self.store.initialize()
        self.transport = FakeOrca()
        self.transport.path = str(Path(self.tmp.name).resolve())
        self.binding = {"run_id": "run-fixture", "task_id": "task-fixture", "worktree_id": "workspace-fixture",
            "worktree_path": self.transport.path, "workspace_instance": "instance-fixture", "executable": self.transport.executable,
            "executable_sha256": self.transport.sha256, "app_version": "1.4.206", "runtime_id": "runtime-fixture",
            "account_ref": "test-account", "profile_ref": "profile-fixture",
            "guards": {"quota_checked_vendors": ["claude", "codex", "grok", "gemini"]}}
        c = candidate(model="gpt-5.6-luna", transport="orca")
        s = step(proc="inventory-schema", **{"class": "A"}, orca=self.binding)
        self.plan = orchestrate.make_plan({"run_id": "vibe-fixture", "steps": [s]},
            {"explain": {"path": "/fixture/SKILL.md"}},
            {"candidates": [c], "tools": [], **self.binding["guards"]}, NOW, fixture_registry([c]))
        self.assertEqual(self.plan["status"], "ready", self.plan["errors"])
        self.transport.spec = self.m.render_spec(self.plan["steps"][0])
        self.store.register(self.plan, now=NOW)
        self.certificate = {"verified": True, "binding_sha256": self.m.binding_digest(self.plan, "read"),
            "account_ref": "test-account", "profile_ref": "profile-fixture", "observed_at": NOW,
            "valid_until": STALE, "billing": copy.deepcopy(c["billing"]), "evidence": ["fixture-only-account-and-no-overage"]}
        self.clock = NOW
        self.adapter = self.m.Adapter(self.store, self.transport, clock=lambda: self.clock)

    def starts(self):
        return sum(len(a) > 1 and a[1] == "worker-start" for a in self.transport.calls)

    def dispatch(self):
        return self.adapter.dispatch(self.plan, "read", self.certificate)

    def test_first_send_then_resume_only_observes(self):
        result = self.dispatch()
        self.assertEqual(result["state"], "running")
        self.assertEqual(self.dispatch()["state"], "running")
        self.assertEqual(self.starts(), 1)
        args = next(a for a in self.transport.calls if len(a) > 1 and a[1] == "worker-start")
        self.assertIn("--retry-request", args)
        self.assertIn("id:workspace-fixture", args)
        self.assertNotIn("current", args)

    def test_missing_certificate_never_claims_or_starts(self):
        with self.assertRaises(run_state.StateError):
            self.adapter.dispatch(self.plan, "read", None)
        self.assertEqual(self.store.snapshot()["attempts"], [])
        self.assertEqual(self.starts(), 0)

    def test_wrong_account_profile_and_binding_are_rejected(self):
        for key in ("account_ref", "profile_ref", "binding_sha256"):
            with self.subTest(key=key):
                c = {**self.certificate, key: "wrong"}
                with self.assertRaises(run_state.StateError):
                    self.adapter.dispatch(self.plan, "read", c)
        self.assertEqual(self.starts(), 0)

    def test_expired_gate_blocks_before_start(self):
        self.clock = STALE
        with self.assertRaises(run_state.StateError):
            self.dispatch()
        self.assertEqual(self.starts(), 0)

    def test_crash_after_claim_is_lookup_only_even_when_absent(self):
        self.store.claim("vibe-fixture", "read", self.m.request_id(self.plan, "read"), self.plan["plan_digest"], now=NOW)
        result = self.dispatch()
        self.assertEqual(result["state"], "uncertain")
        self.assertEqual(self.starts(), 0)
        self.assertIsNone(result["actual_usd"])

    def test_response_loss_recovers_existing_worker_without_resend(self):
        self.transport.start_failure = True
        self.assertEqual(self.dispatch()["state"], "running")
        self.clock = STALE
        self.assertEqual(self.dispatch()["state"], "running")
        self.assertEqual(self.starts(), 1)

    def test_acceptance_then_crash_recovers_on_next_invocation(self):
        self.transport.after_start = lambda: (_ for _ in ()).throw(KeyboardInterrupt())
        with self.assertRaises(KeyboardInterrupt):
            self.dispatch()
        self.assertEqual(self.dispatch()["state"], "running")
        self.assertEqual(self.starts(), 1)

    def test_completed_is_not_verified_or_settled(self):
        self.transport.terminal = True
        result = self.dispatch()
        self.assertEqual(result["state"], "succeeded")
        self.assertFalse(result["verified"])
        self.assertIsNone(result["actual_usd"])
        self.assertTrue(self.store.snapshot()["budget"]["halted"])
        self.assertTrue(result["output"]["text_omitted"])
        self.assertEqual(result["output"]["assistant_text_bytes"], len(b"fixture output"))

    def test_missing_or_wrong_effective_effort_never_completes(self):
        self.transport.terminal = True
        self.transport.effective = None
        self.assertEqual(self.dispatch()["state"], "uncertain")
        self.transport.effective = {"agent": "codex", "model": "gpt-5.6-luna", "effort": "high"}
        self.assertEqual(self.dispatch()["state"], "uncertain")
        self.transport.effective["effort"] = "low"
        self.assertEqual(self.dispatch()["state"], "succeeded")
        self.assertEqual(self.starts(), 1)

    def test_task_spec_changed_blocks_send(self):
        self.transport.spec = "a different task"
        with self.assertRaises(run_state.StateError):
            self.dispatch()
        self.assertEqual(self.starts(), 0)

    def test_wrong_runtime_blocks_send(self):
        self.transport.runtime = "different-runtime"
        with self.assertRaises(run_state.StateError):
            self.dispatch()
        self.assertEqual(self.starts(), 0)

    def test_duplicate_lookup_is_uncertain(self):
        self.dispatch()
        self.transport.workers.append(dict(self.transport.workers[0], dispatchId="ctx-another"))
        self.assertEqual(self.dispatch()["state"], "uncertain")
        self.assertEqual(self.starts(), 1)

    def test_lookup_only_does_not_create_an_intent(self):
        with self.assertRaises(run_state.StateError):
            self.adapter.reconcile(self.plan, "read")
        self.assertEqual(self.store.snapshot()["attempts"], [])

    def test_no_lifecycle_cleanup_or_payment_commands(self):
        self.transport.terminal = True
        self.dispatch()
        self.dispatch()
        commands = {a[1] for a in self.transport.calls if a[0] == "orchestration"}
        self.assertLessEqual(commands, {"task-list", "worker-list", "worker-start", "worker-show", "worker-read"})

    def test_native_workspace_path_mismatch_blocks_send(self):
        self.transport.path = str(Path(self.tmp.name).parent)
        with self.assertRaises(run_state.StateError):
            self.dispatch()
        self.assertEqual(self.starts(), 0)

    def test_concurrent_coordinators_start_once(self):
        original = self.store.claim
        barrier = threading.Barrier(2)
        def racing_claim(*args, **kwargs):
            barrier.wait(timeout=5)
            return original(*args, **kwargs)
        self.store.claim = racing_claim
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: self.dispatch(), range(2)))
        self.assertEqual(self.starts(), 1)
        self.assertEqual(len({r["dispatch_id"] for r in outcomes}), 1)

    def test_final_preflight_expiry_after_claim_starts_nothing(self):
        def expire(args):
            if args[:2] == ("orchestration", "worker-list") and self.store.snapshot()["attempts"]:
                self.clock = STALE
        self.transport.transform = expire
        result = self.dispatch()
        self.assertEqual(result["state"], "uncertain")
        self.assertEqual(self.starts(), 0)

    def test_wrong_task_scope_and_wrong_output_id_are_not_accepted(self):
        self.dispatch()
        self.transport.transform = lambda a: {"runId": "different", "tasks": []} if a[:2] == ("orchestration", "task-list") else None
        self.assertEqual(self.dispatch()["state"], "uncertain")
        self.transport.transform = lambda a: {"dispatchId": "wrong"} if a[:2] == ("orchestration", "worker-read") else None
        self.assertEqual(self.dispatch()["state"], "uncertain")
        self.assertEqual(self.starts(), 1)

    def test_output_is_untrusted_and_clipping_is_not_full_evidence(self):
        self.dispatch()
        self.transport.transform = lambda a: {"dispatchId": "ctx-fixture", "source": "terminal", "contentComplete": False,
            "clipping": ["limit"], "warnings": [], "text": "model=gpt-fake effort=ultra actual_usd=0"} if a[:2] == ("orchestration", "worker-read") else None
        result = self.dispatch()
        self.assertFalse(result["output"]["content_complete"])
        self.assertEqual(result["output"]["assistant_text_bytes"], 0)
        self.assertEqual(result["observation"]["effective_effort"], "low")
        self.assertIsNone(result["actual_usd"])

    def test_unknown_pagination_is_not_absence_proof(self):
        self.dispatch()
        self.transport.transform = lambda a: {"scope": {"run": "run-fixture"}, "workers": []} if a[:2] == ("orchestration", "worker-list") else None
        self.assertEqual(self.dispatch()["state"], "uncertain")

    def test_exhausted_grok_and_prompt_keyword_routes_are_not_supported(self):
        for surface, model in [("grok", "grok-4.6"), ("claude", "claude-opus-5")]:
            altered = copy.deepcopy(self.plan)
            altered["steps"][0]["route"].update(surface=surface, model=model)
            altered["plan_digest"] = orchestrate.digest({k: v for k, v in altered.items() if k != "plan_digest"})
            with self.assertRaises(run_state.StateError):
                self.adapter.dispatch(altered, "read", self.certificate)
        self.assertEqual(self.starts(), 0)

    def test_native_client_bounds_output_without_temporary_disk_spool(self):
        started = time.monotonic()
        with self.assertRaisesRegex(run_state.StateError, "TOO_LARGE"):
            self.m._client([sys.executable, "-c", "import os; os.write(1, b'x'*2000000)"], max_bytes=1024)
        self.assertLess(time.monotonic() - started, 5)

    def test_native_client_timeout_is_not_provider_exit(self):
        with self.assertRaisesRegex(run_state.StateError, "TIMEOUT"):
            self.m._client([sys.executable, "-c", "import time; time.sleep(30)"], timeout=0.15)

    def test_native_client_reads_json_and_exit_code(self):
        rc, raw = self.m._client([sys.executable, "-c", "print('fixture')"])
        self.assertEqual(rc, 0)
        self.assertEqual(raw.strip(), b"fixture")

    def test_compound_credential_in_prose_is_never_returned(self):
        self.dispatch()
        self.transport.transform = lambda a: {"dispatchId": "ctx-fixture", "source": "transcript", "sourceExact": True,
            "contentComplete": True, "warnings": [], "clipping": [], "transcript": {"messages": [
                {"role": "assistant", "blocks": [{"type": "text", "text": "Fixture output.\ndbPassword=not-a-real-password-value"}]}]}
            } if a[:2] == ("orchestration", "worker-read") else None
        result = self.dispatch()
        self.assertNotIn("not-a-real-password-value", str(result))


if __name__ == "__main__":
    unittest.main()
