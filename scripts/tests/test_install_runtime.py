"""Offline tests for scripts/install_runtime.py (no bun build, no config writes, no environment writes)."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "install_runtime.py"
GIT = shutil.which("git")


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True).stdout.strip()


@unittest.skipUnless(GIT, "git not installed")
class InstallRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "src"
        self.src.mkdir()
        git(self.src, "init", "-q")
        git(self.src, "config", "user.email", "t@example.com")
        git(self.src, "config", "user.name", "t")
        git(self.src, "config", "core.autocrlf", "false")
        files = {
            "VERSION": "9.9.9.0\n",
            "LICENSE": "MIT\n",
            "SKILL.md": "---\nname: router\n---\n",
            "bin/tool": "#!/usr/bin/env bash\r\nset -euo pipefail\r\necho \"$HOME/.claude/skills/gstack/bin\"\r\n",
            "browse/src/cli.ts": "const p = join(homedir(), '.claude/skills/gstack');\n",
            "browse/SKILL.md": "---\nname: browse\n---\n",
            "browse/test/a.test.ts": "x\n",
            "qa/sections/browser-setup.md": "Run ~/.claude/skills/gstack/bin/tool\nLog to ~/.gstack/projects/x\n",
            "qa/SKILL.md": "---\nname: qa\n---\n",
            "bin/state": "#!/usr/bin/env bash\nD=\"${GSTACK_HOME:-$HOME/.gstack}\"\nE=~/.gstack-dev/evals\n"
                         "[ -d \".claude/skills/gstack\" ] && echo vendored\n",
            "browse/src/config.ts": "const h = process.env.GSTACK_HOME || path.join(os.homedir(), '.gstack');\n"
                                    "const b = path.join(os.homedir(), '.claude/skills/gstack/bin/x');\n"
                                    "const n = path.join(process.env.HOME || '/tmp', '.gstack', 'ngrok.env');\n"
                                    "const p = path.join(projectDir, '.gstack');\n",
            "review/checklist.md": "upstream checklist\n",
            "review/greptile.md": "upstream only\n",
            "review/SKILL.md": "---\nname: review\n---\n",
            "test/x.ts": "x\n",
            ".github/workflows/ci.yml": "x\n",
        }
        for rel, text in files.items():
            p = self.src / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(text.encode("utf-8"))
        git(self.src, "add", "-A")
        git(self.src, "commit", "-q", "-m", "init")
        self.commit = git(self.src, "rev-parse", "HEAD")
        self.pin = self.tmp / "RUNTIME.json"
        self.write_pin(self.commit[:8], "9.9.9.0")
        self.target = self.tmp / "home" / ".simonk" / "runtime"
        self.state = self.tmp / "home" / ".simonk" / "state"
        self.skills = self.tmp / "skills-src"
        for rel, text in {"VENDORED.md": "# list\n\n- `pr-review`\n- `ios-only` - no upstream folder\n- `qa`\n",
                          "pr-review/SKILL.md": "---\nname: pr-review\n---\nRead ~/.simonk/runtime/review/checklist.md\n",
                          "pr-review/checklist.md": "SimonK checklist\n",
                          "pr-review/evals/cases.json": "{}\n",
                          "ios-only/SKILL.md": "---\nname: ios-only\n---\n",
                          "not-listed/SKILL.md": "---\nname: not-listed\n---\n"}.items():
            p = self.skills / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_pin(self, commit, version, overlay=True):
        pin = {"upstream_commit": commit, "upstream_version": version,
               "state_env": ["GSTACK_HOME"], "config": {"update_check": "false"}}
        if overlay:
            pin["skill_overlay"] = {"upstream_names": {"pr-review": "review"}}
        self.pin.write_text(json.dumps(pin), encoding="utf-8")

    def run_installer(self, *extra):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), "--source", str(self.src), "--target", str(self.target),
                               "--state", str(self.state), "--pin", str(self.pin),
                               "--skills-src", str(self.skills), *extra],
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def apply(self, *extra):
        return self.run_installer("--apply", "--skip-build", "--skip-config", "--skip-env", *extra)

    def test_preview_writes_nothing(self):
        r = self.run_installer()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Preview only", r.stdout)
        self.assertFalse(self.target.exists())
        self.assertFalse(self.state.exists())

    def test_rejects_a_source_that_is_not_the_pinned_commit(self):
        self.write_pin("deadbeef", "9.9.9.0")
        r = self.apply()
        self.assertEqual(r.returncode, 2)
        self.assertIn("not the pinned commit", r.stderr)

    def test_rejects_a_pinned_version_mismatch(self):
        self.write_pin(self.commit[:8], "1.0.0.0")
        r = self.apply()
        self.assertEqual(r.returncode, 2)
        self.assertIn("does not match", r.stderr)

    def test_rejects_local_modifications(self):
        (self.src / "bin" / "tool").write_text("tampered\n", encoding="utf-8")
        r = self.apply()
        self.assertEqual(r.returncode, 2)
        self.assertIn("local modifications", r.stderr)
        self.assertFalse(self.target.exists())

    def test_apply_exports_the_pinned_tree_and_rewrites_the_install_path(self):
        r = self.apply()
        self.assertEqual(r.returncode, 0, r.stderr)
        tool = (self.target / "bin" / "tool").read_bytes()
        self.assertIn(b".simonk/runtime/bin", tool)
        self.assertNotIn(b"\r\n", tool, "text files are stored with LF")
        self.assertIn("join(homedir(), '.simonk/runtime')",
                      (self.target / "browse" / "src" / "cli.ts").read_text(encoding="utf-8"))
        self.assertIn(".simonk/runtime/bin", (self.target / "qa" / "sections" / "browser-setup.md").read_text(encoding="utf-8"))
        for gone in ("SKILL.md", "browse/SKILL.md", "qa/SKILL.md", "test/x.ts", ".github", "browse/test/a.test.ts"):
            self.assertFalse((self.target / gone).exists(), gone)
        self.assertTrue((self.target / "LICENSE").exists())
        self.assertTrue(self.state.is_dir())
        self.assertIn(b".claude/skills/gstack", (self.src / "bin" / "tool").read_bytes(), "the source is never edited")

    def test_home_paths_move_and_project_paths_stay(self):
        self.assertEqual(self.apply().returncode, 0)
        doc = (self.target / "qa" / "sections" / "browser-setup.md").read_text(encoding="utf-8")
        self.assertIn("~/.simonk/state/projects/x", doc)
        self.assertNotIn("~/.gstack", doc)
        script = (self.target / "bin" / "state").read_text(encoding="utf-8")
        self.assertIn("${GSTACK_HOME:-$HOME/.simonk/state}", script, "the default works without the env vars")
        self.assertIn("~/.gstack-dev/evals", script, "a different folder name is not the state folder")
        self.assertIn('[ -d ".claude/skills/gstack" ]', script, "legacy vendored copies are still recognized")
        ts = (self.target / "browse" / "src" / "config.ts").read_text(encoding="utf-8")
        self.assertIn("path.join(os.homedir(), '.simonk/state')", ts)
        self.assertIn("path.join(os.homedir(), '.simonk/runtime/bin/x')", ts)
        self.assertIn("path.join(process.env.HOME || '/tmp', '.simonk/state', 'ngrok.env')", ts)
        self.assertIn("path.join(projectDir, '.gstack')", ts, "per-project state stays in the project")

    def test_simonk_skills_are_laid_over_the_upstream_folders(self):
        r = self.apply()
        self.assertEqual(r.returncode, 0, r.stderr)
        review = self.target / "review"
        self.assertEqual((review / "checklist.md").read_text(encoding="utf-8"), "SimonK checklist\n")
        self.assertIn("name: pr-review", (review / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual((review / "greptile.md").read_text(encoding="utf-8"), "upstream only\n")
        self.assertFalse((review / "evals").exists())
        self.assertFalse((self.target / "ios-only").exists(), "no upstream folder, nothing to replace")
        self.assertFalse((self.target / "not-listed").exists())
        self.assertFalse((self.target / "qa" / "SKILL.md").exists(), "listed but no SimonK copy here")

    def test_pin_without_overlay_keeps_upstream_text(self):
        self.write_pin(self.commit[:8], "9.9.9.0", overlay=False)
        self.assertEqual(self.apply().returncode, 0)
        self.assertEqual((self.target / "review" / "checklist.md").read_text(encoding="utf-8"), "upstream checklist\n")

    def test_missing_skill_list_stops_the_install(self):
        (self.skills / "VENDORED.md").unlink()
        r = self.apply()
        self.assertEqual(r.returncode, 2)
        self.assertIn("skill list not found", r.stderr)
        self.assertFalse(self.target.exists())

    def test_existing_target_needs_force(self):
        self.target.mkdir(parents=True)
        r = self.apply()
        self.assertEqual(r.returncode, 2)
        self.assertIn("--force", r.stderr)

    def test_force_replaces_the_runtime_without_leftovers(self):
        self.assertEqual(self.apply().returncode, 0)
        (self.target / "bin" / "retired-tool").write_text("old\n", encoding="utf-8")
        r = self.apply("--force")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.target / "bin" / "retired-tool").exists())
        self.assertTrue((self.target / "bin" / "tool").exists())
        leftovers = [p.name for p in self.target.parent.iterdir() if p.name.startswith(".runtime.")]
        self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
