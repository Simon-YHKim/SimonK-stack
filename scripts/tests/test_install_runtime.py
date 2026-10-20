"""Offline tests for scripts/windows/install-runtime.ps1 (no bun build, no user environment writes)."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "windows" / "install-runtime.ps1"
PIN = json.loads((REPO / "runtime" / "RUNTIME.json").read_text(encoding="utf-8"))
PWSH = shutil.which("pwsh")


def make_source(root: Path, version: str) -> Path:
    src = root / "src"
    (src / "bin").mkdir(parents=True)
    (src / "bin" / "tool").write_text('#!/usr/bin/env bash\necho "$HOME/.claude/skills/gstack/bin"\n', encoding="utf-8")
    (src / "browse" / "src").mkdir(parents=True)
    (src / "browse" / "src" / "cli.ts").write_text("const p = '.claude/skills/gstack';\n", encoding="utf-8")
    (src / "browse" / "SKILL.md").write_text("---\nname: browse\n---\n", encoding="utf-8")
    (src / "ship").mkdir()
    (src / "ship" / "SKILL.md").write_text("---\nname: ship\n---\n", encoding="utf-8")
    (src / "test").mkdir()
    (src / "test" / "x.ts").write_text("x", encoding="utf-8")
    (src / "VERSION").write_text(version + "\n", encoding="utf-8")
    (src / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (src / "SKILL.md").write_text("---\nname: gstack\n---\n", encoding="utf-8")
    return src


def run(*args):
    # Error text may come back in the console code page, so decode leniently.
    return subprocess.run([PWSH, "-NoProfile", "-File", str(SCRIPT), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


@unittest.skipUnless(PWSH, "pwsh not installed")
class InstallRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_version_mismatch_fails(self):
        src = make_source(self.tmp, "0.0.0")
        r = run("-Source", str(src), "-Target", str(self.tmp / "t"), "-StateRoot", str(self.tmp / "s"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("does not match", r.stdout + r.stderr)

    def test_preview_writes_nothing(self):
        src = make_source(self.tmp, PIN["upstream_version"])
        target = self.tmp / "t"
        r = run("-Source", str(src), "-Target", str(target), "-StateRoot", str(self.tmp / "s"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Preview only", r.stdout)
        self.assertFalse(target.exists())

    def test_apply_copies_runtime_and_patches_path(self):
        src = make_source(self.tmp, PIN["upstream_version"])
        target = self.tmp / "t"
        r = run("-Source", str(src), "-Target", str(target), "-StateRoot", str(self.tmp / "s"), "-Apply", "-SkipBuild", "-SkipEnv")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(".simonk/runtime/bin", (target / "bin" / "tool").read_text(encoding="utf-8"))
        self.assertIn(".simonk/runtime", (target / "browse" / "src" / "cli.ts").read_text(encoding="utf-8"))
        self.assertFalse((target / "ship").exists(), "skill folders stay out of the runtime")
        self.assertFalse((target / "browse" / "SKILL.md").exists(), "browse keeps its tools but not its skill file")
        self.assertFalse((target / "test").exists())
        self.assertFalse((target / "SKILL.md").exists())
        self.assertTrue((target / "LICENSE").exists())
        self.assertTrue((self.tmp / "s").is_dir())
        # the source is never modified
        self.assertIn(".claude/skills/gstack", (src / "bin" / "tool").read_text(encoding="utf-8"))

    def test_apply_refuses_existing_target_without_force(self):
        src = make_source(self.tmp, PIN["upstream_version"])
        target = self.tmp / "t"
        target.mkdir()
        r = run("-Source", str(src), "-Target", str(target), "-StateRoot", str(self.tmp / "s"), "-Apply", "-SkipBuild", "-SkipEnv")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("-Force", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
