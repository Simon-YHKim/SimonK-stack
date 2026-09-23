"""Metadata collection never becomes authorization or a generation request."""
import copy
import importlib.util
import json
import os
import sys
import time
import unittest
from unittest import mock
from pathlib import Path

SCRIPT = Path(__file__).with_name("runtime_collect.py")
NOW = "2026-09-23T13:00:00+00:00"


def codex_raw():
    return {"initialize": {"codexHome": "/fixture/profile"},
            "account": {"account": {"type": "chatgpt", "planType": "pro", "email": "fixture@example.invalid"}},
            "models": {"data": [{"id": "gpt-6-sol", "model": "gpt-6-sol",
                                   "supportedReasoningEfforts": [{"reasoningEffort": "low"},
                                                                 {"reasoningEffort": "ultra"}]}]},
            "limits": {"rateLimits": {"limitId": "codex", "primary": {"usedPercent": 52,
                                       "windowDurationMins": 10080, "resetsAt": 1790400000},
                                      "credits": {"hasCredits": False, "unlimited": False, "balance": "0"},
                                      "spendControlReached": False}}}


def grok_raw():
    return {"subscriptionTier": "SuperGrokHeavy", "accountId": "fixture-account",
            "billing": {"creditUsagePercent": 100, "currentPeriod": {"type": "WEEKLY",
                          "end": "2026-09-26T14:12:19Z"}, "onDemandCap": "0", "onDemandUsed": "0",
                        "prepaidBalance": "0"}}


def agy_raw():
    return {"status": "SUCCESS", "num_turns": 0,
            "usage": {"input_tokens": 0, "output_tokens": 0, "thinking_tokens": 0,
                      "cache_read_tokens": 0, "total_tokens": 0},
            "command": {"name": "usage", "data": {"groups": [
                {"name": "Gemini Models", "buckets": [{"id": "gemini-weekly", "window": "weekly",
                    "remaining_fraction": 0.75, "reset_time": "2026-09-26T00:48:24Z"}]},
                {"name": "Claude and GPT models", "buckets": [{"id": "3p-weekly", "window": "weekly",
                    "remaining_fraction": 0.9, "reset_time": "2026-09-26T00:48:24Z"}]}]}}}


class RuntimeCollectionTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "Runtime collector is not implemented")
        spec = importlib.util.spec_from_file_location("runtime_collect", SCRIPT)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)

    def parse(self, surface, raw):
        return self.m.normalize(surface, raw, NOW, "fixture-profile")

    def test_codex_observations_preserve_efforts_but_do_not_authorize(self):
        out = self.parse("codex", codex_raw())
        self.assertEqual(out["models"][0]["transport_efforts"], ["low", "ultra"])
        self.assertEqual(out["quota_windows"][0]["used_pct"], 52)
        self.assertEqual(out["billing"]["credits"]["balance"], "0")
        self.assertIsNone(out["billing"]["extra_usage_enabled"])
        self.assertFalse(out["billing"]["verified"])
        self.assertFalse(out["generation_verified"])
        self.assertTrue(out["account_verified"])

    def test_raw_identity_and_unknown_fields_never_escape(self):
        raw = codex_raw()
        raw["token"] = "never-copy-this-secret"
        raw["account"]["account"]["token"] = "never-copy-this-secret"
        text = json.dumps(self.parse("codex", raw))
        for value in ("never-copy-this-secret", "fixture@example.invalid", "/fixture/profile"):
            self.assertNotIn(value, text)

    def test_same_profile_is_not_same_account(self):
        one = self.parse("codex", codex_raw())
        changed = codex_raw()
        changed["account"]["account"]["email"] = "second@example.invalid"
        two = self.parse("codex", changed)
        self.assertNotEqual(one["account_ref"], two["account_ref"])
        self.assertEqual(one["profile_ref"], two["profile_ref"])

    def test_missing_identity_is_not_verified(self):
        raw = codex_raw()
        del raw["account"]["account"]["email"]
        out = self.parse("codex", raw)
        self.assertIsNone(out["account_ref"])
        self.assertFalse(out["account_verified"])

    def test_codex_named_buckets_are_not_conflated_or_double_counted(self):
        raw = codex_raw()
        raw["limits"]["rateLimitsByLimitId"] = {
            "codex": copy.deepcopy(raw["limits"]["rateLimits"]),
            "premium": {"primary": {"usedPercent": 100, "windowDurationMins": 300}}}
        windows = self.parse("codex", raw)["quota_windows"]
        self.assertEqual(len(windows), 2)
        self.assertEqual({w["bucket"]: w["used_pct"] for w in windows}, {"codex": 52, "premium": 100})

    def test_grok_missing_overage_flag_stays_unknown(self):
        out = self.parse("grok", grok_raw())
        self.assertEqual(out["quota_windows"][0]["used_pct"], 100)
        self.assertIsNone(out["billing"]["extra_usage_enabled"])
        self.assertEqual(out["billing"]["on_demand_cap"], "0")
        self.assertFalse(out["billing"]["verified"])

    def test_grok_absent_percent_is_not_assumed_zero(self):
        raw = grok_raw()
        del raw["billing"]["creditUsagePercent"]
        self.assertIsNone(self.parse("grok", raw)["quota_windows"][0]["used_pct"])

    def test_invalid_numeric_values_stay_unknown(self):
        for value in (True, -1, 101, float("nan"), "broken"):
            raw = grok_raw()
            raw["billing"]["creditUsagePercent"] = value
            self.assertIsNone(self.parse("grok", raw)["quota_windows"][0]["used_pct"])

    def test_agy_groups_remain_distinct_and_identity_is_unknown(self):
        out = self.parse("antigravity", agy_raw())
        self.assertEqual([w["bucket"] for w in out["quota_windows"]], ["gemini-weekly", "3p-weekly"])
        self.assertEqual(out["quota_windows"][0]["used_pct"], 25)
        self.assertIsNone(out["account_ref"])
        self.assertFalse(out["billing"]["verified"])

    def test_agy_requires_zero_turns_all_zero_tokens_and_usage_command(self):
        variants = []
        for key, value in (("num_turns", 1), ("num_turns", False), ("status", "FAILED")):
            raw = agy_raw()
            raw[key] = value
            variants.append(raw)
        for value in (1, None, "0", False):
            raw = agy_raw()
            raw["usage"]["total_tokens"] = value
            variants.append(raw)
        raw = agy_raw()
        raw["command"]["name"] = "prompt"
        variants.append(raw)
        for raw in variants:
            with self.subTest(raw=raw), self.assertRaises(self.m.CollectorError):
                self.parse("antigravity", raw)

    def test_claude_subscription_does_not_prove_free_fable(self):
        out = self.parse("claude", {"loggedIn": True, "authMethod": "claude.ai",
                                   "apiProvider": "firstParty", "subscriptionType": "max",
                                   "email": "fixture@example.invalid"})
        self.assertTrue(out["account_verified"])
        self.assertEqual(out["billing"]["mode"], "subscription")
        self.assertEqual(out["quota_windows"], [])
        self.assertEqual(out["models"], [])
        self.assertFalse(out["billing"]["verified"])

    def test_expired_quota_does_not_gain_freshness_by_collection(self):
        raw = grok_raw()
        raw["billing"]["currentPeriod"]["end"] = "2026-09-22T00:00:00Z"
        w = self.parse("grok", raw)["quota_windows"][0]
        self.assertIsNone(w["used_pct"])
        self.assertEqual(w["state"], "reset-unobserved")

    def test_snapshot_is_consumable_by_planner_but_not_execution_proof(self):
        snapshot = self.m.snapshot([self.parse("codex", codex_raw())], NOW)
        self.assertEqual(snapshot["observed_at"], NOW)
        self.assertEqual(len(snapshot["candidates"]), 1)
        c = snapshot["candidates"][0]
        self.assertFalse(c["available"])
        self.assertIsNone(c["effective_effort"])
        self.assertEqual(c["billing"]["account_ref"], snapshot["observations"][0]["account_ref"])
        self.assertNotIn("ultra", c["provider_efforts"])

    def test_error_report_never_echoes_raw_exception(self):
        class Broken:
            def collect(self, surface):
                raise OSError("sensitive-token-value")
        result = self.m.collect_all(["codex"], backend=Broken(), now=NOW)
        self.assertEqual(result["observations"][0]["state"], "error")
        self.assertNotIn("sensitive-token-value", json.dumps(result))

    def test_rpc_rejects_generation_or_mutation_before_writing(self):
        with self.m.Rpc([sys.executable, "-c", "import time; time.sleep(3)"], timeout=1) as rpc:
            for method in ("turn/start", "session/prompt", "account/login/start", "thread/start"):
                with self.subTest(method=method), self.assertRaises(self.m.CollectorError):
                    rpc.request(method, {})

    def test_real_rpc_correlates_ids_and_ignores_notifications(self):
        program = ('import sys,json\n'
                   'for line in sys.stdin:\n'
                   ' m=json.loads(line)\n'
                   ' if m.get("method")=="initialize":\n'
                   '  print(json.dumps({"id":99,"result":{"wrong":True}}),flush=True)\n'
                   '  print(json.dumps({"id":m["id"],"result":{"protocolVersion":1}}),flush=True)\n'
                   ' elif m.get("method")=="_x.ai/billing":\n'
                   '  print(json.dumps({"method":"ignored","params":{"secret":"do-not-print"}}),flush=True)\n'
                   '  print(json.dumps({"id":m["id"],"result":{"ok":True}}),flush=True)\n')
        with self.m.Rpc([sys.executable, "-u", "-c", program], timeout=2) as rpc:
            self.assertEqual(rpc.request("initialize", {}), {"protocolVersion": 1})
            self.assertEqual(rpc.request("_x.ai/billing", {}), {"ok": True})
        self.assertIsNotNone(rpc.process.poll())

    def test_orphaned_grandchild_cannot_hold_stdout_cleanup_open(self):
        program = ('import subprocess,sys,json\n'
                   'm=json.loads(sys.stdin.readline())\n'
                   'subprocess.Popen([sys.executable,"-c","import time; time.sleep(4)"],stdout=sys.stdout)\n'
                   'print(json.dumps({"id":m["id"],"result":{}}),flush=True)\n')
        started = time.monotonic()
        with self.m.Rpc([sys.executable, "-u", "-c", program], timeout=0.3) as rpc:
            rpc.request("initialize", {})
            rpc.process.wait(timeout=1)
        self.assertLess(time.monotonic() - started, 2)
        self.assertFalse(rpc.reader.is_alive())

    def test_unexpected_server_request_does_not_echo_large_id(self):
        program = ('import sys,json,time\n'
                   'sys.stdin.readline()\n'
                   'print(json.dumps({"id":"x"*70000,"method":"fs/read","params":{}}),flush=True)\n'
                   'time.sleep(4)\n')
        started = time.monotonic()
        with self.assertRaises(self.m.CollectorError) as ctx:
            with self.m.Rpc([sys.executable, "-u", "-c", program], timeout=0.3) as rpc:
                rpc.request("initialize", {})
        self.assertEqual(ctx.exception.code, "server-request-forbidden")
        self.assertLess(time.monotonic() - started, 2)

    def test_child_environment_uses_allowlist_not_secret_denylist(self):
        env = self.m.child_env({"PATH": "safe-path", "HOME": "/fixture", "CODEX_HOME": "/fixture/codex",
                               "GROK_AUTH_PROVIDER_COMMAND": "must-not-run", "NODE_OPTIONS": "--require bad",
                               "NEW_PROVIDER_SECRET": "secret", "OPENAI_API_KEY": "secret"}, "codex")
        self.assertEqual(env["CODEX_HOME"], "/fixture/codex")
        self.assertEqual(env["PATH"], "safe-path")
        self.assertFalse(any(k in env for k in ("GROK_AUTH_PROVIDER_COMMAND", "NODE_OPTIONS", "NEW_PROVIDER_SECRET", "OPENAI_API_KEY")))

    def test_codex_preserves_nonprimary_billing_facts(self):
        raw = codex_raw()
        raw["limits"]["rateLimitsByLimitId"] = {"premium": {"credits": {"hasCredits": True,
            "unlimited": False, "balance": "5"}, "spendControlReached": True}}
        billing = self.parse("codex", raw)["billing"]["buckets"]
        self.assertEqual(billing["premium"]["credits"]["balance"], "5")
        self.assertTrue(billing["premium"]["spend_control_reached"])

    def test_codex_backend_uses_same_connection_and_detects_account_change(self):
        parent = self
        class FakeRpc:
            methods = []
            reads = 0
            def __init__(self, argv, **kwargs):
                parent.assertEqual(argv[-2:], ["app-server", "--stdio"])
            def __enter__(self):
                return self
            def __exit__(self, *exc):
                pass
            def send(self, message):
                parent.assertEqual(message["method"], "initialized")
            def request(self, method, params):
                self.methods.append(method)
                if method == "initialize":
                    return {"codexHome": str(Path.home() / ".codex")}
                if method == "account/read":
                    parent.assertIs(params["refreshToken"], False)
                    self.reads += 1
                    return {"account": {"type": "chatgpt", "email": str(self.reads) + "@example.invalid"}}
                return {}
        with mock.patch.object(self.m, "resolve_command", return_value=["fixture"]), \
             mock.patch.object(self.m, "Rpc", FakeRpc), \
             mock.patch.dict(os.environ, {"USERPROFILE": str(Path.home()), "HOME": str(Path.home())}, clear=True):
            result = self.m.collect_all(["codex"], now=NOW)
        self.assertEqual(result["observations"][0]["error_code"], "account-changed")
        self.assertEqual(FakeRpc.methods.count("account/read"), 2)

    def test_grok_fallback_only_on_method_not_found(self):
        parent = self
        for error in (-32601, -32000):
            methods = []
            class FakeRpc:
                def __init__(self, argv, **kwargs):
                    parent.assertEqual(argv[-3:], ["agent", "--no-leader", "stdio"])
                def __enter__(self):
                    return self
                def __exit__(self, *exc):
                    pass
                def request(self, method, params):
                    methods.append(method)
                    if method == "initialize":
                        return {"protocolVersion": 1}
                    if method == "_x.ai/billing":
                        raise parent.m.CollectorError("rpc-error", error)
                    return grok_raw()
            with self.subTest(error=error), mock.patch.object(self.m, "resolve_command", return_value=["fixture"]), \
                 mock.patch.object(self.m, "Rpc", FakeRpc):
                result = self.m.collect_all(["grok"], now=NOW)
                self.assertEqual("x.ai/billing" in methods, error == -32601)
                self.assertEqual(result["observations"][0]["state"], "ok" if error == -32601 else "error")

    def test_agy_unverified_version_never_gets_a_prompt_argument(self):
        with mock.patch.object(self.m, "resolve_command", return_value=["fixture"]), \
             mock.patch.object(self.m, "run_text", return_value=("agy 99.0.0", 0)) as run:
            result = self.m.collect_all(["antigravity"], now=NOW)
        self.assertEqual(result["observations"][0]["error_code"], "usage-contract-unverified")
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.args[0], ["fixture", "--version"])

    def test_expired_deadline_cannot_consume_already_queued_response(self):
        with self.m.Rpc([sys.executable, "-c", "import time; time.sleep(3)"], timeout=1) as rpc:
            rpc.messages.put(b'{"id":1,"result":{}}\n')
            rpc.deadline = time.monotonic() - 1
            with self.assertRaises(self.m.CollectorError) as ctx:
                rpc.line()
            self.assertEqual(ctx.exception.code, "timeout")

    def test_observation_snapshot_is_rejected_by_actual_planner(self):
        import orchestrate
        data = self.m.snapshot([self.parse("codex", codex_raw())], NOW)
        plan = orchestrate.make_plan({"run_id": "collector-fixture", "steps": [{"id": "read", "kind": "llm",
            "skills": [], "demand": "routine", "writes": False}]}, {}, data, NOW)
        self.assertEqual(plan["status"], "blocked")
        self.assertIn("BILLING_UNVERIFIED", str(plan))
        self.assertEqual(orchestrate.ready_steps(plan, [], NOW), [])

    def test_output_limit_and_timeout_terminate_own_probe(self):
        programs = [('import sys; sys.stdout.write("x"*20000); sys.stdout.flush()', "output-limit"),
                    ('import time; time.sleep(5)', "timeout")]
        for program, code in programs:
            with self.subTest(code=code):
                with self.assertRaises(self.m.CollectorError) as ctx:
                    with self.m.Rpc([sys.executable, "-u", "-c", program], timeout=0.2, max_bytes=1000) as rpc:
                        rpc.request("initialize", {})
                self.assertEqual(ctx.exception.code, code)
                self.assertIsNotNone(rpc.process.poll())


if __name__ == "__main__":
    unittest.main()
