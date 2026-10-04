"""Offline split-plugin discovery. No child processes, sockets or real homes."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import orchestrate as planner
from test_orchestrate import NOW, candidate, fixture_registry, step

OWNERS = ("SimonKCore", "SimonKAIHub", "SimonKDesign", "SimonKMarket", "SimonKStack")


class SuiteDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="vibe-suite-discovery-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.script_root = self.root / "plugins/SimonKCore/skills/vibe/scripts"
        self.receipt = {"schema_version": 2, "scope": "five-plugin-candidate-safety-v2",
                        "inputs": {"plugins": {o: {} for o in OWNERS}},
                        "owners": {}, "files": []}
        for owner, name in zip(OWNERS, ("vibe", "hub", "design", "market", "qa")):
            self.receipt["owners"][name] = owner
            self.put(f"plugins/{owner}/skills/{name}/SKILL.md",
                     f"---\nname: {name}\ndescription: Offline fixture\n---\n")
            self.put(f"plugins/{owner}/.claude-plugin/plugin.json",
                     json.dumps({"skills": [f"./skills/{name}/"]}))
        self.put("plugins/SimonKCore/skills/vibe/scripts/orchestrate.py", "# fixture binding\n")
        self.save()

    def put(self, member, text):
        path = self.root / member
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = text.encode("utf-8")
        path.write_bytes(raw)
        self.receipt["files"] = [r for r in self.receipt["files"] if r["path"] != member]
        self.receipt["files"].append({"path": member, "sha256": hashlib.sha256(raw).hexdigest(),
                                      "size": len(raw)})

    def save(self):
        (self.root / "bundle.json").write_text(json.dumps(self.receipt), encoding="utf-8")

    def call(self, *args):
        output = io.StringIO()
        with patch.object(planner, "SCRIPT_ROOT", self.script_root), \
                patch.object(Path, "home", side_effect=AssertionError("Home discovery is forbidden")), \
                contextlib.redirect_stdout(output):
            code = planner.main(list(args))
        return code, json.loads(output.getvalue())

    def test_default_catalog_uses_every_plugin_without_home_reads(self):
        code, result = self.call("catalog")
        self.assertEqual(code, 0, result)
        self.assertEqual(set(result), {"vibe", "hub", "design", "market", "qa"})
        self.assertEqual(result["qa"]["path"], str(self.root / "plugins/SimonKStack/skills/qa/SKILL.md"))

    def test_non_core_skill_plan_binds_candidate_path_and_hash(self):
        data = {"request": {"run_id": "split", "steps": [step(skills=["qa"])]},
                "runtime": {"candidates": [candidate()], "observed_at": NOW},
                "registry": fixture_registry([candidate()])}
        for name, value in data.items():
            (self.root / (name + ".json")).write_text(json.dumps(value), encoding="utf-8")
        code, result = self.call("plan", "--input", str(self.root / "request.json"),
                                 "--runtime", str(self.root / "runtime.json"),
                                 "--registry", str(self.root / "registry.json"), "--now", NOW)
        self.assertEqual(code, 0, result)
        self.assertEqual(result["status"], "ready")
        binding = result["steps"][0]["skill_bindings"][0]
        self.assertEqual(binding["path"], str(self.root / "plugins/SimonKStack/skills/qa/SKILL.md"))
        self.assertEqual(binding["sha256"], hashlib.sha256(Path(binding["path"]).read_bytes()).hexdigest())
        self.assertIn("bundle", result["discovery"])

    def test_missing_receipt_blocks_without_falling_back(self):
        (self.root / "bundle.json").unlink()
        self.assertEqual(self.call("catalog")[0], 2)

    def test_missing_plugin_blocks(self):
        (self.root / "plugins/SimonKStack/.claude-plugin/plugin.json").unlink()
        self.assertEqual(self.call("catalog")[0], 2)

    def test_changed_planner_blocks(self):
        (self.script_root / "orchestrate.py").write_text("changed", encoding="utf-8")
        self.assertEqual(self.call("catalog")[0], 2)

    def test_changed_skill_blocks(self):
        (self.root / "plugins/SimonKStack/skills/qa/SKILL.md").write_text(
            "---\nname: qa\ndescription: Drift\n---\n", encoding="utf-8")
        self.assertEqual(self.call("catalog")[0], 2)

    def test_changed_manifest_blocks(self):
        (self.root / "plugins/SimonKStack/.claude-plugin/plugin.json").write_text("{}", encoding="utf-8")
        self.assertEqual(self.call("catalog")[0], 2)

    def test_unlisted_skill_blocks_before_read(self):
        extra = self.root / "plugins/SimonKStack/skills/unlisted"
        extra.mkdir()
        (extra / "SKILL.md").write_text("do not read", encoding="utf-8")
        with patch.object(planner, "skill_inventory", side_effect=AssertionError("Must reject before scanning")):
            self.assertEqual(self.call("catalog")[0], 2)

    def test_owner_membership_mismatch_blocks(self):
        self.receipt["owners"]["qa"] = "SimonKCore"
        self.save()
        self.assertEqual(self.call("catalog")[0], 2)

    def test_duplicate_receipt_keys_block(self):
        raw = json.dumps(self.receipt)
        (self.root / "bundle.json").write_text('{"schema_version":2,' + raw[1:], encoding="utf-8")
        self.assertEqual(self.call("catalog")[0], 2)

    def test_invalid_receipt_types_scopes_and_members_block(self):
        original = json.loads(json.dumps(self.receipt))
        for changes in ({"schema_version": True}, {"schema_version": 3, "scope": "invalid"},
                        {"files": {}}, {"owners": []}, {"inputs": {"plugins": {}}},
                        {"owners": {"../escape": "SimonKCore"}}):
            with self.subTest(changes=changes):
                self.receipt = {**original, **changes}
                self.save()
                self.assertEqual(self.call("catalog")[0], 2)

    def test_duplicate_member_record_blocks(self):
        self.receipt["files"].append(self.receipt["files"][0])
        self.save()
        self.assertEqual(self.call("catalog")[0], 2)

    def test_missing_skill_blocks(self):
        (self.root / "plugins/SimonKStack/skills/qa/SKILL.md").unlink()
        self.assertEqual(self.call("catalog")[0], 2)

    def test_alias_is_rejected_before_inventory(self):
        # Resolve-only simulation also covers Windows junctions without creating
        # privileged OS links; real source/candidate checks cover ordinary paths.
        target = self.root / "plugins/SimonKStack/skills/qa/SKILL.md"
        original = Path.resolve
        def resolve(path, *args, **kwargs):
            return self.root / "outside" if path == target else original(path, *args, **kwargs)
        with patch.object(Path, "resolve", resolve), patch.object(
                planner, "skill_inventory", side_effect=AssertionError("Alias must not scan")):
            self.assertEqual(self.call("catalog")[0], 2)

    def test_declared_name_collision_blocks_even_with_matching_bytes(self):
        self.put("plugins/SimonKStack/skills/qa/SKILL.md",
                 "---\nname: vibe\ndescription: duplicate\n---\n")
        self.save()
        self.assertEqual(self.call("catalog")[0], 2)

    def test_nonfinite_receipt_blocks(self):
        self.receipt["unsupported"] = float("nan")
        self.save()
        self.assertEqual(self.call("catalog")[0], 2)

    def test_oversized_receipt_blocks(self):
        (self.root / "bundle.json").write_bytes(b" " * (8 * 1024 * 1024 + 1))
        self.assertEqual(self.call("catalog")[0], 2)

    def test_explicit_roots_override_candidate_and_never_read_receipt(self):
        (self.root / "bundle.json").write_text("not JSON", encoding="utf-8")
        code, result = self.call("catalog", "--root", str(self.root / "plugins/SimonKStack/skills"))
        self.assertEqual(code, 0, result)
        self.assertEqual(set(result), {"qa"})

    def test_audit_commands_still_require_explicit_scope(self):
        self.assertEqual(self.call("inventory")[0], 2)

    def test_excluded_metadata_is_not_read(self):
        excluded = self.root / "plugins/SimonKStack/skills/qa"
        with patch.object(planner, "skill_inventory", side_effect=AssertionError("Excluded scope must not scan")):
            self.assertEqual(self.call("catalog", "--exclude-root", str(excluded))[0], 2)

    def test_tilde_exclusion_precedes_all_content_reads(self):
        original = Path.expanduser
        def expand(path):
            return self.root if str(path) == "~" else original(path)
        with patch.object(Path, "expanduser", expand), patch.object(
                Path, "open", side_effect=AssertionError("Excluded bundle must not be read")):
            self.assertEqual(self.call("catalog", "--exclude-root", "~")[0], 2)

    def test_legacy_source_layout_retains_home_roots(self):
        fake_home = self.root / "empty-home"
        source = self.root / "source/skills-src/vibe/scripts"
        source.mkdir(parents=True)
        with patch.object(planner, "SCRIPT_ROOT", source), patch.object(Path, "home", return_value=fake_home):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = planner.main(["catalog"])
        self.assertEqual(code, 2)  # missing declared legacy roots, not a candidate error
        self.assertNotIn("error", json.loads(output.getvalue()))

    def detached_roots(self):
        roots = []
        for index, owner in enumerate(OWNERS):
            target = self.root / f"host-{index}/cache/version-{index}/skills"
            shutil.copytree(self.root / f"plugins/{owner}/skills", target)
            roots.append(target)
        self.script_root = roots[0] / "vibe/scripts"
        return roots

    @staticmethod
    def root_args(roots, flag="--root"):
        return [value for root in roots for value in (flag, str(root))]

    def test_host_supplied_detached_roots_need_no_home_or_bundle_inference(self):
        roots = self.detached_roots()
        with patch.object(planner, "candidate_inventory", side_effect=AssertionError("No inference")):
            code, result = self.call("inventory", *self.root_args(roots))
        self.assertEqual(code, 0, result)
        self.assertEqual(set(result["catalog"]), {"vibe", "hub", "design", "market", "qa"})
        self.assertEqual([row["path"] for row in result["roots"]], list(map(str, roots)))
        self.assertFalse(result["package_evaluated"])
        self.assertFalse(result["behavior_evaluated"])

    def test_detached_metadata_coverage_and_cross_owner_plan(self):
        roots = self.detached_roots()
        source = [self.root / f"plugins/{owner}/skills" for owner in OWNERS]
        code, coverage = self.call("coverage", *self.root_args(roots),
                                   *self.root_args(source, "--source-root"),
                                   *self.root_args(roots, "--plugin-root"))
        self.assertEqual(code, 0, coverage)
        self.assertEqual(coverage["status"], "metadata_matched")
        self.assertFalse(coverage["optimization_complete"])
        self.assertTrue(all(row["modes"]["balanced"]["status"] == "not_evaluated"
                            for row in coverage["rows"]))
        values = {"request": {"run_id": "detached", "steps": [step(skills=["qa", "design"])]},
                  "runtime": {"candidates": [candidate()], "observed_at": NOW},
                  "registry": fixture_registry([candidate()])}
        for name, value in values.items():
            (self.root / f"{name}.json").write_text(json.dumps(value), encoding="utf-8")
        code, plan = self.call("plan", *self.root_args(roots), "--input", str(self.root / "request.json"),
                              "--runtime", str(self.root / "runtime.json"), "--registry",
                              str(self.root / "registry.json"), "--now", NOW)
        self.assertEqual(code, 0, plan)
        bindings = plan["steps"][0]["skill_bindings"]
        self.assertEqual([b["path"] for b in bindings],
                         [str(roots[4] / "qa/SKILL.md"), str(roots[2] / "design/SKILL.md")])
        for binding in bindings:
            self.assertEqual(binding["sha256"], hashlib.sha256(Path(binding["path"]).read_bytes()).hexdigest())
        self.assertNotIn("bundle", plan["discovery"])

    def test_detached_missing_root_is_incomplete_not_home_fallback(self):
        roots = self.detached_roots()
        roots[-1] = self.root / "missing/skills"
        code, result = self.call("inventory", *self.root_args(roots))
        self.assertEqual(code, 2, result)
        self.assertEqual(result["status"], "incomplete")
        self.assertIn("ROOT_MISSING", [issue["code"] for issue in result["issues"]])
        self.assertNotIn("qa", result["catalog"])

    def test_detached_order_and_conflicts_are_observable(self):
        roots = self.detached_roots()
        shadow = roots[1] / "qa"
        shadow.mkdir()
        (shadow / "SKILL.md").write_text("---\nname: qa\ndescription: different package\n---\n",
                                        encoding="utf-8")
        code, first = self.call("inventory", *self.root_args(roots))
        self.assertEqual(code, 0, first)  # Complete scan is NOT a conflict-resolution verdict.
        self.assertEqual(first["catalog"]["qa"]["path"], str(shadow / "SKILL.md"))
        self.assertEqual(len(first["catalog"]["qa"]["alternatives"]), 1)
        code, second = self.call("inventory", *self.root_args(list(reversed(roots))))
        self.assertEqual(code, 0, second)
        self.assertEqual(second["catalog"]["qa"]["path"], str(roots[4] / "qa/SKILL.md"))
        self.assertNotEqual(first["inventory_digest"], second["inventory_digest"])


if __name__ == "__main__":
    def deny_effects(event, args):
        if event.startswith(("subprocess.", "socket.")) or event in {"os.system", "os.spawn", "os.exec"}:
            raise RuntimeError("Offline test forbids processes/network")
    sys.addaudithook(deny_effects)
    unittest.main()
