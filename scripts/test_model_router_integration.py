"""Offline model-router -> real planner CLI contracts; never launch providers."""
import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIBE = ROOT / "skills-src" / "vibe" / "scripts"
sys.path.insert(0, str(VIBE))
import orchestrate
from test_orchestrate import NOW, candidate, fixture_registry

SKILL = ROOT / "skills-src" / "model-router" / "SKILL.md"


class ModelRouterIntegrationTests(unittest.TestCase):
    def run_plan(self, nodes, candidates=None, registry=None, **request_fields):
        candidates = candidates if candidates is not None else [candidate(quality_tier=3)]
        registry = registry if registry is not None else fixture_registry(candidates)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("explain", "vibe-bot", "simonk"):
                folder = root / name
                folder.mkdir()
                (folder / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: Offline fixture\n---\n", encoding="utf-8")
            data = {"request": {"run_id": "parent-run", "ancestor_skills": ["vibe", "model-router"],
                                 "steps": nodes, **request_fields},
                    "runtime": {"candidates": candidates, "observed_at": NOW}, "registry": registry}
            for name, value in data.items():
                (root / (name + ".json")).write_text(json.dumps(value), encoding="utf-8")
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            result = subprocess.run(
                [sys.executable, str(VIBE / "orchestrate.py"), "plan", "--input", str(root / "request.json"),
                 "--runtime", str(root / "runtime.json"), "--registry", str(root / "registry.json"),
                 "--root", str(root), "--now", NOW],
                capture_output=True, text=True, encoding="utf-8", timeout=15)
            self.assertIn(result.returncode, (0, 2), result.stderr)
            after = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertEqual(before, after, "Planning must not dispatch or mutate inputs")
            return result.returncode, json.loads(result.stdout)

    def node(self, task_type="CODE_FIX", **changes):
        return {"id": "task", "task_type": task_type, "task": "Offline fixture",
                "skills": ["explain"], "writes": False, "depends_on": [], **changes}

    def test_documented_mapping_matches_executable_contract_and_all_types_plan(self):
        text = SKILL.read_text(encoding="utf-8")
        blocks = re.findall(r"<!-- task-type-contract:start -->\s*```json\s*(.*?)\s*```\s*"
                            r"<!-- task-type-contract:end -->", text, re.S)
        self.assertEqual(len(blocks), 1)
        mapping = json.loads(blocks[0])
        self.assertEqual(mapping, orchestrate.TASK_TYPE_MAP)
        self.assertEqual(len(mapping), 11)
        for task_type, fields in mapping.items():
            with self.subTest(task_type=task_type):
                node = self.node(task_type)
                c = candidate(quality_tier=3, capabilities=["code", "reasoning", "research", "vision"])
                if fields["kind"] == "gui":
                    node.update(skills=["vibe-bot"], target="Offline Console", tool_route_available=False,
                                gui_reason="No authorized tool route in fixture")
                    c = candidate("bot", surface="grok-bot", transport="bot", model=None,
                                  capabilities=["gui"], bot_id="fixture-bot", bot_status="active",
                                  provider_efforts=[], transport_efforts=[], effort_by_demand={})
                rc, p = self.run_plan([node], [c])
                self.assertEqual(rc, 0, p)
                for key, expected in fields.items():
                    self.assertEqual(p["steps"][0][key], expected)
                self.assertEqual(p["run_id"], "parent-run")
                self.assertEqual(p["ancestor_skills"], ["vibe", "model-router"])
                self.assertEqual(p["budget"]["approved_usd"], "0")
                self.assertIsNone(p["steps"][0]["route"]["actual_usd"])
                self.assertIsNone(p["steps"][0]["route"]["effective_effort"])

    def test_registry_fingerprint_comes_from_consumed_registry(self):
        registry = fixture_registry([candidate()])
        rc, plan = self.run_plan([self.node()], [candidate()], registry)
        expected = hashlib.sha256(json.dumps(registry, sort_keys=True, ensure_ascii=False,
                                              separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        self.assertEqual(rc, 0, plan)
        self.assertEqual(plan["model_registry"]["sha256"], expected)
        self.assertEqual(plan["model_registry"]["version"], registry["version"])
        changed = copy.deepcopy(registry)
        changed["version"] = "changed-fixture"
        _, other = self.run_plan([self.node()], [candidate()], changed)
        self.assertNotEqual(other["model_registry"]["sha256"], expected)

    def test_cli_rejects_typed_weakening_and_unknown_type(self):
        for fields in ({"demand": "routine"}, {"needs": []}, {"proc": "bulk-transform"},
                       {"class": "A"}, {"kind": "local"}, {"task_type": "UNKNOWN"}):
            with self.subTest(fields=fields):
                rc, p = self.run_plan([self.node(**fields)])
                self.assertEqual(rc, 2)
                self.assertEqual(p["error"], "ValueError")

    def test_no_paid_unknown_exhausted_or_unverified_effort_fallback(self):
        cases = [
            (candidate(billing={"mode": "api", "verified": True}, upper_usd_per_attempt=0.01),
             "PAID_BUDGET_EXCEEDED"),
            (candidate(billing={"mode": "unknown", "verified": False}), "BILLING_UNVERIFIED"),
            (candidate(billing={"mode": "subscription", "verified": True,
                                "extra_usage_enabled": False, "account_ref": None}), "ACCOUNT_UNVERIFIED"),
            (candidate(quota={"used_pct": None, "observed_at": NOW}), "QUOTA_UNKNOWN"),
            (candidate("grok", surface="grok", quota={"used_pct": 100, "observed_at": NOW}),
             "QUOTA_EXHAUSTED"),
            (candidate(transport_efforts=["low"]), "EFFORT_UNSUPPORTED"),
        ]
        for c, reason in cases:
            with self.subTest(reason=reason):
                rc, p = self.run_plan([self.node()], [c])
                self.assertEqual(rc, 2, p)
                self.assertIn(reason, str(p))
                self.assertIsNone(p["steps"][0]["route"])

    def test_alias_requires_observed_resolution(self):
        c = candidate()
        registry = fixture_registry([c])
        registry["models"][0]["aliases"] = ["fixture-alias"]
        c["model"] = "fixture-alias"
        rc, p = self.run_plan([self.node()], [c], registry)
        self.assertEqual(rc, 2)
        self.assertIn("ALIAS_RESOLUTION_UNVERIFIED", str(p))
        c.update(resolved_model=registry["models"][0]["id"],
                 resolution_observed_at=NOW, resolution_evidence="offline observed alias")
        rc, p = self.run_plan([self.node()], [c], registry)
        self.assertEqual(rc, 0, p)
        self.assertEqual(p["steps"][0]["route"]["requested_model"], "fixture-alias")
        self.assertEqual(p["steps"][0]["route"]["resolved_model"], registry["models"][0]["id"])

    def test_whole_dag_keeps_review_and_existing_coordinator_boundaries(self):
        writer = self.node(writes=True)
        rc, p = self.run_plan([writer])
        self.assertEqual(rc, 2)
        self.assertIn("MISSING_REVIEW", str(p))
        reviewer = self.node("CODE_REVIEW", id="review", verify_of="task", depends_on=["task"])
        rc, p = self.run_plan([writer, reviewer], [candidate(), candidate("reviewer", surface="claude")])
        self.assertEqual(rc, 0, p)
        self.assertEqual(p["steps"][1]["depends_on"], ["task"])
        self.assertEqual(p["steps"][1]["verify_of"], "task")
        ancestry = p["ancestor_skills"]
        rc, resumed = self.run_plan([self.node(skills=["model-router"])], ancestor_skills=ancestry)
        self.assertEqual(rc, 2)
        self.assertIn("RECURSIVE_SKILL", str(resumed))
        for ancestor in ("vibe", "model-router", "simonk"):
            rc, p = self.run_plan([self.node(skills=[ancestor])], ancestor_skills=[ancestor])
            self.assertEqual(rc, 2)
            self.assertIn("RECURSIVE_SKILL", str(p))

    def test_read_only_review_rejection_reaches_cli(self):
        nodes = [self.node("CODE_REVIEW", writes=True),
                 self.node("CODE_REVIEW", id="check", verify_of="task", depends_on=["task"])]
        rc, p = self.run_plan(nodes, [candidate(), candidate("reviewer", surface="claude")])
        self.assertEqual(rc, 2)
        self.assertIn("read-only", p["message"])

    def test_old_model_and_launcher_contracts_are_not_advertised(self):
        text = SKILL.read_text(encoding="utf-8")
        cases = (SKILL.parent / "evals" / "cases.json").read_text(encoding="utf-8")
        for old in ("claude-sonnet-4-6", "claude-opus-4-7", "gpt-5.4", "deepseek-v3", '"dispatch_id"'):
            self.assertNotIn(old, text + cases)
        for required in ("orchestrate.py", "model-registry.json", "ancestor_skills", "plan_digest"):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
