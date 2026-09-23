"""Offline contract tests for the umbrella planner; no worker or Bot is launched."""
import copy
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT = Path(__file__).with_name("orchestrate.py")
NOW = "2026-09-23T10:00:00+00:00"


def candidate(name="small", surface="codex", **changes):
    item = {
        "id": name, "surface": surface, "transport": "cli",
        "model": "fixture-" + name, "lifecycle": "active", "available": True,
        "observed_at": NOW, "evidence": "offline test fixture", "quality_tier": 2,
        "capabilities": ["reasoning", "code", "research"], "resource_rank": 1,
        "provider_efforts": ["low", "high", "xhigh"],
        "transport_efforts": ["low", "high", "xhigh"],
        "effort_by_demand": {"routine": "low", "reasoning": "high", "critical": "xhigh"},
        "billing": {"mode": "subscription", "verified": True,
                    "extra_usage_enabled": False, "account_ref": "test-account"},
        "quota": {"used_pct": 10, "observed_at": NOW, "bucket": "test-weekly"},
    }
    item.update(changes)
    return item


def step(name="read", **changes):
    item = {"id": name, "task": "Inspect the supplied input", "kind": "llm",
            "skills": ["explain"], "needs": ["reasoning"], "demand": "routine",
            "depends_on": [], "writes": False}
    item.update(changes)
    return item


def fixture_registry(candidates):
    """Isolate planner behavior from changing production model catalogs."""
    vendor = {"codex": "openai", "claude": "anthropic", "antigravity": "google", "grok": "xai"}
    sources = {"openai": "https://developers.openai.com/api/docs/models",
               "anthropic": "https://platform.claude.com/docs/en/models/overview",
               "google": "https://ai.google.dev/gemini-api/docs/models",
               "xai": "https://docs.x.ai/developers/models"}
    models = {}
    for c in candidates or [candidate()]:
        if c["surface"] not in vendor:
            continue
        v = vendor[c["surface"]]
        models[c["model"]] = {"id": c["model"], "surface": c["surface"], "vendor": v,
                              "id_namespace": "provider-api",
                              "lifecycle": "active", "api_efforts": ["low", "medium", "high", "xhigh", "max"],
                              "aliases": [], "sources": [v], "pricing": None}
    if not models:
        return fixture_registry([candidate()])
    return {"schema_version": 1, "version": "offline-fixture", "checked_at": NOW,
            "models": list(models.values()), "sources": sources}


class OrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "The /vibe umbrella planner is not implemented")
        spec = importlib.util.spec_from_file_location("vibe_orchestrate", SCRIPT)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.catalog = {name: {"name": name, "path": "/fixture/" + name + "/SKILL.md",
                              "description": name} for name in ("explain", "dev-orchestrator", "vibe-bot")}

    def plan(self, steps=None, candidates=None, budget=None, **runtime_changes):
        runtime = {"candidates": candidates if candidates is not None else [candidate()],
                   "tools": [], "observed_at": NOW}
        runtime.update(runtime_changes)
        request = {"run_id": "test-run", "steps": steps or [step()], "budget": budget or {}}
        return self.m.make_plan(request, self.catalog, runtime, NOW, fixture_registry(runtime["candidates"]))

    def events(self, plan, *events):
        return [dict(run_id=plan["run_id"], plan_digest=plan["plan_digest"], **event) for event in events]

    def tool_cost(self, argv):
        return {"argv_sha256": self.m.digest(argv), "verified": True, "evidence": "Inspected offline command",
                "observed_at": NOW, "upper_usd_per_attempt": 0}

    def test_subscription_and_effort_are_explicit(self):
        p = self.plan()
        self.assertEqual(p["status"], "ready")
        self.assertEqual(p["steps"][0]["route"]["requested_effort"], "low")
        self.assertIsNone(p["steps"][0]["route"]["effective_effort"])
        self.assertEqual(p["budget"]["reserved_upper_usd"], 0)

    def test_paid_default_is_zero(self):
        c = candidate(billing={"mode": "api", "verified": True, "account_ref": "api"},
                      upper_usd_per_attempt=0.1)
        self.assertEqual(self.plan(candidates=[c])["status"], "blocked")

    def test_quality_mode_does_not_authorize_spend(self):
        c = candidate(quality_tier=3, billing={"mode": "api", "verified": True},
                      upper_usd_per_attempt=0.1)
        self.assertEqual(self.plan(candidates=[c], budget={"mode": "quality"})["status"], "blocked")

    def test_unknown_billing_is_not_zero(self):
        c = candidate(billing={"mode": "unknown", "verified": False})
        p = self.plan(candidates=[c])
        self.assertEqual(p["status"], "blocked")
        self.assertIn("BILLING_UNVERIFIED", str(p))

    def test_paid_price_missing_is_not_zero(self):
        c = candidate(billing={"mode": "api", "verified": True})
        p = self.plan(candidates=[c], budget={"approved_usd": 1})
        self.assertIn("COST_UNKNOWN", str(p))

    def test_retry_and_review_reservations_are_in_total(self):
        c = candidate(billing={"mode": "api", "verified": True, "account_ref": "test-api"}, upper_usd_per_attempt=0.3)
        p = self.plan([step(), step("review", depends_on=["read"])], [c],
                      {"approved_usd": 1, "max_attempts": 2})
        self.assertEqual(p["status"], "blocked")
        self.assertAlmostEqual(p["budget"]["reserved_upper_usd"], 1.2)

    def test_invalid_money_and_nan_are_rejected(self):
        for value in (-1, float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.plan(budget={"approved_usd": value})

    def test_paid_unknown_or_negative_quote_is_rejected(self):
        for value in (-1, float("nan"), True):
            c = candidate(billing={"mode": "api", "verified": True}, upper_usd_per_attempt=value)
            self.assertEqual(self.plan(candidates=[c], budget={"approved_usd": 2})["status"], "blocked")

    def test_provider_and_transport_effort_must_intersect(self):
        p = self.plan([step(demand="critical")],
                      [candidate(quality_tier=3, transport_efforts=["low", "high"])])
        self.assertEqual(p["status"], "blocked")
        self.assertIn("EFFORT_UNSUPPORTED", str(p))

    def test_pending_model_and_stale_observation_are_excluded(self):
        for changes in ({"lifecycle": "pending"}, {"observed_at": "2026-09-22T00:00:00Z"}):
            p = self.plan(candidates=[candidate(**changes)])
            self.assertEqual(p["status"], "blocked")

    def test_quota_exhaustion_and_unverified_overage_are_blocked(self):
        for changes in ({"quota": {"used_pct": 100, "observed_at": NOW}},
                        {"billing": {"mode": "subscription", "verified": True}}):
            self.assertEqual(self.plan(candidates=[candidate(**changes)])["status"], "blocked")

    def test_quality_floor_wins_over_cheapest_candidate(self):
        p = self.plan([step(demand="critical")],
                      [candidate("cheap", quality_tier=1), candidate("strong", quality_tier=3)])
        self.assertEqual(p["steps"][0]["route"]["candidate_id"], "strong")

    def test_mechanical_step_uses_no_extra_model(self):
        argv = ["rg", "--files"]
        p = self.plan([step(kind="local", skills=[], needs=[], argv=["rg", "--files"], software=["rg"])],
                      [], tools=["rg"], tool_costs=[self.tool_cost(argv)])
        self.assertEqual(p["steps"][0]["route"]["surface"], "local")
        self.assertEqual(p["budget"]["reserved_upper_usd"], 0)

    def test_missing_software_is_reported(self):
        p = self.plan([step(kind="local", skills=[], argv=["rg", "--files"], software=["rg"])], [])
        self.assertIn("SOFTWARE_UNAVAILABLE", str(p))

    def test_all_skills_are_discovered_and_duplicate_precedence_is_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = [Path(tmp) / "one", Path(tmp) / "two"]
            for root, desc in zip(roots, ("first", "second")):
                (root / "custom").mkdir(parents=True)
                (root / "custom" / "SKILL.md").write_text(
                    '---\nname: custom\ndescription: "' + desc + '"\n---\nBody', encoding="utf-8")
            result = self.m.discover_skills(roots)
            self.assertEqual(result["custom"]["description"], "first")

    def inventory(self, roots, **options):
        self.assertTrue(callable(getattr(self.m, "skill_inventory", None)),
                        "Evidence-preserving skill inventory is not implemented")
        return self.m.skill_inventory(roots, **options)

    def skill_file(self, root, folder="custom", name="custom", body="Body", description="Useful skill"):
        path = root / folder / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'---\nname: {name}\ndescription: {description}\n---\n{body}', encoding="utf-8")
        return path

    def test_inventory_preserves_shadowed_copies_and_byte_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            roots = [Path(tmp) / "one", Path(tmp) / "two"]
            first = self.skill_file(roots[0], body="first")
            second = self.skill_file(roots[1], body="second")
            inv = self.inventory(roots)
            self.assertEqual(inv["status"], "complete")
            self.assertEqual(len(inv["records"]), 2)
            selected = inv["catalog"]["custom"]
            self.assertEqual(selected["path"], str(first.resolve()))
            self.assertEqual(selected["alternatives"][0]["path"], str(second.resolve()))
            self.assertNotEqual(selected["sha256"], selected["alternatives"][0]["sha256"])
            self.assertEqual(self.m.discover_skills(roots), inv["catalog"])

    def test_inventory_keeps_logical_aliases_without_duplicate_physical_homes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.skill_file(root)
            inv = self.inventory([root, root / "."])
            self.assertEqual(len(inv["records"]), 1)
            self.assertEqual(inv["catalog"]["custom"]["alternatives"], [])

    def test_inventory_is_scoped_and_reports_missing_roots_and_bad_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.skill_file(root, "good", "good")
            bad = self.skill_file(root, "bad", "bad")
            bad.write_bytes(b"\xff\x00invalid")
            self.skill_file(root / "nested", "hidden", "hidden")
            inv = self.inventory([root, root / "absent"])
            self.assertEqual(set(inv["catalog"]), {"good"})
            self.assertEqual(inv["status"], "incomplete")
            self.assertTrue(any(i["code"] == "SKILL_UNREADABLE" for i in inv["issues"]))
            self.assertTrue(any(i["code"] == "ROOT_MISSING" for i in inv["issues"]))
            self.assertNotIn("invalid", json.dumps(inv))

    def test_inventory_exclusion_happens_before_read_and_is_not_full_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self.skill_file(root, "protected", "protected")
            original_open = Path.open
            def guarded_open(p, *args, **kwargs):
                self.assertNotEqual(p.resolve(), path.resolve(), "Excluded skill was opened")
                return original_open(p, *args, **kwargs)
            with patch.object(Path, "open", guarded_open):
                inv = self.inventory([root], exclude_roots=[path.parent])
            self.assertEqual(inv["catalog"], {})
            self.assertEqual(inv["status"], "incomplete")
            self.assertTrue(any(i["code"] == "EXCLUDED" for i in inv["issues"]))

    def test_inventory_does_not_guess_a_name_from_malformed_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, content in {"no-front": "# body", "duplicate": "---\nname: a\nname: b\n---\n",
                                  "object": "---\nname: [a, b]\n---\n"}.items():
                p = self.skill_file(root, name, name)
                p.write_text(content, encoding="utf-8")
            inv = self.inventory([root])
            self.assertEqual(inv["catalog"], {})
            self.assertEqual(len(inv["issues"]), 3)

    def test_inventory_resolved_alias_exclusion_precedes_content_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root, protected = base / "installed", base / "protected"
            root.mkdir()
            path = self.skill_file(protected)
            alias = root / "innocent-alias"
            if os.name == "nt":
                result = subprocess.run(["cmd", "/c", "mklink", "/J", str(alias), str(path.parent)],
                                        capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 0, "Disposable junction creation failed")
            else:
                alias.symlink_to(path.parent, target_is_directory=True)
            original_open = Path.open
            def guarded_open(p, *args, **kwargs):
                self.assertNotEqual(p.resolve(), path.resolve(), "Resolved excluded skill was read")
                return original_open(p, *args, **kwargs)
            with patch.object(Path, "open", guarded_open):
                excluded = self.inventory([root], exclude_roots=[protected])
            self.assertEqual(excluded["status"], "incomplete")
            self.assertEqual(excluded["records"], [])
            included = self.inventory([root, protected])
            self.assertEqual(len(included["records"]), 1)
            self.assertEqual(len(included["records"][0]["aliases"]), 2)

    def test_inventory_root_access_failure_and_size_limit_are_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self.skill_file(root)
            with patch.object(Path, "iterdir", side_effect=PermissionError("raw private error")):
                inv = self.inventory([root])
            self.assertEqual(inv["issues"][0]["code"], "ROOT_UNREADABLE")
            self.assertNotIn("raw private", json.dumps(inv))
            with patch.object(self.m, "MAX_SKILL_BYTES", 10):
                inv = self.inventory([root])
            self.assertEqual(inv["catalog"], {})
            self.assertEqual(inv["issues"][0]["code"], "SKILL_LIMIT")

    def test_inventory_multiline_description_and_utf8_bom_are_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = self.skill_file(root)
            p.write_bytes(('\ufeff---\nname: "custom"\ndescription: >-\n  Use when reading\n'
                           '  한국어 documents.\nversion: 1.0\n---\nsecret body not metadata').encode())
            inv = self.inventory([root])
            item = inv["catalog"]["custom"]
            self.assertIn("한국어", item["description"])
            self.assertNotIn("secret body", json.dumps(inv))
            import hashlib
            self.assertEqual(item["sha256"], hashlib.sha256(p.read_bytes()).hexdigest())

    def test_inventory_preserves_installed_internal_underscore_skill_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.skill_file(root, "_internal-command", "_internal-command")
            inv = self.inventory([root])
            self.assertIn("_internal-command", inv["catalog"])
            self.assertEqual(inv["status"], "complete")

    def test_host_skill_qualified_names_are_selectable_only_on_host(self):
        native = {"schema_version": 1, "host_ref": "fixture-host", "observed_at": NOW, "evidence": ["fixture catalog"],
                  "skills": [{"name": "docs:documents", "canonical_name": "documents",
                              "description": "Read docs", "uri": "skill://documents/main"}]}
        inv = self.inventory([], host_skills=native)
        self.assertEqual(inv["catalog"]["docs:documents"]["origin"], "host")
        self.assertIsNone(inv["catalog"]["docs:documents"]["sha256"])
        req = {"run_id": "native-test", "steps": [step(skills=["docs:documents"])]}
        runtime = {"candidates": [candidate("cli"), candidate("host", transport="host", effective_effort="low",
                                                                host_ref="fixture-host")],
                   "observed_at": NOW, "tools": []}
        p = self.m.make_plan(req, inv["catalog"], runtime, NOW, fixture_registry(runtime["candidates"]))
        self.assertEqual(p["status"], "ready")
        self.assertEqual(p["steps"][0]["route"]["transport"], "host")
        self.assertIsNone(p["steps"][0]["skill_bindings"][0]["path"])
        self.assertEqual(p["steps"][0]["handoff"]["host_skills"][0]["resource_uri"], "skill://documents/main")
        self.assertEqual(p["steps"][0]["handoff"]["read_skills"], [])
        self.assertIn("HOST_SKILL_REQUIRES_HOST", str(p))

    def test_host_skill_cannot_be_laundered_as_a_local_command(self):
        native = {"schema_version": 1, "host_ref": "fixture-host", "observed_at": NOW, "evidence": ["fixture catalog"],
                  "skills": [{"name": "native", "canonical_name": "native", "description": "Native",
                              "uri": "skill://native/main"}]}
        inv = self.inventory([], host_skills=native)
        req = {"run_id": "local-native", "steps": [step(kind="local", skills=["native"],
                  argv=["rg", "--files"], software=["rg"], needs=[])]}
        runtime = {"candidates": [], "observed_at": NOW, "tools": ["rg"],
                   "tool_costs": [self.tool_cost(["rg", "--files"])]}
        p = self.m.make_plan(req, inv["catalog"], runtime, NOW, fixture_registry([]))
        self.assertEqual(p["status"], "blocked")

    def test_host_identity_staleness_and_recursive_aliases_fail_closed(self):
        native = {"schema_version": 1, "host_ref": "fixture-host", "observed_at": NOW, "evidence": ["fixture catalog"],
                  "skills": [{"name": "pkg:procedure", "canonical_name": "procedure",
                              "description": "Procedure", "uri": "skill://procedure/main"},
                             {"name": "pkg:vibe", "canonical_name": "vibe",
                              "description": "Main", "uri": "skill://vibe/main"}]}
        for changes, skill, ancestors, expected in (
                ({"host_ref": "other"}, "pkg:procedure", [], "HOST_SKILL_CONTEXT_MISMATCH"),
                ({}, "pkg:vibe", [], "RECURSIVE_SKILL"),
                ({}, "pkg:procedure", ["procedure"], "RECURSIVE_SKILL")):
            with self.subTest(expected=expected):
                inv = self.inventory([], host_skills=native)
                c = candidate(transport="host", effective_effort="low", host_ref="fixture-host")
                c.update(changes)
                req = {"run_id": "host-identity", "ancestor_skills": ancestors,
                       "steps": [step(skills=[skill])]}
                p = self.m.make_plan(req, inv["catalog"], {"candidates": [c], "observed_at": NOW},
                                     NOW, fixture_registry([c]))
                self.assertEqual(p["status"], "blocked")
                self.assertIn(expected, str(p))
        native["observed_at"] = "2026-09-22T10:00:00Z"
        inv = self.inventory([], host_skills=native)
        c = candidate(transport="host", effective_effort="low", host_ref="fixture-host")
        p = self.m.make_plan({"run_id": "stale-native", "steps": [step(skills=["pkg:procedure"])]},
                            inv["catalog"], {"candidates": [c]}, NOW, fixture_registry([c]))
        self.assertIn("HOST_SKILL_STALE", str(p))

    def test_host_manifest_expiry_bounds_dispatch_readiness(self):
        observed = "2026-09-23T09:46:00+00:00"
        native = {"schema_version": 1, "host_ref": "fixture-host", "observed_at": observed, "evidence": ["fixture catalog"],
                  "skills": [{"name": "docs:native", "canonical_name": "native",
                              "description": "Native", "uri": "skill://native/main"}]}
        inv = self.inventory([], host_skills=native)
        c = candidate(transport="host", effective_effort="low", host_ref="fixture-host")
        p = self.m.make_plan({"run_id": "expiring-native", "steps": [step(skills=["docs:native"])]},
                            inv["catalog"], {"candidates": [c]}, NOW, fixture_registry([c]))
        self.assertEqual(p["status"], "ready")
        self.assertTrue(self.m.ready_steps(p, [], NOW))
        self.assertEqual(self.m.ready_steps(p, [], "2026-09-23T10:02:00+00:00"), [])

    def test_host_snapshot_rejects_conflicting_uri_identity_and_missing_provenance(self):
        native = {"schema_version": 1, "host_ref": "fixture-host", "observed_at": NOW,
                  "evidence": ["fixture host tool catalog"],
                  "skills": [{"name": "pkg:a", "canonical_name": "a", "description": "A", "uri": "skill://a/main"},
                             {"name": "pkg:b", "canonical_name": "b", "description": "B", "uri": "skill://a/main"}]}
        with self.assertRaises(ValueError):
            self.inventory([], host_skills=native)
        native["skills"] = native["skills"][:1]
        native["evidence"] = []
        with self.assertRaises(ValueError):
            self.inventory([], host_skills=native)

    def test_host_observation_refresh_preserves_durable_intent_but_not_changed_skill(self):
        import run_state
        later = (datetime.fromisoformat(NOW) + timedelta(seconds=30)).isoformat()
        def native_plan(now, uri="skill://native/main"):
            native = {"schema_version": 1, "host_ref": "fixture-host", "observed_at": now,
                      "evidence": ["fixture catalog at " + now],
                      "skills": [{"name": "docs:native", "canonical_name": "native",
                                  "description": "Native", "uri": uri}]}
            inv = self.inventory([], host_skills=native)
            c = candidate(transport="host", effective_effort="low", host_ref="fixture-host",
                          observed_at=now, quota={"used_pct": 10, "observed_at": now})
            return self.m.make_plan({"run_id": "native-refresh", "steps": [step(skills=["docs:native"])]},
                                   inv["catalog"], {"candidates": [c]}, now, fixture_registry([c]))
        with tempfile.TemporaryDirectory() as tmp:
            store = run_state.Store(Path(tmp) / "fixture.sqlite3")
            store.initialize()
            first, refreshed = native_plan(NOW), native_plan(later)
            store.register(first, now=NOW)
            store.refresh(refreshed, now=later)
            self.assertNotEqual(first["plan_digest"], refreshed["plan_digest"])
            with self.assertRaisesRegex(run_state.StateError, "INTENT_CHANGED"):
                store.refresh(native_plan(later, "skill://different/main"), now=later)
            claim = store.claim("native-refresh", "read", "fixture-claim", refreshed["plan_digest"], now=later)
            self.assertTrue(claim["dispatch_allowed"])

    def test_cli_requires_explicit_audit_roots_and_reports_gaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.skill_file(root / "src")
            self.skill_file(root / "installed", body="different")
            args = [sys.executable, "-B", str(SCRIPT), "coverage", "--source-root", str(root / "src"),
                    "--root", str(root / "installed")]
            result = subprocess.run(args, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 2)
            report = json.loads(result.stdout)
            self.assertEqual(report["rows"][0]["installation"], "drifted")
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream), patch.object(self.m, "skill_inventory") as scanner:
                self.assertEqual(self.m.main(["inventory"]), 2)
            scanner.assert_not_called()

    def test_default_catalog_includes_system_root_without_scanning_home_in_test(self):
        inv = self.inventory([])
        with contextlib.redirect_stdout(io.StringIO()), patch.object(self.m, "skill_inventory", return_value=inv) as scan:
            self.assertEqual(self.m.main(["catalog"]), 0)
        self.assertIn(Path.home() / ".codex" / "skills" / ".system", scan.call_args.args[0])

    def test_coverage_compares_selected_install_not_a_matching_shadow(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for label, body in (("src", "fresh"), ("old", "stale"), ("new", "fresh")):
                self.skill_file(root / label, body=body)
            src = self.inventory([root / "src"])
            installed = self.inventory([root / "old", root / "new"])
            result = self.m.skill_coverage(src, installed)
            self.assertEqual(result["rows"][0]["installation"], "drifted")
            self.assertEqual(result["rows"][0]["plugin_content"], "not_checked")
            self.assertFalse(result["optimization_complete"])
            for mode in ("economy", "balanced", "quality"):
                evidence = result["rows"][0]["modes"][mode]
                self.assertEqual(evidence["status"], "not_evaluated")
                self.assertIsNone(evidence["actual_usd"])
                self.assertIsNone(evidence["quality"])
                self.assertIsNone(evidence["latency_ms"])

    def test_coverage_reports_missing_skills_ambiguous_sources_and_duplicate_plugin_homes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.skill_file(root / "src")
            self.skill_file(root / "src", "missing", "missing")
            self.skill_file(root / "src", "amb1", "ambiguous", body="one")
            self.skill_file(root / "src", "amb2", "ambiguous", body="two")
            for label in ("installed", "p1", "p2"):
                self.skill_file(root / label)
            report = self.m.skill_coverage(self.inventory([root / "src"]),
                     self.inventory([root / "installed"]), self.inventory([root / "p1", root / "p2"]))
            rows = {r["name"]: r for r in report["rows"]}
            self.assertEqual(rows["missing"]["installation"], "missing")
            self.assertEqual(rows["ambiguous"]["installation"], "ambiguous_source")
            self.assertEqual(rows["custom"]["plugin_home"], "duplicate")
            self.assertEqual(report["status"], "gaps")

    def test_coverage_does_not_claim_full_package_or_eval_parity_from_skill_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for label in ("source", "installed", "plugin"):
                p = self.skill_file(root / label)
                (p.parent / "evals").mkdir()
                (p.parent / "evals" / "cases.json").write_text('{"cases": []}', encoding="utf-8")
            report = self.m.skill_coverage(self.inventory([root / "source"]),
                     self.inventory([root / "installed"]), self.inventory([root / "plugin"]))
            self.assertEqual(report["rows"][0]["installation"], "matched")
            self.assertEqual(report["rows"][0]["plugin_home"], "single")
            self.assertEqual(report["hash_scope"], "SKILL.md bytes only")
            self.assertFalse(report["optimization_complete"])
            self.assertEqual(report["rows"][0]["modes"]["balanced"]["status"], "not_evaluated")

    def test_recursive_orchestrator_is_blocked(self):
        self.assertIn("RECURSIVE_SKILL", str(self.plan([step(skills=["vibe"])])))

    def test_unknown_skill_is_not_silently_ignored(self):
        self.assertIn("SKILL_NOT_FOUND", str(self.plan([step(skills=["does-not-exist"])])))

    def test_duplicate_ids_missing_dependencies_and_cycles_are_rejected(self):
        for steps in ([step(), step()], [step(depends_on=["absent"])],
                      [step(depends_on=["second"]), step("second", depends_on=["read"])]):
            with self.subTest(steps=steps), self.assertRaises(ValueError):
                self.plan(steps)

    def test_ready_wave_waits_for_verified_evidence(self):
        p = self.plan([step(), step("summary", depends_on=["read"])])
        self.assertEqual(self.m.ready_steps(p, [], now=NOW), ["read"])
        self.assertEqual(self.m.ready_steps(p, self.events(p, {"id": "read", "status": "done"}), now=NOW), [])
        self.assertEqual(self.m.ready_steps(p, self.events(p, {"id": "read", "status": "done",
                         "verified": True, "evidence": ["checked output"]}), now=NOW), ["summary"])

    def test_failed_work_is_not_retried_automatically(self):
        p = self.plan()
        self.assertEqual(self.m.ready_steps(p, self.events(p, {"id": "read", "status": "failed"}), now=NOW), [])

    def test_gui_with_cli_alternative_is_sent_back_to_tools(self):
        p = self.plan([step(kind="gui", skills=["vibe-bot"], tool_route_available=True, target="Console")])
        self.assertIn("PREFER_TOOL_ROUTE", str(p))

    def bot(self, **changes):
        c = candidate("bot", surface="grok-bot", transport="bot", model=None,
                      capabilities=["gui"], bot_id="grok-bot", bot_status="active",
                      provider_efforts=[], transport_efforts=[], effort_by_demand={})
        c.update(changes)
        return c

    def gui(self, **changes):
        s = step(kind="gui", skills=["vibe-bot"], needs=["gui"],
                 target="Example Console", tool_route_available=False,
                 gui_reason="No authorized API for the required screen")
        s.update(changes)
        return s

    def test_bot_has_no_invented_effort(self):
        p = self.plan([self.gui()], [self.bot()])
        self.assertEqual(p["status"], "ready")
        self.assertIsNone(p["steps"][0]["route"]["requested_effort"])
        self.assertEqual(p["steps"][0]["route"]["vendor"], "xai")
        self.assertEqual(p["steps"][0]["handoff"]["mode"], "console")

    def test_held_bot_is_not_routed(self):
        p = self.plan([self.gui()], [self.bot(bot_status="ON HOLD")])
        self.assertIn("BOT_INACTIVE", str(p))

    def test_grok_cli_and_bot_are_not_independent_verifiers(self):
        steps = [step(surface="grok"), self.gui(id="review", verify_of="read", depends_on=["read"])]
        p = self.plan(steps, [candidate("grok", surface="grok"), self.bot()])
        self.assertIn("SAME_VENDOR_REVIEW", str(p))

    def test_writes_require_independent_review(self):
        self.assertIn("MISSING_REVIEW", str(self.plan([step(writes=True)])))

    def test_host_cannot_claim_model_switch(self):
        c = candidate(transport="host", effective_effort="high")
        self.assertIn("HOST_EFFORT_MISMATCH", str(self.plan(candidates=[c])))

    def test_requests_are_not_mutated(self):
        nodes = [step()]
        before = copy.deepcopy(nodes)
        self.plan(nodes)
        self.assertEqual(nodes, before)

    def test_writer_waits_when_required_reviewer_is_unroutable(self):
        p = self.plan([step(writes=True), step("review", verify_of="read", depends_on=["read"])])
        self.assertEqual(p["status"], "blocked")
        self.assertEqual(self.m.ready_steps(p, [], now=NOW), [])

    def test_old_run_or_changed_plan_evidence_is_rejected(self):
        p = self.plan([step(), step("summary", depends_on=["read"])])
        for wrong in ({"run_id": "old-run"}, {"plan_digest": "old-plan"}):
            events = self.events(p, {"id": "read", "status": "done", "verified": True, "evidence": ["old"]})
            events[0].update(wrong)
            with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                self.m.ready_steps(p, events, now=NOW)

    def test_local_cannot_hide_llm_spend(self):
        for binary in ("grok", "codex", "claude", "agy"):
            argv = [binary, "-p", "paid request"]
            p = self.plan([step(kind="local", skills=[], argv=argv, software=[binary])], [],
                          tools=[binary], tool_costs=[self.tool_cost(argv)])
            self.assertIn("LLM_CLI_AS_LOCAL", str(p))

    def test_unverified_wrapper_is_not_free(self):
        p = self.plan([step(kind="local", skills=[], argv=["python", "api.py"], software=["python"])],
                      [], tools=["python"])
        self.assertIn("LOCAL_COST_UNVERIFIED", str(p))

    def test_local_test_cannot_replace_independent_review(self):
        argv = ["echo", "PASS"]
        p = self.plan([step(writes=True), step("test", kind="local", skills=[], argv=argv,
                      software=["echo"], verify_of="read", depends_on=["read"])],
                      tools=["echo"], tool_costs=[self.tool_cost(argv)])
        self.assertEqual(p["status"], "blocked")

    def test_nonfinite_quality_and_invalid_rank_are_rejected(self):
        for change in ({"quality_tier": float("nan")}, {"quality_tier": True},
                       {"resource_rank": float("nan")}, {"resource_rank": -1}):
            self.assertEqual(self.plan(candidates=[candidate(**change)])["status"], "blocked")

    def test_budget_comparison_does_not_round_up_authorization(self):
        c = candidate(billing={"mode": "api", "verified": True}, upper_usd_per_attempt="1")
        p = self.plan(candidates=[c], budget={"approved_usd": "0.9999999999999999999999", "max_attempts": 1})
        self.assertEqual(p["status"], "blocked")

    def test_bot_result_requires_actual_correlated_screenshot(self):
        import json
        bot_root = SCRIPT.parent.parent.parent / "vibe-bot"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            meta, result, evidence = root / "meta.json", root / "result.md", root / "evidence.json"
            meta.write_text(json.dumps({"nonce": "vb-1234abcd", "mode": "console", "target": "Console"}), encoding="utf-8")
            result.write_text("vb-1234abcd\n메뉴 경로: Settings > Status\n값: ready", encoding="utf-8")
            self.assertTrue(self.m.verify_bot_result(bot_root, meta, result, "vb-1234abcd"))
            evidence.write_text(json.dumps({"nonce": "vb-1234abcd", "target": "Console", "images": ["missing.png"]}), encoding="utf-8")
            self.assertTrue(self.m.verify_bot_result(bot_root, meta, result, "vb-1234abcd", evidence))

    def test_bot_positive_result_and_directory_escape(self):
        import base64
        import json
        bot_root = SCRIPT.parent.parent.parent / "vibe-bot"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            meta, result, evidence = root / "meta.json", root / "result.md", root / "evidence.json"
            meta.write_text(json.dumps({"nonce": "vb-1234abcd", "mode": "console", "target": "Console"}), encoding="utf-8")
            result.write_text("vb-1234abcd\n메뉴 경로: Settings > Status\n스크린샷: shot.png\n값: ready", encoding="utf-8")
            (root / "shot.png").write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="))
            evidence.write_text(json.dumps({"nonce": "vb-1234abcd", "target": "Console", "images": ["shot.png"]}), encoding="utf-8")
            self.assertEqual(self.m.verify_bot_result(bot_root, meta, result, "vb-1234abcd", evidence), [])
            evidence.write_text(json.dumps({"nonce": "vb-1234abcd", "target": "Console", "images": ["../outside.png"]}), encoding="utf-8")
            self.assertIn("BOT_SCREENSHOT_MISSING_OR_OUTSIDE_RUN",
                          self.m.verify_bot_result(bot_root, meta, result, "vb-1234abcd", evidence))

    def test_all_five_surfaces_have_a_route_when_observed(self):
        for surface in self.m.SURFACES:
            with self.subTest(surface=surface):
                c = self.bot() if surface == "grok-bot" else candidate(surface=surface)
                s = self.gui() if surface == "grok-bot" else step(surface=surface)
                self.assertEqual(self.plan([s], [c])["status"], "ready")

    def test_independent_review_succeeds_across_model_vendors(self):
        p = self.plan([step(writes=True), step("review", verify_of="read", depends_on=["read"])],
                      [candidate(), candidate("reviewer", surface="claude")])
        self.assertEqual(p["status"], "ready")
        self.assertNotEqual(p["steps"][0]["route"]["vendor"], p["steps"][1]["route"]["vendor"])

    def test_orca_unknown_model_never_passes_the_legacy_gate(self):
        p = self.plan([step(proc="research-deep", **{"class": "B"})], [candidate(transport="orca")])
        self.assertIn("ORCA_UNREGISTERED_PROCESS_OR_MODEL", p["errors"])

    def test_cli_plan_round_trip_is_read_only(self):
        import json
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "explain").mkdir()
            (root / "explain" / "SKILL.md").write_text("---\nname: explain\ndescription: Explain\n---\n", encoding="utf-8")
            request, runtime = root / "request.json", root / "runtime.json"
            request.write_text(json.dumps({"run_id": "cli-test", "steps": [step()]}), encoding="utf-8")
            runtime.write_text(json.dumps({"candidates": [candidate()], "observed_at": NOW}), encoding="utf-8")
            registry_path = root / "registry.json"
            registry_path.write_text(json.dumps(fixture_registry([candidate()])), encoding="utf-8")
            before = sorted(p.name for p in root.iterdir())
            result = subprocess.run([sys.executable, str(SCRIPT), "plan", "--input", str(request),
                                     "--runtime", str(runtime), "--root", str(root), "--now", NOW,
                                     "--registry", str(registry_path)],
                                    capture_output=True, text=True, encoding="utf-8", timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "ready")
            self.assertEqual(sorted(p.name for p in root.iterdir()), before)

    def test_ready_requires_fresh_dispatch_time(self):
        p = self.plan()
        self.assertEqual(self.m.ready_steps(p, [], now="2026-09-23T10:16:00Z"), [])

    def test_missing_bot_metadata_cannot_downgrade_verification(self):
        root = SCRIPT.parent.parent.parent / "vibe-bot"
        self.assertIn("BOT_RESULT_OR_META_MISSING", self.m.verify_bot_result(
            root, "missing-meta.json", "missing-result.md", "vb-1234abcd"))

    def test_writer_output_unlocks_review_but_not_general_successors(self):
        nodes = [step(writes=True), step("review", verify_of="read", depends_on=["read"]),
                 step("publish-report", depends_on=["read"])]
        p = self.plan(nodes, [candidate(), candidate("reviewer", surface="claude")])
        events = self.events(p, {"id": "read", "status": "done", "verified": True, "evidence": ["tests pass"]})
        self.assertEqual(self.m.ready_steps(p, events, now=NOW), ["review"])
        events += self.events(p, {"id": "review", "status": "done", "verified": True, "evidence": ["review accepted"]})
        self.assertEqual(self.m.ready_steps(p, events, now=NOW), ["publish-report"])

    def test_review_barrier_covers_transitive_successors(self):
        nodes = [step(writes=True), step("review", verify_of="read", depends_on=["read"]),
                 step("test-artifact", verify_of="read", depends_on=["read"]),
                 step("finish", depends_on=["test-artifact"])]
        p = self.plan(nodes, [candidate(), candidate("reviewer", surface="claude")])
        events = self.events(p, *[{"id": name, "status": "done", "verified": True, "evidence": ["output"]}
                                  for name in ("read", "test-artifact")])
        self.assertEqual(self.m.ready_steps(p, events, now=NOW), ["review"])

    def test_default_planner_rejects_unregistered_runtime_model(self):
        c = candidate()
        p = self.m.make_plan({"run_id": "registry-check", "steps": [step()]}, self.catalog,
                             {"candidates": [c]}, NOW)
        self.assertEqual(p["status"], "blocked")
        self.assertIn("MODEL_NOT_REGISTERED", str(p))

    def test_planner_locks_registry_and_does_not_invent_resolved_model(self):
        now = "2026-09-23T13:00:00+00:00"
        c = candidate(model="gpt-6-sol", observed_at=now, quota={"used_pct": 10, "observed_at": now})
        p = self.m.make_plan({"run_id": "registry-check", "steps": [step()]}, self.catalog,
                             {"candidates": [c]}, now)
        self.assertEqual(p["status"], "ready")
        self.assertIn("model_registry", p)
        self.assertEqual(p["steps"][0]["route"]["requested_model"], "gpt-6-sol")
        self.assertIsNone(p["steps"][0]["route"]["resolved_model"])

    def test_harness_ultra_is_not_an_ordinary_worker_effort(self):
        now = "2026-09-23T13:00:00+00:00"
        c = candidate(model="gpt-6-sol", observed_at=now, quota={"used_pct": 10, "observed_at": now},
                      provider_efforts=["ultra"], transport_efforts=["ultra"],
                      effort_by_demand={"routine": "ultra"})
        p = self.m.make_plan({"run_id": "registry-check", "steps": [step()]}, self.catalog,
                             {"candidates": [c]}, now)
        self.assertEqual(p["status"], "blocked")

    def test_ready_rechecks_alias_access_and_registry_expiry(self):
        clock = datetime.fromisoformat(NOW)
        old = (clock - timedelta(seconds=899)).isoformat()
        boundary = (clock + timedelta(seconds=1)).isoformat()
        later = (clock + timedelta(seconds=3)).isoformat()
        for expiring in ("alias", "access", "registry"):
            with self.subTest(expiring=expiring):
                c = candidate()
                registry = fixture_registry([c])
                if expiring == "registry":
                    registry["checked_at"] = (clock - timedelta(days=7)
                                               + timedelta(seconds=1)).isoformat()
                else:
                    target = c["model"]
                    alias = copy.deepcopy(registry["models"][0])
                    alias.update(id="fixture-alias", id_namespace="provider-api-alias",
                                 documented_target=target, api_efforts=None)
                    if expiring == "access":
                        alias["requires_access_program"] = "fixture-access"
                        c["access_proof"] = {"program": "fixture-access", "verified": True,
                                             "account_ref": "test-account", "observed_at": old,
                                             "evidence": "authorized fixture"}
                    registry["models"].append(alias)
                    c.update(model=alias["id"], resolved_model=target,
                             resolution_observed_at=old if expiring == "alias" else NOW,
                             resolution_evidence="fixture resolution")
                p = self.m.make_plan({"run_id": "expiry-test", "steps": [step()]}, self.catalog,
                                     {"candidates": [c]}, NOW, registry)
                self.assertEqual(p["status"], "ready")
                self.assertEqual(self.m.ready_steps(p, [], now=NOW), ["read"])
                self.assertEqual(self.m.ready_steps(p, [], now=boundary), ["read"])
                self.assertEqual(self.m.ready_steps(p, [], now=later), [])

    def test_ready_requires_derived_validity_bound(self):
        p = self.plan()
        p["steps"][0]["route"].pop("valid_until", None)
        p["plan_digest"] = self.m.digest({k: v for k, v in p.items() if k != "plan_digest"})
        self.assertEqual(self.m.ready_steps(p, [], now=NOW), [])

    def typed(self, task_type="CODE_FIX", **changes):
        node = {"id": "read", "task": "Offline classification fixture", "task_type": task_type,
                "skills": ["explain"], "depends_on": [], "writes": False}
        node.update(changes)
        return node

    def test_typed_request_is_compiled_on_the_actual_plan_path(self):
        node = self.typed()
        before = copy.deepcopy(node)
        p = self.plan([node])
        self.assertEqual(node, before)
        self.assertEqual(p["status"], "ready")
        out = p["steps"][0]
        for key, expected in {"kind": "llm", "proc": "coding", "class": "B",
                              "needs": ["code"], "demand": "reasoning"}.items():
            self.assertEqual(out[key], expected)
        self.assertEqual(out["route"]["requested_effort"], "high")

    def test_typed_contract_rejects_unknown_types_and_conflicts(self):
        for change in ({"task_type": "UNKNOWN"}, {"task_type": None}, {"task_type": []},
                       {"kind": "local"}, {"proc": "bulk-transform"}, {"class": "A"},
                       {"needs": []}, {"needs": "code"}, {"demand": "routine"},
                       {"demand": "ultra"}, {"writes": "false"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.plan([self.typed(**change)])

    def test_typed_contract_requires_explicit_write_scope(self):
        node = self.typed()
        del node["writes"]
        with self.assertRaises(ValueError):
            self.plan([node])

    def test_typed_contract_allows_stronger_requirements_and_preserves_metadata(self):
        node = self.typed(demand="critical", needs=["code", "reasoning"],
                          parent_run_id="parent", orca={"task_id": "native-task"})
        p = self.plan([node], [candidate(quality_tier=3)])
        self.assertEqual(p["status"], "ready")
        out = p["steps"][0]
        self.assertEqual(out["route"]["requested_effort"], "xhigh")
        self.assertEqual(out["parent_run_id"], "parent")
        self.assertEqual(out["orca"], {"task_id": "native-task"})

    def test_typed_writer_requires_same_dag_independent_review(self):
        writer = self.typed(writes=True)
        self.assertIn("MISSING_REVIEW", str(self.plan([writer])))
        reviewer = self.typed("CODE_REVIEW", id="review", depends_on=["read"], verify_of="read")
        self.assertEqual(self.plan([writer, reviewer])["status"], "blocked")
        p = self.plan([writer, reviewer], [candidate(), candidate("reviewer", surface="claude")])
        self.assertEqual(p["status"], "ready")
        self.assertEqual(p["steps"][1]["verify_of"], "read")
        self.assertNotEqual(p["steps"][0]["route"]["vendor"], p["steps"][1]["route"]["vendor"])

    def test_typed_gui_does_not_grant_tool_bypass_or_bot_authority(self):
        node = self.typed("COMPUTER_USE", skills=["vibe-bot"])
        p = self.plan([node], [self.bot()])
        self.assertIn("PREFER_TOOL_ROUTE", str(p))
        self.assertIn("GUI_TARGET_REQUIRED", str(p))
        node.update(target="Offline Console", tool_route_available=False,
                    gui_reason="Fixture has no authorized CLI/API route")
        self.assertEqual(self.plan([node], [self.bot()])["status"], "ready")

    def test_typed_task_map_uses_only_existing_process_classes(self):
        import routing
        expected = {"CODE_NEW", "CODE_FIX", "CODE_REVIEW", "RESEARCH", "AGENTIC",
                    "COMPUTER_USE", "DESIGN_UI", "KOREAN_DOC", "BULK_LIGHT",
                    "REASONING_ABSTRACT", "VISION"}
        self.assertEqual(set(self.m.TASK_TYPE_MAP), expected)
        for mapping in self.m.TASK_TYPE_MAP.values():
            self.assertEqual(routing.PROC_BY_ID[mapping["proc"]][1], mapping["class"])
            self.assertEqual(set(mapping), {"kind", "needs", "demand", "proc", "class"})

    def test_untyped_requests_remain_backward_compatible(self):
        node = step()
        self.assertEqual(self.m.compile_task_type(node), node)
        self.assertEqual(self.plan([node])["status"], "ready")

    def test_missing_account_identity_cannot_become_a_route(self):
        for value in (None, "", "  ", 123):
            c = candidate()
            c["billing"]["account_ref"] = value
            with self.subTest(value=value):
                p = self.plan([self.typed()], [c])
                self.assertEqual(p["status"], "blocked")
                self.assertIn("ACCOUNT_UNVERIFIED", str(p))

    def test_ancestry_is_validated_and_preserved_in_plan(self):
        request = {"run_id": "parent", "ancestor_skills": ["vibe", "simonk", "model-router"],
                   "steps": [self.typed()]}
        runtime = {"candidates": [candidate()]}
        p = self.m.make_plan(request, self.catalog, runtime, NOW, fixture_registry(runtime["candidates"]))
        self.assertEqual(p.get("ancestor_skills"), request["ancestor_skills"])
        p["ancestor_skills"].append("changed-output")
        self.assertNotIn("changed-output", request["ancestor_skills"])
        for invalid in (None, "simonk", [None], [""], ["  "], [{}]):
            request["ancestor_skills"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.m.make_plan(request, self.catalog, runtime, NOW, fixture_registry(runtime["candidates"]))

    def test_read_only_code_review_cannot_masquerade_as_a_writer(self):
        reviewer = self.typed("CODE_REVIEW", writes=True)
        checker = self.typed("CODE_REVIEW", id="check", verify_of="read", depends_on=["read"])
        with self.assertRaises(ValueError):
            self.plan([reviewer, checker], [candidate(), candidate("reviewer", surface="claude")])


class TddGuardRegression(unittest.TestCase):
    def test_nested_python_tests_are_tests_without_weakening_source_gate(self):
        guard = SCRIPT.parents[3] / "skills-src/simon-tdd/scripts/tdd-guard-check.sh"
        bash = "C:/Program Files/Git/bin/bash.exe" if os.name == "nt" else "bash"
        source = guard.read_text(encoding="utf-8").replace("\r", "")
        fixtures = (
            ("pkg/tool.py\npkg/test_tool.py", 0),
            ("pkg/test_tool.py", 0),
            ("test_tool.py", 0),
            ("pkg/tool.py", 1),
            ("pkg/tool.py\npkg/test_unrelated.py", 1),
        )
        for staged, expected in fixtures:
            with self.subTest(staged=staged):
                env = dict(os.environ, VIBE_GUARD_STAGED=staged)
                result = subprocess.run(
                    [bash, "-s"], input="git() { printf '%s\\n' \"$VIBE_GUARD_STAGED\"; }\n" + source,
                    text=True, encoding="utf-8", capture_output=True, env=env, timeout=15,
                )
                self.assertEqual(result.returncode, expected, result.stderr)


if __name__ == "__main__":
    unittest.main()
