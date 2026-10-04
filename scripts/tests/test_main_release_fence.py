"""Source-only main safety: no home updates, plugin switch, or GitHub release.

D-82 follow-up 1 moved only dist publishing to its own gate
(distribution/dist-publish.allow, tested in test_dist_release.py); the hold
below still fences SessionStart and release.yml. Since D-82's last step the
catalog serves the five dist plugins instead of the legacy pinned root plugin.
"""

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

    def test_marketplace_serves_the_five_dist_plugins(self):
        # D-82 last step: the catalog switched from the legacy root plugin (pinned at
        # 313c04b8) to the five dist plugins, after the HTTPS install, migration, update,
        # rollback and late-build checks (hub D-84). No sha and no version: each dist
        # publish reaches users through the plugin's own release version.
        data = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        self.assertEqual(data["name"], "simonk-stack")
        self.assertNotIn("version", data)
        expected = {"simonk-core": "SimonKCore", "simonk-stack": "SimonKStack",
                    "simonk-aihub": "SimonKAIHub", "simonk-design": "SimonKDesign",
                    "simonk-market": "SimonKMarket"}
        self.assertEqual([item["name"] for item in data["plugins"]], list(expected))
        for item in data["plugins"]:
            with self.subTest(plugin=item["name"]):
                self.assertNotIn("version", item)
                self.assertEqual(item["source"], {
                    "source": "git-subdir",
                    "url": "https://github.com/Simon-YHKim/SimonK-stack.git",
                    "path": f"plugins/{expected[item['name']]}",
                    "ref": "dist",
                })
        self.assertNotIn(STABLE_SHA, MARKETPLACE.read_text(encoding="utf-8"))

    def test_hold_fences_session_start_and_release_but_not_dist_publish(self):
        self.assertTrue(HOLD.is_file(), "Candidate must carry an explicit release hold")
        readers = sorted(
            path.relative_to(ROOT).as_posix()
            for path in [*(ROOT / ".github" / "workflows").glob("*.yml"),
                         *(ROOT / ".claude" / "hooks").iterdir()]
            if path.is_file() and HOLD.name in path.read_text(encoding="utf-8"))
        self.assertEqual(readers, [".claude/hooks/session-start.sh",
                                   ".github/workflows/release.yml"])

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
