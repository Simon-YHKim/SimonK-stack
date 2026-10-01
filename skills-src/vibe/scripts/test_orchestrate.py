"""Offline contract tests for the umbrella planner; no worker or Bot is launched."""
import base64
import copy
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
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
    model = changes.get("model", "fixture-" + name)
    item = {
        "id": name, "surface": surface, "transport": "host", "effective_effort": "low",
        "model": model, "lifecycle": "active", "available": True,
        "observed_at": NOW, "evidence": "offline test fixture", "quality_tier": 2,
        "capabilities": ["reasoning", "code", "research"], "resource_rank": 1,
        "provider_efforts": ["low", "high", "xhigh"],
        "transport_efforts": ["low", "high", "xhigh"],
        "effort_by_demand": {"routine": "low", "reasoning": "high", "critical": "xhigh"},
        "billing": {"mode": "subscription", "verified": True,
                    "extra_usage_enabled": False, "model_included": True, "included_model": model,
                    "api_fallback_disabled": True, "paid_credit_fallback_disabled": True,
                    "account_ref": "test-account"},
        "quota": {"used_pct": 10, "observed_at": NOW, "bucket": "test-weekly"},
    }
    if surface == "codex":
        item["billing"]["credits"] = {"has_credits": False, "unlimited": False,
                                       "balance": "0"}
    item.update(changes)
    if surface in {"antigravity", "grok", "grok-bot"} and "quota" not in changes:
        item["quota"].update({"surface": surface, "transport": item["transport"],
                              "account_ref": item["billing"]["account_ref"],
                              "state": "observed", "evidence": "fixture account-bound quota"})
    return item


def image_tool(**changes):
    item = {
        "id": "fixture-image", "surface": "codex", "transport": "host-image",
        "tool_ref": "fixture.image", "host_ref": "fixture-host",
        "interaction_ref": "fixture-interaction", "available": True,
        "observed_at": NOW, "evidence": ["fixture current-host catalog"],
        "adapter_contract": "image-host-atomic-subscription-v1",
        "idempotent_request": True, "lookup_by_request": True,
        "billing": {"mode": "subscription", "verified": True,
                    "account_ref": "fixture-image-account", "image_included": True,
                    "extra_usage_enabled": False, "api_fallback_disabled": True,
                    "paid_credit_fallback_disabled": True,
                    "provider_hard_cap_usd": 0, "provider_hard_cap_enforced": True,
                    "observed_at": NOW,
                    "evidence": ["fixture provider-enforced cap"]},
        "quota": {"used_pct": 10, "observed_at": NOW, "bucket": "fixture-image",
                  "account_ref": "fixture-image-account", "surface": "codex",
                  "transport": "host-image", "evidence": ["fixture account-bound image quota"]},
    }
    item.update(changes)
    return item


def step(name="read", **changes):
    item = {"id": name, "task": "Inspect the supplied input", "kind": "llm",
            "skills": ["explain"], "needs": ["reasoning"], "demand": "routine",
            "depends_on": [], "writes": False}
    item.update(changes)
    return item


def cli_binding(surface):
    """Structural preflight fixture only; paths are not dispatch evidence."""
    binding = {"executable": "/fixture/worker.exe", "executable_sha256": "a" * 64,
               "cwd": "/fixture/private", "profile_path": "/fixture/profile",
               "profile_ref": "fixture-profile", "account_ref": "test-account",
               "result_path": "/fixture/private/result.json"}
    if surface == "codex":
        binding.update(content_path="/fixture/private/content.txt",
                       result_path="/fixture/private/result.jsonl")
    return binding


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


def production_registry_now():
    """Keep packaged-registry integration checks valid after a reviewed refresh."""
    path = SCRIPT.parent.parent / "references" / "model-registry.json"
    checked_at = json.loads(path.read_text(encoding="utf-8"))["checked_at"]
    return (datetime.fromisoformat(checked_at) + timedelta(hours=1)).isoformat()


class OrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "The /vibe umbrella planner is not implemented")
        spec = importlib.util.spec_from_file_location("vibe_orchestrate", SCRIPT)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.catalog = {name: {"name": name, "path": "/fixture/" + name + "/SKILL.md",
                              "description": name} for name in ("explain", "dev-orchestrator", "vibe-bot")}

    def plan(self, steps=None, candidates=None, budget=None, task_fit_policy=None, debate=None, **runtime_changes):
        runtime = {"candidates": candidates if candidates is not None else [candidate()],
                   "tools": [], "observed_at": NOW}
        runtime.update(runtime_changes)
        request = {"run_id": "test-run", "steps": steps or [step()], "budget": budget or {}}
        if debate is not None:
            request["debate"] = debate
        return self.m.make_plan(request, self.catalog, runtime, NOW,
                                fixture_registry(runtime["candidates"]), task_fit_policy)

    @staticmethod
    def debate_fixture():
        roles = {"proposer": "opening-gpt", "challenger": "opening-claude",
                 "proposer_rebuttal": "rebuttal-gpt", "challenger_rebuttal": "rebuttal-claude",
                 "judge": "judge-gpt"}
        steps = [step("opening-gpt", surface="codex"),
                 step("opening-claude", surface="claude"),
                 step("rebuttal-gpt", surface="codex", depends_on=["opening-gpt", "opening-claude"]),
                 step("rebuttal-claude", surface="claude", depends_on=["opening-gpt", "opening-claude"]),
                 step("judge-gpt", surface="codex", depends_on=["rebuttal-gpt", "rebuttal-claude"])]
        candidates = [candidate("gpt", surface="codex"), candidate("claude", surface="claude")]
        return roles, steps, candidates

    def test_debate_routes_two_vendors_and_waits_for_verified_rebuttals(self):
        roles, steps, candidates = self.debate_fixture()
        plan = self.plan(steps, candidates, debate=roles)
        self.assertEqual(plan["status"], "ready", plan["errors"])
        self.assertEqual(plan["debate"], roles)
        self.assertEqual(self.m.ready_steps(plan, [], NOW), ["opening-gpt", "opening-claude"])
        openings = self.events(plan, *({"id": role, "status": "done", "verified": True,
                                        "evidence": ["fixture-dispatch"]}
                                       for role in ("opening-gpt", "opening-claude")))
        self.assertEqual(self.m.ready_steps(plan, openings, NOW), ["rebuttal-gpt", "rebuttal-claude"])
        unverified = openings + self.events(plan, {"id": "rebuttal-gpt", "status": "done",
                                              "verified": False, "evidence": ["fixture"]},
                                            {"id": "rebuttal-claude", "status": "done",
                                              "verified": True, "evidence": ["fixture"]})
        self.assertEqual(self.m.ready_steps(plan, unverified, NOW), [])
        unverified[-2]["verified"] = True
        self.assertEqual(self.m.ready_steps(plan, unverified, NOW), ["judge-gpt"])

    def test_debate_rejects_same_vendor_or_rebuttal_account_switch(self):
        roles, steps, candidates = self.debate_fixture()
        same = copy.deepcopy(steps)
        for node in same:
            node["surface"] = "codex"
        self.assertIn("DEBATE_REQUIRES_TWO_VENDORS", self.plan(same, candidates, debate=roles)["errors"])
        switched = candidates + [candidate("claude-other", surface="claude",
                                            billing={**candidates[1]["billing"], "account_ref": "other",
                                                     "included_model": "fixture-claude-other"},
                                            quality_tier=3, resource_rank=2)]
        changed = copy.deepcopy(steps)
        changed[3]["quality_floor"] = 3
        # A coordinator cannot silently turn a rebuttal into a different account.
        result = self.plan(changed, switched, debate=roles)
        self.assertIn("DEBATE_REBUTTAL_ROUTE_MISMATCH", result["errors"])

    def test_debate_requires_distinct_real_nodes_and_complete_dependencies(self):
        roles, steps, candidates = self.debate_fixture()
        repeated = dict(roles, judge=roles["proposer"])
        with self.assertRaisesRegex(ValueError, "distinct"):
            self.plan(steps, candidates, debate=repeated)
        incomplete = copy.deepcopy(steps)
        incomplete[-1]["depends_on"] = ["rebuttal-gpt"]
        with self.assertRaisesRegex(ValueError, "judge"):
            self.plan(incomplete, candidates, debate=roles)

    def test_debate_roles_are_part_of_durable_immutable_intent(self):
        import run_state
        roles, steps, candidates = self.debate_fixture()
        plan = self.plan(steps, candidates, debate=roles)
        changed = copy.deepcopy(plan)
        changed["debate"]["judge"] = roles["proposer_rebuttal"]
        self.assertNotEqual(run_state.spec_digest(plan), run_state.spec_digest(changed))
        changed["plan_digest"] = self.m.digest({k: v for k, v in changed.items() if k != "plan_digest"})
        with tempfile.TemporaryDirectory(prefix="vibe-debate-state-") as folder:
            store = run_state.Store(Path(folder) / "state.sqlite3")
            store.initialize()
            with self.assertRaisesRegex(run_state.StateError, "DEBATE_PLAN_INVALID"):
                store.register(changed, now=NOW)

    def task_fit_fixture(self, task_type="PLAN_ARCHITECTURE", model="claude-opus-5-5",
                         efforts=None, rank=0, checked_at=NOW, valid_until="2026-09-24T10:00:00+00:00"):
        return {"schema_version": 1, "version": "offline-shadow-1", "status": "shadow-only",
                "checked_at": checked_at, "valid_until": valid_until,
                "sources": {"manufacturer": "https://www.anthropic.com/claude-opus-5-5"},
                "profiles": {task_type: [{"model": model, "efforts": efforts or ["high"],
                                         "rank": rank, "sources": ["manufacturer"]}]}}

    def events(self, plan, *events):
        return [dict(run_id=plan["run_id"], plan_digest=plan["plan_digest"], **event) for event in events]

    def tool_cost(self, argv):
        return {"argv_sha256": self.m.digest(argv), "verified": True, "evidence": "Reviewed fixture command",
                "observed_at": NOW, "upper_usd_per_attempt": 0,
                "transitive_effects_audited": True, "billing_mode": "nonmetered"}

    def test_gui_request_is_discoverable_from_main_skill_description(self):
        text = (SCRIPT.parent.parent / "SKILL.md").read_text(encoding="utf-8")
        description = text.split("description:", 1)[1].splitlines()[0].strip().strip("'")
        for keyword in ("Play Console", "CLI/API/MCP", "vibe-bot"):
            with self.subTest(keyword=keyword):
                self.assertIn(keyword, description)
        # The current Codex host shortens this catalog entry to 48 characters.
        prefix = description[:48].lower()
        self.assertIn("/vibe", prefix)
        self.assertIn("simonkstack", prefix)
        self.assertIn("rout", prefix)
        self.assertIn("Produces a verified routing plan", description)

    def test_subscription_and_effort_are_explicit(self):
        p = self.plan()
        self.assertEqual(p["status"], "ready")
        self.assertEqual(p["steps"][0]["route"]["requested_effort"], "low")
        self.assertEqual(p["steps"][0]["route"]["effective_effort"], "low")
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

    def test_zero_budget_never_routes_metered_api_even_with_zero_quote(self):
        for mode in ("api", "metered"):
            with self.subTest(mode=mode):
                c = candidate(billing={"mode": mode, "verified": True,
                                       "account_ref": "fixture-api"}, upper_usd_per_attempt=0)
                p = self.plan(candidates=[c])
                self.assertEqual(p["status"], "blocked")
                self.assertIn("SUBSCRIPTION_ONLY", str(p))

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

    def test_subscription_needs_model_inclusion_and_no_api_fallback(self):
        for billing_change, reason in (({"model_included": None}, "MODEL_INCLUSION_UNVERIFIED"),
                                       ({"model_included": False}, "MODEL_INCLUSION_UNVERIFIED"),
                                       ({"api_fallback_disabled": None}, "API_FALLBACK_UNVERIFIED"),
                                       ({"api_fallback_disabled": False}, "API_FALLBACK_UNVERIFIED")):
            with self.subTest(billing_change=billing_change):
                billing = dict(candidate()["billing"], **billing_change)
                plan = self.plan(candidates=[candidate(billing=billing)])
                self.assertEqual(plan["status"], "blocked")
                self.assertIn(reason, str(plan))

    def test_codex_and_grok_subscription_must_exclude_purchased_credit_fallback(self):
        for surface in ("codex", "grok"):
            for value in (None, False):
                with self.subTest(surface=surface, value=value):
                    billing = dict(candidate(surface=surface)["billing"])
                    if value is None:
                        billing.pop("paid_credit_fallback_disabled")
                    else:
                        billing["paid_credit_fallback_disabled"] = value
                    plan = self.plan(candidates=[candidate(surface=surface, billing=billing)])
                    self.assertEqual(plan["status"], "blocked")
                    self.assertIn("PAID_CREDIT_FALLBACK_UNVERIFIED", str(plan))

    def test_codex_positive_or_unknown_purchased_credits_block_claimed_zero_spend(self):
        missing = dict(candidate()["billing"])
        missing.pop("credits")
        for buckets in ({}, {"codex": {}}, {"codex": {"credits": {
                "has_credits": False, "unlimited": False, "balance": "0"}}}):
            with self.subTest(buckets=buckets):
                billing = dict(missing, buckets=buckets)
                plan = self.plan(candidates=[candidate(billing=billing)])
                self.assertEqual(plan["status"], "blocked")
                self.assertIn("PAID_CREDIT_EXPOSURE", str(plan))
        billing = dict(candidate()["billing"], buckets={"codex": {}})
        plan = self.plan(candidates=[candidate(billing=billing)])
        self.assertEqual(plan["status"], "blocked")
        self.assertIn("PAID_CREDIT_EXPOSURE", str(plan))
        for credits in (None,
                        {"has_credits": True, "balance": "3.25"},
                        {"has_credits": True, "balance": None},
                        {"has_credits": True, "unlimited": False, "balance": "0"},
                        {"has_credits": False, "unlimited": False, "balance": None},
                        {"has_credits": None, "unlimited": False, "balance": "0"},
                        {"has_credits": False, "balance": "3.25"}):
            with self.subTest(credits=credits):
                billing = dict(candidate()["billing"], credits=credits)
                plan = self.plan(candidates=[candidate(billing=billing)])
                self.assertEqual(plan["status"], "blocked")
                self.assertIn("PAID_CREDIT_EXPOSURE", str(plan))
        billing = dict(candidate()["billing"], buckets={"codex": {
            "credits": {"has_credits": True, "balance": "3.25"}}})
        plan = self.plan(candidates=[candidate(billing=billing)])
        self.assertEqual(plan["status"], "blocked")
        self.assertIn("PAID_CREDIT_EXPOSURE", str(plan))
        billing = dict(candidate()["billing"], credits={
            "has_credits": False, "unlimited": False, "balance": "0"})
        self.assertEqual(self.plan(candidates=[candidate(billing=billing)])["status"], "ready")

    def test_claude_uses_separate_usage_credits_toggle(self):
        billing = dict(candidate(surface="claude")["billing"])
        billing.pop("paid_credit_fallback_disabled")
        self.assertEqual(self.plan(candidates=[candidate(surface="claude", billing=billing)])["status"],
                         "ready")

    def test_subscription_inclusion_is_bound_to_resolved_model(self):
        for billing_change, reason in (({"included_model": "other-model"}, "MODEL_INCLUSION_UNVERIFIED"),
                                       ({"included_model": None}, "MODEL_INCLUSION_UNVERIFIED")):
            with self.subTest(billing_change=billing_change):
                billing = dict(candidate()["billing"], **billing_change)
                plan = self.plan(candidates=[candidate(billing=billing)])
                self.assertEqual(plan["status"], "blocked")
                self.assertIn(reason, str(plan))

    def test_quality_floor_wins_over_cheapest_candidate(self):
        p = self.plan([step(demand="critical")],
                      [candidate("cheap", quality_tier=1, effective_effort="xhigh"),
                       candidate("strong", quality_tier=3, effective_effort="xhigh")])
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
        runtime = {"candidates": [candidate("cli", transport="cli"), candidate("host", transport="host", effective_effort="low",
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

    def test_default_catalog_uses_candidate_receipt_or_system_root(self):
        bound = self.m.candidate_inventory()
        if bound is not None:
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                self.assertEqual(self.m.main(["catalog"]), 0)
            catalog = json.loads(stream.getvalue())
            self.assertEqual(set(catalog), set(bound["catalog"]))
            self.assertIn("vibe", catalog)
            self.assertIn("vibe-bot", catalog)
            return
        inv = self.inventory([])
        with contextlib.redirect_stdout(io.StringIO()), patch.object(self.m, "skill_inventory", return_value=inv) as scan:
            self.assertEqual(self.m.main(["catalog"]), 0)
        self.assertIn(Path.home() / ".codex" / "skills" / ".system", scan.call_args.args[0])

    def test_default_catalog_does_not_fallback_from_a_bound_candidate(self):
        inv = self.inventory([])
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream), \
                patch.object(self.m, "candidate_inventory", return_value=inv) as bound, \
                patch.object(self.m, "skill_inventory") as fallback:
            self.assertEqual(self.m.main(["catalog"]), 0)
        bound.assert_called_once_with([], None)
        fallback.assert_not_called()
        self.assertEqual(json.loads(stream.getvalue()), inv["catalog"])

    def test_receipt_bound_codex_overlay_accepts_only_verified_zoom_projection(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            script_root = base / "plugins/SimonKCore/skills/vibe/scripts"
            owners = {
                "vibe": "SimonKCore", "ai-helper": "SimonKAIHub",
                "design-helper": "SimonKDesign", "market-helper": "SimonKMarket",
                "zoom-out": "SimonKStack",
                "careful": "SimonKCore", "unfreeze": "SimonKCore",
                "freeze": "SimonKStack", "guard": "SimonKStack",
                "investigate": "SimonKStack",
            }
            source_files = {}

            def put(path, data):
                target = base / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)

            script_path = "plugins/SimonKCore/skills/vibe/scripts/orchestrate.py"
            source_files[script_path] = b"# fixture\n"
            for owner in ("SimonKCore", "SimonKStack"):
                source_files[f"plugins/{owner}/.simonk-runtime/safety_runtime.py"] = b"# fixture\n"
            for owner in sorted(set(owners.values())):
                names = sorted(name for name, home in owners.items() if home == owner)
                source_files[f"plugins/{owner}/.claude-plugin/plugin.json"] = json.dumps(
                    {"skills": [f"./skills/{name}/" for name in names]}
                ).encode()
                for name in names:
                    body = f"---\nname: {name}\ndescription: Fixture\n---\nFixture\n".encode()
                    if name == "zoom-out":
                        body = body.replace(b"---\nFixture", b"disable-model-invocation: true\n---\nFixture")
                    source_files[f"plugins/{owner}/skills/{name}/SKILL.md"] = body
            for path, data in source_files.items():
                put(path, data)
            bundle = {"schema_version": 2, "scope": "five-plugin-candidate-safety-v2",
                      "inputs": {"plugins": {owner: {} for owner in set(owners.values())}},
                      "owners": owners,
                      "files": [{"path": path, "sha256": hashlib.sha256(data).hexdigest(),
                                 "size": len(data)} for path, data in sorted(source_files.items())]}
            bundle_data = json.dumps(bundle).encode()
            put("bundle.json", bundle_data)

            zoom_path = "plugins/SimonKStack/skills/zoom-out/SKILL.md"
            original_zoom = source_files[zoom_path]
            projected_zoom = original_zoom.replace(b"disable-model-invocation: true\n", b"", 1)
            generated = {zoom_path: projected_zoom,
                         "plugins/SimonKStack/skills/zoom-out/agents/openai.yaml": (
                             b"interface:\n  display_name: Zoom Out\n"
                             b"  short_description: One-layer-up code map on explicit request.\n"
                             b"policy:\n  allow_implicit_invocation: false\n")}
            for owner in set(owners.values()):
                generated[f"plugins/{owner}/.codex-plugin/plugin.json"] = b"{}\n"
            for path, data in generated.items():
                put(path, data)
            overlay = {"schema_version": 2, "scope": "five-plugin-codex-compat-overlay-v2",
                       "candidate_digest": hashlib.sha256(bundle_data).hexdigest(),
                       "replacement_originals": {zoom_path: base64.b64encode(original_zoom).decode()},
                       "generated": {path: {"sha256": hashlib.sha256(data).hexdigest(),
                                            "size": len(data)} for path, data in generated.items()},
                       "host_compatibility_verified": False, "installation_ready": False,
                       "limitations": []}
            put("overlay.json", json.dumps(overlay).encode())
            with patch.object(self.m, "SCRIPT_ROOT", script_root):
                found = self.m.candidate_inventory()
                self.assertEqual(found["status"], "complete")
                self.assertEqual(len(found["catalog"]), 10)
                self.assertIn("overlay", found["catalog"].discovery)
                put(zoom_path, projected_zoom + b"tamper")
                with self.assertRaises(ValueError):
                    self.m.candidate_inventory()
                put(zoom_path, projected_zoom)
                forged_zoom = projected_zoom + b"forged"
                put(zoom_path, forged_zoom)
                overlay["generated"][zoom_path] = {"sha256": hashlib.sha256(forged_zoom).hexdigest(),
                                                   "size": len(forged_zoom)}
                put("overlay.json", json.dumps(overlay).encode())
                with self.assertRaises(ValueError):
                    self.m.candidate_inventory()

                # D-29 keeps manifests unmodified but removes five skill roots
                # and two safety runtimes from the Codex subset.
                put(zoom_path, projected_zoom)
                overlay["generated"][zoom_path] = {"sha256": hashlib.sha256(projected_zoom).hexdigest(),
                                                  "size": len(projected_zoom)}
                overlay["replacement_originals"][zoom_path] = base64.b64encode(original_zoom).decode()
                put("overlay.json", json.dumps(overlay).encode())
                before_subset = {p.relative_to(base).as_posix(): p.read_bytes()
                                 for p in base.rglob("*") if p.is_file()}
                excluded_skills = (("SimonKCore", "careful"), ("SimonKStack", "freeze"),
                                   ("SimonKStack", "guard"), ("SimonKStack", "investigate"),
                                   ("SimonKCore", "unfreeze"))
                excluded_prefixes = tuple(f"plugins/{owner}/skills/{name}/"
                                          for owner, name in excluded_skills) + tuple(
                    f"plugins/{owner}/.simonk-runtime/" for owner in ("SimonKCore", "SimonKStack"))
                excluded_paths = {p for p in before_subset if p.startswith(excluded_prefixes)}
                for owner, name in excluded_skills:
                    shutil.rmtree(base / f"plugins/{owner}/skills/{name}")
                for owner in ("SimonKCore", "SimonKStack"):
                    shutil.rmtree(base / f"plugins/{owner}/.simonk-runtime")
                rows = lambda paths: [{"path": p, "sha256": hashlib.sha256(before_subset[p]).hexdigest(),
                                       "size": len(before_subset[p])} for p in sorted(paths)]
                subset = {"schema_version": 1, "scope": "five-plugin-codex-general-skills-only-v2",
                          "decision_ref": "D-29",
                          "source_overlay_digest": hashlib.sha256((base / "overlay.json").read_bytes()).hexdigest(),
                          "excluded_skills": [f"simonk-{owner.removeprefix('SimonK').lower()}:{name}"
                                              for owner, name in excluded_skills],
                          "included_members": rows(set(before_subset) - excluded_paths),
                          "excluded_members": rows(excluded_paths),
                          "host_compatibility_verified": False, "installation_ready": False,
                          "limitations": []}
                with self.assertRaises(ValueError):
                    self.m.candidate_inventory()  # Omission without receipt is never a fallback.
                put("subset.json", json.dumps(subset).encode())
                found = self.m.candidate_inventory()
                self.assertEqual(found["status"], "complete")
                self.assertEqual(len(found["catalog"]), 5)
                self.assertNotIn("careful", found["catalog"])
                self.assertIn("subset", found["catalog"].discovery)
                removed_row = subset["included_members"].pop()
                put("subset.json", json.dumps(subset).encode())
                with self.assertRaises(ValueError):
                    self.m.candidate_inventory()
                subset["included_members"].append(removed_row)
                put("subset.json", json.dumps(subset).encode())
                put("plugins/SimonKCore/skills/careful/SKILL.md", b"unreceipted safety control")
                with self.assertRaises(ValueError):
                    self.m.candidate_inventory()
                shutil.rmtree(base / "plugins/SimonKCore/skills/careful")
                subset["source_overlay_digest"] = "0" * 64
                put("subset.json", json.dumps(subset).encode())
                with self.assertRaises(ValueError):
                    self.m.candidate_inventory()
                put(zoom_path, projected_zoom)
                overlay["generated"][zoom_path] = {"sha256": hashlib.sha256(projected_zoom).hexdigest(),
                                                   "size": len(projected_zoom)}
                overlay["replacement_originals"][zoom_path] = base64.b64encode(b"wrong").decode()
                put("overlay.json", json.dumps(overlay).encode())
                with self.assertRaises(ValueError):
                    self.m.candidate_inventory()

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
                      provider_efforts=[], transport_efforts=[], effort_by_demand={},
                      billing={"mode": "subscription", "verified": True,
                               "extra_usage_enabled": False, "bot_usage_included": True,
                               "api_fallback_disabled": True,
                               "paid_credit_fallback_disabled": True,
                               "account_ref": "test-bot-account"})
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

    def test_bot_needs_included_subscription_usage_not_a_model_claim(self):
        for included in (None, False):
            with self.subTest(included=included):
                billing = dict(self.bot()["billing"], bot_usage_included=included,
                               model_included=True)
                p = self.plan([self.gui()], [self.bot(billing=billing)])
                self.assertEqual(p["status"], "blocked")
                self.assertIn("BOT_USAGE_INCLUSION_UNVERIFIED", str(p))
        billing = dict(self.bot()["billing"], model_included=None)
        self.assertEqual(self.plan([self.gui()], [self.bot(billing=billing)])["status"], "ready")

    def test_bot_purchased_credit_fallback_must_be_excluded(self):
        billing = dict(self.bot()["billing"])
        billing.pop("paid_credit_fallback_disabled")
        p = self.plan([self.gui()], [self.bot(billing=billing)])
        self.assertEqual(p["status"], "blocked")
        self.assertIn("PAID_CREDIT_FALLBACK_UNVERIFIED", str(p))

    def test_xai_quota_must_match_exact_surface_transport_and_account(self):
        # A synthetic host route isolates quota binding from the unavailable CLI adapter.
        for surface, node, good in (("grok", step(surface="grok"), candidate(
                                        "grok", surface="grok", transport="host", effective_effort="low")),
                                    ("grok-bot", self.gui(), self.bot())):
            self.assertEqual(self.plan([node], [good])["status"], "ready")
            for field, wrong in (("surface", "grok-bot" if surface == "grok" else "grok"),
                                 ("transport", "cli" if surface == "grok-bot" else "bot"),
                                 ("account_ref", "other-account"), ("evidence", ""),
                                 ("state", "reset-unobserved")):
                with self.subTest(surface=surface, field=field):
                    bad = copy.deepcopy(good)
                    bad["quota"][field] = wrong
                    p = self.plan([node], [bad])
                    self.assertEqual(p["status"], "blocked")
                    self.assertIn("QUOTA_BINDING_UNVERIFIED", str(p))

    def test_held_bot_is_not_routed(self):
        p = self.plan([self.gui()], [self.bot(bot_status="ON HOLD")])
        self.assertIn("BOT_INACTIVE", str(p))

    def test_reported_roster_status_is_not_live_bot_evidence(self):
        reported = "active - reported in user-supplied 2026-09-24 snapshot; live access unverified"
        for status in (reported, "ACTIVE (reported)", None, 1):
            with self.subTest(status=status):
                p = self.plan([self.gui()], [self.bot(bot_status=status)])
                self.assertEqual(p["status"], "blocked")
                self.assertIn("BOT_INACTIVE", p["steps"][0]["rejected_candidates"][0]["reasons"])
        self.assertEqual(self.plan([self.gui()], [self.bot(bot_status="active")])["status"], "ready")

    def test_grok_and_bot_are_not_independent_verifiers(self):
        steps = [step(surface="grok"), self.gui(id="review", verify_of="read", depends_on=["read"])]
        p = self.plan(steps, [candidate("grok", surface="grok", transport="host",
                                        effective_effort="low"), self.bot()])
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

    def test_local_zero_quote_requires_explicit_transitive_effects_and_nonmetered_billing(self):
        argv = ["python", "fixed-local-fixture.py"]
        local = step(kind="local", skills=[], argv=argv, software=["python"])
        quote = self.tool_cost(argv)
        for change, reason in (({"transitive_effects_audited": False}, "LOCAL_EFFECTS_UNVERIFIED"),
                               ({"billing_mode": "metered"}, "SUBSCRIPTION_ONLY"),
                               ({"billing_mode": "unknown"}, "LOCAL_BILLING_UNVERIFIED"),
                               ({"billing_mode": "nonmetered", "upper_usd_per_attempt": 1},
                                "LOCAL_BILLING_UNVERIFIED")):
            with self.subTest(change=change):
                plan = self.plan([local], [], tools=["python"], tool_costs=[dict(quote, **change)])
                self.assertEqual(plan["status"], "blocked")
                self.assertIn(reason, plan["steps"][0]["errors"])
        for removed, reason in (("transitive_effects_audited", "LOCAL_EFFECTS_UNVERIFIED"),
                                ("billing_mode", "LOCAL_BILLING_UNVERIFIED")):
            with self.subTest(removed=removed):
                incomplete = dict(quote)
                incomplete.pop(removed)
                plan = self.plan([local], [], tools=["python"], tool_costs=[incomplete])
                self.assertIn(reason, plan["steps"][0]["errors"])
        self.assertEqual(self.plan([local], [], tools=["python"], tool_costs=[quote])["status"], "ready")

    def test_gstack_bin_local_tool_handoff_requests_isolation(self):
        script = "C:/Users/fixture/.claude/skills/gstack/bin/gstack-config"
        for argv, software, flagged in (
                ([script, "get", "telemetry"], script, True),
                (["bash", script.replace("/", "\\"), "get", "telemetry"], "bash", True),
                (["sh", "/home/fixture/.claude/skills/gstack/bin/gstack-slug"], "sh", True),
                (["python", "/home/fixture/skills/gstack/bin"], "python", False),
                (["bash", "/fixture/skills/not-gstack/bin/tool"], "bash", False),
                (["python", "fixed-local-fixture.py"], "python", False)):
            with self.subTest(argv=argv):
                p = self.plan([step(kind="local", skills=[], argv=argv, software=[software])], [],
                              tools=[software], tool_costs=[self.tool_cost(argv)])
                self.assertEqual(p["status"], "ready", p["steps"][0]["errors"])
                handoff = p["steps"][0]["handoff"]
                self.assertEqual(handoff.get("gstack_isolation"), True if flagged else None)
                self.assertEqual(handoff["argv"], argv)

    def test_gstack_skill_host_and_orca_handoffs_carry_isolation_brief(self):
        self.catalog["review"] = {"name": "review", "path": "/fixture/review/SKILL.md",
                                  "description": "Pre-landing PR review. (gstack)"}
        self.catalog["qa"] = {"name": "qa", "path": "/home/fixture/.claude/skills/gstack/qa/SKILL.md",
                              "description": "QA"}
        for skills, transport, expected in ((["review"], "host", "required"),
                                            (["explain", "qa"], "host", "required"),
                                            (["review"], "orca", "best-effort"),
                                            (["explain"], "host", None),
                                            (["explain"], "orca", None)):
            with self.subTest(skills=skills, transport=transport):
                p = self.plan([step(skills=skills)], [candidate(transport=transport)])
                handoff = p["steps"][0]["handoff"]
                self.assertEqual(handoff.get("gstack_isolation"), expected)
                if expected is None:
                    self.assertNotIn("gstack_brief", handoff)
                    continue
                brief = handoff["gstack_brief"]
                for text in ("run_state.py\" gstack-env --run 'test-run'", "export line",
                             "TELEMETRY: off", "UPDATE_CHECK: false", "stop this node"):
                    self.assertIn(text, brief)
                self.assertEqual(brief.startswith("Orca cannot pass environment"), transport == "orca")
                if transport == "host":
                    self.assertEqual(p["status"], "ready", p["errors"])

    def test_gstack_bin_in_any_argv_element_requests_isolation(self):
        bin_dir = "/home/fixture/.claude/skills/gstack/bin/"
        for argv in (["bun", bin_dir + "gstack-gbrain-sync.ts"],
                     ["node", bin_dir + "gstack-render.ts"],
                     ["env", "bash", bin_dir + "gstack-config", "get", "telemetry"],
                     ["bash", "-c", bin_dir + "gstack-config get telemetry"],
                     ["bash", "-c", "cd /repo && ~/.claude/skills/gstack/bin/gstack-slug"],
                     ["python", "C:\\fixture\\.claude\\skills\\gstack\\bin\\gstack-detach"]):
            with self.subTest(argv=argv):
                p = self.plan([step(kind="local", skills=[], argv=argv, software=[argv[0]])], [],
                              tools=[argv[0]], tool_costs=[self.tool_cost(argv)])
                self.assertEqual(p["status"], "ready", p["steps"][0]["errors"])
                self.assertIs(p["steps"][0]["handoff"].get("gstack_isolation"), True)
        for argv in (["bash", "-c", "echo myskills/gstack/bin/x"], ["node", "/fixture/skills/gstack/binary/x.ts"]):
            self.assertFalse(self.m.gstack_command(argv))

    def gstack_root(self, folder):
        # Gstack-derived preambles as packaged in a plugin: no "(gstack)" suffix, no gstack path part.
        root = Path(folder) / "simonk-stack" / "skills"
        for name, body in (("qa", "_UPD=$(~/.claude/skills/gstack/bin/gstack-update-check || true)\n"),
                           ("ship", "mkdir -p ~/.gstack/sessions\n"),
                           ("learn", 'cat "${GSTACK_HOME:-$HOME/.gstack}/projects/x/learnings.jsonl"\n'),
                           ("explain", "Read the code and explain it.\n")):
            (root / name).mkdir(parents=True)
            (root / name / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: Use when {name} is requested.\n---\n\n```bash\n{body}```\n",
                encoding="utf-8", newline="\n")
        return root

    def gstack_plan(self, catalog, name, transport="host"):
        c = candidate(transport=transport)
        return self.m.make_plan({"run_id": "r1", "steps": [step(skills=[name])], "budget": {}}, catalog,
                                {"candidates": [c], "tools": [], "observed_at": NOW}, NOW, fixture_registry([c]))

    def test_inventory_flags_gstack_preamble_skills_for_isolation(self):
        with tempfile.TemporaryDirectory(prefix="vibe-inventory-") as folder:
            root = self.gstack_root(folder)
            catalog = self.m.skill_inventory([root])["catalog"]
            shadow = Path(folder) / "shadow"
            (shadow / "explain").mkdir(parents=True)
            (shadow / "explain" / "SKILL.md").write_text(
                "---\nname: explain\ndescription: Shadowed copy.\n---\n\ntouch ~/.gstack/x\n", encoding="utf-8")
            shadowed = self.m.skill_inventory([root, shadow])["catalog"]["explain"]
        for name in ("qa", "ship", "learn"):
            self.assertIs(catalog[name].get("gstack"), True)
            for transport, level in (("host", "required"), ("orca", "best-effort")):
                with self.subTest(name=name, transport=transport):
                    handoff = self.gstack_plan(catalog, name, transport)["steps"][0]["handoff"]
                    self.assertEqual(handoff.get("gstack_isolation"), level)
                    self.assertIn("gstack-env --run 'r1'", handoff["gstack_brief"])
        self.assertNotIn("gstack", catalog["explain"])
        self.assertNotIn("gstack_isolation", self.gstack_plan(catalog, "explain")["steps"][0]["handoff"])
        self.assertNotIn("gstack", shadowed)
        self.assertIs(shadowed["alternatives"][0]["gstack"], True)
        self.assertTrue(self.m.gstack_skill(shadowed))
        self.assertTrue(self.m.gstack_skill({"path": "/x/qa/SKILL.md",
                                             "description": "Use for QA. (gstack) Voice triggers: run QA."}))

    def test_gstack_flag_keeps_inventory_and_non_gstack_plan_digests(self):
        with tempfile.TemporaryDirectory(prefix="vibe-inventory-") as folder:
            root = self.gstack_root(folder)
            after = self.m.skill_inventory([root])
            with patch.object(self.m, "GSTACK_REFERENCE", re.compile(rb"(?!)")):
                before = self.m.skill_inventory([root])  # Detection as it was before the flag.
        self.assertNotIn("gstack", before["catalog"]["qa"])
        self.assertIs(after["catalog"]["qa"]["gstack"], True)
        self.assertEqual(after["inventory_digest"], before["inventory_digest"])
        for transport in ("host", "orca"):
            with self.subTest(transport=transport):
                self.assertEqual(self.gstack_plan(after["catalog"], "explain", transport)["plan_digest"],
                                 self.gstack_plan(before["catalog"], "explain", transport)["plan_digest"])
                self.assertNotEqual(self.gstack_plan(after["catalog"], "qa", transport)["plan_digest"],
                                    self.gstack_plan(before["catalog"], "qa", transport)["plan_digest"])

    def test_gstack_brief_does_not_depend_on_install_path(self):
        self.catalog["review"] = {"name": "review", "path": "/fixture/review/SKILL.md",
                                  "description": "Pre-landing PR review. (gstack)"}
        first = self.plan([step(skills=["review"])], [candidate(transport="orca")])
        with patch.object(self.m, "SCRIPT_ROOT", Path("/other/install/vibe/scripts")):
            second = self.plan([step(skills=["review"])], [candidate(transport="orca")])
        brief = first["steps"][0]["handoff"]["gstack_brief"]
        self.assertEqual(second["steps"][0]["handoff"], first["steps"][0]["handoff"])
        self.assertNotIn(self.m.SCRIPT_ROOT.as_posix(), brief)
        self.assertIn("python -B \"<vibe skill folder>/scripts/run_state.py\" gstack-env --run 'test-run'", brief)

    def test_docs_pin_debate_version_and_state_gstack_limits(self):
        skill = (SCRIPT.parent.parent / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue("`/ai-debate` >= 0.2.0" in skill)
        doc = (SCRIPT.parent.parent / "references" / "orchestration.md").read_text(encoding="utf-8")
        for text in ("instruction-level", "274 lines", "gstack-detach", "gstack-repo-mode",
                     "repo classifier", "TASK_SPEC_CHANGED", "TASK_SPEC_MISMATCH"):
            with self.subTest(text=text):
                self.assertTrue(text in doc, text)
        self.assertFalse("46 lines" in doc)

    def test_metered_local_quote_requires_positive_authorized_budget(self):
        argv = ["python", "api.py"]
        local = step(kind="local", skills=[], argv=argv, software=["python"])
        quote = dict(self.tool_cost(argv), billing_mode="metered", upper_usd_per_attempt="0.25")
        blocked = self.plan([local], [], tools=["python"], tool_costs=[quote])
        self.assertIn("SUBSCRIPTION_ONLY", blocked["steps"][0]["errors"])
        allowed = self.plan([local], [], budget={"approved_usd": "0.5"},
                            tools=["python"], tool_costs=[quote])
        self.assertEqual(allowed["status"], "ready")
        self.assertEqual(allowed["budget"]["reserved_upper_usd"], 0.5)

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

    def test_registered_transports_pass_planner_fixture_preflight(self):
        for surface in ("claude", "codex", "grok-bot"):
            with self.subTest(surface=surface):
                c = self.bot() if surface == "grok-bot" else candidate(surface=surface, transport="cli")
                s = self.gui() if surface == "grok-bot" else step(
                    surface=surface, skills=[], cli=cli_binding(surface))
                self.assertEqual(self.plan([s], [c])["status"], "ready")

    def test_direct_cli_preflight_rejects_nodes_its_adapter_cannot_execute(self):
        policy = {"mode": "balanced", "approved_usd": "0", "max_attempts": 2}
        for surface in ("claude", "codex"):
            with self.subTest(surface=surface):
                c = candidate(surface=surface, transport="cli")
                for change in ({"skills": ["explain"]}, {"software": ["rg"]},
                               {"writes": True}, {"verify_of": "producer"},
                               {"depends_on": ["producer"]}):
                    with self.subTest(change=change):
                        node = step(surface=surface, **dict({"skills": []}, **change))
                        errors, _, _ = self.m.assess_candidate(c, node, policy, NOW)
                        self.assertIn("CLI_NODE_UNSUPPORTED", errors)

    def test_direct_cli_preflight_requires_exact_binding_shape(self):
        for surface in ("claude", "codex"):
            with self.subTest(surface=surface):
                plan = self.plan([step(surface=surface, skills=[])], [candidate(surface=surface, transport="cli")])
                self.assertEqual(plan["status"], "blocked")
                self.assertIn("CLI_BINDING_REQUIRED", str(plan))
                bad = dict(cli_binding(surface), account_ref="other-account")
                plan = self.plan([step(surface=surface, skills=[], cli=bad)],
                                 [candidate(surface=surface, transport="cli")])
                self.assertIn("CLI_BINDING_REQUIRED", str(plan))

    def test_direct_cli_preflight_allows_only_canonical_debate_edges(self):
        roles, _, _ = self.debate_fixture()
        policy = {"mode": "balanced", "approved_usd": "0", "max_attempts": 2}
        for surface, node_id in (("codex", "rebuttal-gpt"), ("claude", "rebuttal-claude")):
            with self.subTest(surface=surface):
                c = candidate(surface=surface, transport="cli")
                good = step(node_id, skills=[], cli=cli_binding(surface),
                            depends_on=[roles["proposer"], roles["challenger"]])
                errors, _, _ = self.m.assess_candidate(c, good, policy, NOW, debate=roles)
                self.assertNotIn("CLI_NODE_UNSUPPORTED", errors)
                extra = step(node_id, skills=[], cli=cli_binding(surface),
                             depends_on=[roles["proposer"], roles["challenger"], roles["judge"]])
                errors, _, _ = self.m.assess_candidate(c, extra, policy, NOW, debate=roles)
                self.assertIn("CLI_NODE_UNSUPPORTED", errors)

    def test_unimplemented_cli_and_orca_adapters_never_become_ready(self):
        for surface, transport in (("antigravity", "cli"), ("antigravity", "orca"),
                                   ("grok", "cli"), ("grok", "orca")):
            with self.subTest(surface=surface, transport=transport):
                c = candidate(surface=surface, transport=transport)
                c["quota"]["transport"] = transport
                plan = self.plan([step(surface=surface)], [c])
                self.assertEqual(plan["status"], "blocked")
                self.assertIn("EXECUTION_ADAPTER_UNAVAILABLE", str(plan))

    def test_grok_cli_remains_unavailable_even_with_full_subscription_evidence(self):
        good = candidate(surface="grok", transport="cli")
        p = self.plan([step(surface="grok")], [good])
        self.assertEqual(p["status"], "blocked")
        self.assertIn("EXECUTION_ADAPTER_UNAVAILABLE", str(p))

    def test_antigravity_host_requires_credit_and_exact_quota_evidence(self):
        good = candidate(surface="antigravity", transport="host", effective_effort="low")
        good["quota"]["transport"] = "host"
        billing = dict(good["billing"])
        billing.pop("paid_credit_fallback_disabled")
        p = self.plan([step(surface="antigravity")], [dict(good, billing=billing)])
        self.assertIn("PAID_CREDIT_FALLBACK_UNVERIFIED", str(p))
        wrong_quota = dict(good["quota"], account_ref="other-account")
        p = self.plan([step(surface="antigravity")], [dict(good, quota=wrong_quota)])
        self.assertIn("QUOTA_BINDING_UNVERIFIED", str(p))

    def test_independent_review_succeeds_across_model_vendors(self):
        p = self.plan([step(writes=True), step("review", verify_of="read", depends_on=["read"])],
                      [candidate(), candidate("reviewer", surface="claude")])
        self.assertEqual(p["status"], "ready")
        self.assertNotEqual(p["steps"][0]["route"]["vendor"], p["steps"][1]["route"]["vendor"])

    def test_orca_unknown_model_never_passes_the_legacy_gate(self):
        p = self.plan([step(proc="research-deep", **{"class": "B"})], [candidate(transport="orca")])
        self.assertIn("ORCA_UNREGISTERED_PROCESS_OR_MODEL", p["errors"])

    def test_current_generation_models_stay_off_orca_until_lane_migration(self):
        # Lane migration is a separate decision; registering a model must not open an Orca lane.
        for model in ("claude-opus-5-5", "claude-sonnet-5-5", "gpt-6.1-sol", "gpt-6-sol",
                      "gpt-6-luna", "grok-4.7", "grok-4.5"):
            with self.subTest(model=model):
                node = {"id": "n", "proc": "research-deep", "class": "B",
                        "route": {"transport": "orca", "model": model, "requested_effort": "high"}}
                self.assertEqual(self.m._legacy_validation([node], {}),
                                 ["ORCA_UNREGISTERED_PROCESS_OR_MODEL"])

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
            host = candidate(transport="host", effective_effort="low")
            runtime.write_text(json.dumps({"candidates": [host], "observed_at": NOW}), encoding="utf-8")
            registry_path = root / "registry.json"
            registry_path.write_text(json.dumps(fixture_registry([host])), encoding="utf-8")
            before = sorted(p.name for p in root.iterdir())
            cache_dir = SCRIPT.parent / "__pycache__"
            before_cache = sorted(p.name for p in cache_dir.glob("*.pyc"))
            result = subprocess.run([sys.executable, "-B", str(SCRIPT), "plan", "--input", str(request),
                                     "--runtime", str(runtime), "--root", str(root), "--now", NOW,
                                     "--registry", str(registry_path)],
                                    capture_output=True, text=True, encoding="utf-8", timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "ready")
            self.assertEqual(sorted(p.name for p in root.iterdir()), before)
            self.assertEqual(sorted(p.name for p in cache_dir.glob("*.pyc")), before_cache)

    def test_cli_inventory_plain_python_does_not_write_bytecode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts = root / "scripts"
            scripts.mkdir()
            for name in ("orchestrate.py", "model_registry.py"):
                shutil.copyfile(SCRIPT.with_name(name), scripts / name)
            skills = root / "skills"
            (skills / "explain").mkdir(parents=True)
            (skills / "explain" / "SKILL.md").write_text(
                "---\nname: explain\ndescription: Explain\n---\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(scripts / "orchestrate.py"), "inventory", "--root", str(skills)],
                capture_output=True, text=True, encoding="utf-8", timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "complete")
            self.assertFalse(list(scripts.rglob("*.pyc")))

    def test_packaged_cli_entrypoints_do_not_create_unreceipted_bytecode(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts = Path(tmp) / "scripts"
            scripts.mkdir()
            for source in SCRIPT.parent.glob("*.py"):
                shutil.copyfile(source, scripts / source.name)
            env = os.environ.copy()
            env.pop("PYTHONDONTWRITEBYTECODE", None)
            env.pop("PYTHONPYCACHEPREFIX", None)
            for name in ("orchestrate.py", "runtime_collect.py", "run_state.py",
                         "execute_orca.py", "execute_bot.py"):
                with self.subTest(entrypoint=name):
                    result = subprocess.run([sys.executable, str(scripts / name), "--help"],
                                            capture_output=True, text=True, encoding="utf-8",
                                            cwd=tmp, env=env, timeout=15)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertFalse(list(scripts.rglob("*.pyc")))

    def test_legacy_user_entrypoints_import_without_bytecode_or_effects(self):
        probe = (
            "import runpy, sys\n"
            "class StopProbe(Exception): pass\n"
            "def trace(frame, event, arg):\n"
            "    if event == 'call' and frame.f_code.co_filename == sys.argv[1] "
            "and frame.f_code.co_name in ('main', 'run'):\n"
            "        raise StopProbe\n"
            "    return trace\n"
            "sys.settrace(trace)\n"
            "try: runpy.run_path(sys.argv[1], run_name='__main__')\n"
            "except StopProbe: print('STOPPED')\n"
        )
        for name in ("make_intake.py", "make_decision_sheet.py", "selftest.py",
                     "aggregate_ledger.py", "adversarial_eval.py", "sync_skill_table.py"):
            with self.subTest(entrypoint=name), tempfile.TemporaryDirectory() as tmp:
                scripts = Path(tmp) / "scripts"
                scripts.mkdir()
                for source in SCRIPT.parent.glob("*.py"):
                    shutil.copyfile(source, scripts / source.name)
                env = os.environ.copy()
                env.pop("PYTHONDONTWRITEBYTECODE", None)
                env.pop("PYTHONPYCACHEPREFIX", None)
                result = subprocess.run([sys.executable, "-c", probe, str(scripts / name)],
                                        capture_output=True, text=True, encoding="utf-8",
                                        cwd=tmp, env=env, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "STOPPED")
                self.assertFalse(list(scripts.rglob("*.pyc")))

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
        now = production_registry_now()
        c = candidate(model="gpt-6-sol", observed_at=now, quota={"used_pct": 10, "observed_at": now})
        p = self.m.make_plan({"run_id": "registry-check", "steps": [step()]}, self.catalog,
                             {"candidates": [c]}, now)
        self.assertEqual(p["status"], "ready")
        self.assertIn("model_registry", p)
        self.assertEqual(p["steps"][0]["route"]["requested_model"], "gpt-6-sol")
        self.assertIsNone(p["steps"][0]["route"]["resolved_model"])

    def test_harness_ultra_is_not_an_ordinary_worker_effort(self):
        now = production_registry_now()
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
        p = self.plan([node], [candidate(effective_effort="high")])
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
        p = self.plan([node], [candidate(quality_tier=3, effective_effort="xhigh")])
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
        p = self.plan([writer, reviewer], [candidate(effective_effort="high"),
                                           candidate("reviewer", surface="claude",
                                                     effective_effort="high")])
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
                    "REASONING_ABSTRACT", "VISION", "PLAN_ARCHITECTURE",
                    "CODE_COMPLEX", "CODE_SIMPLE", "WRITING", "IMAGE_GENERATION"}
        self.assertEqual(set(self.m.TASK_TYPE_MAP), expected)
        for mapping in self.m.TASK_TYPE_MAP.values():
            self.assertEqual(routing.PROC_BY_ID[mapping["proc"]][1], mapping["class"])
            self.assertEqual(set(mapping), {"kind", "needs", "demand", "proc", "class"})

    def test_task_specific_demand_avoids_max_for_every_coding_and_planning_node(self):
        for task_type, quality, expected_effort in (
            ("CODE_SIMPLE", 2, "low"), ("CODE_COMPLEX", 3, "high"),
            ("PLAN_ARCHITECTURE", 2, "high"),
        ):
            with self.subTest(task_type=task_type):
                p = self.plan([self.typed(task_type)],
                              [candidate(quality_tier=quality, effective_effort=expected_effort)])
                self.assertEqual(p["status"], "ready")
                self.assertEqual(p["steps"][0]["route"]["requested_effort"], expected_effort)
        critical = self.typed("CODE_COMPLEX", demand="critical")
        p = self.plan([critical], [candidate(quality_tier=3, effective_effort="xhigh")])
        self.assertEqual(p["steps"][0]["route"]["requested_effort"], "xhigh")

    def test_task_fit_shadow_records_different_winner_without_changing_dispatch(self):
        opener = candidate("generic", model="gpt-6-sol", quality_tier=3,
                           resource_rank=0, capabilities=["reasoning"], effective_effort="high")
        opus = candidate("task-fit", surface="claude", model="claude-opus-5-5",
                         quality_tier=3, resource_rank=9, capabilities=["reasoning"],
                         effective_effort="high")
        p = self.plan([self.typed("PLAN_ARCHITECTURE")], [opener, opus],
                      task_fit_policy=self.task_fit_fixture())
        route = p["steps"][0]["route"]
        shadow = p["steps"][0]["shadow_task_fit"]
        self.assertEqual(p["status"], "ready")
        self.assertEqual(route["candidate_id"], "generic")
        self.assertEqual(shadow["status"], "ranked")
        self.assertEqual(shadow["suggested_candidate_id"], "task-fit")
        self.assertEqual(shadow["active_candidate_id"], "generic")
        self.assertTrue(shadow["would_change"])
        self.assertEqual(shadow["policy_version"], "offline-shadow-1")
        self.assertEqual(shadow["evidence_scope"], "public-advisory-not-host-validation")

    def test_task_fit_shadow_cannot_promote_unsafe_or_wrong_effort(self):
        generic = candidate("generic", model="gpt-6-sol", quality_tier=3,
                            resource_rank=0, capabilities=["reasoning"], effective_effort="high")
        opus = candidate("task-fit", surface="claude", model="claude-opus-5-5",
                         quality_tier=3, resource_rank=9, capabilities=["reasoning"],
                         effective_effort="high")
        no_overage = copy.deepcopy(opus)
        no_overage["billing"]["model_included"] = False
        p = self.plan([self.typed("PLAN_ARCHITECTURE")], [generic, no_overage],
                      task_fit_policy=self.task_fit_fixture())
        self.assertEqual(p["steps"][0]["route"]["candidate_id"], "generic")
        self.assertNotEqual(p["steps"][0]["shadow_task_fit"].get("suggested_candidate_id"), "task-fit")
        wrong_effort = self.task_fit_fixture(efforts=["low"])
        p = self.plan([self.typed("PLAN_ARCHITECTURE")], [generic, opus],
                      task_fit_policy=wrong_effort)
        self.assertEqual(p["steps"][0]["shadow_task_fit"]["status"], "no-matched-evidence")
        self.assertEqual(p["steps"][0]["route"]["candidate_id"], "generic")

    def test_task_fit_shadow_never_outranks_money_or_high_quota_pressure(self):
        generic = candidate("generic", model="gpt-6-sol", quality_tier=3,
                            resource_rank=0, capabilities=["reasoning"], effective_effort="high")
        opus = candidate("task-fit", surface="claude", model="claude-opus-5-5",
                         quality_tier=3, resource_rank=9, capabilities=["reasoning"],
                         effective_effort="high")
        policy = self.task_fit_fixture()
        quota_heavy = copy.deepcopy(opus)
        quota_heavy["quota"]["used_pct"] = 90
        p = self.plan([self.typed("PLAN_ARCHITECTURE")], [generic, quota_heavy],
                      task_fit_policy=policy)
        self.assertEqual(p["steps"][0]["shadow_task_fit"]["status"], "unranked-wins")
        self.assertIsNone(p["steps"][0]["shadow_task_fit"]["suggested_candidate_id"])
        metered = copy.deepcopy(opus)
        metered["billing"] = {"mode": "api", "verified": True, "account_ref": "fixture-api"}
        metered["upper_usd_per_attempt"] = 0.1
        p = self.plan([self.typed("PLAN_ARCHITECTURE")], [generic, metered],
                      budget={"approved_usd": 1}, task_fit_policy=policy)
        self.assertEqual(p["steps"][0]["shadow_task_fit"]["status"], "unranked-wins")
        self.assertIsNone(p["steps"][0]["shadow_task_fit"]["suggested_candidate_id"])

    def test_task_fit_shadow_expiry_and_image_generation_boundary(self):
        policy = self.task_fit_fixture(checked_at="2026-09-21T10:00:00+00:00",
                                       valid_until="2026-09-22T10:00:00+00:00")
        p = self.plan([self.typed("PLAN_ARCHITECTURE")],
                      [candidate(quality_tier=3, effective_effort="high")],
                      task_fit_policy=policy)
        self.assertEqual(p["steps"][0]["shadow_task_fit"]["status"], "expired")
        self.assertEqual(p["status"], "ready")
        image = self.typed("IMAGE_GENERATION")
        for surface in ("claude", "codex"):
            with self.subTest(surface=surface):
                fake = candidate(surface=surface, capabilities=["image_generation", "vision"])
                blocked = self.plan([image], [fake])
                self.assertEqual(blocked["status"], "blocked")
                node = blocked["steps"][0]
                self.assertEqual(node["kind"], "image")
                self.assertEqual(node["needs"], ["image_generation"])
                self.assertIn("IMAGE_GENERATION_REQUIRES_VERIFIED_TOOL", node["errors"])
                self.assertIsNone(node["route"])
                self.assertIsNone(node["handoff"])
        with self.assertRaisesRegex(ValueError, "Invalid step kind"):
            self.plan([step(kind="image")])

    def test_image_generation_requires_atomic_subscription_host_tool(self):
        image = self.typed("IMAGE_GENERATION", task="Draw an original blue circle")
        tool = image_tool()
        p = self.plan([image], image_tools=[tool], host_ref="fixture-host",
                      interaction_ref="fixture-interaction")
        self.assertEqual(p["status"], "ready", p["steps"][0]["errors"])
        node = p["steps"][0]
        self.assertEqual(node["kind"], "image")
        self.assertEqual(node["route"]["tool_ref"], "fixture.image")
        self.assertEqual(node["route"]["model"], None)
        self.assertEqual(node["handoff"]["kind"], "host-image")
        self.assertEqual(self.m.ready_steps(p, [], NOW), ["read"])
        older_billing = copy.deepcopy(tool)
        older_billing["billing"]["observed_at"] = (
            datetime.fromisoformat(NOW) - timedelta(minutes=10)).isoformat()
        older_plan = self.plan([image], image_tools=[older_billing],
                               host_ref="fixture-host", interaction_ref="fixture-interaction")
        self.assertEqual(older_plan["steps"][0]["route"]["valid_until"],
                         (datetime.fromisoformat(NOW) + timedelta(minutes=5)).isoformat())
        for billing_change in ({"paid_credit_fallback_disabled": False},
                               {"provider_hard_cap_enforced": False},
                               {"provider_hard_cap_usd": 1},
                               {"observed_at": None},
                               {"observed_at": "2026-09-01T00:00:00+00:00"},
                               {"image_included": False}):
            with self.subTest(billing_change=billing_change):
                unsafe = copy.deepcopy(tool)
                unsafe["billing"].update(billing_change)
                blocked = self.plan([image], image_tools=[unsafe], host_ref="fixture-host",
                                    interaction_ref="fixture-interaction")
                self.assertEqual(blocked["status"], "blocked")
                self.assertIsNone(blocked["steps"][0]["route"])
        wrong_host = self.plan([image], image_tools=[tool], host_ref="other-host",
                               interaction_ref="fixture-interaction")
        self.assertEqual(wrong_host["status"], "blocked")
        no_lookup = copy.deepcopy(tool)
        no_lookup["lookup_by_request"] = False
        self.assertEqual(self.plan([image], image_tools=[no_lookup], host_ref="fixture-host",
                                   interaction_ref="fixture-interaction")["status"], "blocked")

    def test_image_quota_requires_account_bound_evidence(self):
        image = self.typed("IMAGE_GENERATION")
        for change in ({"evidence": []}, {"account_ref": None},
                       {"account_ref": "other-account"},
                       {"surface": "claude"}, {"transport": "cli"}):
            with self.subTest(change=change):
                tool = image_tool()
                tool["quota"].update(change)
                blocked = self.plan([image], image_tools=[tool], host_ref="fixture-host",
                                    interaction_ref="fixture-interaction")
                self.assertEqual(blocked["status"], "blocked")
                self.assertIn("IMAGE_QUOTA_UNVERIFIED", self.m.assess_image_tool(
                    tool, {"host_ref": "fixture-host", "interaction_ref": "fixture-interaction"},
                    image, NOW))

    def test_image_tool_malformed_billing_fails_closed(self):
        image = self.typed("IMAGE_GENERATION")
        for billing in (None, [], "subscription"):
            with self.subTest(billing=billing):
                tool = image_tool(billing=billing)
                blocked = self.plan([image], image_tools=[tool], host_ref="fixture-host",
                                    interaction_ref="fixture-interaction")
                self.assertEqual(blocked["status"], "blocked")
                self.assertIsNone(blocked["steps"][0]["route"])
                self.assertIn("IMAGE_SUBSCRIPTION_HARD_CAP_UNVERIFIED",
                              blocked["steps"][0]["rejected_candidates"][0]["reasons"])
                self.assertIn("IMAGE_QUOTA_UNVERIFIED",
                              blocked["steps"][0]["rejected_candidates"][0]["reasons"])

    def test_image_host_adapter_claims_once_and_never_auto_settles(self):
        import execute_image
        import run_state

        tool = image_tool()
        image = self.typed("IMAGE_GENERATION", task="Draw an original blue circle")
        plan = self.plan([image], image_tools=[tool], host_ref="fixture-host",
                         interaction_ref="fixture-interaction")
        receipt = {"request_id": execute_image.request_identity(plan, "read"),
                   "handle": {"kind": "host-image", "id": "fixture-job",
                              "identity": execute_image.request_identity(plan, "read")},
                   "state": "succeeded", "observed_at": NOW,
                   "evidence": ["fixture output receipt"],
                   "result_sha256": hashlib.sha256(b"fixture image").hexdigest()}
        later = (datetime.fromisoformat(NOW) + timedelta(minutes=1)).isoformat()

        class Host:
            sends = 0
            lookups = 0

            def observe_image_tool(self):
                return copy.deepcopy(tool)

            def generate_once(self, **kwargs):
                self.sends += 1
                self.assert_args = kwargs
                return copy.deepcopy(receipt)

            def lookup_by_request(self, request_id):
                self.lookups += 1
                updated = copy.deepcopy(receipt)
                updated["observed_at"] = later
                return updated

        host = Host()
        with tempfile.TemporaryDirectory() as directory:
            store = run_state.Store(Path(directory) / "image.sqlite3")
            store.initialize()
            store.register(plan, NOW)
            first = execute_image.dispatch(plan, "read", store, host, NOW)
            second = execute_image.dispatch(plan, "read", store, host, later)
            self.assertEqual(first["status"], "succeeded")
            self.assertEqual(second["status"], "succeeded")
            self.assertEqual((host.sends, host.lookups), (1, 1))
            self.assertTrue(host.assert_args["subscription_only"])
            self.assertEqual(host.assert_args["provider_hard_cap_usd"], 0)
            self.assertFalse(first["verified"])
            self.assertIsNone(first["actual_usd"])
            store.reject(first["dispatch_id"], ["fixture rejection"], later)
            rejected = execute_image.dispatch(plan, "read", store, host, later)
            self.assertEqual(rejected["status"], "rejected")
            self.assertEqual((host.sends, host.lookups), (1, 2))
            receipt["result_sha256"] = hashlib.sha256(b"different image").hexdigest()
            with self.assertRaisesRegex(execute_image.ImageDispatchError,
                                        "IMAGE_TERMINAL_RECEIPT_CHANGED"):
                execute_image.dispatch(plan, "read", store, host, later)
            self.assertEqual(host.sends, 1)

    def test_image_host_adapter_rechecks_after_claim_and_holds_changed_cost(self):
        import execute_image
        import run_state

        tool = image_tool()
        image = self.typed("IMAGE_GENERATION", task="Draw an original blue circle")
        plan = self.plan([image], image_tools=[tool], host_ref="fixture-host",
                         interaction_ref="fixture-interaction")

        class ChangedHost:
            observations = 0
            sends = 0
            lookups = 0

            def observe_image_tool(self):
                self.observations += 1
                result = copy.deepcopy(tool)
                if self.observations > 1:
                    result["billing"]["provider_hard_cap_enforced"] = False
                return result

            def generate_once(self, **kwargs):
                self.sends += 1
                raise AssertionError("must not send")

            def lookup_by_request(self, request_id):
                self.lookups += 1
                return None

        host = ChangedHost()
        with tempfile.TemporaryDirectory() as directory:
            store = run_state.Store(Path(directory) / "image.sqlite3")
            store.initialize()
            store.register(plan, NOW)
            with self.assertRaisesRegex(execute_image.ImageDispatchError,
                                        "IMAGE_HOST_REVALIDATION_FAILED"):
                execute_image.dispatch(plan, "read", store, host, NOW)
            self.assertEqual(host.sends, 0)
            self.assertEqual(store.ready("test-run", NOW), [])
            recovered = execute_image.reconcile(plan, "read", store, host, NOW)
            self.assertEqual(recovered["status"], "uncertain")
            repeat = execute_image.dispatch(plan, "read", store, host, NOW)
            self.assertEqual(repeat["status"], "uncertain")
            self.assertEqual((host.sends, host.lookups), (0, 2))

    def test_packaged_complex_coding_fit_can_advise_opus_medium_without_dispatch(self):
        policy = self.m.load_task_fit_policy()
        observed = (datetime.fromisoformat(policy["checked_at"])
                    + timedelta(minutes=1)).isoformat()
        active = candidate("generic", model="gpt-6-sol", quality_tier=3)
        opus = candidate("opus-medium", surface="claude", model="claude-opus-5-5",
                         quality_tier=3, resource_rank=9)
        result = self.m.shadow_task_fit({"task_type": "CODE_COMPLEX"},
                                        [(0, active, "high", 0),
                                         (1, opus, "medium", 0)],
                                        active, policy, observed)
        self.assertEqual(result["status"], "ranked")
        self.assertEqual(result["suggested_candidate_id"], "opus-medium")
        self.assertEqual(result["suggested_effort"], "medium")
        self.assertEqual(result["advisory_rank"], 0)
        self.assertEqual(result["active_candidate_id"], "generic")

    def test_packaged_task_fit_entries_use_registered_models_and_api_efforts(self):
        policy = self.m.load_task_fit_policy()
        models = {m["id"]: m for m in self.m.load_registry()["models"]}
        for profile, entries in policy["profiles"].items():
            for entry in entries:
                with self.subTest(profile=profile, model=entry["model"]):
                    model = models[entry["model"]]
                    self.assertIn(model["surface"], {"claude", "codex"})
                    self.assertNotIn("generation", model)
                    self.assertLessEqual(set(entry["efforts"]), set(model["api_efforts"]))

    def test_legacy_generation_loses_only_to_an_equally_ranked_current_model(self):
        # Candidate-ID order let a legacy model beat an equally ranked current one.
        def seat(name, rank=1, used=10, **changes):
            c = candidate(name, model=name, resource_rank=rank, **changes)
            c["quota"]["used_pct"] = used
            return c

        def chosen(*seats):
            registry = fixture_registry(list(seats))
            for model in registry["models"]:
                if model["id"] == "a-old":
                    model["generation"] = "legacy"
            p = self.m.make_plan({"run_id": "tie", "steps": [step()], "budget": {}}, self.catalog,
                                 {"candidates": list(seats), "tools": [], "observed_at": NOW}, NOW, registry)
            self.assertEqual(p["status"], "ready", p["steps"][0]["errors"])
            return p["steps"][0]["route"]["candidate_id"]

        self.assertEqual(chosen(seat("a-old"), seat("b-new")), "b-new")
        self.assertEqual(chosen(seat("a-old", generation="current"), seat("b-new", generation="legacy")), "b-new")
        # Quota pressure under the 80% line no longer outranks the label.
        self.assertEqual(chosen(seat("a-old", used=5), seat("b-new", used=50)), "b-new")
        # Declared resource rank and the 80% quota guard still decide first.
        self.assertEqual(chosen(seat("a-old"), seat("b-new", rank=2)), "a-old")
        self.assertEqual(chosen(seat("a-old"), seat("b-new", used=90)), "a-old")

    def test_packaged_grok_47_beats_an_equally_ranked_legacy_grok_45(self):
        now = production_registry_now()

        def grok(model):
            c = candidate("grok:" + model, surface="grok", model=model, observed_at=now,
                          effective_effort="high")
            c["quota"]["observed_at"] = now
            return c

        steps = [{"id": "fix", "task": "t", "task_type": "CODE_FIX", "skills": ["explain"],
                  "depends_on": [], "writes": False},
                 {"id": "plan", "task": "t", "task_type": "PLAN_ARCHITECTURE", "skills": ["explain"],
                  "depends_on": [], "writes": False}]
        p = self.m.make_plan({"run_id": "grok-tie", "steps": steps}, self.catalog,
                             {"candidates": [grok("grok-4.7"), grok("grok-4.5")]}, now)
        self.assertEqual(p["status"], "ready")
        self.assertEqual([s["route"]["candidate_id"] for s in p["steps"]], ["grok:grok-4.7"] * 2)

    def test_shadow_task_fit_prefers_current_generation_on_an_exact_tie(self):
        policy = copy.deepcopy(self.m.load_task_fit_policy())
        observed = (datetime.fromisoformat(policy["checked_at"]) + timedelta(minutes=1)).isoformat()
        source = next(iter(policy["sources"]))
        policy["profiles"]["CODE_COMPLEX"] = [
            {"model": "old-model", "efforts": ["high"], "rank": 0, "sources": [source]},
            {"model": "new-model", "efforts": ["high"], "rank": 0, "sources": [source]}]
        old = candidate("a-old", model="old-model", generation="legacy")
        new = candidate("b-new", model="new-model")
        result = self.m.shadow_task_fit({"task_type": "CODE_COMPLEX"},
                                        [(0, old, "high", 0), (0, new, "high", 0)], new, policy, observed)
        self.assertEqual(result["status"], "ranked")
        self.assertEqual(result["suggested_candidate_id"], "b-new")
        self.assertFalse(result["would_change"])

    def test_advisory_table_names_gpt_61_sol_within_the_body_budget(self):
        text = (SCRIPT.parent.parent / "SKILL.md").read_text(encoding="utf-8")
        body = text.split("\n---\n", 1)[1].splitlines()
        self.assertLessEqual(len(body), 400)
        start = body.index("| Deliverable | Advisory starting points, never active routes | Initial reasoning |")
        rows = body[start + 2:body.index("", start)]
        for deliverable in ("Architecture", "Difficult, multi-file coding", "Focused bug fix",
                            "Polished writing"):
            with self.subTest(deliverable=deliverable):
                row = next(line for line in rows if line.startswith("| " + deliverable))
                self.assertIn("GPT-6.1 Sol", row)

    def test_packaged_task_fit_policy_is_shadow_only_and_malformed_entries_fail_cleanly(self):
        policy = self.m.load_task_fit_policy()
        self.assertEqual(policy["status"], "shadow-only")
        self.assertEqual(set(policy["profiles"]),
                         {"PLAN_ARCHITECTURE", "CODE_COMPLEX", "CODE_SIMPLE", "WRITING"})
        self.assertNotIn("VISION", policy["profiles"])
        self.assertNotIn("IMAGE_GENERATION", policy["profiles"])
        for field, value in (("efforts", [["high"]]), ("sources", [["manufacturer"]]),
                             ("rank", True)):
            with self.subTest(field=field):
                malformed = self.task_fit_fixture()
                malformed["profiles"]["PLAN_ARCHITECTURE"][0][field] = value
                with self.assertRaisesRegex(ValueError, "Invalid task-fit entry"):
                    self.m.validate_task_fit_policy(malformed)

    def test_coding_quality_floor_is_independent_of_requested_effort(self):
        for task_type, insufficient_tier, required_floor in (
            ("CODE_SIMPLE", 1, 2), ("CODE_COMPLEX", 2, 3),
        ):
            with self.subTest(task_type=task_type):
                blocked = self.plan([self.typed(task_type)],
                                    [candidate(quality_tier=insufficient_tier)])
                self.assertEqual(blocked["status"], "blocked")
                self.assertIn("QUALITY_FLOOR", str(blocked))
                eligible = self.plan([self.typed(task_type)],
                                     [candidate(quality_tier=required_floor,
                                                effective_effort="high" if task_type == "CODE_COMPLEX" else "low")])
                self.assertEqual(eligible["status"], "ready")
                self.assertEqual(eligible["steps"][0]["quality_floor"], required_floor)
                with self.assertRaises(ValueError):
                    self.plan([self.typed(task_type, quality_floor=insufficient_tier)])
        with self.assertRaises(ValueError):
            self.plan([step(quality_floor="2")])

    def test_claude_and_codex_share_task_quality_and_subscription_guards(self):
        profiles = (("PLAN_ARCHITECTURE", 2, "high"),
                    ("CODE_SIMPLE", 2, "low"),
                    ("CODE_COMPLEX", 3, "high"),
                    ("WRITING", 2, "high"))
        for surface in ("claude", "codex"):
            other = "codex" if surface == "claude" else "claude"
            for task_type, minimum_tier, effort in profiles:
                with self.subTest(surface=surface, task_type=task_type):
                    node = self.typed(task_type, surface=surface)
                    steps = [node]
                    candidates = [candidate("writer", surface=surface, quality_tier=minimum_tier,
                                            capabilities=["code", "reasoning", "writing"],
                                            effective_effort=effort)]
                    if task_type == "WRITING":
                        steps.append(step("review", surface=other, verify_of="read",
                                          depends_on=["read"]))
                        candidates.append(candidate("reviewer", surface=other,
                                                    capabilities=["reasoning", "research"]))
                    ready = self.plan(steps, candidates)
                    self.assertEqual(ready["status"], "ready")
                    self.assertEqual(ready["steps"][0]["route"]["requested_effort"], effort)
                    self.assertEqual(ready["steps"][0]["route"]["surface"], surface)
                    self.assertEqual(ready["budget"]["reserved_upper_usd"], 0)
                    if task_type == "WRITING":
                        self.assertEqual(ready["steps"][1]["route"]["surface"], other)
                    if task_type.startswith("CODE_"):
                        self.assertEqual(ready["steps"][0]["quality_floor"], minimum_tier)
                    weak = copy.deepcopy(candidates)
                    weak[0]["quality_tier"] = minimum_tier - 1
                    self.assertIn("QUALITY_FLOOR", str(self.plan(steps, weak)))
                    unsafe = copy.deepcopy(candidates)
                    unsafe[0]["billing"]["model_included"] = False
                    self.assertIn("MODEL_INCLUSION_UNVERIFIED", str(self.plan(steps, unsafe)))

    def test_writing_requires_writing_capability_not_generic_reasoning(self):
        node = self.typed("WRITING")
        reviewer = step("review", verify_of="read", depends_on=["read"])
        review_route = candidate("reviewer", surface="claude")
        blocked = self.plan([node, reviewer], [candidate(), review_route])
        self.assertEqual(blocked["status"], "blocked")
        self.assertIn("CAPABILITY_MISMATCH", str(blocked))
        eligible = candidate(capabilities=["writing", "reasoning"], effective_effort="high")
        routed = self.plan([node, reviewer], [eligible, review_route])
        self.assertEqual(routed["status"], "ready")
        self.assertEqual(routed["steps"][0]["route"]["requested_effort"], "high")

    def test_typed_writing_requires_independent_review_even_without_file_edits(self):
        writer = self.typed("WRITING", writes=False)
        writer_route = candidate("writer", surface="claude",
                                 capabilities=["writing", "reasoning"], effective_effort="high")
        without_review = self.plan([writer], [writer_route])
        self.assertEqual(without_review["status"], "blocked")
        self.assertIn("MISSING_REVIEW", without_review["steps"][0]["errors"])

        reviewer = step("review", verify_of="read", depends_on=["read"])
        consumer = step("consume", depends_on=["read"])
        same_vendor = candidate("same-vendor-reviewer", surface="claude",
                                capabilities=["reasoning", "research"])
        not_independent = self.plan([writer, reviewer], [writer_route, same_vendor])
        self.assertEqual(not_independent["status"], "blocked")
        self.assertIn("SAME_VENDOR_REVIEW", str(not_independent))
        independent = candidate("reviewer", surface="codex",
                                capabilities=["reasoning", "research"])
        reviewed = self.plan([writer, reviewer, consumer], [writer_route, independent])
        self.assertEqual(reviewed["status"], "ready")
        self.assertNotEqual(reviewed["steps"][0]["route"]["vendor"],
                            reviewed["steps"][1]["route"]["vendor"])
        written = self.events(reviewed, {"id": "read", "status": "done",
                                         "verified": True, "evidence": ["fixture output"]})
        self.assertEqual(self.m.ready_steps(reviewed, written, now=NOW), ["review"])
        approved = written + self.events(reviewed, {"id": "review", "status": "done",
                                                  "verified": True, "evidence": ["fixture review"]})
        self.assertEqual(self.m.ready_steps(reviewed, approved, now=NOW), ["consume"])

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


class GrokCliGuardRegression(unittest.TestCase):
    """Synthetic transport only; no model or billing mutation."""

    def test_native_grok_transport_stays_on_operational_hold(self):
        import execute_grok_cli as grok
        import run_state
        with self.assertRaisesRegex(run_state.StateError, "GROK_CLI_OPERATIONAL_HOLD"):
            grok.GrokCli("C:/untrusted/grok.exe", "fixture")

    def setUp(self):
        import execute_grok_cli as grok
        import run_state
        import runtime_collect
        self.grok, self.run_state = grok, run_state
        self.tmp = tempfile.TemporaryDirectory(prefix="vibe-grok-offline-")
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name).resolve()
        binary = root / "grok.exe"
        binary.write_bytes(b"fixture")
        sha = hashlib.sha256(binary.read_bytes()).hexdigest()
        profile = root / "profile"
        profile.mkdir()
        profile_ref = runtime_collect.opaque("grok", str(profile))
        account_ref = runtime_collect.opaque("grok", profile_ref, "fixture-account")
        binding = {"executable": str(binary), "executable_sha256": sha,
                   "cwd": str(root), "profile_path": str(profile),
                   "profile_ref": profile_ref, "account_ref": account_ref,
                   "prompt_path": str(root / "prompt.txt"),
                   "result_path": str(root / "result.jsonl"),
                   "content_path": str(root / "result.txt")}
        c = candidate("grok-cli", surface="grok", transport="cli", model="grok-test")
        c["billing"]["account_ref"] = account_ref
        c["quota"]["account_ref"] = account_ref
        node = step("opening", surface="grok", skills=[], software=[],
                    task="Provide an independent position", cli=binding)
        # Exercise source mechanics only; production planner keeps Grok CLI unavailable.
        with patch.object(grok.orchestrate, "GUARDED_EXECUTION_ADAPTERS",
                          grok.orchestrate.GUARDED_EXECUTION_ADAPTERS | {("grok", "cli")}):
            self.plan = grok.orchestrate.make_plan({"run_id": "grok-fixture", "steps": [node],
                "budget": {"max_attempts": 1}}, {}, {"candidates": [c], "tools": []},
                NOW, fixture_registry([c]))
        self.assertEqual(self.plan["status"], "ready", self.plan["errors"])
        self.store = run_state.Store(root / "state.sqlite3")
        self.store.initialize()
        self.store.register(self.plan, now=NOW)

        class FakeGrok:
            def __init__(self):
                self.executable, self.sha256 = str(binary), sha
                self.observed = {"account_verified": True, "account_ref": account_ref,
                    "profile_ref": profile_ref, "local_tool_config_empty": True,
                    "auth": {"logged_in": True},
                    "billing": {"mode": "subscription", "extra_usage_enabled": False,
                                "on_demand_cap": "0", "prepaid_balance": "0"},
                    "models": [{"model": "grok-test", "transport_efforts": ["low"]}]}
                self.trace, self.sends = [], []

            def check_binary(self):
                return None

            def auth(self, binding, env, now):
                return copy.deepcopy(self.observed)

            def send(self, argv, binding, env):
                self.sends.append((argv, env, Path(binding["prompt_path"]).read_text(encoding="utf-8")))
                return 0, b"\n".join(json.dumps(e).encode() for e in self.trace) + b"\n"

        self.cli = FakeGrok()
        self.adapter = grok.Adapter(self.store, self.cli, clock=lambda: NOW)
        self.cert = {"verified": True, "subscription_only": True,
            "binding_sha256": grok.binding_digest(self.plan, "opening"),
            "account_ref": account_ref, "profile_ref": profile_ref,
            "billing": copy.deepcopy(c["billing"]), "quota": copy.deepcopy(c["quota"]),
            "model": "grok-test", "effort": "low", "observed_at": NOW,
            "valid_until": "2026-09-23T10:10:00+00:00",
            "evidence": ["fixture account-bound subscription proof"]}
        session = grok.request_id(self.plan, "opening")
        self.cli.trace = [
            {"type": "system", "subtype": "init", "session_id": session,
             "apiKeySource": "oauth", "model": "grok-test"},
            {"type": "assistant", "session_id": session,
             "message": {"model": "grok-test", "content": [{"type": "text", "text": "Position"}],
                         "stop_reason": "end_turn"}},
            {"type": "result", "session_id": session, "subtype": "success",
             "is_error": False, "stop_reason": "end_turn", "result": "Position",
             "num_turns": 1, "usage": {"input_tokens": 8, "output_tokens": 2,
                                      "server_tool_use": {"web_search_requests": 0}},
             "modelUsage": {"grok-test": {"modelCalls": 1}}}]

    def test_one_send_private_prompt_and_lookup_only_reentry(self):
        result = self.adapter.dispatch(self.plan, "opening", self.cert)
        self.assertEqual(result["state"], "succeeded", result)
        self.assertIsNone(result["actual_usd"])
        self.assertFalse(result["verified"])
        argv, env, prompt = self.cli.sends[0]
        for flag in ("--prompt-file", "--no-auto-update", "--no-subagents", "MCPTool"):
            self.assertIn(flag, argv)
        self.assertNotIn("Provide an independent position", " ".join(argv))
        self.assertNotIn("XAI_API_KEY", env)
        self.assertIn("Provide an independent position", prompt)
        self.assertEqual(self.adapter.dispatch(self.plan, "opening", None)["state"], "succeeded")
        self.assertEqual(len(self.cli.sends), 1)

    def test_missing_cost_proof_and_changed_account_block_before_send(self):
        for change in ({"paid_credit_fallback_disabled": None},
                       {"model_included": False}, {"extra_usage_enabled": True}):
            bad = copy.deepcopy(self.cert)
            bad["billing"].update(change)
            with self.assertRaises(self.run_state.StateError):
                self.adapter.dispatch(self.plan, "opening", bad)
        self.cli.observed["account_ref"] = "changed"
        with self.assertRaises(self.run_state.StateError):
            self.adapter.dispatch(self.plan, "opening", self.cert)
        self.cli.observed["account_ref"] = self.cert["account_ref"]
        self.cli.observed["local_tool_config_empty"] = False
        with self.assertRaises(self.run_state.StateError):
            self.adapter.dispatch(self.plan, "opening", self.cert)
        self.assertEqual(self.cli.sends, [])

    def test_tool_wrong_model_and_api_key_trace_rejected(self):
        for mutate in (
            lambda t: t[1]["message"]["content"].append({"type": "tool_use", "name": "run_terminal_cmd"}),
            lambda t: t[1]["message"].update(model="other-model"),
            lambda t: t[0].update(apiKeySource="user"),
        ):
            trace = copy.deepcopy(self.cli.trace)
            mutate(trace)
            raw = b"\n".join(json.dumps(e).encode() for e in trace) + b"\n"
            with self.assertRaises(self.run_state.StateError):
                self.grok.parse_result(raw, self.grok.request_id(self.plan, "opening"),
                                       "grok-test")

    def test_ambiguous_tool_trace_remains_uncertain_without_second_send(self):
        self.cli.trace[1]["message"]["content"].append(
            {"type": "tool_use", "name": "run_terminal_cmd"})
        first = self.adapter.dispatch(self.plan, "opening", self.cert)
        self.assertEqual(first["state"], "uncertain")
        again = self.adapter.dispatch(self.plan, "opening", None)
        self.assertEqual(again["dispatch_id"], first["dispatch_id"])
        self.assertEqual(again["state"], "uncertain")
        self.assertEqual(len(self.cli.sends), 1)

    def test_preexisting_lookalike_trace_without_capture_receipt_is_not_accepted(self):
        self.store.claim(self.plan["run_id"], "opening",
                         self.grok.request_id(self.plan, "opening"),
                         self.plan["plan_digest"], now=NOW)
        path = Path(self.plan["steps"][0]["cli"]["result_path"])
        path.write_bytes(b"\n".join(json.dumps(e).encode() for e in self.cli.trace) + b"\n")
        result = self.adapter.reconcile(self.plan, "opening")
        self.assertEqual(result["state"], "uncertain")
        self.assertEqual(self.cli.sends, [])


class TddGuardRegression(unittest.TestCase):
    def test_nested_python_tests_are_tests_without_weakening_source_gate(self):
        source_guard = SCRIPT.parents[3] / "skills-src/simon-tdd/scripts/tdd-guard-check.sh"
        bundle_guard = SCRIPT.parents[4] / "SimonKStack/skills/simon-tdd/scripts/tdd-guard-check.sh"
        guard = source_guard if source_guard.is_file() else bundle_guard
        self.assertTrue(guard.is_file(), "TDD guard must be present in source or candidate")
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
