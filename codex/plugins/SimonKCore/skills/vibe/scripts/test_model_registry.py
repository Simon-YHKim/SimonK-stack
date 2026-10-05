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
                         "claude-fable-5-1", "claude-sonnet-5-5", "claude-sonnet-5",
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
        self.assertTrue({"claude-opus-5", "claude-opus-5-5", "gpt-5.6-terra", "gpt-6.1-sol"} <= seen)

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

    def test_registry_and_task_fit_windows_cover_the_2026_10_05_recheck(self):
        # The 2026-10-04 facts (21:46 KST) would expire REGISTRY_STALE on 2026-10-11 21:46 KST.
        data = self.m.load_registry()
        policy = json.loads((REFERENCES / "task-fit-policy.json").read_text(encoding="utf-8"))
        floor = datetime.fromisoformat("2026-10-05T14:00:00+09:00")
        checked = datetime.fromisoformat(data["checked_at"])
        self.assertGreaterEqual(checked, floor)
        self.assertGreaterEqual(datetime.fromisoformat(policy["checked_at"]), floor)
        # checked_at is the earliest evidence, never later than the policy's own reading.
        self.assertLessEqual(checked, datetime.fromisoformat(policy["checked_at"]))
        earliest = min(checked + timedelta(seconds=self.m.MAX_FACT_AGE_SECONDS),
                       datetime.fromisoformat(policy["valid_until"]))
        self.assertGreaterEqual(earliest, datetime.fromisoformat("2026-10-12T14:00:00+09:00"))

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
        # Simon's 2026-10-05 instruction gave claude-sonnet-5-5 and gpt-6-luna class A lanes.
        self.assertTrue({"gpt-6-sol", "grok-4.7", "grok-4.5"} <= unlaned)
        self.assertFalse({"claude-sonnet-5-5", "gpt-6-luna"} & unlaned)
        pending = catalog_map_section("Lane migration pending")
        self.assertIn("ORCA_UNREGISTERED_PROCESS_OR_MODEL", pending)
        for model_id in sorted(unlaned):
            with self.subTest(model=model_id):
                self.assertIn("`" + model_id + "`", pending)

    def test_d67_lanes_passed_canary_but_still_pending_certificate(self):
        # D-67 adds lanes alongside the legacy keys; registration is not a working route.
        # 2.14.2: the read-only canary (2026-10-04) passed for both lanes, but native send and the
        # account/billing certificate are still missing, so they stay pending (not keep-*).
        data = self.m.load_registry()
        migration = data["legacy_lane_migration"]
        for lane in ("claude-opus-5-5", "gpt-6.1-sol"):
            with self.subTest(lane=lane):
                self.assertIn(lane, routing_lanes())
                self.assertEqual(migration[lane], {"candidate": lane, "status": "pending-transport-and-certificate"})
        for legacy in ("claude-opus-5", "gpt-5.6-sol", "gpt-5.6-terra", "grok-4.6"):
            self.assertIn(legacy, routing_lanes())  # ledger.py rejects rows whose lane is not in LANES.
        self.assertEqual(migration["claude-opus-5"],
                         {"candidate": "claude-opus-5-5", "status": "pending-transport-and-certificate"})
        self.assertEqual(migration["gpt-5.6-sol"],
                         {"candidate": "gpt-6.1-sol", "status": "pending-transport-and-certificate"})
        # The D-67 canary covered only these two lanes; terra's tier evaluation keeps its own status.
        # The class A lanes passed their own canary on 2026-10-05 (D-91).
        self.assertEqual(migration["gpt-5.6-terra"],
                         {"candidate": "gpt-6.1-sol", "status": "pending-evaluation-not-equivalent-tier"})
        self.assertEqual(migration["gpt-5.6-luna"],
                         {"candidate": "gpt-6-luna", "status": "pending-transport-and-certificate"})
        self.assertNotIn("gpt-6-sol", {v["candidate"] for v in migration.values()})
        self.assertEqual(migration["grok-4.6"], {"candidate": "grok-4.7", "status": "pending-quota-and-canary"})
        certificate = {k for k, v in migration.items() if v["status"] == "pending-transport-and-certificate"}
        self.assertEqual(certificate, {"claude-opus-5-5", "claude-opus-5", "gpt-6.1-sol", "gpt-5.6-sol",
                                       "claude-sonnet-5", "claude-sonnet-5-5", "gpt-5.6-luna", "gpt-6-luna"})
        section = catalog_map_section("Lane migration pending")
        rows = {line.split("|")[1].strip(): line for line in section.splitlines() if line.startswith("| `")}
        pending = " ".join(section.split())
        self.assertIn("launch.requested", pending)
        self.assertIn("2026-10-04", pending)
        for lane in ("claude-opus-5-5", "gpt-6.1-sol"):
            with self.subTest(row=lane):
                self.assertIn("`" + lane + "`", pending)
                self.assertIn("`pending-transport-and-certificate`", rows["`" + lane + "`"])
                self.assertNotIn("pending-transport-and-canary", rows["`" + lane + "`"])

    def test_simon_261005_class_a_uses_current_lanes_canary_passed_pending_certificate(self):
        # Simon 2026-10-05 ("5.5로 전환해"): class A moves to the current-generation lanes, added
        # beside the legacy keys like D-67. Both passed the read-only canary (D-91, run_0a369252175f)
        # but are not running lanes until the launch certificate exists.
        lanes = ast.literal_eval(module_literal("routing.py", "LANES"))
        classes = ast.literal_eval(module_literal("routing.py", "CLASS_LANES"))
        self.assertEqual(classes["A"], ["gpt-6-luna", "claude-sonnet-5-5", "claude-opus-5-5"])
        listed = {lane for order in classes.values() for lane in order}
        listed |= set(ast.literal_eval(module_literal("routing.py", "PROCESS_LANES"))["coding"])
        for legacy in ("gpt-5.6-luna", "claude-sonnet-5"):
            with self.subTest(legacy=legacy):
                self.assertIn(legacy, lanes)  # ledger.py rejects rows whose lane is not in LANES.
                self.assertNotIn(legacy, listed)
                self.assertIn("원장 호환용(우선순위 밖)", lanes[legacy]["ctx"])
        # lane: (vendor, std, top, efforts Orca 1.4.218 accepts)
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
                self.assertEqual(migration[lane], {"candidate": lane, "status": "pending-transport-and-certificate"})
        self.assertEqual(migration["claude-sonnet-5"],
                         {"candidate": "claude-sonnet-5-5", "status": "pending-transport-and-certificate"})
        self.assertEqual(migration["gpt-5.6-luna"],
                         {"candidate": "gpt-6-luna", "status": "pending-transport-and-certificate"})
        section = catalog_map_section("Lane migration pending")
        rows = {line.split("|")[1].strip(): line for line in section.splitlines() if line.startswith("| `")}
        blocked = next(b for b in section.split("\n- ") if "ORCA_UNREGISTERED_PROCESS_OR_MODEL" in b)
        blocked = blocked.split("ORCA_UNREGISTERED_PROCESS_OR_MODEL")[0]
        for lane in expected:
            with self.subTest(row=lane):
                self.assertIn("`pending-transport-and-certificate`", rows["`" + lane + "`"])
                self.assertNotIn("pending-transport-and-canary", rows["`" + lane + "`"])
                self.assertNotIn("`" + lane + "`", blocked)
        self.assertIn("run_0a369252175f", " ".join(section.split()))

    def test_task_fit_policy_keeps_sonnet_55_out_until_its_reentry_conditions(self):
        # D-90: Artificial Analysis puts Sonnet 5.5 off the intelligence/cost-per-task frontier at
        # every effort, so the shadow policy names other models; re-entry needs a re-measurement.
        policy = json.loads((REFERENCES / "task-fit-policy.json").read_text(encoding="utf-8"))
        named = {entry["model"] for entries in policy["profiles"].values() for entry in entries}
        self.assertNotIn("claude-sonnet-5-5", named)
        def rank0(profile):
            return {e["model"] for e in policy["profiles"][profile] if e["rank"] == 0}
        self.assertEqual(rank0("CODE_SIMPLE"), {"gpt-6.1-sol", "gpt-6-sol"})
        self.assertIn({"model": "claude-opus-5-5", "efforts": ["medium"], "rank": 2,
                       "sources": ["anthropic_opus", "aa_opus"]}, policy["profiles"]["CODE_SIMPLE"])
        self.assertEqual(rank0("WRITING"), {"claude-opus-5-5"})
        self.assertTrue(any("D-90" in note and "재진입 조건" in note for note in policy["notes"]))

    def test_catalog_map_states_lane_dispositions_and_legacy_routing_as_built(self):
        migration = self.m.load_registry()["legacy_lane_migration"]
        keep = sorted(k for k, v in migration.items() if v["status"].startswith("keep-"))
        # D-90: a held migration is stopped with written resume conditions.
        held = sorted(k for k, v in migration.items() if v["status"].startswith("held-"))
        self.assertEqual(len(keep) + len(held)
                         + sum(v["status"].startswith("pending-") for v in migration.values()),
                         len(migration))
        self.assertTrue(keep)
        # Simon's 2026-10-05 instruction resumed the only held entry (claude-sonnet-5, D-90); the
        # held-* checks below stay generic for any future hold.
        self.assertEqual(held, [])
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


if __name__ == "__main__":
    unittest.main()
