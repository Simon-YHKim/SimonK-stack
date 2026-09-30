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

    def send(self, argv, binding, env):
        self.sends.append((copy.deepcopy(argv), dict(env)))
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

    def test_one_send_same_intent_reentry_never_resends(self):
        result = self.adapter.dispatch(self.plan, "opening", self.certificate)
        self.assertEqual(result["state"], "succeeded")
        self.assertEqual(result["verified"], False)
        self.assertIsNone(result["actual_usd"])
        self.assertEqual(len(self.cli.sends), 1)
        argv, env = self.cli.sends[0]
        self.assertIn("--safe-mode", argv)
        self.assertIn("--strict-mcp-config", argv)
        self.assertEqual(argv[argv.index("--tools") + 1], "")
        self.assertEqual(argv[argv.index("--model") + 1], "fixture-claude")
        self.assertEqual(argv[argv.index("--effort") + 1], "low")
        self.assertNotEqual(argv[argv.index("--session-id") + 1], self.m.request_id(self.plan, "opening"))
        self.assertNotIn("ANTHROPIC_API_KEY", env)
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


if __name__ == "__main__":
    unittest.main()
