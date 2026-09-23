"""Central model facts must constrain, never fabricate, runtime capabilities."""
import copy
import ast
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT = Path(__file__).with_name("model_registry.py")
NOW = "2026-09-23T13:00:00+00:00"


def registry():
    return {
        "schema_version": 1, "version": "test-1", "checked_at": NOW,
        "sources": {"official": "https://developers.openai.com/api/docs/models/gpt-6-sol"},
        "models": [{"id": "gpt-6-sol", "surface": "codex", "vendor": "openai",
                    "id_namespace": "provider-api",
                    "lifecycle": "active", "api_efforts": ["low", "medium", "high"],
                    "aliases": ["sol"], "sources": ["official"],
                    "pricing": {"scope": "direct-api-standard-usd-per-million-tokens",
                                "input": "2", "cached_input": "0.2", "output": "10"}}],
    }


def candidate(**changes):
    c = {"id": "test-seat", "surface": "codex", "transport": "cli", "model": "gpt-6-sol",
         "lifecycle": "active", "available": True, "provider_efforts": ["low", "high", "ultra"],
         "transport_efforts": ["low", "high", "ultra"],
         "observed_at": NOW,
         "billing": {"mode": "unknown", "verified": False},
         "quota": {"used_pct": None, "observed_at": NOW}}
    c.update(changes)
    return c


class ModelRegistryTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "Central model registry implementation is missing")
        spec = importlib.util.spec_from_file_location("vibe_model_registry", SCRIPT)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)

    def bind(self, c=None, data=None):
        return self.m.constrain_runtime({"candidates": [c or candidate()]}, data or registry(), NOW)

    def test_unknown_model_cannot_become_active_from_runtime_claim(self):
        c = self.bind(candidate(model="gpt-made-up"))["candidates"][0]
        self.assertFalse(c["available"])
        self.assertIn("MODEL_NOT_REGISTERED", c["registry_errors"])

    def test_model_vendor_mismatch_is_rejected(self):
        c = self.bind(candidate(surface="claude"))["candidates"][0]
        self.assertFalse(c["available"])
        self.assertIn("MODEL_SURFACE_MISMATCH", c["registry_errors"])

    def test_efforts_intersect_api_and_runtime_not_harness_modes(self):
        c = self.bind()["candidates"][0]
        self.assertEqual(c["provider_efforts"], ["low", "high"])
        self.assertEqual(c["transport_efforts"], ["low", "high"])
        self.assertNotIn("ultra", c["provider_efforts"])

    def test_no_default_effort_when_runtime_did_not_observe_one(self):
        c = self.bind(candidate(provider_efforts=[], transport_efforts=[]))["candidates"][0]
        self.assertEqual(c["provider_efforts"], [])
        self.assertEqual(c["transport_efforts"], [])

    def test_alias_needs_explicit_observed_resolution(self):
        c = self.bind(candidate(model="sol"))["candidates"][0]
        self.assertFalse(c["available"])
        self.assertIn("ALIAS_RESOLUTION_UNVERIFIED", c["registry_errors"])

    def test_alias_locks_requested_and_resolved_models(self):
        c = self.bind(candidate(model="sol", resolved_model="gpt-6-sol",
                                resolution_observed_at=NOW, resolution_evidence="model/list"))["candidates"][0]
        self.assertTrue(c["available"])
        self.assertEqual(c["requested_model"], "sol")
        self.assertEqual(c["model"], "gpt-6-sol")

    def test_alias_resolution_has_a_runtime_not_catalog_ttl(self):
        c = self.bind(candidate(model="sol", resolved_model="gpt-6-sol",
                                resolution_observed_at="2026-09-23T12:44:59Z",
                                resolution_evidence="model/list"))["candidates"][0]
        self.assertFalse(c["available"])
        self.assertIn("ALIAS_RESOLUTION_STALE", c["registry_errors"])

    def test_model_ids_declare_their_namespace(self):
        data = registry()
        del data["models"][0]["id_namespace"]
        with self.assertRaises(ValueError):
            self.m.validate_registry(data)

    def test_valid_until_is_the_earliest_required_evidence_expiry(self):
        old = (datetime.fromisoformat(NOW) - timedelta(seconds=899)).isoformat()
        expected = (datetime.fromisoformat(NOW) + timedelta(seconds=1)).isoformat()
        for field in ("runtime", "quota", "alias", "registry"):
            with self.subTest(field=field):
                c, data = candidate(valid_until="2099-01-01T00:00:00Z"), registry()
                if field == "runtime":
                    c["observed_at"] = old
                elif field == "quota":
                    c["quota"]["observed_at"] = old
                elif field == "alias":
                    c.update(model="sol", resolved_model="gpt-6-sol",
                             resolution_observed_at=old, resolution_evidence="model/list")
                else:
                    data["checked_at"] = (datetime.fromisoformat(NOW) - timedelta(days=7)
                                          + timedelta(seconds=1)).isoformat()
                self.assertEqual(self.bind(c, data)["candidates"][0]["valid_until"], expected)

    def test_missing_runtime_time_cannot_reuse_supplied_validity(self):
        c = candidate(valid_until="2099-01-01T00:00:00Z")
        del c["observed_at"]
        self.assertIsNone(self.bind(c)["candidates"][0]["valid_until"])

    def test_mismatched_resolved_model_is_rejected(self):
        c = self.bind(candidate(resolved_model="gpt-6-astra"))["candidates"][0]
        self.assertFalse(c["available"])
        self.assertIn("MODEL_RESOLUTION_MISMATCH", c["registry_errors"])

    def test_public_listing_does_not_grant_runtime_or_billing(self):
        c = self.bind(candidate(available=False))["candidates"][0]
        self.assertFalse(c["available"])
        self.assertEqual(c["billing"], {"mode": "unknown", "verified": False})
        self.assertIsNone(c["quota"]["used_pct"])
        self.assertNotIn("upper_usd_per_attempt", c)

    def test_retired_and_preview_are_not_silently_promoted(self):
        for state in ("retired", "preview"):
            data = registry()
            data["models"][0]["lifecycle"] = state
            self.assertFalse(self.bind(data=data)["candidates"][0]["available"])

    def test_runtime_deprecation_is_not_overwritten(self):
        self.assertFalse(self.bind(candidate(lifecycle="retired"))["candidates"][0]["available"])

    def test_registry_facts_have_finite_freshness(self):
        data = registry()
        data["checked_at"] = "2026-08-01T00:00:00Z"
        c = self.bind(data=data)["candidates"][0]
        self.assertFalse(c["available"])
        self.assertIn("REGISTRY_STALE", c["registry_errors"])

    def test_future_registry_is_not_fresh(self):
        data = registry()
        data["checked_at"] = "2026-09-24T00:00:00Z"
        self.assertFalse(self.bind(data=data)["candidates"][0]["available"])

    def test_observations_are_not_mutated(self):
        original = {"candidates": [candidate()]}
        saved = copy.deepcopy(original)
        result = self.m.constrain_runtime(original, registry(), NOW)
        self.assertEqual(original, saved)
        self.assertEqual(result["model_registry"]["version"], "test-1")
        self.assertEqual(len(result["model_registry"]["sha256"]), 64)

    def test_duplicate_models_and_alias_collisions_fail(self):
        data = registry()
        data["models"].append(copy.deepcopy(data["models"][0]))
        with self.assertRaises(ValueError):
            self.m.validate_registry(data)
        data["models"][1]["id"] = "gpt-6-other"
        with self.assertRaises(ValueError):
            self.m.validate_registry(data)

    def test_source_must_be_known_and_official_for_vendor(self):
        data = registry()
        data["sources"]["official"] = "https://example.invalid/untrusted"
        with self.assertRaises(ValueError):
            self.m.validate_registry(data)
        data = registry()
        data["models"][0]["sources"] = ["missing"]
        with self.assertRaises(ValueError):
            self.m.validate_registry(data)

    def test_price_scope_does_not_conflate_api_and_subscription(self):
        data = registry()
        data["models"][0]["pricing"]["scope"] = "subscription"
        with self.assertRaises(ValueError):
            self.m.validate_registry(data)
        for bad in ("NaN", "Infinity", "-1", True):
            data = registry()
            data["models"][0]["pricing"]["input"] = bad
            with self.assertRaises(ValueError):
                self.m.validate_registry(data)

    def test_bot_has_provider_managed_model_effort_and_distinct_billing(self):
        c = candidate(surface="grok-bot", model=None, transport="bot", bot_id="fixture")
        out = self.bind(c)["candidates"][0]
        self.assertTrue(out["available"])
        self.assertIsNone(out["model"])
        self.assertEqual(out["provider_efforts"], [])
        self.assertEqual(out["billing"], c["billing"])

    def test_bot_cannot_claim_an_unverified_model(self):
        out = self.bind(candidate(surface="grok-bot", model="grok-4.7", transport="bot"))["candidates"][0]
        self.assertFalse(out["available"])
        self.assertIn("BOT_MODEL_CONTROL_UNVERIFIED", out["registry_errors"])

    def test_loader_rejects_duplicate_json_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            path.write_text('{"schema_version":1,"schema_version":2}', encoding="utf-8")
            with self.assertRaises(ValueError):
                self.m.load_registry(path)

    def test_packaged_registry_contains_current_four_vendors(self):
        data = self.m.load_registry()
        ids = {m["id"] for m in data["models"]}
        self.assertTrue({"gpt-6-astra", "gpt-6-sol", "gpt-6-luna", "claude-opus-5-5",
                         "claude-fable-5-1", "claude-sonnet-5", "gemini-3.8-flash", "grok-4.7"} <= ids)
        self.assertEqual({m["vendor"] for m in data["models"]}, {"openai", "anthropic", "google", "xai"})

    def test_every_legacy_lane_has_an_explicit_migration_disposition(self):
        tree = ast.parse(SCRIPT.with_name("routing.py").read_text(encoding="utf-8"))
        lanes = next(node.value for node in tree.body if isinstance(node, ast.Assign)
                     and any(isinstance(target, ast.Name) and target.id == "LANES" for target in node.targets))
        expected = {key.value for key in lanes.keys}
        data = self.m.load_registry()
        self.assertEqual(set(data["legacy_lane_migration"]), expected)
        self.assertTrue(expected <= {m["id"] for m in data["models"]})

    def test_migration_cannot_reference_an_unknown_model(self):
        data = registry()
        data["legacy_lane_migration"] = {"gpt-6-sol": {"candidate": "invented", "status": "pending"}}
        with self.assertRaises(ValueError):
            self.m.validate_registry(data)

    def test_restricted_alias_needs_fresh_account_scoped_access(self):
        data = registry()
        alias = copy.deepcopy(data["models"][0])
        alias.update(id="gpt-daybreak-blue-latest", id_namespace="provider-api-alias", aliases=[],
                     documented_target="gpt-6-sol", api_efforts=None, requires_access_program="daybreak_blue")
        data["models"].append(alias)
        c = candidate(model=alias["id"], resolved_model="gpt-6-sol", resolution_observed_at=NOW,
                      resolution_evidence="model/list", billing={"mode": "unknown", "account_ref": "seat-a"})
        self.assertFalse(self.bind(c, data)["candidates"][0]["available"])
        c["access_proof"] = {"program": "daybreak_blue", "verified": True, "observed_at": NOW,
                             "evidence": "authorized catalog", "account_ref": "seat-a"}
        self.assertTrue(self.bind(c, data)["candidates"][0]["available"])
        for change in ({"account_ref": "seat-b"}, {"observed_at": "2026-09-22T00:00:00Z"}):
            wrong = copy.deepcopy(c)
            wrong["access_proof"].update(change)
            self.assertFalse(self.bind(wrong, data)["candidates"][0]["available"])


if __name__ == "__main__":
    unittest.main()
