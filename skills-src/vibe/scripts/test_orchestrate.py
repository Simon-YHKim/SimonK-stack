"""Offline contract tests for the umbrella planner; no worker or Bot is launched."""
import copy
import importlib.util
import tempfile
import unittest
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
        c = candidate(billing={"mode": "api", "verified": True}, upper_usd_per_attempt=0.3)
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


if __name__ == "__main__":
    unittest.main()
