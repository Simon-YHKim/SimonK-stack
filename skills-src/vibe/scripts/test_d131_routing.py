"""Offline D-131 examples using the packaged registry, policy and actual agy collector shape."""
import unittest
from datetime import datetime, timedelta

import agy_lanes
import orchestrate
import runtime_collect
from test_execute_agy_prose import agy_raw
from test_orchestrate import candidate, cli_binding


def inputs():
    now = (datetime.fromisoformat(orchestrate.load_task_fit_policy()["checked_at"]) + timedelta(minutes=1)).isoformat()
    raw = dict(agy_raw(), _agy_models=list(agy_lanes.MODELS))
    runtime = runtime_collect.snapshot([runtime_collect.normalize("antigravity", raw, now, "/fixture/agy")], now)
    for model, effort, surface, transport in (("gpt-6.2-sol", "high", "codex", "host"),
                                              ("gpt-6.2-astra", "xhigh", "codex", "cli"),
                                              ("claude-opus-5-5", "high", "claude", "host")):
        c = candidate(model, surface=surface, model=model, transport=transport, quality_tier=3, observed_at=now,
                      effective_effort=effort, effort_by_demand=dict.fromkeys(orchestrate.DEMAND_TIER, effort))
        c["quota"]["observed_at"] = now
        runtime["candidates"].append(c)

    def node(ident, task, **fields):
        return dict({"id": ident, "task_type": task, "task": ident, "writes": False}, **fields)

    request = {"run_id": "d131-example", "steps": [
        node("implement", "CODE_NEW", surface="codex", writes=True),
        node("research", "RESEARCH", surface="codex", scale="large", cli=cli_binding("codex")),
        node("design", "PLAN_ARCHITECTURE", surface="antigravity"),
        node("batch", "BULK_LIGHT", surface="antigravity"),
        node("opinion", "REASONING_ABSTRACT", surface="antigravity"),
        node("draft", "KOREAN_PROSE"),
        node("check-code", "CODE_REVIEW_FINAL", surface="claude", verify_of="implement", depends_on=["implement"]),
        node("check-prose", "KOREAN_DOC", surface="claude", verify_of="draft", depends_on=["draft"])]}
    return request, runtime, now


class D131Routes(unittest.TestCase):
    def test_shared_plan_assigns_both_gpt_lanes_and_three_gemini_families(self):
        req, runtime, now = inputs()
        plan = orchestrate.make_plan(req, {}, runtime, now)
        self.assertEqual(plan["status"], "ready", [(s["id"], s["errors"]) for s in plan["steps"]])
        routes = {s["id"]: s["route"]["model"] for s in plan["steps"]}
        self.assertEqual([routes[key] for key in ("implement", "research", "design", "batch", "opinion", "draft")],
                         ["gpt-6.2-sol", "gpt-6.2-astra", agy_lanes.NEON, agy_lanes.HYDROGEN,
                          agy_lanes.ARGON, agy_lanes.NEON])
        self.assertEqual(orchestrate.ready_steps(plan, [], now)[:2], ["implement", "research"])

    def test_ineligible_orca_writer_does_not_mask_eligible_sol_host(self):
        req, runtime, now = inputs()
        host = next(c for c in runtime["candidates"] if c["model"] == "gpt-6.2-sol")
        native = dict(host, id="preferred-native", transport="orca", resource_rank=0)
        runtime["candidates"].append(native)
        step = orchestrate.make_plan(req, {}, runtime, now)["steps"][0]
        self.assertEqual(step["route"]["transport"], "host")
        self.assertTrue(any(c["candidate_id"] == native["id"] and "ORCA_CODING_LANE_NOT_ALLOWED" in c["reasons"]
                            for c in step["rejected_candidates"]))

    def test_model_specific_prose_fallback_and_shared_ceiling(self):
        req, runtime, now = inputs()
        runtime["prose_tools"][1]["quota"]["used_pct"] = 85
        draft = next(s for s in orchestrate.make_plan(req, {}, runtime, now)["steps"] if s["id"] == "draft")
        self.assertEqual((draft["route"]["model"], draft["selection"]["rank"]), (agy_lanes.ARGON, 1))
        runtime["prose_tools"][0]["quota"]["used_pct"] = None
        draft = next(s for s in orchestrate.make_plan(req, {}, runtime, now)["steps"] if s["id"] == "draft")
        self.assertIsNone(draft["route"])

    def test_codex_computer_use_requires_current_host_and_exact_model(self):
        req, runtime, now = inputs()
        seat = next(c for c in runtime["candidates"] if c["model"] == "gpt-6.2-astra")
        seat.update(transport="host", host_ref="current")
        tool = {"id": "cu", "transport": "computer-use", "host_surface": "codex", "host_ref": "current",
                "observed_at": now, "available": True, "interactive": True, "evidence": ["fixture tool inventory"]}
        runtime.update(host_ref="current", gui_tools=[tool])
        req["steps"] = [dict(id="screen", task_type="COMPUTER_USE", writes=False, skills=["vibe-bot"],
                             target="fixture window", gui_reason="screen-only", tool_route_available=False)]
        catalog = {"vibe-bot": {"name": "vibe-bot", "path": "/fixture/bot"}}
        def route():
            return orchestrate.make_plan(req, catalog, runtime, now)["steps"][0]["route"]
        self.assertEqual(route()["model"], "gpt-6.2-astra")
        seat["host_ref"] = "another"
        self.assertIsNone(route())
