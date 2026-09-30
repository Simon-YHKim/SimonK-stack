"""Source-only main safety: no home updates, plugin switch, or GitHub release."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
HOLD = ROOT / "distribution" / "main-source-only.hold"
HOOK = ROOT / ".claude" / "hooks" / "session-start.sh"
ATTRIBUTES = ROOT / ".gitattributes"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
STABLE_SHA = "313c04b8a1d9c9a623ae5571d70b5d10ef873ced"
BASH = (Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"
        if os.name == "nt" else Path(shutil.which("bash") or "/missing/bash"))


def posix(path: Path) -> str:
    path = path.absolute()
    if os.name == "nt":
        return "/" + path.drive[0].lower() + path.as_posix()[2:]
    return str(path)


class MainReleaseFenceTests(unittest.TestCase):
    @unittest.skipUnless(BASH.is_file(), "Git Bash/POSIX Bash is required")
    def test_held_session_start_does_not_touch_home_or_launch_tools(self):
        self.assertTrue(HOLD.is_file(), "Candidate must carry an explicit release hold")
        self.assertNotIn(b"\r", HOOK.read_bytes(), "Bash hook must be LF on this checkout")
        self.assertIn("/.claude/hooks/session-start.sh text eol=lf",
                      ATTRIBUTES.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="simonk main fence ") as raw:
            base = Path(raw)
            repo = base / "source with spaces"
            (repo / "distribution").mkdir(parents=True)
            shutil.copyfile(HOLD, repo / "distribution" / HOLD.name)
            fixture_hook = repo / ".claude" / "hooks" / "session-start.sh"
            fixture_hook.parent.mkdir(parents=True)
            shutil.copyfile(HOOK, fixture_hook)
            other_project = base / "other project"
            other_project.mkdir()
            home = base / "home"
            home.mkdir()
            empty_path = base / "empty-bin"
            empty_path.mkdir()
            env = {k: v for k, v in os.environ.items()
                   if k.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP"}}
            env.update(HOME=posix(home), USERPROFILE=str(home), PATH=str(empty_path),
                       BASH_ENV="", ENV="")
            for project_dir in (repo, other_project):
                with self.subTest(project=project_dir.name):
                    env["CLAUDE_PROJECT_DIR"] = posix(project_dir)
                    result = subprocess.run(
                        [str(BASH), "--noprofile", "--norc", posix(fixture_hook)],
                        cwd=base, env=env, text=True, encoding="utf-8",
                        capture_output=True, timeout=10,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn("source-only release hold", result.stdout)
                    self.assertEqual(list(home.iterdir()), [])

    def test_marketplace_legacy_plugin_is_pinned_to_previous_main(self):
        data = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        entry = next(item for item in data["plugins"]
                     if item["name"] == "simonk-stack")
        self.assertEqual(entry["source"], {
            "source": "github",
            "repo": "Simon-YHKim/SimonK-stack",
            "ref": "main",
            "sha": STABLE_SHA,
        })

    @unittest.skipUnless(BASH.is_file(), "Git Bash/POSIX Bash is required")
    def test_main_push_release_script_exits_before_gh_when_held(self):
        workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("branches: [main]", workflow)
        release_step = workflow.split("- name: Create tag + release if new", 1)[1]
        script = "\n".join(
            line[10:] for line in release_step.split("run: |", 1)[1].splitlines()[1:]
            if line.startswith("          ")
        )
        self.assertIn("gh release create", script)
        self.assertIn("distribution/main-source-only.hold", script)
        script = script.replace("${{ steps.ver.outputs.version }}", "9.9.9")
        script = script.replace("${{ github.sha }}", "0123456789abcdef")
        with tempfile.TemporaryDirectory(prefix="simonk release fence ") as raw:
            repo = Path(raw)
            (repo / "distribution").mkdir()
            shutil.copyfile(HOLD, repo / "distribution" / HOLD.name)
            empty_path = repo / "empty-bin"
            empty_path.mkdir()
            result = subprocess.run(
                [str(BASH), "--noprofile", "--norc", "-c", script],
                cwd=repo, env={"PATH": str(empty_path), "BASH_ENV": "", "ENV": ""},
                text=True, encoding="utf-8", capture_output=True, timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("source-only release hold", result.stdout)
            self.assertNotIn("release 9.9.9", result.stdout)


if __name__ == "__main__":
    unittest.main()
