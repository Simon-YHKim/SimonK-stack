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
            "browse/src/cli.ts": "const p = '.claude/skills/gstack';\n",
            "browse/SKILL.md": "---\nname: browse\n---\n",
            "browse/test/a.test.ts": "x\n",
            "qa/sections/browser-setup.md": "Run ~/.claude/skills/gstack/bin/tool\n",
            "qa/SKILL.md": "---\nname: qa\n---\n",
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

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_pin(self, commit, version):
        self.pin.write_text(json.dumps({"upstream_commit": commit, "upstream_version": version,
                                        "state_env": ["GSTACK_HOME"], "config": {"update_check": "false"}}),
                            encoding="utf-8")

    def run_installer(self, *extra):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), "--source", str(self.src), "--target", str(self.target),
                               "--state", str(self.state), "--pin", str(self.pin), *extra],
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
        self.assertIn(".simonk/runtime", (self.target / "browse" / "src" / "cli.ts").read_text(encoding="utf-8"))
        self.assertIn(".simonk/runtime/bin", (self.target / "qa" / "sections" / "browser-setup.md").read_text(encoding="utf-8"))
        for gone in ("SKILL.md", "browse/SKILL.md", "qa/SKILL.md", "test/x.ts", ".github", "browse/test/a.test.ts"):
            self.assertFalse((self.target / gone).exists(), gone)
        self.assertTrue((self.target / "LICENSE").exists())
        self.assertTrue(self.state.is_dir())
        self.assertIn(b".claude/skills/gstack", (self.src / "bin" / "tool").read_bytes(), "the source is never edited")

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
