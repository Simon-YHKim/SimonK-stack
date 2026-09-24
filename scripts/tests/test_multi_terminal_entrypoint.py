"""Real PowerShell wave entries against disposable state; no native execution."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills-src/multi-terminal-dispatcher"
sys.path.insert(0, str(SKILL / "scripts/tests"))
import test_dispatch_wave as wave_fixture

PWSH = shutil.which("pwsh")
WRAPPER = ROOT / "scripts/multi-terminal-launch.ps1"


@unittest.skipUnless(PWSH, "PowerShell 7 is required for executable entrypoint tests")
class RootWaveEntrypointTests(unittest.TestCase):
    wrapper = WRAPPER

    def setUp(self):
        # Reuse only the reviewed fixture builder. No native shell test body is
        # invoked; these tests provide their own guarded child environment.
        self.fixture = wave_fixture.WaveTests("test_actual_powershell_preview_and_rejected_dispatch")
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.root = self.fixture.root
        self.literal = self.root / "caller's 경로; $"
        self.literal.mkdir()
        self.plan = self.literal / "plan's input.json"
        self.plan.write_text(json.dumps(self.fixture.plan), encoding="utf-8")
        # PYTHONPATH is a path list on Windows; keep its guard outside ';'.
        self.guard = self.root / "python-guard"
        self.guard.mkdir()
        (self.guard / "sitecustomize.py").write_text(
            "import sys\n"
            "def deny(event,args):\n"
            "    if event.startswith(('subprocess.','socket.','os.system','os.exec','os.spawn','os.posix_spawn','os.kill')):\n"
            "        raise RuntimeError('OFFLINE_WAVE_EFFECT_BLOCKED')\n"
            "sys.addaudithook(deny)\n", encoding="utf-8")
        self.env = {**os.environ, "PYTHONPATH": str(self.guard), "PYTHONNOUSERSITE": "1",
                    "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}

    def snapshot(self):
        return {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.rglob("*") if p.is_file()}

    def invoke(self, *args, wrapper=None, env_changes=None, inputs=True, json_output=True, driver=None):
        wrapper = wrapper or self.wrapper
        self.assertTrue(wrapper.is_file(), "The packaged PowerShell wave entry is missing")
        before = self.snapshot()
        inputs = ["-PlanPath", str(self.plan), "-DbPath", str(self.fixture.db)] if inputs else []
        entry = [str(driver), str(wrapper)] if driver else [str(wrapper)]
        result = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", *entry,
                                 *inputs, *args], cwd=self.literal, env={**self.env, **(env_changes or {})},
                                capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(self.snapshot(), before, "Preview/rejected sends must not mutate fixture state")
        self.assertNotIn("OFFLINE_WAVE_EFFECT_BLOCKED", result.stderr + result.stdout,
                         "The entry attempted a forbidden child/network effect")
        if json_output:
            self.assertTrue(result.stdout.strip(), result.stderr)
            return result.returncode, json.loads(result.stdout)
        return result.returncode, result.stdout + result.stderr

    def test_default_explicit_and_dry_run_preview_preserve_state(self):
        for args in ((), ("-Action", "preview"), ("-DryRun",)):
            with self.subTest(args=args):
                rc, value = self.invoke(*args)
                self.assertEqual(rc, 0, value)
                self.assertEqual(value["status"], "preview")
                self.assertEqual(value["ready"], ["one", "two"])
                self.assertEqual(value["selected"], ["one", "two"])
                self.assertEqual(value["new_dispatches"], [])

    def test_reconcile_empty_state_and_dispatch_without_certificate_never_send(self):
        for action, status, expected_rc in (("reconcile", "waiting", 0), ("dispatch", "blocked", 2)):
            with self.subTest(action=action):
                rc, value = self.invoke("-Action", action)
                self.assertEqual((rc, value["status"]), (expected_rc, status))
                self.assertEqual(value["new_dispatches"], [])
                self.assertEqual(self.fixture.store.snapshot()["attempts"], [])

    def test_literal_node_and_certificate_path_forward_to_helper(self):
        certificate = self.literal / "empty's certificates.json"
        certificate.write_text("{}", encoding="utf-8")
        rc, value = self.invoke("-Node", "two", "-CertificatesPath", str(certificate))
        self.assertEqual(rc, 0, value)
        self.assertEqual(value["selected"], ["two"])
        rc, value = self.invoke("-Action", "dispatch", "-Node", "two", "-CertificatesPath", str(certificate))
        self.assertEqual((rc, value["status"]), (2, "blocked"))
        self.assertEqual(value["new_dispatches"], [])

    def test_empty_legacy_and_conflicting_dry_run_fail_closed(self):
        for args in (("-ConfigPath", ""), ("-CostThreshold", "0"),
                     ("-DryRun", "-Action", "dispatch"), ("-Node", "")):
            with self.subTest(args=args):
                rc, value = self.invoke(*args)
                self.assertEqual((rc, value["error"]), (2, "WAVE_INPUT_REQUIRED"))
        rc, value = self.invoke(inputs=False)
        self.assertEqual((rc, value["error"]), (2, "WAVE_INPUT_REQUIRED"))

    def test_typed_node_array_is_preserved(self):
        driver = self.literal / "typed-driver.ps1"
        driver.write_text("param([string]$Wrapper,[string]$PlanPath,[string]$DbPath)\n"
                          "$ErrorActionPreference='Stop'\n"
                          "& $Wrapper -PlanPath $PlanPath -DbPath $DbPath -Node @('two','one')\n"
                          "exit $LASTEXITCODE\n", encoding="utf-8")
        rc, value = self.invoke(driver=driver)
        self.assertEqual(rc, 0, value)
        self.assertEqual(value["selected"], ["two", "one"])

    def test_false_switch_and_explicit_empty_arrays_are_preserved(self):
        cases = (("-DryRun:$false", 0, None),
                 ("-DryRun:$false -Action dispatch", 2, "WAVE_BLOCKED"),
                 ("-Node @()", 2, "WAVE_INPUT_REQUIRED"),
                 ("-Tasks @()", 2, "WAVE_INPUT_REQUIRED"))
        for flags, expected_rc, error in cases:
            with self.subTest(flags=flags):
                driver = self.literal / "typed-flags.ps1"
                driver.write_text("param([string]$Wrapper,[string]$PlanPath,[string]$DbPath)\n"
                                  "$ErrorActionPreference='Stop'\n"
                                  "& $Wrapper -PlanPath $PlanPath -DbPath $DbPath " + flags +
                                  "\nexit $LASTEXITCODE\n", encoding="utf-8")
                rc, value = self.invoke(driver=driver)
                self.assertEqual(rc, expected_rc, value)
                self.assertEqual(value.get("error"), error)

    def test_missing_helper_or_python_never_falls_back(self):
        isolated = self.literal / "isolated.ps1"
        self.assertTrue(self.wrapper.is_file(), "The packaged PowerShell wave entry is missing")
        shutil.copy2(self.wrapper, isolated)
        for options in ({"wrapper": isolated}, {"env_changes": {"PATH": ""}}):
            with self.subTest(options=options):
                rc, value = self.invoke(**options)
                self.assertEqual((rc, value["error"]), (2, "WAVE_HELPER_UNAVAILABLE"))

    def test_invalid_binding_is_nonzero_and_does_not_run(self):
        rc, output = self.invoke("-Action", "not-an-action", json_output=False)
        self.assertNotEqual(rc, 0, output)

    def test_python_effect_barrier_is_active(self):
        for code in ("import os; os.system('cmd /c exit 0')", "import socket; socket.socket()"):
            result = subprocess.run([sys.executable, "-B", "-c", code], env=self.env,
                                    capture_output=True, text=True, encoding="utf-8", timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("OFFLINE_WAVE_EFFECT_BLOCKED", result.stderr)


class PackagedWaveEntrypointTests(RootWaveEntrypointTests):
    wrapper = SKILL / "scripts/multi-terminal-launch.ps1"

    def test_package_and_checkout_parameter_contracts_match(self):
        self.assertTrue(self.wrapper.is_file(), "The packaged PowerShell wave entry is missing")
        def parameters(path):
            text = path.read_text(encoding="utf-8")
            return text[text.index("[CmdletBinding"):text.index("$ErrorActionPreference")]
        self.assertEqual(parameters(self.wrapper), parameters(WRAPPER))
        root = WRAPPER.read_text(encoding="utf-8")
        self.assertIn("& $canonical @PSBoundParameters", root)
        self.assertNotIn("dispatch_wave.py", root)
        self.assertNotIn("Get-Command python", root)

    def test_independent_package_has_no_source_checkout_dependency(self):
        self.assertTrue(self.wrapper.is_file(), "The packaged PowerShell wave entry is missing")
        skills = self.literal / "independent/SimonKCore/skills"
        target = skills / "multi-terminal-dispatcher/scripts"
        target.mkdir(parents=True)
        for name in ("multi-terminal-launch.ps1", "dispatch_wave.py"):
            shutil.copy2(SKILL / "scripts" / name, target / name)
        core = skills / "vibe/scripts"
        core.mkdir(parents=True)
        for name in ("execute_orca.py", "orchestrate.py", "model_registry.py", "routing.py", "run_state.py", "ledger.py"):
            shutil.copy2(ROOT / "skills-src/vibe/scripts" / name, core / name)
        rc, value = self.invoke(wrapper=target / "multi-terminal-launch.ps1")
        self.assertEqual((rc, value["status"]), (0, "preview"))
        self.assertEqual(value["ready"], ["one", "two"])
        self.assertFalse((skills.parent / "scripts/multi-terminal-launch.ps1").exists())

    def test_root_delegates_stdout_and_arbitrary_child_exit_code(self):
        scripts = self.literal / "facade-fixture/scripts"
        scripts.mkdir(parents=True)
        wrapper = scripts / "multi-terminal-launch.ps1"
        shutil.copy2(WRAPPER, wrapper)
        target = scripts.parent / "skills-src/multi-terminal-dispatcher/scripts/multi-terminal-launch.ps1"
        target.parent.mkdir(parents=True)
        target.write_text("[Console]::Out.WriteLine('{\"status\":\"fixture-only\"}')\nexit 17\n", encoding="utf-8")
        rc, value = self.invoke(wrapper=wrapper)
        self.assertEqual((rc, value), (17, {"status": "fixture-only"}))


if __name__ == "__main__":
    unittest.main()
