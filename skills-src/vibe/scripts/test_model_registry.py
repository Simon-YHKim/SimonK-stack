"""Central model facts must constrain, never fabricate, runtime capabilities."""
import copy
import ast
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

SCRIPT = Path(__file__).with_name("model_registry.py")
REFERENCES = SCRIPT.parent.parent / "references"
NOW = "2026-09-23T13:00:00+00:00"


def catalog_map_section(heading):
    text = (REFERENCES / "model-catalog-map.md").read_text(encoding="utf-8")
    return text.split("## " + heading, 1)[1].split("\n## ", 1)[0]


def catalog_map_rows():
    """CLI-name table rows: surface, CLI catalog name, registry ID, effort carried by the name."""
    rows = []
    for line in catalog_map_section("CLI name map").splitlines():
        if line.startswith("| `"):
            rows.append([cell.strip().strip("`") for cell in line.strip().strip("|").split("|")][:4])
    return rows


def module_literal(filename, name):
    """A top-level literal read without importing the module (no import side effects)."""
    tree = ast.parse(SCRIPT.with_name(filename).read_text(encoding="utf-8"))
    return next(node.value for node in tree.body if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == name for target in node.targets))


def routing_lanes():
    return {key.value for key in module_literal("routing.py", "LANES").keys}


def routing_lane_vendors():
    return {lane: spec["vendor"] for lane, spec in ast.literal_eval(module_literal("routing.py", "LANES")).items()}


def evaluator_vendors():
    return ast.literal_eval(module_literal("adversarial_eval.py", "VENDOR_OF"))


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
        self.assertTrue({"gpt-6-astra", "gpt-6.1-sol", "gpt-6-sol", "gpt-6-luna", "claude-opus-5-5",
                         "claude-fable-5-1", "claude-sonnet-5-5", "claude-sonnet-5", "claude-haiku-5-5",
                         "gemini-3.8-flash", "grok-4.7"} <= ids)
        self.assertEqual({m["vendor"] for m in data["models"]}, {"openai", "anthropic", "google", "xai"})

    def test_gpt_61_sol_catalog_does_not_promote_unavailable_runtime(self):
        data = self.m.load_registry()
        model = next(m for m in data["models"] if m["id"] == "gpt-6.1-sol")
        self.assertEqual(model["api_efforts"], ["low", "medium", "high", "xhigh", "max"])
        self.assertEqual(model["context_tokens"], 1050000)
        self.assertEqual(model["max_output_tokens"], 128000)
        self.assertEqual(model["pricing"]["scope"], "direct-api-standard-usd-per-million-tokens")
        self.assertEqual(model["pricing"]["cached_input"], "0.1")
        observed_at = data["checked_at"]
        trial = candidate(model="gpt-6.1-sol", available=False, observed_at=observed_at,
                          billing={"mode": "unknown", "verified": False},
                          quota={"used_pct": None, "observed_at": observed_at})
        constrained = self.m.constrain_runtime({"candidates": [trial]}, data, observed_at)["candidates"][0]
        self.assertFalse(constrained["available"])
        self.assertFalse(constrained["billing"]["verified"])

    def test_sonnet_55_catalog_update_does_not_authorize_alias_dispatch(self):
        data = self.m.load_registry()
        models = {model["id"]: model for model in data["models"]}
        new = models["claude-sonnet-5-5"]
        self.assertEqual(new["released_at"], "2026-09-28")
        self.assertEqual(new["api_efforts"], ["low", "medium", "high", "xhigh", "max"])
        self.assertEqual(new["pricing"]["scope"], "direct-api-standard-usd-per-million-tokens")
        self.assertIsNone(new["pricing"]["cache_write"])
        # D-90 held this migration; Simon's 2026-10-05 instruction resumed it, pending a canary.
        self.assertEqual(data["legacy_lane_migration"]["claude-sonnet-5"],
                         {"candidate": "claude-sonnet-5-5", "status": "pending-transport-and-certificate"})
        observed_at = data["checked_at"]
        trial = candidate(surface="claude", model="sonnet", resolved_model=None, observed_at=observed_at,
                          quota={"used_pct": None, "observed_at": observed_at})
        result = self.m.constrain_runtime({"candidates": [trial]}, data, observed_at)["candidates"][0]
        self.assertEqual(result["model"], "claude-sonnet-5-5")
        self.assertFalse(result["available"])
        self.assertIn("ALIAS_RESOLUTION_UNVERIFIED", result["registry_errors"])

    def test_every_legacy_lane_has_an_explicit_migration_disposition(self):
        expected = routing_lanes()
        data = self.m.load_registry()
        self.assertEqual(set(data["legacy_lane_migration"]), expected)
        self.assertTrue(expected <= {m["id"] for m in data["models"]})

    def test_every_routing_lane_has_the_same_vendor_in_the_adversarial_evaluator(self):
        # A lane missing from VENDOR_OF silently drops out of G10 matchups (load_probes skips it).
        lanes, vendors = routing_lane_vendors(), evaluator_vendors()
        self.assertEqual(set(lanes) - set(vendors), set(), "routing.LANES key without a VENDOR_OF entry")
        self.assertEqual(set(vendors) - set(lanes), set(), "VENDOR_OF key that is not a routing lane")
        for lane, vendor in lanes.items():
            with self.subTest(lane=lane):
                self.assertEqual(vendors[lane], vendor)

    def test_eval_probes_carry_each_lane_successor_beside_the_legacy_lane(self):
        # D-67 adds lanes alongside legacy ones; old names stay because the eval ledger uses them.
        probes = json.loads((SCRIPT.parent.parent / "eval" / "probes.json").read_text(encoding="utf-8"))["probes"]
        lanes, vendors = routing_lanes(), evaluator_vendors()
        migration = self.m.load_registry()["legacy_lane_migration"]
        seen = set()
        for probe in probes:
            with self.subTest(probe=probe["id"]):
                self.assertTrue(set(probe["lanes"]) <= lanes, sorted(set(probe["lanes"]) - lanes))
                self.assertGreaterEqual(len({vendors[lane] for lane in probe["lanes"]}), 3)
                for lane in probe["lanes"]:
                    successor = migration[lane]["candidate"]
                    if successor != lane and successor in lanes:
                        self.assertIn(successor, probe["lanes"])
                seen.update(probe["lanes"])
        # D-101 (2026-10-12): the only Codex lane a probe may offer is gpt-6-astra. Withdrawn lanes and
        # the deprecated Daybreak alias (gate only) never enter a new matchup.
        self.assertTrue({"claude-opus-5", "claude-opus-5-5", "gpt-6-astra"} <= seen)
        retired = (ast.literal_eval(module_literal("routing.py", "WITHDRAWN_LANES"))
                   | ast.literal_eval(module_literal("routing.py", "DEPRECATED_LANES")))
        self.assertEqual(seen & retired, set())
        self.assertEqual({lane for lane in seen if vendors[lane] == "codex"}, {"gpt-6-astra"})

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

    def test_registry_and_task_fit_windows_cover_the_2026_10_12_recheck(self):
        # The 2026-10-06 facts (12:45 KST) would expire REGISTRY_STALE on 2026-10-13 12:45 KST.
        data = self.m.load_registry()
        policy = json.loads((REFERENCES / "task-fit-policy.json").read_text(encoding="utf-8"))
        floor = datetime.fromisoformat("2026-10-12T11:00:00+09:00")
        checked = datetime.fromisoformat(data["checked_at"])
        self.assertGreaterEqual(checked, floor)
        self.assertGreaterEqual(datetime.fromisoformat(policy["checked_at"]), floor)
        # checked_at is the earliest evidence, never later than the policy's own reading.
        self.assertLessEqual(checked, datetime.fromisoformat(policy["checked_at"]))
        earliest = min(checked + timedelta(seconds=self.m.MAX_FACT_AGE_SECONDS),
                       datetime.fromisoformat(policy["valid_until"]))
        self.assertGreaterEqual(earliest, datetime.fromisoformat("2026-10-19T11:00:00+09:00"))

    def test_2026_10_12_provider_fact_changes_are_registered_and_fail_closed(self):
        # Three provider facts changed between the 2026-10-06 and 2026-10-12 rechecks.
        data = self.m.load_registry()
        models = {m["id"]: m for m in data["models"]}
        # Anthropic halved Sonnet 5.5 cache reads on 2026-10-07 ($0.20 -> $0.10 / MTok).
        self.assertEqual(models["claude-sonnet-5-5"]["pricing"]["cached_input"], "0.1")
        self.assertEqual(models["claude-sonnet-5"]["pricing"]["cached_input"], "0.2")
        self.assertEqual(models["gemini-3.8-flash"]["source_updated_at"], "2026-10-09")
        # OpenAI marked the Daybreak Blue alias deprecated; no shutdown date or replacement ID yet.
        alias = models["gpt-daybreak-blue-latest"]
        self.assertEqual((alias["lifecycle"], alias["documented_target"]), ("deprecated", "gpt-5.6-sol"))
        # The refresh changed facts only. D-98 (same morning) moved the gate lane to gpt-6.1-sol and
        # D-101 (same afternoon, Simon's directive) moved it back; the alias itself stays deprecated
        # and the central planner still blocks it.
        self.assertEqual(data["legacy_lane_migration"]["gpt-daybreak-blue-latest"],
                         {"candidate": "gpt-daybreak-blue-latest", "status": "keep-security-pin-resolve-per-run"})
        observed_at = data["checked_at"]
        trial = candidate(model="gpt-daybreak-blue-latest", resolved_model="gpt-5.6-sol", observed_at=observed_at,
                          resolution_observed_at=observed_at, resolution_evidence="model/list",
                          billing={"mode": "unknown", "account_ref": "seat-a"},
                          quota={"used_pct": None, "observed_at": observed_at},
                          access_proof={"program": "daybreak_blue", "verified": True, "observed_at": observed_at,
                                        "evidence": "authorized catalog", "account_ref": "seat-a"})
        out = self.m.constrain_runtime({"candidates": [trial]}, data, observed_at)["candidates"][0]
        self.assertEqual(out["registry_errors"], ["MODEL_NOT_ACTIVE"])
        self.assertFalse(out["available"])

    def test_grok_45_is_registered_without_its_unverified_xhigh(self):
        data = self.m.load_registry()
        model = next(m for m in data["models"] if m["id"] == "grok-4.5")
        self.assertEqual((model["surface"], model["lifecycle"], model["generation"]),
                         ("grok", "active", "legacy"))
        self.assertEqual(model["api_efforts"], ["low", "medium", "high"])
        observed_at = data["checked_at"]
        trial = candidate(surface="grok", model="grok-4.5", observed_at=observed_at,
                          provider_efforts=["low", "high", "xhigh"], transport_efforts=["high", "xhigh"],
                          quota={"used_pct": None, "observed_at": observed_at})
        out = self.m.constrain_runtime({"candidates": [trial]}, data, observed_at)["candidates"][0]
        self.assertEqual(out["registry_errors"], [])
        self.assertEqual(out["provider_efforts"], ["low", "high"])
        self.assertEqual(out["transport_efforts"], ["high"])

    def test_registry_generation_reaches_the_candidate_and_replaces_runtime_claims(self):
        # The planner can prefer a current model only if the registry label survives binding.
        data = self.m.load_registry()
        observed_at = data["checked_at"]
        for model_id, claimed, expected in (("grok-4.5", None, "legacy"), ("grok-4.5", "current", "legacy"),
                                            ("grok-4.7", None, None), ("grok-4.7", "legacy", None)):
            with self.subTest(model=model_id, claimed=claimed):
                trial = candidate(surface="grok", model=model_id, observed_at=observed_at,
                                  quota={"used_pct": None, "observed_at": observed_at})
                if claimed is not None:
                    trial["generation"] = claimed
                out = self.m.constrain_runtime({"candidates": [trial]}, data, observed_at)["candidates"][0]
                self.assertEqual(out["registry_errors"], [])
                if expected is None:
                    self.assertNotIn("generation", out)
                else:
                    self.assertEqual(out["generation"], expected)
        for trial in (candidate(model="gpt-made-up", generation="current"),
                      candidate(surface="grok-bot", model=None, generation="legacy")):
            with self.subTest(surface=trial["surface"], model=trial["model"]):
                self.assertNotIn("generation", self.bind(trial)["candidates"][0])

    def test_previous_generations_stay_active_and_are_labelled_legacy(self):
        models = {m["id"]: m for m in self.m.load_registry()["models"]}
        for model_id in ("claude-opus-5", "claude-sonnet-5", "gpt-5.6-sol", "gpt-5.6-terra",
                         "gpt-5.6-luna", "grok-4.6", "grok-4.5"):
            with self.subTest(model=model_id):
                self.assertEqual(models[model_id].get("generation"), "legacy")
                self.assertEqual(models[model_id]["lifecycle"], "active")
        for model_id in ("claude-fable-5-1", "claude-opus-5-5", "claude-sonnet-5-5",
                         "gpt-6.1-sol", "gpt-6-astra", "grok-4.7"):
            with self.subTest(model=model_id):
                self.assertNotIn("generation", models[model_id])

    def test_cli_only_catalog_names_are_mapped_but_never_registered(self):
        data = self.m.load_registry()
        models = {m["id"]: m for m in data["models"]}
        keys = {key for m in data["models"] for key in [m["id"], *m.get("aliases", [])]}
        rows = catalog_map_rows()
        self.assertTrue({"grok-4.7-build-fast", "gemini-3.8-flash-high", "gemini-3.8-flash-medium",
                         "gemini-3.8-flash-low", "gemini-3.1-pro-high", "gemini-3.1-pro-low",
                         "claude-haiku-4-5-20251001", "claude-opus-5-5-high",
                         "claude-sonnet-5-5-medium"} <= {row[1] for row in rows})
        for surface, name, target, effort in rows:
            with self.subTest(name=name):
                self.assertNotIn(name, keys)
                if target != "unregistered":
                    self.assertEqual(models[target]["surface"], surface)
                    self.assertIn(effort, models[target]["api_efforts"])
        observed_at = data["checked_at"]
        for surface, name in (("grok", "grok-4.7-build-fast"), ("antigravity", "gemini-3.8-flash-high"),
                              ("claude", "claude-haiku-4-5-20251001"), ("antigravity", "claude-opus-5-5-high")):
            with self.subTest(runtime=name):
                trial = candidate(surface=surface, model=name, observed_at=observed_at,
                                  quota={"used_pct": None, "observed_at": observed_at})
                out = self.m.constrain_runtime({"candidates": [trial]}, data, observed_at)["candidates"][0]
                self.assertFalse(out["available"])
                self.assertIn("MODEL_NOT_REGISTERED", out["registry_errors"])

    def test_pending_lane_migration_names_every_active_model_without_an_orca_lane(self):
        data = self.m.load_registry()
        unlaned = {m["id"] for m in data["models"] if m["lifecycle"] == "active"} - routing_lanes()
        # Simon's 2026-10-05 instruction gave claude-sonnet-5-5 and gpt-6-luna class A lanes;
        # D-99 (2026-10-12) gave claude-haiku-5-5 one.
        self.assertTrue({"gpt-6-sol", "grok-4.7", "grok-4.5"} <= unlaned)
        self.assertFalse({"claude-sonnet-5-5", "gpt-6-luna", "claude-haiku-5-5"} & unlaned)
        pending = catalog_map_section("Lane migration pending")
        self.assertIn("ORCA_UNREGISTERED_PROCESS_OR_MODEL", pending)
        for model_id in sorted(unlaned):
            with self.subTest(model=model_id):
                self.assertIn("`" + model_id + "`", pending)

    def test_d67_lanes_passed_canary_but_still_pending_certificate(self):
        # D-67 adds lanes alongside the legacy keys; registration is not a working route.
        # 2.14.2: the read-only canary (2026-10-04) passed for both lanes, but native send and the
        # account/billing certificate are still missing, so they stay pending (not keep-*).
        # D-101 (2026-10-12): Simon withdrew gpt-6.1-sol and the other non-Astra GPT lanes. The keys
        # stay for the ledger; their migrations are held, and only claude-opus-5-5 is still pending.
        data = self.m.load_registry()
        migration = data["legacy_lane_migration"]
        for lane in ("claude-opus-5-5", "gpt-6.1-sol"):
            self.assertIn(lane, routing_lanes())
        self.assertEqual(migration["claude-opus-5-5"],
                         {"candidate": "claude-opus-5-5", "status": "pending-transport-and-certificate"})
        for legacy in ("claude-opus-5", "gpt-5.6-sol", "gpt-5.6-terra", "grok-4.6"):
            self.assertIn(legacy, routing_lanes())  # ledger.py rejects rows whose lane is not in LANES.
        self.assertEqual(migration["claude-opus-5"],
                         {"candidate": "claude-opus-5-5", "status": "pending-transport-and-certificate"})
        withdrawn = {"candidate": "gpt-6-astra", "status": "held-withdrawn-by-owner"}
        for lane in ("gpt-6.1-sol", "gpt-5.6-sol", "gpt-5.6-terra"):
            with self.subTest(withdrawn=lane):
                self.assertEqual(migration[lane], withdrawn)
        # The class A work of the two Luna lanes went to claude-haiku-5-5.
        for lane in ("gpt-6-luna", "gpt-5.6-luna"):
            with self.subTest(withdrawn=lane):
                self.assertEqual(migration[lane], {"candidate": "claude-haiku-5-5", "status": "held-withdrawn-by-owner"})
        self.assertNotIn("gpt-6-sol", {v["candidate"] for v in migration.values()})
        self.assertEqual(migration["grok-4.6"], {"candidate": "grok-4.7", "status": "pending-quota-and-canary"})
        certificate = {k for k, v in migration.items() if v["status"] == "pending-transport-and-certificate"}
        # 2026-10-12: D-99 added claude-haiku-5-5; D-101 withdrew every GPT lane except gpt-6-astra and
        # returned the Daybreak key to its own keep-* pin.
        self.assertEqual(certificate, {"claude-opus-5-5", "claude-opus-5", "claude-sonnet-5", "claude-sonnet-5-5",
                                       "claude-haiku-5-5"})
        section = catalog_map_section("Lane migration pending")
        rows = {line.split("|")[1].strip(): line for line in section.splitlines() if line.startswith("| `")}
        pending = " ".join(section.split())
        self.assertIn("launch.requested", pending)
        self.assertIn("2026-10-04", pending)
        self.assertIn("`claude-opus-5-5`", pending)
        self.assertIn("`pending-transport-and-certificate`", rows["`claude-opus-5-5`"])
        self.assertNotIn("pending-transport-and-canary", rows["`claude-opus-5-5`"])
        # The table row of a withdrawn lane states its held status, not a pending route.
        for lane in ("gpt-6.1-sol", "gpt-6-luna"):
            with self.subTest(row=lane):
                self.assertIn("`held-withdrawn-by-owner`", rows["`" + lane + "`"])
                self.assertNotIn("pending-", rows["`" + lane + "`"])

    def test_simon_261005_class_a_uses_current_lanes_canary_passed_pending_certificate(self):
        # Simon 2026-10-05 ("5.5로 전환해"): class A moves to the current-generation lanes, added
        # beside the legacy keys like D-67. Both passed the read-only canary (D-91, run_0a369252175f)
        # but are not running lanes until the launch certificate exists.
        lanes = ast.literal_eval(module_literal("routing.py", "LANES"))
        classes = ast.literal_eval(module_literal("routing.py", "CLASS_LANES"))
        # D-99 (2026-10-12) put claude-haiku-5-5 into class A; D-101 (same day, Simon's directive)
        # withdrew gpt-6-luna, so Haiku leads and Sonnet 5.5 and Opus 5.5 follow in the same order.
        self.assertEqual([lane for lane in classes["A"] if lane != "claude-haiku-5-5"],
                         ["claude-sonnet-5-5", "claude-opus-5-5"])
        listed = {lane for order in classes.values() for lane in order}
        listed |= set(ast.literal_eval(module_literal("routing.py", "PROCESS_LANES"))["coding"])
        for legacy in ("gpt-5.6-luna", "claude-sonnet-5", "gpt-6-luna"):
            with self.subTest(legacy=legacy):
                self.assertIn(legacy, lanes)  # ledger.py rejects rows whose lane is not in LANES.
                self.assertNotIn(legacy, listed)
                self.assertIn("원장 호환용(우선순위 밖)", lanes[legacy]["ctx"])
        # lane: (vendor, std, top, efforts Orca 1.4.218 accepts). The gpt-6-luna key keeps its lane
        # facts for ledger rows even though D-101 withdrew it from routing.
        expected = {
            "claude-sonnet-5-5": ("claude", "medium", "high", ("low", "medium", "high", "xhigh", "max")),
            "gpt-6-luna": ("codex", "low", "medium", ("minimal", "low", "medium", "high", "xhigh")),
        }
        migration = self.m.load_registry()["legacy_lane_migration"]
        for lane, (vendor, std, top, orca) in expected.items():
            with self.subTest(lane=lane):
                spec = lanes[lane]
                self.assertEqual((spec["cli"], spec["vendor"], spec["effort_style"], spec["dispatch"]),
                                 (vendor, vendor, "flag", "orca"))
                self.assertEqual((spec["std"], spec["top"], spec["orca_efforts"]), (std, top, orca))
                self.assertNotIn("quota_bucket", spec)  # Sonnet 5.5 uses the general claude weekly quota.
        self.assertEqual(migration["claude-sonnet-5-5"],
                         {"candidate": "claude-sonnet-5-5", "status": "pending-transport-and-certificate"})
        self.assertEqual(migration["claude-sonnet-5"],
                         {"candidate": "claude-sonnet-5-5", "status": "pending-transport-and-certificate"})
        # D-101: withdrawn by the owner, not for a defect. The D-91 canary passed and stays on record.
        for lane in ("gpt-6-luna", "gpt-5.6-luna"):
            self.assertEqual(migration[lane], {"candidate": "claude-haiku-5-5", "status": "held-withdrawn-by-owner"})
        self.assertIn("결함 아님", lanes["gpt-6-luna"]["ctx"])
        section = catalog_map_section("Lane migration pending")
        rows = {line.split("|")[1].strip(): line for line in section.splitlines() if line.startswith("| `")}
        blocked = next(b for b in section.split("\n- ") if "ORCA_UNREGISTERED_PROCESS_OR_MODEL" in b)
        blocked = blocked.split("ORCA_UNREGISTERED_PROCESS_OR_MODEL")[0]
        self.assertIn("`pending-transport-and-certificate`", rows["`claude-sonnet-5-5`"])
        self.assertNotIn("pending-transport-and-canary", rows["`claude-sonnet-5-5`"])
        self.assertIn("`held-withdrawn-by-owner`", rows["`gpt-6-luna`"])
        for lane in expected:
            with self.subTest(row=lane):
                self.assertNotIn("`" + lane + "`", blocked)
        self.assertIn("run_0a369252175f", " ".join(section.split()))

    def test_task_fit_policy_d101_claude_order_for_simple_code_and_astra_xhigh_only(self):
        # D-90 took Sonnet 5.5 out of all four profiles (Artificial Analysis puts it off the
        # intelligence/cost-per-task frontier at every effort). D-101 (2026-10-12, Simon's directive)
        # returns it to CODE_SIMPLE rank 1 only. That is a directive, not a re-measurement: the other
        # three profiles still exclude it and the D-90 re-entry conditions stay written down.
        policy = json.loads((REFERENCES / "task-fit-policy.json").read_text(encoding="utf-8"))
        self.assertEqual(policy["version"], "2026-10-12-shadow.2")
        self.assertEqual((policy["checked_at"], policy["valid_until"]),
                         ("2026-10-12T11:48:51+09:00", "2026-10-19T11:48:51+09:00"))
        profiles = policy["profiles"]

        def rows(profile):
            return [(e["model"], tuple(e["efforts"]), e["rank"]) for e in profiles[profile]]

        self.assertEqual(rows("CODE_SIMPLE"), [("claude-haiku-5-5", ("low", "medium"), 0),
                                               ("claude-sonnet-5-5", ("medium",), 1),
                                               ("claude-opus-5-5", ("medium",), 2)])
        self.assertEqual(rows("PLAN_ARCHITECTURE"), [("claude-opus-5-5", ("high", "xhigh"), 0),
                                                     ("gpt-6-astra", ("xhigh",), 0)])
        self.assertEqual(rows("CODE_COMPLEX"), [("claude-opus-5-5", ("medium",), 0),
                                                ("claude-opus-5-5", ("high", "xhigh"), 1),
                                                ("gpt-6-astra", ("xhigh",), 0)])
        self.assertEqual(rows("WRITING"), [("claude-opus-5-5", ("medium", "high"), 0)])
        for profile in ("PLAN_ARCHITECTURE", "CODE_COMPLEX", "WRITING"):
            with self.subTest(profile=profile):
                self.assertNotIn("claude-sonnet-5-5", {e["model"] for e in profiles[profile]})
        # GPT side: gpt-6-astra at xhigh only, in every profile.
        registry = {m["id"]: m for m in self.m.load_registry()["models"]}
        for profile, entries in profiles.items():
            for entry in entries:
                with self.subTest(profile=profile, model=entry["model"]):
                    if registry[entry["model"]]["vendor"] == "openai":
                        self.assertEqual((entry["model"], entry["efforts"]), ("gpt-6-astra", ["xhigh"]))
        self.assertEqual((policy["sources"]["anthropic_haiku"], policy["sources"]["anthropic_haiku_docs"]),
                         ("https://www.anthropic.com/claude-haiku-5-5",
                          "https://platform.claude.com/docs/en/models/haiku-5-5/overview"))
        self.assertTrue(any("D-90" in note and "재진입 조건" in note for note in policy["notes"]))
        note = next(n for n in policy["notes"] if n.startswith("D-101("))
        for needle in ("gpt 6.1 sol은 너무 느려서 빼기로 결정", "gpt 쪽은 astra 말고는 쓰지마. gpt 를 넣어야한다면 astra xhigh.",
                       "D-90 재진입 조건이 충족돼서가 아니다", "재측정을 올리지 않았고", "소유자 지시", "shadow-only"):
            with self.subTest(note=needle):
                self.assertIn(needle, note)

    def test_catalog_map_states_lane_dispositions_and_legacy_routing_as_built(self):
        migration = self.m.load_registry()["legacy_lane_migration"]
        keep = sorted(k for k, v in migration.items() if v["status"].startswith("keep-"))
        # D-90: a held migration is stopped with written resume conditions.
        held = sorted(k for k, v in migration.items() if v["status"].startswith("held-"))
        self.assertEqual(len(keep) + len(held)
                         + sum(v["status"].startswith("pending-") for v in migration.values()),
                         len(migration))
        self.assertTrue(keep)
        # Simon's 2026-10-05 instruction resumed the first held entry (claude-sonnet-5, D-90).
        # D-101 (2026-10-12) holds the five GPT lanes the owner withdrew; the Daybreak key is a keep-*
        # pin again. The held-* checks below stay generic for any future hold.
        self.assertEqual(held, ["gpt-5.6-luna", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-6-luna", "gpt-6.1-sol"])
        self.assertEqual(set(held), ast.literal_eval(module_literal("routing.py", "WITHDRAWN_LANES")))
        self.assertEqual(keep, ["claude-fable-5-1", "gemini-3.8-flash", "gpt-6-astra", "gpt-daybreak-blue-latest"])
        pending = " ".join(catalog_map_section("Lane migration pending").split())
        self.assertNotIn("every `legacy_lane_migration` entry is still pending", pending)
        for model_id in keep:
            with self.subTest(keep=model_id):
                self.assertIn("`" + model_id + "`", pending)
        for model_id in held:
            with self.subTest(held=model_id):
                self.assertIn("`" + model_id + "`", pending)
                self.assertIn("`" + migration[model_id]["status"] + "`", pending)
                self.assertIn("재개 조건", pending)
        # Host routes can pick a legacy model; the map must not say registration never routes.
        text = (REFERENCES / "model-catalog-map.md").read_text(encoding="utf-8")
        self.assertNotIn("Registration is not routing", text)
        self.assertIn("generation: legacy", " ".join(catalog_map_section("Registered legacy entries").split()))

    def test_d101_gpt_side_is_astra_xhigh_only_in_every_active_routing_position(self):
        # D-101 (2026-10-12, Simon: "gpt 쪽은 astra 말고는 쓰지마. gpt 를 넣어야한다면 astra xhigh."):
        # inventory guard. It fails if any active routing position, output rule, eval probe or task-fit
        # row names a Codex-vendor lane other than gpt-6-astra. The one allowed exception is the
        # deprecated Daybreak alias as the fixed security-artifact-gate pin.
        lanes = ast.literal_eval(module_literal("routing.py", "LANES"))
        classes = ast.literal_eval(module_literal("routing.py", "CLASS_LANES"))
        process_lanes = ast.literal_eval(module_literal("routing.py", "PROCESS_LANES"))
        fixed = {p[0]: p[3] for p in ast.literal_eval(module_literal("routing.py", "PROCESSES")) if p[3]}
        coordinator = ast.literal_eval(module_literal("routing.py", "COORDINATOR"))
        rules = ast.literal_eval(module_literal("routing.py", "OUTPUT_RULES"))
        withdrawn = ast.literal_eval(module_literal("routing.py", "WITHDRAWN_LANES"))
        deprecated = ast.literal_eval(module_literal("routing.py", "DEPRECATED_LANES"))
        pins = ast.literal_eval(module_literal("routing.py", "DEPRECATED_LANE_PINS"))
        pinned_effort = ast.literal_eval(module_literal("routing.py", "EFFORT_PINNED"))
        astra, daybreak, gate = "gpt-6-astra", "gpt-daybreak-blue-latest", "security-artifact-gate"
        codex = {lane for lane, spec in lanes.items() if spec["vendor"] == "codex"}

        # Every Codex key is exactly one of: the single working lane, the deprecated gate alias, withdrawn.
        self.assertEqual(withdrawn, {"gpt-6.1-sol", "gpt-6-luna", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"})
        self.assertEqual(deprecated, {daybreak})
        self.assertEqual(codex, {astra} | deprecated | withdrawn)
        self.assertFalse(withdrawn & deprecated)
        self.assertEqual(pins, {daybreak: gate})
        self.assertEqual(pinned_effort, {astra: "xhigh"})
        self.assertEqual((lanes[astra]["std"], lanes[astra]["top"]), ("xhigh", "xhigh"))
        self.assertEqual(lanes[astra]["orca_efforts"][-1], "xhigh")

        positions = {"class " + name + " #" + str(i + 1): lane
                     for name, order in classes.items() for i, lane in enumerate(order)}
        positions.update({"process " + name + " #" + str(i + 1): lane
                          for name, order in process_lanes.items() for i, lane in enumerate(order)})
        positions.update({"fixed " + proc: lane for proc, (lane, _effort) in fixed.items()})
        positions["coordinator"] = coordinator[0]
        positions.update({"output rule " + lane: lane for lane in rules})
        probes = json.loads((SCRIPT.parent.parent / "eval" / "probes.json").read_text(encoding="utf-8"))["probes"]
        positions.update({"probe " + probe["id"] + " #" + str(i + 1): lane
                          for probe in probes for i, lane in enumerate(probe["lanes"])})
        self.assertGreater(len(positions), 100)  # the sweep really covers the tables.
        for where, lane in sorted(positions.items()):
            with self.subTest(position=where, lane=lane):
                self.assertIn(lane, lanes)
                self.assertNotIn(lane, withdrawn)
                if lanes[lane]["vendor"] == "codex" and lane != astra:
                    # The only exception: Daybreak as the fixed gate, and its gate output rule.
                    self.assertEqual(lane, daybreak)
                    self.assertIn(where, ("fixed " + gate, "output rule " + daybreak))
        # Fixed efforts: every GPT position that names an effort names xhigh.
        self.assertEqual(coordinator, (astra, "xhigh"))
        self.assertEqual(fixed["security-bizlogic-2nd"], (astra, "xhigh"))
        self.assertEqual(fixed[gate], (daybreak, "xhigh"))

        # Final class lists (D-101). B, A-verify, D and coding are unchanged.
        self.assertEqual(classes["A"], ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"])
        self.assertEqual(classes["B"], [astra, "claude-fable-5-1", "claude-opus-5-5"])
        self.assertEqual(classes["A-verify"], [astra, "claude-fable-5-1", "claude-opus-5-5"])
        self.assertEqual(classes["C-realtime"], ["grok-4.6", "claude-opus-5-5", astra])
        self.assertEqual(classes["C-platform"], ["gemini-3.8-flash", "claude-opus-5-5", astra])
        self.assertEqual(classes["D"], ["claude-opus-5-5"])
        self.assertEqual(process_lanes["coding"], ["claude-opus-5-5", "claude-fable-5-1"])
        # A quota demotion past gpt-6-astra lands on a Claude lane, never on another GPT lane.
        for name, order in classes.items():
            if astra in order[:-1]:
                with self.subTest(demotion=name):
                    self.assertEqual(lanes[order[order.index(astra) + 1]]["vendor"], "claude")

        # Task-fit rows: an OpenAI model row is gpt-6-astra at xhigh, nothing else.
        registry = self.m.load_registry()
        vendor_of = {m["id"]: m["vendor"] for m in registry["models"]}
        policy = json.loads((REFERENCES / "task-fit-policy.json").read_text(encoding="utf-8"))
        gpt_rows = 0
        for profile, entries in policy["profiles"].items():
            for entry in entries:
                with self.subTest(profile=profile, model=entry["model"]):
                    self.assertIn(entry["model"], vendor_of)
                    self.assertNotIn(entry["model"], withdrawn | deprecated | {"gpt-6-sol"})
                    if vendor_of[entry["model"]] == "openai":
                        gpt_rows += 1
                        self.assertEqual((entry["model"], entry["efforts"]), (astra, ["xhigh"]))
        self.assertEqual(gpt_rows, 2)  # PLAN_ARCHITECTURE and CODE_COMPLEX.
        self.assertFalse(any(vendor_of[e["model"]] == "openai" for p in ("CODE_SIMPLE", "WRITING")
                             for e in policy["profiles"][p]))

        # Withdrawn keys stay readable for ledger rows and say why they are out.
        for lane in sorted(withdrawn):
            with self.subTest(withdrawn=lane):
                self.assertIn("원장 호환용(우선순위 밖)", lanes[lane]["ctx"])
                self.assertEqual(evaluator_vendors()[lane], "codex")
                self.assertEqual(registry["legacy_lane_migration"][lane]["status"], "held-withdrawn-by-owner")
                self.assertIn(registry["legacy_lane_migration"][lane]["candidate"], {astra, "claude-haiku-5-5"})
        # Withdrawal is a routing decision, not a provider fact: the models stay active in the registry.
        models = {m["id"]: m for m in registry["models"]}
        for lane in sorted(withdrawn):
            self.assertEqual(models[lane]["lifecycle"], "active")

    def test_d101_artifact_gate_returns_to_daybreak_as_the_only_deprecated_position(self):
        # D-101 (2026-10-12, Simon: "보안게이트는 데이브레이크로 할려했는데 그게 안돼면 opus 5.5로 하자."):
        # the artifact gate is the deprecated Daybreak alias again. The provider fact and the central
        # planner block are untouched; the Opus fallback is not implemented.
        lanes = ast.literal_eval(module_literal("routing.py", "LANES"))
        classes = ast.literal_eval(module_literal("routing.py", "CLASS_LANES"))
        coding = ast.literal_eval(module_literal("routing.py", "PROCESS_LANES"))["coding"]
        fixed = {p[0]: p[3] for p in ast.literal_eval(module_literal("routing.py", "PROCESSES")) if p[3]}
        gate = "gpt-daybreak-blue-latest"
        self.assertEqual(fixed["security-artifact-gate"], (gate, "xhigh"))
        self.assertEqual(fixed["security-bizlogic-2nd"], ("gpt-6-astra", "xhigh"))
        # G1_SEC_SAME_MODEL: the two gates are different models. G1: both are Codex and the coding
        # lanes are Claude only, so the gate never grades its own vendor's work.
        self.assertNotEqual(fixed["security-artifact-gate"][0], fixed["security-bizlogic-2nd"][0])
        gate_vendors = {lanes[fixed[p][0]]["vendor"] for p in ("security-artifact-gate", "security-bizlogic-2nd")}
        self.assertEqual(gate_vendors, {"codex"})
        self.assertFalse({lanes[lane]["vendor"] for lane in coding} & gate_vendors)
        self.assertEqual(lanes[gate]["orca_efforts"][-1], "xhigh")  # the pinned effort is the Orca cap.

        # The alias holds no other position.
        elsewhere = {lane for order in classes.values() for lane in order} | set(coding)
        elsewhere |= {lane for proc, (lane, _effort) in fixed.items() if proc != "security-artifact-gate"}
        elsewhere.add(ast.literal_eval(module_literal("routing.py", "COORDINATOR"))[0])
        self.assertNotIn(gate, elsewhere)
        self.assertEqual(ast.literal_eval(module_literal("routing.py", "DEPRECATED_LANES")), {gate})
        self.assertIn("deprecated", lanes[gate]["ctx"])
        self.assertIn("게이트 고정 전용", lanes[gate]["ctx"])
        rules = ast.literal_eval(module_literal("routing.py", "OUTPUT_RULES"))
        self.assertNotIn("gpt-6.1-sol", rules)  # the gate's output rule moved back with the gate.
        self.assertIn("GATE: BLOCK", rules[gate]["allow"])
        self.assertIn("FAIL", rules[gate]["deny"])
        self.assertIn("LANE_DEPRECATED", rules[gate]["deny"])
        self.assertIn("references/security-artifact-gate.md",
                      SCRIPT.with_name("routing.py").read_text(encoding="utf-8"))

        data = self.m.load_registry()
        self.assertEqual(data["version"], "2026-10-12.3")
        self.assertEqual((data["checked_at"], data["data_as_of"]), ("2026-10-12T11:43:08+09:00", "2026-10-12"))
        models = {m["id"]: m for m in data["models"]}
        self.assertEqual(models[gate]["lifecycle"], "deprecated")  # the move does not revive the alias.
        migration = data["legacy_lane_migration"]
        self.assertEqual(migration[gate], {"candidate": gate, "status": "keep-security-pin-resolve-per-run"})
        # MODEL_NOT_ACTIVE is unchanged: the packaged registry still blocks an alias candidate.
        observed_at = data["checked_at"]
        trial = candidate(model=gate, resolved_model="gpt-5.6-sol", observed_at=observed_at,
                          resolution_observed_at=observed_at, resolution_evidence="model/list",
                          billing={"mode": "unknown", "account_ref": "seat-a"},
                          quota={"used_pct": None, "observed_at": observed_at},
                          access_proof={"program": "daybreak_blue", "verified": True, "observed_at": observed_at,
                                        "evidence": "authorized catalog", "account_ref": "seat-a"})
        out = self.m.constrain_runtime({"candidates": [trial]}, data, observed_at)["candidates"][0]
        self.assertEqual(out["registry_errors"], ["MODEL_NOT_ACTIVE"])
        self.assertFalse(out["available"])
        # Both canary records stay: D-98 as history, D-101 as the current evidence.
        self.assertTrue(any(n.startswith("D-98(") and "ctx_ff39c4a979ba" in n for n in data["notes"]))
        note = next(n for n in data["notes"] if n.startswith("D-101("))
        for needle in ("gpt 6.1 sol은 너무 느려서 빼기로 결정", "보안게이트는 데이브레이크로 할려했는데 그게 안돼면 opus 5.5로 하자.",
                       "gpt 쪽은 astra 말고는 쓰지마. gpt 를 넣어야한다면 astra xhigh.",
                       "run_b08adccb4ec8", "ctx_41243c1a0d26", "launch.requested == launch.effective",
                       "CWE-89", "CWE-78", "CWE-22", "CWE-502", "MODEL_NOT_ACTIVE", "심은 샘플 1건",
                       "예고 없이 사라질 수 있다", "'GPT-5'", "결함 때문이 아니다", "D-91 canary",
                       "held-withdrawn-by-owner", "재개 조건", "canary 를 돌리지 않은 것", "구현하지 않았다",
                       "G1 과 충돌", "Simon 의 판정이 필요하다"):
            with self.subTest(note=needle):
                self.assertIn(needle, note)
        section = " ".join(catalog_map_section("Lane migration pending").split())
        for needle in ("D-101", "ctx_41243c1a0d26", "`held-withdrawn-by-owner`", "재개 조건",
                       "`keep-security-pin-resolve-per-run`", "D-98", "ctx_ff39c4a979ba"):
            with self.subTest(section=needle):
                self.assertIn(needle, section)

    def test_d101_gate_reference_states_the_rubric_fail_closed_rules_and_the_open_fallback(self):
        # The rules are a written contract for whoever reads the gate output; no script parses it.
        path = REFERENCES / "security-artifact-gate.md"
        self.assertTrue(path.is_file(), "security artifact gate reference is missing")
        raw = path.read_text(encoding="utf-8")
        text = " ".join(raw.split())
        self.assertIn("**`gpt-daybreak-blue-latest` @ `xhigh`**", text)
        self.assertNotIn("**`gpt-6.1-sol` @ `xhigh`**", text)
        pinned = text.split("## Pinned lane", 1)[1].split("## Before each run", 1)[0]
        for needle in ("D-101", "Simon's directive", "gpt 6.1 sol은 너무 느려서 빼기로 결정",
                       "The alias works on this account today", "still marks the alias deprecated",
                       "`MODEL_NOT_ACTIVE`", "still cannot make this gate ready", "**LANE_DEPRECATED**",
                       "Anywhere else it is still rejected", "`keep-security-pin-resolve-per-run`"):
            with self.subTest(pinned=needle):
                self.assertIn(needle, pinned)
        for cwe in ("CWE-89", "CWE-78", "CWE-22", "CWE-502", "CWE-798", "CWE-327", "CWE-918"):
            with self.subTest(rubric=cwe):
                self.assertIn("| " + cwe + " |", raw)
        rubric = text.split("## Rubric", 1)[1].split("## Required output", 1)[0]
        self.assertIn("Authentication or authorization bypass", rubric)
        self.assertIn("Unsafe file or permission handling", rubric)
        shape = text.split("## Required output", 1)[1].split("## Fail-closed rules", 1)[0]
        self.assertIn("The first line is exactly `GATE: BLOCK` or `GATE: PASS`", shape)
        self.assertIn("one finding per line: `CWE-<n> | <location> | <reason>`", shape)
        rules = text.split("## Fail-closed rules", 1)[1].split("## Open item", 1)[0]
        self.assertIn("**FAIL, never PASS**", rules)
        for needle in ("**Empty output**", "**Refusal or blocked output**", "**Missing first line**",
                       "**Ambiguous verdict**", "Do not read silence as a pass",
                       "Nothing in the scripts parses gate output today"):
            with self.subTest(rule=needle):
                self.assertIn(needle, rules)
        self.assertIn("The gate never grades work made by its own vendor", text)
        # Before each run: the catalog check, and a missing alias or empty/blocked output is a FAIL.
        before = text.split("## Before each run", 1)[1].split("## Rubric", 1)[0]
        for needle in ("~/.codex/models_cache.json", "still listed", "no retirement or upgrade entry",
                       "the gate **FAILS**", "It never passes", "Do not start the gate on another model",
                       "empty or blocked", "No script performs this catalog check today"):
            with self.subTest(before=needle):
                self.assertIn(needle, before)
        # The Opus fallback is an open item, not an implemented route.
        open_item = text.split("## Open item", 1)[1].split("## Replacement rule", 1)[0]
        for needle in ("**OPEN. Not implemented. Needs Simon's ruling.**", "`claude-opus-5-5`", "collides with G1",
                       "(a) `claude-opus-5-5` fallback", "G1 is relaxed for this fallback case only",
                       "(b) `gpt-6-astra` takes both security gates",
                       "G1_SEC_SAME_MODEL is relaxed for this fallback case only",
                       "Neither option is coded, tested or canaried", "the gate fails and the coding round stops"):
            with self.subTest(open_item=needle):
                self.assertIn(needle, open_item)
        replacement = text.split("## Replacement rule", 1)[1].split("## Canary records", 1)[0]
        for needle in ("newer cyber model", "~/.codex/models_cache.json", "same seeded canary",
                       "tier-1 record", "No automatic promotion"):
            with self.subTest(replacement=needle):
                self.assertIn(needle, replacement)
        canary = text.split("## Canary records", 1)[1]
        for needle in ("run_b08adccb4ec8", "ctx_41243c1a0d26", "run_8f7a27febc38", "ctx_ff39c4a979ba",
                       "`launch.requested == launch.effective`", "`GATE: BLOCK`", "one seeded sample",
                       "not proof of parity", "about 30 seconds", "\"GPT-5\"", "may disappear without notice",
                       "not because of a defect"):
            with self.subTest(canary=needle):
                self.assertIn(needle, canary)
        # validate_skill E012: a reference file must not link to another reference file.
        self.assertNotRegex(raw, r"\]\((?!https?://)[^)]*\)")
        skill = (SCRIPT.parent.parent / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("(references/security-artifact-gate.md)", skill)

    def test_d99_haiku_55_is_registered_with_both_price_tiers(self):
        # D-99 (2026-10-12): facts re-read from the official pages; the price depends on prompt length.
        data = self.m.load_registry()
        haiku = next(m for m in data["models"] if m["id"] == "claude-haiku-5-5")
        self.assertEqual((haiku["surface"], haiku["vendor"], haiku["lifecycle"], haiku["id_namespace"]),
                         ("claude", "anthropic", "active", "provider-api"))
        self.assertNotIn("generation", haiku)
        self.assertEqual((haiku["released_at"], haiku["retirement_not_before"]), ("2026-10-07", "2027-10-07"))
        self.assertEqual((haiku["context_tokens"], haiku["max_output_tokens"]), (1000000, 128000))
        self.assertEqual(haiku["api_efforts"], ["low", "medium", "high", "xhigh", "max"])
        self.assertEqual((haiku["thinking"], haiku["aliases"]), ("adaptive", ["haiku"]))
        self.assertIn("2.1.293", haiku["transport_note"])
        self.assertIn("default effort is medium", haiku["transport_note"])
        pricing = haiku["pricing"]
        self.assertEqual(pricing["scope"], "direct-api-standard-usd-per-million-tokens")
        # Prompts up to 100,000 tokens pay the base prices.
        self.assertEqual((pricing["input"], pricing["cached_input"], pricing["output"]), ("0.1", "0.01", "0.5"))
        # Prompts over 100,000 tokens pay the single tier: five times the base prices.
        self.assertEqual(pricing["tiers"], [{"above_input_tokens": 100000, "input": "0.5", "cached_input": "0.05",
                                             "output": "2.5", "cache_write": None}])
        for field in ("input", "cached_input", "output"):
            with self.subTest(field=field):
                self.assertEqual(Decimal(pricing["tiers"][0][field]), 5 * Decimal(pricing[field]))
        # Each tier has two cache-write durations; one field cannot hold both, so the note carries them.
        self.assertIsNone(pricing["cache_write"])
        for needle in ("over 100,000 tokens", "exactly 100,000 tokens pays the base prices",
                       "including cache reads and cache writes", "each request is priced on its own",
                       "$0.125/MTok", "$0.20/MTok", "$0.625/MTok", "$1/MTok"):
            with self.subTest(note=needle):
                self.assertIn(needle, pricing["note"])
        self.assertEqual((data["sources"]["cl_haiku55"], data["sources"]["cl_haiku55_news"]),
                         ("https://platform.claude.com/docs/en/models/haiku-5-5/overview",
                          "https://www.anthropic.com/claude-haiku-5-5"))
        self.assertTrue({"cl_haiku55", "cl_haiku55_news", "cl_models", "cl_effort", "cl_pricing",
                         "cl_lifecycle", "cl_billing"} <= set(haiku["sources"]))
        # Schema: the threshold is a non-negative integer and tier prices are finite numbers.
        for field, bad in (("above_input_tokens", "100000"), ("above_input_tokens", -1),
                           ("above_input_tokens", 100000.0), ("above_input_tokens", True),
                           ("input", "NaN"), ("output", "-2.5")):
            with self.subTest(field=field, bad=bad):
                broken = copy.deepcopy(data)
                entry = next(m for m in broken["models"] if m["id"] == "claude-haiku-5-5")
                entry["pricing"]["tiers"][0][field] = bad
                with self.assertRaises(ValueError):
                    self.m.validate_registry(broken)
        # The exact ID binds and efforts intersect; a public listing grants no billing or access.
        observed_at = data["checked_at"]
        trial = candidate(surface="claude", model="claude-haiku-5-5", observed_at=observed_at,
                          provider_efforts=["low", "medium", "ultra"], transport_efforts=["low", "ultracode"],
                          quota={"used_pct": None, "observed_at": observed_at})
        out = self.m.constrain_runtime({"candidates": [trial]}, data, observed_at)["candidates"][0]
        self.assertEqual(out["registry_errors"], [])
        self.assertEqual((out["provider_efforts"], out["transport_efforts"]), (["low", "medium"], ["low"]))
        self.assertEqual(out["billing"], {"mode": "unknown", "verified": False})
        # The haiku alias varies by provider: without a fresh matching resolution it never dispatches.
        for resolved, expected in ((None, "ALIAS_RESOLUTION_UNVERIFIED"),
                                   ("claude-haiku-4-5", "MODEL_RESOLUTION_MISMATCH")):
            with self.subTest(resolved=resolved):
                alias = candidate(surface="claude", model="haiku", resolved_model=resolved, observed_at=observed_at,
                                  quota={"used_pct": None, "observed_at": observed_at})
                result = self.m.constrain_runtime({"candidates": [alias]}, data, observed_at)["candidates"][0]
                self.assertEqual(result["model"], "claude-haiku-5-5")
                self.assertFalse(result["available"])
                self.assertIn(expected, result["registry_errors"])

    def test_d99_class_a_adds_haiku_55_and_d101_makes_it_the_first_lane(self):
        # D-99: registered beside the other lanes after its canary (run_8f7a27febc38), then the
        # Claude-side first fallback. D-101 (same day, Simon's directive) withdrew gpt-6-luna, so it is
        # now the first class A lane. Sonnet 5.5 stays, and it is still not a running lane without the
        # certificate. No canary was run for the new order.
        lanes = ast.literal_eval(module_literal("routing.py", "LANES"))
        classes = ast.literal_eval(module_literal("routing.py", "CLASS_LANES"))
        coding = ast.literal_eval(module_literal("routing.py", "PROCESS_LANES"))["coding"]
        fixed = {p[0]: p[3] for p in ast.literal_eval(module_literal("routing.py", "PROCESSES")) if p[3]}
        new = "claude-haiku-5-5"
        self.assertEqual(classes["A"], [new, "claude-sonnet-5-5", "claude-opus-5-5"])
        # Class B, A-verify and D are untouched.
        self.assertEqual(classes["B"], ["gpt-6-astra", "claude-fable-5-1", "claude-opus-5-5"])
        self.assertEqual(classes["A-verify"], ["gpt-6-astra", "claude-fable-5-1", "claude-opus-5-5"])
        self.assertEqual(classes["D"], ["claude-opus-5-5"])
        elsewhere = {lane for name, order in classes.items() if name != "A" for lane in order} | set(coding)
        elsewhere |= {lane for lane, _effort in fixed.values()}
        self.assertNotIn(new, elsewhere)
        spec = lanes[new]
        self.assertEqual((spec["cli"], spec["vendor"], spec["effort_style"], spec["dispatch"]),
                         ("claude", "claude", "flag", "orca"))
        self.assertEqual((spec["std"], spec["top"]), ("low", "medium"))
        self.assertEqual(spec["orca_efforts"], ("low", "medium", "high", "xhigh", "max"))
        self.assertEqual(spec["orca_efforts"], lanes["claude-sonnet-5-5"]["orca_efforts"])
        self.assertNotIn("quota_bucket", spec)  # the general claude weekly quota.
        self.assertTrue(spec["ctx"].startswith("canary 통과 · 인증서 전"), spec["ctx"])
        self.assertEqual(evaluator_vendors()[new], "claude")

        data = self.m.load_registry()
        migration = data["legacy_lane_migration"]
        self.assertEqual(migration[new], {"candidate": new, "status": "pending-transport-and-certificate"})
        self.assertEqual(migration["claude-sonnet-5-5"],
                         {"candidate": "claude-sonnet-5-5", "status": "pending-transport-and-certificate"})
        note = next(n for n in data["notes"] if n.startswith("D-99("))
        for needle in ("run_8f7a27febc38", "ctx_cd78cf210447", "launch.requested == launch.effective",
                       "message.model claude-haiku-5-5", "2,3,5,6,7", "ERROR=5 WARN=7 INFO=9 DEBUG=3",
                       "선두 레인이 아니다", "Sonnet 5.5 는 그대로 남는다", "쿼터 절감은 미측정",
                       "별도 비교 근거가 필요하다"):
            with self.subTest(note=needle):
                self.assertIn(needle, note)
        section = catalog_map_section("Lane migration pending")
        rows = {line.split("|")[1].strip(): line for line in section.splitlines() if line.startswith("| `")}
        self.assertIn("`pending-transport-and-certificate`", rows["`" + new + "`"])
        self.assertIn("ctx_cd78cf210447", " ".join(section.split()))
        # A registry ID is no longer a CLI-only catalog name.
        self.assertNotIn(new, {row[1] for row in catalog_map_rows()})
        # D-99 left the shadow task-fit policy alone. D-101 names it in CODE_SIMPLE only (rank 0).
        policy = json.loads((REFERENCES / "task-fit-policy.json").read_text(encoding="utf-8"))
        named = {profile for profile, entries in policy["profiles"].items()
                 if new in {entry["model"] for entry in entries}}
        self.assertEqual(named, {"CODE_SIMPLE"})
        # Eval probes offer it for class A problems only.
        probes = json.loads((SCRIPT.parent.parent / "eval" / "probes.json").read_text(encoding="utf-8"))["probes"]
        for probe in probes:
            with self.subTest(probe=probe["id"]):
                self.assertEqual(new in probe["lanes"], probe["class"] == "A")


if __name__ == "__main__":
    unittest.main()
