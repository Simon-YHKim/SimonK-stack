"""Claude subscription CLI adapter fixtures; no provider generation is launched."""
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

SCRIPT = Path(__file__).with_name("execute_cli.py")
LATER = "2026-09-23T10:10:00+00:00"


class FakeClaude:
    def __init__(self, executable, sha256, auth):
        self.executable, self.sha256, self.auth_result = executable, sha256, auth
        self.auth_reads, self.auth_envs, self.sends = 0, [], []
        self.response = None
        self.failure = None
        self.after_auth = None

    def check_binary(self):
        return None

    def auth(self, binding, env, now):
        self.auth_reads += 1
        self.auth_envs.append(dict(env))
        if self.after_auth:
            self.after_auth(self.auth_reads)
        return self.auth_result

    def send(self, argv, binding, env, prompt):
        self.sends.append((copy.deepcopy(argv), dict(env), prompt))
        if self.failure:
            raise self.failure
        if isinstance(self.response, dict):
            response = {**self.response, "session_id": argv[argv.index("--session-id") + 1]}
            return 0, json.dumps(response).encode()
        return 0, self.response


class ClaudeCliAdapterTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "Guarded subscription CLI adapter is missing")
        spec = importlib.util.spec_from_file_location("execute_cli", SCRIPT)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.tmp = tempfile.TemporaryDirectory(prefix="vibe-cli-test-")
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name).resolve()
        executable = root / "claude.exe"
        executable.write_bytes(b"offline fixture only")
        sha256 = hashlib.sha256(executable.read_bytes()).hexdigest()
        profile = root / "profile"
        profile.mkdir()
        observed = runtime_collect.normalize("claude", {"loggedIn": True,
            "authMethod": "claude.ai", "apiProvider": "firstParty", "subscriptionType": "max",
            "email": "fixture@example.test"}, NOW, str(profile))
        self.binding = {"executable": str(executable), "executable_sha256": sha256,
            "cwd": str(root), "profile_path": str(profile), "profile_ref": observed["profile_ref"],
            "account_ref": observed["account_ref"], "result_path": str(root / "result.json")}
        c = candidate("claude", surface="claude", model="fixture-claude",
                      billing={"mode": "subscription", "verified": True,
                          "extra_usage_enabled": False, "model_included": True,
                          "included_model": "fixture-claude", "api_fallback_disabled": True,
                          "account_ref": observed["account_ref"]})
        s = step("opening", surface="claude", skills=[], software=[],
                 task="Argue the independent position from supplied evidence", cli=self.binding)
        self.plan = orchestrate.make_plan({"run_id": "test-cli", "steps": [s],
            "budget": {"max_attempts": 1}}, {}, {"candidates": [c], "tools": []}, NOW,
            fixture_registry([c]))
        self.assertEqual(self.plan["status"], "ready", self.plan["errors"])
        self.store = run_state.Store(root / "state.sqlite3")
        self.store.initialize()
        self.store.register(self.plan, now=NOW)
        self.cli = FakeClaude(str(executable), sha256, observed)
        self.adapter = self.m.Adapter(self.store, self.cli, clock=lambda: NOW)
        self.certificate = {"verified": True, "subscription_only": True,
            "binding_sha256": self.m.binding_digest(self.plan, "opening"),
            "account_ref": observed["account_ref"], "profile_ref": observed["profile_ref"],
            "billing": copy.deepcopy(c["billing"]), "quota": copy.deepcopy(c["quota"]),
            "model": "fixture-claude", "effort": "low", "observed_at": NOW,
            "valid_until": LATER, "evidence": ["fixture account, model and extra-usage settings"]}
        self.cli.response = {"type": "result", "is_error": False,
            "result": "Independent position", "modelUsage": {"fixture-claude": {"inputTokens": 1}}}

    def debate_plan(self):
        root = Path(self.tmp.name).resolve()
        claude = candidate("claude", surface="claude", model="fixture-claude",
            billing=copy.deepcopy(self.certificate["billing"]))
        gpt = candidate("gpt", surface="codex", model="fixture-gpt",
            billing={**candidate("gpt")["billing"], "account_ref": "gpt-account"})
        roles = {"proposer": "gpt-open", "challenger": "claude-open",
                 "proposer_rebuttal": "gpt-rebuttal", "challenger_rebuttal": "claude-rebuttal",
                 "judge": "claude-judge"}
        def claude_step(node_id, dependencies):
            binding = {**self.binding, "result_path": str(root / (node_id + ".json"))}
            return step(node_id, surface="claude", skills=[], software=[],
                        task="Debate the supplied positions", depends_on=dependencies, cli=binding)
        steps = [step("gpt-open", surface="codex", skills=[]),
                 claude_step("claude-open", []),
                 step("gpt-rebuttal", surface="codex", skills=[],
                      depends_on=["gpt-open", "claude-open"]),
                 claude_step("claude-rebuttal", ["gpt-open", "claude-open"]),
                 claude_step("claude-judge", ["gpt-rebuttal", "claude-rebuttal"])]
        self.plan = orchestrate.make_plan({"run_id": "test-debate-cli", "steps": steps,
            "debate": roles, "budget": {"max_attempts": 1}}, {},
            {"candidates": [claude, gpt], "tools": []}, NOW, fixture_registry([claude, gpt]))
        self.assertEqual(self.plan["status"], "ready", self.plan["errors"])
        self.store = run_state.Store(root / "debate-state.sqlite3")
        self.store.initialize()
        self.store.register(self.plan, now=NOW)
        self.adapter = self.m.Adapter(self.store, self.cli, clock=lambda: NOW)
        return roles

    def record_gpt(self, node_id, text):
        root = Path(self.tmp.name).resolve()
        path = root / (node_id + ".txt")
        raw = text.encode("utf-8")
        path.write_bytes(raw)
        attempt = self.store.claim(self.plan["run_id"], node_id, "req-" + node_id,
                                   self.plan["plan_digest"], now=NOW)
        handle = {"kind": "fixture-gpt", "id": node_id, "identity": "fixture"}
        self.store.bind(attempt["dispatch_id"], handle, now=NOW)
        self.store.observe(attempt["dispatch_id"], {"state": "succeeded", "handle": handle,
            "observed_at": NOW, "evidence": ["fixture content checked"],
            "resolved_model": "fixture-gpt", "effective_effort": "low",
            "content_path": str(path), "content_sha256": hashlib.sha256(raw).hexdigest(),
            "content_format": "text/plain;charset=utf-8"}, now=NOW)
        self.store.settle(attempt["dispatch_id"], "0", ["fixture nonmetered receipt"], now=NOW)
        self.store.verify(attempt["dispatch_id"], ["fixture content accepted"], now=NOW)
        return path

    def debate_certificate(self, node_id):
        node = next(n for n in self.plan["steps"] if n["id"] == node_id)
        certificate = {**self.certificate,
            "binding_sha256": self.m.binding_digest(self.plan, node_id),
            "billing": node["route"]["billing"], "quota": node["route"]["quota"]}
        if node["depends_on"]:
            certificate["inputs_sha256"] = self.m.input_digest(self.plan, node_id, self.store)
            certificate["cross_vendor_transfer_authorized"] = True
        return certificate

    def record_claude_opening(self, text="Claude independent position"):
        self.cli.response["result"] = text
        self.adapter.dispatch(self.plan, "claude-open", self.debate_certificate("claude-open"))
        opening = next(a for a in self.store.snapshot()["attempts"] if a["node_id"] == "claude-open")
        self.store.settle(opening["dispatch_id"], "0", ["fixture included-use receipt"], now=NOW)
        self.store.verify(opening["dispatch_id"], ["fixture position accepted"], now=NOW)

    def test_one_send_same_intent_reentry_never_resends(self):
        result = self.adapter.dispatch(self.plan, "opening", self.certificate)
        self.assertEqual(result["state"], "succeeded")
        self.assertEqual(result["verified"], False)
        self.assertIsNone(result["actual_usd"])
        self.assertEqual(len(self.cli.sends), 1)
        argv, env, prompt = self.cli.sends[0]
        self.assertIn("--safe-mode", argv)
        self.assertIn("--strict-mcp-config", argv)
        self.assertEqual(argv[argv.index("--tools") + 1], "")
        self.assertEqual(argv[argv.index("--model") + 1], "fixture-claude")
        self.assertEqual(argv[argv.index("--effort") + 1], "low")
        self.assertNotEqual(argv[argv.index("--session-id") + 1], self.m.request_id(self.plan, "opening"))
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertIn("Argue the independent position", prompt)
        self.assertEqual(self.adapter.dispatch(self.plan, "opening", None)["state"], "succeeded")
        self.assertEqual(len(self.cli.sends), 1)
        self.assertTrue(Path(self.binding["result_path"]).is_file())

    def test_missing_certificate_or_wrong_auth_blocks_before_claim(self):
        with self.assertRaises(run_state.StateError):
            self.adapter.dispatch(self.plan, "opening", None)
        self.assertEqual(self.store.snapshot()["attempts"], [])
        self.assertEqual(self.cli.sends, [])
        self.cli.auth_result = {**self.cli.auth_result, "account_ref": "other"}
        with self.assertRaises(run_state.StateError):
            self.adapter.dispatch(self.plan, "opening", self.certificate)
        self.assertEqual(self.store.snapshot()["attempts"], [])
        self.assertEqual(self.cli.sends, [])

    def test_api_environment_is_removed_in_both_auth_and_send(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "never-forward-fixture",
                                  "CLAUDE_CODE_USE_BEDROCK": "1", "ANTHROPIC_BASE_URL": "https://fixture.invalid"}):
            self.adapter.dispatch(self.plan, "opening", self.certificate)
        for env in [*self.cli.auth_envs, self.cli.sends[0][1]]:
            for key in ("ANTHROPIC_API_KEY", "CLAUDE_CODE_USE_BEDROCK", "ANTHROPIC_BASE_URL"):
                self.assertNotIn(key, env)

    def test_ambiguous_response_holds_intent_without_retry(self):
        self.cli.response = {"type": "result", "is_error": False,
            "result": "Position", "modelUsage": {"unrelated-model": {}}}
        result = self.adapter.dispatch(self.plan, "opening", self.certificate)
        self.assertEqual(result["state"], "uncertain")
        self.assertEqual(len(self.cli.sends), 1)
        self.assertEqual(self.adapter.dispatch(self.plan, "opening", self.certificate)["state"], "uncertain")
        self.assertEqual(len(self.cli.sends), 1)

    def test_cli_failure_holds_intent_without_retry(self):
        self.cli.failure = TimeoutError("fixture timeout")
        result = self.adapter.dispatch(self.plan, "opening", self.certificate)
        self.assertEqual(result["state"], "uncertain")
        self.assertEqual(len(self.cli.sends), 1)
        self.assertEqual(self.adapter.dispatch(self.plan, "opening", None)["state"], "uncertain")
        self.assertEqual(len(self.cli.sends), 1)

    def test_result_collision_after_claim_blocks_send(self):
        def collide(auth_reads):
            if auth_reads == 2:
                Path(self.binding["result_path"]).write_text("{}", encoding="utf-8")
        self.cli.after_auth = collide
        result = self.adapter.dispatch(self.plan, "opening", self.certificate)
        self.assertEqual(result["state"], "not_started")
        self.assertEqual(self.cli.sends, [])

    def test_result_tamper_is_not_accepted_on_reentry(self):
        self.assertEqual(self.adapter.dispatch(self.plan, "opening", self.certificate)["state"], "succeeded")
        Path(self.binding["result_path"]).write_text("{}", encoding="utf-8")
        with self.assertRaises(run_state.StateError):
            self.adapter.dispatch(self.plan, "opening", None)
        self.assertEqual(len(self.cli.sends), 1)

    def test_debate_rebuttal_uses_verified_cross_vendor_outputs(self):
        self.debate_plan()
        self.record_gpt("gpt-open", "GPT independent objection")
        self.record_claude_opening()
        certificate = self.debate_certificate("claude-rebuttal")
        self.cli.response["result"] = "Claude rebuttal"
        result = self.adapter.dispatch(self.plan, "claude-rebuttal", certificate)
        self.assertEqual(result["state"], "succeeded")
        argv, _, prompt = self.cli.sends[-1]
        self.assertNotIn("GPT independent objection", str(argv))
        self.assertIn("GPT independent objection", prompt)
        self.assertIn("Claude independent position", prompt)
        self.assertIn("challenger_rebuttal", prompt)
        self.assertEqual(result["observation"]["inputs_sha256"], certificate["inputs_sha256"])
        self.assertEqual(self.adapter.dispatch(self.plan, "claude-rebuttal", None)["state"], "succeeded")
        self.assertEqual(len(self.cli.sends), 2)

    def test_unverified_or_tampered_debate_input_never_sends(self):
        self.debate_plan()
        path = self.record_gpt("gpt-open", "GPT opening")
        with self.assertRaises(run_state.StateError):
            self.adapter.dispatch(self.plan, "claude-rebuttal", self.debate_certificate("claude-open"))
        self.assertEqual(self.cli.sends, [])
        path.write_text("changed", encoding="utf-8")
        with self.assertRaises(run_state.StateError):
            self.m.input_digest(self.plan, "claude-rebuttal", self.store)
        self.assertEqual(self.cli.sends, [])

    def test_judge_reads_both_positions_and_rebuttals_only_after_verification(self):
        self.debate_plan()
        self.record_gpt("gpt-open", "GPT opening")
        self.record_claude_opening("Claude opening")
        self.record_gpt("gpt-rebuttal", "GPT rebuttal")
        with self.assertRaises(run_state.StateError):
            self.m.input_digest(self.plan, "claude-judge", self.store)
        self.cli.response["result"] = "Claude rebuttal"
        self.adapter.dispatch(self.plan, "claude-rebuttal", self.debate_certificate("claude-rebuttal"))
        rebuttal = next(a for a in self.store.snapshot()["attempts"] if a["node_id"] == "claude-rebuttal")
        self.store.settle(rebuttal["dispatch_id"], "0", ["fixture included-use receipt"], now=NOW)
        self.store.verify(rebuttal["dispatch_id"], ["fixture rebuttal accepted"], now=NOW)
        certificate = self.debate_certificate("claude-judge")
        withheld = {**certificate, "cross_vendor_transfer_authorized": False}
        with self.assertRaises(run_state.StateError):
            self.adapter.dispatch(self.plan, "claude-judge", withheld)
        self.assertEqual(len(self.cli.sends), 2)
        self.cli.response["result"] = "Separate judge verdict"
        result = self.adapter.dispatch(self.plan, "claude-judge", certificate)
        self.assertEqual(result["state"], "succeeded")
        self.assertTrue(result["observation"]["judge_vendor_overlap"])
        prompt = self.cli.sends[-1][2]
        for expected in ("GPT opening", "Claude opening", "GPT rebuttal", "Claude rebuttal", '"role":"judge"'):
            self.assertIn(expected, prompt)
        self.assertEqual(len(self.cli.sends), 3)

    def test_dependent_spec_never_prints_prior_model_prose(self):
        self.debate_plan()
        self.record_gpt("gpt-open", "GPT private prose")
        self.record_claude_opening("Claude private prose")
        plan_file = Path(self.tmp.name) / "plan.json"
        plan_file.write_text(json.dumps(self.plan), encoding="utf-8")
        with patch("builtins.print") as output:
            code = self.m.main(["spec", "--plan", str(plan_file),
                                "--node", "claude-rebuttal", "--db", str(self.store.path)])
        self.assertEqual(code, 2)
        self.assertNotIn("prior_positions", str(output.call_args_list))
        self.assertNotIn("private prose", str(output.call_args_list))

    def test_dependent_prose_quote_and_long_stdin_are_supported(self):
        self.debate_plan()
        self.record_gpt("gpt-open", '"Quoted opening prose, not a JSON document.')
        self.record_claude_opening("C" * 14000)
        self.cli.response["result"] = "rebuttal"
        result = self.adapter.dispatch(self.plan, "claude-rebuttal",
                                       self.debate_certificate("claude-rebuttal"))
        self.assertEqual(result["state"], "succeeded")
        argv, _, prompt = self.cli.sends[-1]
        self.assertLess(len(" ".join(argv)), 2000)
        self.assertGreater(len(prompt), 14000)
        self.assertIn('"Quoted opening prose', prompt)

    def test_quoted_prose_cannot_hide_structured_sensitive_key(self):
        for content in ('"Note {"session":"abc"}',
                        '"Note accessToken=abc1234', '"Note session: abc',
                        '"Note "session" = abc'):
            with self.subTest(content=content), self.assertRaises(run_state.StateError) as error:
                self.m.checked_position(content)
            self.assertEqual(error.exception.code, "SENSITIVE_PAYLOAD")

    def test_reconcile_uses_persisted_digest_after_predecessor_disappears(self):
        self.debate_plan()
        path = self.record_gpt("gpt-open", "GPT opening")
        self.record_claude_opening()
        self.cli.response["result"] = "Claude rebuttal"
        result = self.adapter.dispatch(self.plan, "claude-rebuttal",
                                       self.debate_certificate("claude-rebuttal"))
        self.assertEqual(result["state"], "succeeded")
        path.rename(path.with_suffix(".moved"))
        self.assertEqual(self.adapter.reconcile(self.plan, "claude-rebuttal")["state"], "succeeded")
        self.assertEqual(len(self.cli.sends), 2)

    def test_opening_spec_identity_unchanged(self):
        task = "Argue the independent position from supplied evidence"
        expected = ("Independent read-only /vibe node. Do not claim to have used tools or other models. State uncertainty and evidence.\n"
                    + self.m.safe_json({"role": None, "task": task, "acceptance": []}))
        self.assertEqual(self.m.render_spec(self.plan, "opening"), expected)


if __name__ == "__main__":
    unittest.main()
