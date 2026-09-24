"""Offline PowerShell -> real /vibe planner regressions; no provider generation."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VIBE = ROOT / "skills-src/vibe/scripts"
sys.path.insert(0, str(VIBE))
import orchestrate
from test_orchestrate import candidate, fixture_registry

PWSH = shutil.which("pwsh")
WRAPPER = ROOT / "scripts/simonk.ps1"
# The legacy implementation is tested safely: provider/cloud functions are
# sentinels, including the bootstrap function replaced after dot-sourcing.
HARNESS = r"""
param([string] $Wrapper, [string] $CasePath, [string] $ProjectDir)
$ErrorActionPreference = 'Stop'
$script:providerCalls = 0
$script:bootstrapCalls = 0
function global:claude { $script:providerCalls++ }
function global:codex { $script:providerCalls++ }
function global:grok { $script:providerCalls++ }
function global:agy { $script:providerCalls++ }
function global:gcloud { $script:bootstrapCalls++ }
function global:Start-Process { $script:providerCalls++ }
function global:python { $script:providerCalls++ }
$env:SIMONK_PROJECT_DIR = $ProjectDir
$sourceOutput = @(. $Wrapper)
$loadedCloudHelper = [bool](Get-Command simonk-gcloud-check -ErrorAction SilentlyContinue)
function global:Invoke-GcloudBootstrap { $script:bootstrapCalls++ }
$call = Get-Content -LiteralPath $CasePath -Raw | ConvertFrom-Json -AsHashtable
$before = (Get-Location).Path
$global:LASTEXITCODE = 0
$caught = $false
try { $output = @(& { simonK @call } 6>&1) }
catch { $caught = $true; $output = @('caught exception'); $global:LASTEXITCODE = 2 }
$rc = $global:LASTEXITCODE
[ordered]@{
    output = ($output | Out-String).Trim()
    code = $rc
    provider_calls = $script:providerCalls
    bootstrap_calls = $script:bootstrapCalls
    cwd_unchanged = ((Get-Location).Path -eq $before)
    caught = $caught
    source_output_count = $sourceOutput.Count
    loaded_cloud_helper = $loadedCloudHelper
} | ConvertTo-Json -Depth 8 -Compress
exit $rc
"""


@unittest.skipUnless(PWSH, "PowerShell 7 is required for executable entrypoint tests")
class SimonkEntrypointTests(unittest.TestCase):
    wrapper = WRAPPER

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "fixture's 경로; $"
        self.root.mkdir()
        self.harness = self.root / "harness.ps1"
        self.harness.write_text(HARNESS, encoding="utf-8")
        # Keep PYTHONPATH outside the literal-path fixture: ';' is a Windows
        # path-list separator, so quoting cannot preserve it inside PYTHONPATH.
        self.python_guard = Path(self.temp.name) / "python-guard"
        self.python_guard.mkdir()
        (self.python_guard / "sitecustomize.py").write_text(
            "import sys\n"
            "def deny(event,args):\n"
            "    if event.startswith(('subprocess.','socket.','os.system','os.exec','os.spawn','os.posix_spawn','os.kill')):\n"
            "        raise RuntimeError('OFFLINE_TEST_EFFECT_BLOCKED')\n"
            "sys.addaudithook(deny)\n", encoding="utf-8")
        self.now = datetime.now(timezone.utc).isoformat()
        self.candidates = [self.observed(candidate()), self.observed(candidate("review", surface="claude"))]
        self.request = {
            "run_id": "same-parent-run", "ancestor_skills": ["vibe", "simonk"],
            "budget": {"mode": "economy", "approved_usd": "0", "spent_usd": "0",
                       "external_reserved_usd": "0", "max_attempts": 1, "max_parallel": 1},
            "steps": [self.node()],
        }
        self.catalog = self.root / "skills"
        for name in ("explain", "simonk", "vibe", "vibe-bot"):
            folder = self.catalog / name
            folder.mkdir(parents=True)
            (folder / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: Offline fixture\n---\n", encoding="utf-8")

    def observed(self, item):
        item["observed_at"] = self.now
        item["quota"]["observed_at"] = self.now
        return item

    def node(self, **changes):
        return {"id": "inspect", "task_type": "CODE_FIX", "task": "Offline fixture",
                "skills": ["explain"], "writes": False, "depends_on": [], **changes}

    def run_wrapper(self, params=None, *, wrapper=None, env_changes=None):
        wrapper = wrapper or self.wrapper
        self.assertTrue(wrapper.is_file(), "The packaged PowerShell entry is missing")
        case = self.root / "call.json"
        case.write_text(json.dumps(params or {}), encoding="utf-8")
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", str(self.harness),
                                 str(wrapper), str(case), str(self.root)],
                                capture_output=True, text=True, encoding="utf-8", timeout=20,
                                cwd=self.root, env={**os.environ, "PYTHONUTF8": "1",
                                                    "PYTHONDONTWRITEBYTECODE": "1",
                                                    "PYTHONPATH": str(self.python_guard),
                                                    "PYTHONNOUSERSITE": "1", **(env_changes or {})})
        self.assertTrue(result.stdout.strip(), result.stderr)
        envelope = json.loads(result.stdout)
        self.assertEqual(envelope["provider_calls"], 0, envelope)
        self.assertEqual(envelope["bootstrap_calls"], 0, envelope)
        self.assertTrue(envelope["cwd_unchanged"], envelope)
        self.assertFalse(envelope["caught"], envelope)
        self.assertEqual(envelope["source_output_count"], 0, envelope)
        self.assertFalse(envelope["loaded_cloud_helper"], envelope)
        self.assertEqual(envelope["code"], result.returncode)
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after, "Planning must not dispatch or mutate input/project files")
        return result.returncode, json.loads(envelope["output"] or result.stderr.strip())

    def inputs(self):
        registry = fixture_registry(self.candidates)
        registry["checked_at"] = self.now
        values = {"request": self.request, "runtime": {"candidates": self.candidates,
                                                         "observed_at": self.now}, "registry": registry}
        for name, value in values.items():
            (self.root / (name + ".json")).write_text(json.dumps(value), encoding="utf-8")
        return {"RequestPath": str(self.root / "request.json"),
                "RuntimePath": str(self.root / "runtime.json"),
                "RegistryPath": str(self.root / "registry.json"), "Root": [str(self.catalog)]}

    def test_empty_and_legacy_text_fail_closed_without_echo_or_provider(self):
        for params in ({}, {"TaskArgs": ["private-fixture; $(throw 'not code')"]}):
            with self.subTest(params=params):
                rc, result = self.run_wrapper(params)
                self.assertEqual(rc, 2)
                self.assertEqual(result["error"], "SIMONK_PLAN_INPUT_REQUIRED")
                self.assertNotIn("private-fixture", json.dumps(result))

    def test_real_plan_preserves_parent_intent_budget_and_central_registry(self):
        params = self.inputs()
        rc, plan = self.run_wrapper(params)
        self.assertEqual(rc, 0, plan)
        expected = orchestrate.make_plan(self.request, orchestrate.discover_skills([self.catalog]),
                                        {"candidates": self.candidates, "observed_at": self.now},
                                        plan["planned_at"], json.loads((self.root / "registry.json").read_text()))
        self.assertEqual(plan, expected, "The shim must not create an independent routing/budget policy")
        self.assertEqual(plan["run_id"], "same-parent-run")
        self.assertEqual(plan["ancestor_skills"], ["vibe", "simonk"])
        self.assertEqual(plan["budget"]["approved_usd"], "0")
        self.assertIsNone(plan["steps"][0]["route"]["actual_usd"])
        self.assertIsNone(plan["steps"][0]["route"]["effective_effort"])

    def test_whole_dag_reviewer_dependency_survives(self):
        self.request["steps"] = [self.node(writes=True), self.node(
            id="review", task_type="CODE_REVIEW", depends_on=["inspect"], verify_of="inspect")]
        rc, plan = self.run_wrapper(self.inputs())
        self.assertEqual(rc, 0, plan)
        self.assertEqual(plan["steps"][1]["depends_on"], ["inspect"])
        self.assertEqual(plan["steps"][1]["verify_of"], "inspect")
        self.assertNotEqual(plan["steps"][0]["route"]["vendor"], plan["steps"][1]["route"]["vendor"])
        self.assertEqual(orchestrate.ready_steps(plan, [], plan["planned_at"]), ["inspect"])

    def test_ancestor_recursion_and_missing_reviewer_are_blocked(self):
        for node, reason in ((self.node(skills=["simonk"]), "RECURSIVE_SKILL"),
                             (self.node(writes=True), "MISSING_REVIEW")):
            with self.subTest(reason=reason):
                self.request["steps"] = [node]
                rc, plan = self.run_wrapper(self.inputs())
                self.assertEqual(rc, 2)
                self.assertIn(reason, str(plan))

    def test_paid_unknown_exhausted_and_unsupported_effort_fail_closed(self):
        cases = [(candidate(upper_usd_per_attempt="0.01", billing={"mode": "api", "verified": True,
                                                                  "account_ref": "fixture"}), "PAID_BUDGET_EXCEEDED"),
                 (candidate(billing={"mode": "unknown", "verified": False}), "BILLING_UNVERIFIED"),
                 (candidate("grok", surface="grok", quota={"used_pct": 100}), "QUOTA_EXHAUSTED"),
                 (candidate(transport_efforts=["low"]), "EFFORT_UNSUPPORTED")]
        for c, reason in cases:
            with self.subTest(reason=reason):
                self.candidates = [self.observed(c)]
                rc, plan = self.run_wrapper(self.inputs())
                self.assertEqual(rc, 2)
                self.assertIn(reason, str(plan))

    def test_missing_malformed_and_mixed_inputs_do_not_fallback(self):
        params = self.inputs()
        for changes in ({"RuntimePath": ""}, {"RequestPath": str(self.root / "absent.json")},
                        {"TaskArgs": ["do not silently ignore this task"]}):
            with self.subTest(changes=changes):
                rc, error = self.run_wrapper({**params, **changes})
                self.assertEqual(rc, 2)
                self.assertIn("error", error)
        (self.root / "request.json").write_text("{malformed", encoding="utf-8")
        rc, error = self.run_wrapper(params)
        self.assertEqual(rc, 2)
        self.assertIn("error", error)

    def test_missing_sibling_planner_never_uses_installed_copy(self):
        isolated = self.root / "isolated/scripts/simonk.ps1"
        isolated.parent.mkdir(parents=True)
        isolated.write_bytes(self.wrapper.read_bytes())
        rc, error = self.run_wrapper(self.inputs(), wrapper=isolated)
        self.assertEqual(rc, 2)
        self.assertEqual(error["error"], "SIMONK_PLANNER_UNAVAILABLE")

    def test_missing_python_does_not_use_a_shell_function_or_provider(self):
        rc, error = self.run_wrapper(self.inputs(), env_changes={"PATH": ""})
        self.assertEqual(rc, 2)
        self.assertEqual(error["error"], "SIMONK_PYTHON_UNAVAILABLE")

    def test_python_child_effect_barrier_is_active(self):
        for code in ("import os; os.system('cmd /c exit 0')", "import socket; socket.socket()"):
            result = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True,
                                    text=True, encoding="utf-8", timeout=10,
                                    env={**os.environ, "PYTHONPATH": str(self.python_guard),
                                         "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("OFFLINE_TEST_EFFECT_BLOCKED", result.stderr)

    def test_multiple_roots_and_literal_paths_reach_real_planner(self):
        self.candidates = [self.candidates[0]]
        params = self.inputs()
        params["Root"] = [str(self.root / "empty-catalog"), str(self.catalog)]
        rc, plan = self.run_wrapper(params)
        self.assertEqual(rc, 0, plan)
        self.assertEqual(plan["steps"][0]["route"]["requested_model"], "fixture-small")

    def test_host_supplied_split_roots_preserve_cross_plugin_binding(self):
        roots = []
        for index, name in enumerate(("core-leaf", "hub-leaf", "design-leaf", "market-leaf", "stack-leaf")):
            root = self.root / f"plugin-{index}/version-{index}/skills"
            leaf = root / name
            leaf.mkdir(parents=True)
            (leaf / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Split fixture\n---\n",
                                           encoding="utf-8")
            roots.append(root)
        self.request["steps"] = [self.node(skills=["design-leaf", "stack-leaf"])]
        params = {**self.inputs(), "Root": list(map(str, roots))}
        rc, plan = self.run_wrapper(params)
        self.assertEqual(rc, 0, plan)
        self.assertEqual([row["path"] for row in plan["discovery"]["roots"]], list(map(str, roots)))
        self.assertEqual([b["path"] for b in plan["steps"][0]["skill_bindings"]],
                         [str(roots[2] / "design-leaf/SKILL.md"), str(roots[4] / "stack-leaf/SKILL.md")])
        self.assertNotIn("bundle", plan["discovery"])

    def test_documented_batch_recipe_rejects_pre_body_binding_errors(self):
        # Do not use HARNESS: its catch deliberately normalizes errors to JSON.
        # A binding failure happens before the function can set LASTEXITCODE.
        skill = (ROOT / "skills-src/simonk/SKILL.md").read_text(encoding="utf-8")
        guard = "$ErrorActionPreference = 'Stop'"
        self.assertIn(guard, skill)
        for invocation in ("simonK -RequestPath", "simonK -R ambiguous", "simonK -RuntimePath"):
            with self.subTest(invocation=invocation):
                batch = self.root / "batch.ps1"
                batch.write_text("param([string] $Wrapper)\n" + guard + "\n. $Wrapper\n"
                                 "$global:LASTEXITCODE = 0\n" + invocation +
                                 "\nexit $LASTEXITCODE\n", encoding="utf-8")
                result = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File",
                                         str(batch), str(self.wrapper)], capture_output=True, text=True,
                                        encoding="utf-8", timeout=10)
                self.assertNotEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")


class PackagedSimonkEntrypointTests(SimonkEntrypointTests):
    wrapper = ROOT / "skills-src/simonk/scripts/simonk.ps1"

    def test_package_and_checkout_adapters_have_the_same_contract(self):
        def body(path):
            return "\n".join(line for line in path.read_text(encoding="utf-8").splitlines()
                             if not line.lstrip().startswith("#"))
        expected = body(WRAPPER).replace("../skills-src/vibe/scripts/orchestrate.py",
                                        "../../vibe/scripts/orchestrate.py")
        self.assertEqual(body(self.wrapper), expected)

    def test_packaged_entry_runs_without_the_source_checkout(self):
        skill_root = self.root / "independent/SimonKCore/skills"
        wrapper = skill_root / "simonk/scripts/simonk.ps1"
        wrapper.parent.mkdir(parents=True)
        self.assertTrue(self.wrapper.is_file(), "The packaged PowerShell entry is missing")
        shutil.copy2(self.wrapper, wrapper)
        for name in ("orchestrate.py", "model_registry.py", "routing.py"):
            target = skill_root / "vibe/scripts" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(VIBE / name, target)
        params = self.inputs()
        rc, plan = self.run_wrapper(params, wrapper=wrapper)
        self.assertEqual(rc, 0, plan)
        self.assertEqual(plan["run_id"], self.request["run_id"])
        self.assertFalse((skill_root.parent / "scripts/simonk.ps1").exists())


if __name__ == "__main__":
    unittest.main()
