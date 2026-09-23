"""Real PowerShell installer against disposable clones/profiles; never user settings."""
import codecs
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts/install-simonk-profile.ps1"
PWSH = shutil.which("pwsh")
HARNESS = r"""
param([string] $Installer, [string] $CasePath)
$ErrorActionPreference = 'Stop'
# The old installer mutates user-scope environment. Never execute that body:
# its absent explicit-target/preview contract is the initial RED condition.
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($Installer, [ref]$tokens, [ref]$errors)
$names = @($ast.ParamBlock.Parameters | ForEach-Object { $_.Name.VariablePath.UserPath })
if ($errors.Count -or @('RepoRoot','ProfilePath','Apply' | Where-Object { $_ -notin $names }).Count) {
    '{"status":"legacy_blocked","error":"SAFE_INSTALL_CONTRACT_MISSING"}'
    exit 3
}
$script:sideEffects = 0
function global:claude { $script:sideEffects++ }
function global:codex { $script:sideEffects++ }
function global:grok { $script:sideEffects++ }
function global:agy { $script:sideEffects++ }
function global:gcloud { $script:sideEffects++ }
function global:Start-Process { $script:sideEffects++ }
$env:SIMONK_PROJECT_DIR = 'process-sentinel'
$before = [Environment]::GetEnvironmentVariable('SIMONK_PROJECT_DIR', 'User')
$call = Get-Content -LiteralPath $CasePath -Raw | ConvertFrom-Json -AsHashtable
$output = @(& $Installer @call)
$rc = $LASTEXITCODE
if ($script:sideEffects -or (Get-Command simonK -ErrorAction SilentlyContinue) -or
    $env:SIMONK_PROJECT_DIR -ne 'process-sentinel' -or
    [Environment]::GetEnvironmentVariable('SIMONK_PROJECT_DIR', 'User') -cne $before) {
    '{"status":"side_effect_detected"}'; exit 9
}
$output
exit $rc
"""


@unittest.skipUnless(PWSH, "PowerShell 7 is required")
class ProfileInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="profile-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "persistent's 경로; $"
        (self.repo / "scripts").mkdir(parents=True)
        (self.repo / "skills-src/vibe/scripts").mkdir(parents=True)
        shutil.copy2(ROOT / "scripts/simonk.ps1", self.repo / "scripts/simonk.ps1")
        for relative in ("scripts/orchestrate.py", "scripts/model_registry.py", "scripts/routing.py",
                         "references/model-registry.json"):
            destination = self.repo / "skills-src/vibe" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / "skills-src/vibe" / relative, destination)
        self.git("init", "-b", "main")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-m", "fixture")
        self.profile = self.root / "profiles" / "user's 경로.ps1"
        self.harness = self.root / "harness.ps1"
        self.harness.write_text(HARNESS, encoding="utf-8")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                              capture_output=True, text=True, encoding="utf-8")

    def run_installer(self, *, apply=False, repo=None, profile=None):
        case = self.root / "case.json"
        args = {"RepoRoot": str(repo or self.repo), "ProfilePath": str(profile or self.profile)}
        if apply:
            args["Apply"] = True
        case.write_text(json.dumps(args), encoding="utf-8")
        result = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", str(self.harness),
                                 str(INSTALLER), str(case)], capture_output=True, text=True,
                                encoding="utf-8", timeout=20, cwd=self.root,
                                env={**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertTrue(result.stdout.strip(), result.stderr)
        data = json.loads(result.stdout)
        self.assertNotEqual(data["status"], "side_effect_detected", data)
        return result.returncode, data

    def write_profile(self, raw):
        self.profile.parent.mkdir(exist_ok=True)
        self.profile.write_bytes(raw)

    def test_preview_creates_no_profile_or_directory(self):
        rc, result = self.run_installer()
        self.assertEqual(rc, 0, result)
        self.assertEqual(result["status"], "preview")
        self.assertTrue(result["changed"])
        self.assertFalse(self.profile.parent.exists())

    def test_new_install_is_loadable_and_idempotent(self):
        rc, result = self.run_installer(apply=True)
        self.assertEqual(rc, 0, result)
        before = self.profile.read_bytes()
        self.assertEqual(result["status"], "installed")
        rc, again = self.run_installer(apply=True)
        self.assertEqual((rc, again["status"]), (0, "unchanged"))
        self.assertEqual(self.profile.read_bytes(), before)
        load = self.root / "load.ps1"
        load.write_text("param([string] $Target)\n$ErrorActionPreference='Stop'\n"
                        ". $Target\nsimonK 'legacy text must not start a model'\nexit $LASTEXITCODE\n",
                        encoding="utf-8")
        loaded = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", str(load), str(self.profile)],
                                capture_output=True, text=True, encoding="utf-8", timeout=15)
        self.assertEqual(loaded.returncode, 2, loaded.stderr)
        self.assertEqual(json.loads(loaded.stderr)["error"], "SIMONK_PLAN_INPUT_REQUIRED")

    def test_exact_v1_migration_preserves_neighbors_and_backup(self):
        original = ("# 사용자 앞부분\r\n$kept=42\r\n\r\n"
                    "# <!-- simonk-profile-block:v1 -->\r\n"
                    "# Added by SimonK-stack/scripts/install-simonk-profile.ps1\r\n"
                    "if (Test-Path 'C:\\old\\scripts\\simonk.ps1') {\r\n"
                    "    . 'C:\\old\\scripts\\simonk.ps1'\r\n}\r\n\r\n# 사용자 뒷부분\r\n")
        raw = codecs.BOM_UTF8 + original.encode("utf-8")
        self.write_profile(raw)
        rc, result = self.run_installer(apply=True)
        self.assertEqual(rc, 0, result)
        self.assertEqual(Path(result["backup_path"]).read_bytes(), raw)
        after = self.profile.read_bytes()
        self.assertTrue(after.startswith(codecs.BOM_UTF8))
        text = after.decode("utf-8-sig")
        self.assertTrue(text.startswith("# 사용자 앞부분\r\n$kept=42\r\n\r\n"))
        self.assertTrue(text.endswith("\r\n\r\n# 사용자 뒷부분\r\n"))
        self.assertNotIn("C:\\old", text)
        self.assertEqual(text.count("simonk-profile-block:v2:begin"), 1)

    def test_utf16_and_no_final_newline_are_preserved_outside_block(self):
        raw = codecs.BOM_UTF16_LE + "# 사용자 설정".encode("utf-16-le")
        self.write_profile(raw)
        rc, result = self.run_installer(apply=True)
        self.assertEqual(rc, 0, result)
        self.assertEqual(Path(result["backup_path"]).read_bytes(), raw)
        self.assertTrue(self.profile.read_bytes().startswith(raw))

    def test_unrecognized_or_duplicate_owned_markers_fail_closed(self):
        for text in ("# <!-- simonk-profile-block:v1 -->\n# modified user code\n",
                     "# simonk-profile-block:v2:begin\n# missing end\n",
                     "# <!-- simonk-profile-block:v1 -->\n# <!-- simonk-profile-block:v1 -->\n"):
            with self.subTest(text=text):
                self.write_profile(text.encode())
                rc, result = self.run_installer(apply=True)
                self.assertEqual(rc, 2, result)
                self.assertEqual(self.profile.read_bytes(), text.encode())
                self.assertEqual(list(self.profile.parent.iterdir()), [self.profile])

    def test_different_wrapper_or_missing_planner_is_rejected(self):
        planner = self.repo / "skills-src/vibe/scripts/orchestrate.py"
        wrapper = self.repo / "scripts/simonk.ps1"
        planner.unlink()
        rc, result = self.run_installer(apply=True)
        self.assertEqual(rc, 2, result)
        shutil.copy2(ROOT / "skills-src/vibe/scripts/orchestrate.py", planner)
        wrapper.write_text("throw 'unsafe old entry point'", encoding="utf-8")
        rc, result = self.run_installer(apply=True)
        self.assertEqual(rc, 2, result)
        self.assertFalse(self.profile.exists())

    def test_missing_planner_dependency_is_rejected(self):
        (self.repo / "skills-src/vibe/scripts/model_registry.py").unlink()
        rc, result = self.run_installer(apply=True)
        self.assertEqual(rc, 2, result)
        self.assertFalse(self.profile.exists())

    def test_installed_profile_reaches_real_offline_planner(self):
        rc, result = self.run_installer(apply=True)
        self.assertEqual(rc, 0, result)
        catalog = self.root / "catalog" / "explain"
        catalog.mkdir(parents=True)
        (catalog / "SKILL.md").write_text("---\nname: explain\ndescription: Offline fixture\n---\n", encoding="utf-8")
        argv = ["python", "--version"]
        now = datetime.now(timezone.utc).isoformat()
        request = self.root / "request.json"
        runtime = self.root / "runtime.json"
        request.write_text(json.dumps({"run_id": "profile-fixture", "steps": [{"id": "inspect", "kind": "local",
            "task": "Read local version", "skills": ["explain"], "software": ["python"], "argv": argv,
            "needs": [], "depends_on": [], "writes": False}]}), encoding="utf-8")
        runtime.write_text(json.dumps({"candidates": [], "tools": ["python"], "observed_at": now,
            "tool_costs": [{"argv_sha256": hashlib.sha256(json.dumps(argv, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                            "verified": True, "evidence": ["fixture command"], "observed_at": now,
                            "upper_usd_per_attempt": 0}]}), encoding="utf-8")
        load = self.root / "plan.ps1"
        load.write_text("param([string]$Target,[string]$Request,[string]$Runtime,[string]$Catalog)\n"
                        "$ErrorActionPreference='Stop'\n. $Target\n"
                        "simonK -RequestPath $Request -RuntimePath $Runtime -Root $Catalog\nexit $LASTEXITCODE\n",
                        encoding="utf-8")
        observed = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", str(load), str(self.profile),
                                  str(request), str(runtime), str(catalog.parent)], capture_output=True,
                                 text=True, encoding="utf-8", timeout=20, env={**os.environ, "PYTHONUTF8": "1"})
        self.assertEqual(observed.returncode, 0, observed.stdout + observed.stderr)
        plan = json.loads(observed.stdout)
        self.assertEqual((plan["status"], plan["run_id"]), ("ready", "profile-fixture"))
        self.assertEqual(plan["steps"][0]["route"]["transport"], "tool")

    def test_linked_worktree_is_never_persisted(self):
        linked = self.root / "temporary-worktree"
        self.git("worktree", "add", "-b", "fixture-feature", str(linked))
        rc, result = self.run_installer(apply=True, repo=linked)
        self.assertEqual(rc, 2, result)
        self.assertFalse(self.profile.exists())

    def test_invalid_encoding_is_not_rewritten(self):
        original = b"# profile\n\xff\xfe\xfa"
        self.write_profile(original)
        rc, result = self.run_installer(apply=True)
        self.assertEqual(rc, 2, result)
        self.assertEqual(self.profile.read_bytes(), original)

    def test_preview_existing_profile_is_byte_identical(self):
        original = "# 사용자 설정\n$keep='safe'\n".encode()
        self.write_profile(original)
        rc, result = self.run_installer()
        self.assertEqual(rc, 0, result)
        self.assertEqual(self.profile.read_bytes(), original)
        self.assertEqual(list(self.profile.parent.iterdir()), [self.profile])

    def test_v2_target_update_replaces_one_block_and_preserves_backup(self):
        rc, result = self.run_installer(apply=True)
        self.assertEqual(rc, 0, result)
        original = self.profile.read_bytes()
        other = self.root / "another-persistent-clone"
        shutil.copytree(self.repo, other)
        rc, changed = self.run_installer(apply=True, repo=other)
        self.assertEqual(rc, 0, changed)
        self.assertEqual(Path(changed["backup_path"]).read_bytes(), original)
        text = self.profile.read_text(encoding="utf-8")
        self.assertIn(str(other), text)
        self.assertEqual(text.count("simonk-profile-block:v2:begin"), 1)
        self.assertNotIn(str(self.repo).replace("'", "''"), text)

    def test_changed_wrapper_is_not_loaded_by_existing_profile(self):
        rc, result = self.run_installer(apply=True)
        self.assertEqual(rc, 0, result)
        sentinel = self.root / "unexpected-side-effect"
        (self.repo / "scripts/simonk.ps1").write_text(
            "[IO.File]::WriteAllText('" + str(sentinel).replace("'", "''") + "','unexpected')", encoding="utf-8")
        load = self.root / "load-changed.ps1"
        load.write_text("param([string] $Target)\n. $Target\n"
                        "if (Get-Command simonK -ErrorAction SilentlyContinue) { exit 9 }\n", encoding="utf-8")
        observed = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", str(load), str(self.profile)],
                                  capture_output=True, text=True, encoding="utf-8", timeout=15)
        self.assertEqual(observed.returncode, 0, observed.stderr)
        self.assertFalse(sentinel.exists())

    def test_managed_looking_text_inside_user_context_is_not_replaced(self):
        v1 = ("# <!-- simonk-profile-block:v1 -->\n"
              "# Added by SimonK-stack/scripts/install-simonk-profile.ps1\n"
              "if (Test-Path 'C:\\old\\scripts\\simonk.ps1') {\n"
              "    . 'C:\\old\\scripts\\simonk.ps1'\n}")
        rc, result = self.run_installer(apply=True)
        self.assertEqual(rc, 0, result)
        v2 = self.profile.read_text(encoding="utf-8")
        for block in (v1, v2):
            for prefix, suffix in (("$example = @'\n", "\n'@\n"), ("<#\n", "\n#>\n"),
                                   ("function UserExample {\n", "\n}\n")):
                with self.subTest(version=block[:36], prefix=prefix):
                    original = (prefix + block + suffix).encode()
                    self.write_profile(original)
                    rc, result = self.run_installer(apply=True)
                    self.assertEqual(rc, 2, result)
                    self.assertEqual(self.profile.read_bytes(), original)

    def test_wrapper_is_locked_between_hash_and_load(self):
        rc, result = self.run_installer(apply=True)
        self.assertEqual(rc, 0, result)
        sentinel = self.root / "race-side-effect"
        loader = self.root / "race.ps1"
        loader.write_text(r"""
param([string]$Target,[string]$Sentinel)
$script:denied = $false
function Get-FileHash {
    [CmdletBinding()] param([string]$LiteralPath,[string]$Algorithm)
    $actual = Microsoft.PowerShell.Utility\Get-FileHash -LiteralPath $LiteralPath -Algorithm $Algorithm
    $payload = "[IO.File]::WriteAllText('" + $Sentinel.Replace("'", "''") + "','unexpected')"
    try { [IO.File]::WriteAllText($LiteralPath, $payload) } catch { $script:denied = $true }
    return $actual
}
. $Target
@{write_blocked=$script:denied; loaded=[bool](Get-Command simonK -ErrorAction SilentlyContinue)} | ConvertTo-Json -Compress
""", encoding="utf-8")
        observed = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", str(loader), str(self.profile),
                                  str(sentinel)], capture_output=True, text=True, encoding="utf-8", timeout=15)
        self.assertEqual(observed.returncode, 0, observed.stderr)
        self.assertEqual(json.loads(observed.stdout), {"write_blocked": True, "loaded": True})
        self.assertFalse(sentinel.exists())


if __name__ == "__main__":
    unittest.main()
