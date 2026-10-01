"""Offline Codex CLI subscription adapter regressions; never launches a model."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import orchestrate
import run_state
import runtime_collect
from test_orchestrate import NOW, candidate, fixture_registry, step

SCRIPT = Path(__file__).with_name("execute_codex_cli.py")
LATER = "2026-09-23T10:10:00+00:00"


class FakeCodex:
    def __init__(self, executable, sha256, observed):
        self.executable, self.sha256, self.observed = executable, sha256, observed
        self.auth_reads, self.sends = 0, []
        self.failure = None
        self.events = None

    def check_binary(self):
        return None

    def auth(self, binding, env, now):
        self.auth_reads += 1
        return copy.deepcopy(self.observed)

    def send(self, argv, binding, env, prompt):
        self.sends.append((copy.deepcopy(argv), dict(env), prompt))
        if self.failure:
            raise self.failure
        return 0, json.dumps(self.events[0]).encode() + b"\n" + b"\n".join(
            json.dumps(event).encode() for event in self.events[1:]) + b"\n"


class CodexCliAdapterTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "Guarded Codex CLI adapter is missing")
        spec = importlib.util.spec_from_file_location("execute_codex_cli", SCRIPT)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.tmp = tempfile.TemporaryDirectory(prefix="vibe-codex-cli-test-")
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name).resolve()
        executable = root / "codex.exe"
        executable.write_bytes(b"offline fixture only")
        sha256 = hashlib.sha256(executable.read_bytes()).hexdigest()
        profile = root / "profile"
        profile.mkdir()
        profile_ref = runtime_collect.opaque("codex", str(profile))
        account_ref = runtime_collect.opaque("codex", profile_ref, "fixture@example.test")
        self.observed = {"account_verified": True, "account_ref": account_ref,
                         "profile_ref": profile_ref, "billing": {"mode": "subscription",
                             "credits": {"has_credits": False, "unlimited": False, "balance": "0"}},
                         "auth": {"method": "chatgpt", "plan": "plus"},
                         "models": [{"model": "fixture-gpt", "transport_efforts": ["low"]}]}
        self.binding = {"executable": str(executable), "executable_sha256": sha256,
                        "cwd": str(root), "profile_path": str(profile),
                        "profile_ref": profile_ref, "account_ref": account_ref,
                        "result_path": str(root / "result.jsonl"),
                        "content_path": str(root / "result.txt")}
        self.candidate = candidate("gpt", model="fixture-gpt", billing={
            "mode": "subscription", "verified": True, "extra_usage_enabled": False,
            "model_included": True, "included_model": "fixture-gpt",
            "api_fallback_disabled": True, "paid_credit_fallback_disabled": True,
            "credits": {"has_credits": False, "unlimited": False, "balance": "0"},
            "account_ref": account_ref})
        node = step("opening", surface="codex", skills=[], software=[],
                    task="Argue the independent position from supplied evidence", cli=self.binding)
        self.plan = orchestrate.make_plan({"run_id": "test-codex-cli", "steps": [node],
            "budget": {"max_attempts": 1}}, {}, {"candidates": [self.candidate], "tools": []},
            NOW, fixture_registry([self.candidate]))
        self.assertEqual(self.plan["status"], "ready", self.plan["errors"])
        self.store = run_state.Store(root / "state.sqlite3")
        self.store.initialize()
        self.store.register(self.plan, now=NOW)
        self.cli = FakeCodex(str(executable), sha256, self.observed)
        self.adapter = self.m.Adapter(self.store, self.cli, clock=lambda: NOW)
        self.certificate = {"verified": True, "subscription_only": True,
            "binding_sha256": self.m.binding_digest(self.plan, "opening"),
            "account_ref": account_ref, "profile_ref": profile_ref,
            "billing": copy.deepcopy(self.candidate["billing"]),
            "quota": copy.deepcopy(self.candidate["quota"]),
            "model": "fixture-gpt", "effort": "low", "observed_at": NOW,
            "valid_until": LATER, "evidence": ["fixture subscription-only proof"]}
        self.cli.events = [
            {"type": "thread.started", "thread_id": "fixture-thread"},
            {"type": "turn.started"},
            {"type": "item.completed", "item": {"id": "item_0", "type": "agent_message",
                                                 "text": "Independent position"}},
            {"type": "turn.completed", "usage": {"input_tokens": 12,
                                                   "output_tokens": 4}}]

    def test_subscription_guard_one_send_and_lookup_only_reentry(self):
        result = self.adapter.dispatch(self.plan, "opening", self.certificate)
        self.assertEqual(result["state"], "succeeded")
        self.assertFalse(result["verified"])
        self.assertIsNone(result["actual_usd"])
        self.assertEqual(len(self.cli.sends), 1)
        argv, env, prompt = self.cli.sends[0]
        self.assertEqual(argv[:2], [self.cli.executable, "exec"])
        for flag in ("--json", "--ephemeral", "--ignore-user-config", "read-only"):
            self.assertIn(flag, argv)
        self.assertEqual(argv[argv.index("-m") + 1], "fixture-gpt")
        self.assertIn('model_reasoning_effort="low"', argv)
        self.assertNotIn("OPENAI_API_KEY", env)
        self.assertIn("Argue the independent position", prompt)
        self.assertEqual(result["observation"]["thread_id"], "fixture-thread")
        self.assertEqual(self.adapter.dispatch(self.plan, "opening", None)["state"], "succeeded")
        self.assertEqual(len(self.cli.sends), 1)

    def test_missing_credit_proof_or_changed_auth_blocks_before_claim(self):
        for change in ({"paid_credit_fallback_disabled": None},
                       {"model_included": False}):
            with self.subTest(change=change):
                bad = copy.deepcopy(self.certificate)
                bad["billing"].update(change)
                with self.assertRaises(run_state.StateError):
                    self.adapter.dispatch(self.plan, "opening", bad)
        self.cli.observed["account_ref"] = "different"
        with self.assertRaises(run_state.StateError):
            self.adapter.dispatch(self.plan, "opening", self.certificate)
        self.assertEqual(self.store.snapshot()["attempts"], [])
        self.assertEqual(self.cli.sends, [])

    def test_fresh_account_purchased_credits_block_even_with_zero_spend_certificate(self):
        for billing_change in ({}, {"credits": None},
                               {"credits": {"has_credits": False, "unlimited": False,
                                            "balance": "0"}, "buckets": {"codex": {}}},
                               {"buckets": {"codex": {"credits": {
                                   "has_credits": False, "unlimited": False,
                                   "balance": "0"}}}},
                               {"credits": {"has_credits": True, "unlimited": False,
                                            "balance": "3.25"}},
                               {"buckets": {"codex": {"credits": {
                                   "has_credits": True, "unlimited": False,
                                   "balance": "3.25"}}}}):
            with self.subTest(billing_change=billing_change):
                self.cli.observed["billing"] = {"mode": "subscription", **billing_change}
                with self.assertRaisesRegex(run_state.StateError,
                                            "CODEX_PAID_CREDIT_EXPOSURE"):
                    self.adapter.dispatch(self.plan, "opening", self.certificate)
        self.assertEqual(self.store.snapshot()["attempts"], [])
        self.assertEqual(self.cli.sends, [])

    def test_unrepresentable_fresh_billing_buckets_block_before_send(self):
        for buckets in ({"premium/credits": {"credits": {"hasCredits": True,
                            "unlimited": False, "balance": "3.25"}}},
                        {"premium": ["malformed"]}, ["malformed"]):
            with self.subTest(buckets=buckets):
                raw = {"limits": {"rateLimits": {"limitId": "codex", "credits": {
                    "hasCredits": False, "unlimited": False, "balance": "0"}},
                    "rateLimitsByLimitId": buckets}}
                self.cli.auth = lambda binding, env, now: runtime_collect.normalize(
                    "codex", raw, now, binding["profile_path"])
                with self.assertRaisesRegex(runtime_collect.CollectorError,
                                            "billing-shape-unknown"):
                    self.adapter.dispatch(self.plan, "opening", self.certificate)
        self.assertEqual(self.store.snapshot()["attempts"], [])
        self.assertEqual(self.cli.sends, [])

    def test_conflicting_fresh_credit_balance_aliases_block_before_send(self):
        raw = {"account": {"account": {"type": "chatgpt", "planType": "plus",
                                    "email": "fixture@example.test"}},
               "models": {"data": [{"model": "fixture-gpt",
                                    "supportedReasoningEfforts": [{"reasoningEffort": "low"}]}]},
               "limits": {"rateLimits": {"limitId": "codex", "credits": {
                   "hasCredits": False, "unlimited": False,
                   "balance": {"val": "0", "value": "3.25"}}}}}
        self.cli.auth = lambda binding, env, now: runtime_collect.normalize(
            "codex", raw, now, binding["profile_path"])
        with self.assertRaisesRegex(run_state.StateError, "CODEX_PAID_CREDIT_EXPOSURE"):
            self.adapter.dispatch(self.plan, "opening", self.certificate)
        self.assertEqual(self.store.snapshot()["attempts"], [])
        self.assertEqual(self.cli.sends, [])

    def test_api_key_environment_is_never_forwarded(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "fixture-only",
                                     "CODEX_API_KEY": "fixture-only"}):
            self.adapter.dispatch(self.plan, "opening", self.certificate)
        env = self.cli.sends[0][1]
        self.assertNotIn("OPENAI_API_KEY", env)
        self.assertNotIn("CODEX_API_KEY", env)
        self.assertEqual(env["CODEX_HOME"], self.binding["profile_path"])

    def test_repo_workdir_is_not_a_private_debate_workspace(self):
        (Path(self.binding["cwd"]) / ".git").mkdir()
        with self.assertRaises(run_state.StateError):
            self.adapter.dispatch(self.plan, "opening", self.certificate)
        self.assertEqual(self.store.snapshot()["attempts"], [])
        self.assertEqual(self.cli.sends, [])

    def test_artifacts_outside_private_cwd_are_rejected_before_claim(self):
        nested_repo = Path(self.binding["cwd"]) / "public-repo"
        (nested_repo / ".git").mkdir(parents=True)
        for key, name in (("result_path", "result.jsonl"),
                          ("content_path", "result.txt")):
            with self.subTest(key=key):
                binding = {**self.binding, key: str(nested_repo / name)}
                node = step("opening", surface="codex", skills=[], software=[],
                            task="Argue the independent position from supplied evidence",
                            cli=binding)
                plan = orchestrate.make_plan({"run_id": "test-" + key,
                    "steps": [node], "budget": {"max_attempts": 1}}, {},
                    {"candidates": [self.candidate], "tools": []}, NOW,
                    fixture_registry([self.candidate]))
                self.assertEqual(plan["status"], "ready")
                store = run_state.Store(Path(self.binding["cwd"]) / ("state-" + key + ".sqlite3"))
                store.initialize()
                store.register(plan, now=NOW)
                adapter = self.m.Adapter(store, self.cli, clock=lambda: NOW)
                with self.assertRaisesRegex(run_state.StateError,
                                            "PRIVATE_CODEX_RESULTS_REQUIRED"):
                    adapter.context(plan, "opening")
                self.assertEqual(store.snapshot()["attempts"], [])
        self.assertEqual(self.store.snapshot()["attempts"], [])
        self.assertEqual(self.cli.sends, [])

    def test_tool_activity_is_not_accepted_or_retried(self):
        self.cli.events.insert(-1, {"type": "item.completed", "item": {"id": "item_x",
                                  "type": "command_execution", "command": "echo unsafe"}})
        result = self.adapter.dispatch(self.plan, "opening", self.certificate)
        self.assertEqual(result["state"], "uncertain")
        self.assertEqual(self.adapter.dispatch(self.plan, "opening", None)["state"],
                         "uncertain")
        self.assertEqual(len(self.cli.sends), 1)

    def test_failed_turn_and_unrecognized_event_are_not_accepted(self):
        for extra in ({"type": "turn.failed", "error": {"message": "fixture"}},
                      {"type": "future.unknown"}):
            with self.subTest(extra=extra), self.assertRaises(run_state.StateError):
                raw = b"\n".join(json.dumps(item).encode() for item in
                    [*self.cli.events[:-1], extra, self.cli.events[-1]]) + b"\n"
                self.m.parse_result(raw)

    def test_timeout_holds_original_intent_without_resend(self):
        self.cli.failure = TimeoutError("fixture timeout")
        result = self.adapter.dispatch(self.plan, "opening", self.certificate)
        self.assertEqual(result["state"], "uncertain")
        self.assertEqual(self.adapter.dispatch(self.plan, "opening", None)["state"],
                         "uncertain")
        self.assertEqual(len(self.cli.sends), 1)

    def test_result_tamper_is_rejected_without_resend(self):
        self.assertEqual(self.adapter.dispatch(self.plan, "opening", self.certificate)["state"],
                         "succeeded")
        Path(self.binding["content_path"]).write_text("changed", encoding="utf-8")
        with self.assertRaises(run_state.StateError):
            self.adapter.dispatch(self.plan, "opening", None)
        self.assertEqual(len(self.cli.sends), 1)

    def test_codex_rebuttal_binds_verified_cross_vendor_inputs(self):
        root = Path(self.tmp.name).resolve()
        claude = candidate("claude", surface="claude", model="fixture-claude",
                           billing={**candidate("claude")["billing"],
                                    "account_ref": "claude-account"})
        roles = {"proposer": "gpt-open", "challenger": "claude-open",
                 "proposer_rebuttal": "gpt-rebuttal",
                 "challenger_rebuttal": "claude-rebuttal", "judge": "claude-judge"}
        binding = {**self.binding, "result_path": str(root / "rebuttal.jsonl"),
                   "content_path": str(root / "rebuttal.txt")}
        steps = [step("gpt-open", surface="codex", skills=[]),
                 step("claude-open", surface="claude", skills=[]),
                 step("gpt-rebuttal", surface="codex", skills=[], software=[],
                      task="Rebut the other opening", depends_on=["gpt-open", "claude-open"],
                      cli=binding),
                 step("claude-rebuttal", surface="claude", skills=[],
                      depends_on=["gpt-open", "claude-open"]),
                 step("claude-judge", surface="claude", skills=[],
                      depends_on=["gpt-rebuttal", "claude-rebuttal"])]
        plan = orchestrate.make_plan({"run_id": "test-codex-debate", "steps": steps,
             "debate": roles, "budget": {"max_attempts": 1}}, {},
             {"candidates": [self.candidate, claude], "tools": []}, NOW,
             fixture_registry([self.candidate, claude]))
        self.assertEqual(plan["status"], "ready", plan["errors"])
        store = run_state.Store(root / "debate.sqlite3")
        store.initialize()
        store.register(plan, now=NOW)
        for node_id, content, model in (("gpt-open", "GPT opening", "fixture-gpt"),
                                        ("claude-open", "Claude opening", "fixture-claude")):
            path = root / (node_id + ".txt")
            raw = content.encode()
            path.write_bytes(raw)
            claim = store.claim(plan["run_id"], node_id, "fixture-" + node_id,
                                plan["plan_digest"], now=NOW)
            handle = {"kind": "fixture", "id": node_id, "identity": "fixture"}
            store.bind(claim["dispatch_id"], handle, now=NOW)
            store.observe(claim["dispatch_id"], {"state": "succeeded", "handle": handle,
                "observed_at": NOW, "evidence": ["fixture input"], "resolved_model": model,
                "effective_effort": "low", "content_path": str(path),
                "content_sha256": hashlib.sha256(raw).hexdigest(),
                "content_format": "text/plain;charset=utf-8"}, now=NOW)
            store.settle(claim["dispatch_id"], "0", ["fixture receipt"], now=NOW)
            store.verify(claim["dispatch_id"], ["fixture acceptance"], now=NOW)
        adapter = self.m.Adapter(store, self.cli, clock=lambda: NOW)
        route = next(n["route"] for n in plan["steps"] if n["id"] == "gpt-rebuttal")
        certificate = {**self.certificate,
            "binding_sha256": self.m.binding_digest(plan, "gpt-rebuttal"),
            "billing": route["billing"], "quota": route["quota"],
            "inputs_sha256": self.m.execute_cli.input_digest(plan, "gpt-rebuttal", store),
            "cross_vendor_transfer_authorized": True}
        result = adapter.dispatch(plan, "gpt-rebuttal", certificate)
        self.assertEqual(result["state"], "succeeded")
        self.assertEqual(result["observation"]["inputs_sha256"], certificate["inputs_sha256"])
        self.assertIn("Claude opening", self.cli.sends[-1][2])
        self.assertNotIn("Claude opening", str(self.cli.sends[-1][0]))
        self.assertEqual(adapter.dispatch(plan, "gpt-rebuttal", None)["state"], "succeeded")
        self.assertEqual(len(self.cli.sends), 1)


if __name__ == "__main__":
    unittest.main()
