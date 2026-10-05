"""Main stays safe without a hold: no home writes, no GitHub release, dist catalog.

Hub decision D-87 (2026-10-05) retired the D-33 source-only hold together with
what it fenced: the SessionStart bootstrap is now a read-only notice and the
main-push release workflow is gone. These tests pin that state so neither can
come back unnoticed. Publishing to the dist branch keeps its own gate
(distribution/dist-publish.allow, tested in test_dist_release.py).
"""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
HOLD = ROOT / "distribution" / "main-source-only.hold"
HOOK = ROOT / ".claude" / "hooks" / "session-start.sh"
ATTRIBUTES = ROOT / ".gitattributes"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
WORKFLOWS = ROOT / ".github" / "workflows"
STABLE_SHA = "313c04b8a1d9c9a623ae5571d70b5d10ef873ced"
BASH = (Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"
        if os.name == "nt" else Path(shutil.which("bash") or "/missing/bash"))
# Commands a SessionStart hook must not run: anything that writes, deletes,
# fetches or installs. Matched on non-comment lines only.
FORBIDDEN_HOOK_COMMANDS = re.compile(
    r"(^|[\s;|&(])(git|rm|cp|mv|mkdir|ln|curl|wget|tee|touch|bun|npm|pip|chmod|sed\s+-i)\b"
    r"|>>?\s*[~$\"/]")
RELEASE_MAKERS = re.compile(
    r"gh\s+release\s+create|actions/create-release|softprops/action-gh-release|ncipollo/release-action")


def posix(path: Path) -> str:
    path = path.absolute()
    if os.name == "nt":
        return "/" + path.drive[0].lower() + path.as_posix()[2:]
    return str(path)


def code_lines(text: str):
    return [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


class MainReleaseFenceTests(unittest.TestCase):
    def test_session_start_hook_has_no_writing_or_fetching_command(self):
        self.assertNotIn(b"\r", HOOK.read_bytes(), "Bash hook must be LF on this checkout")
        self.assertIn("/.claude/hooks/session-start.sh text eol=lf",
                      ATTRIBUTES.read_text(encoding="utf-8"))
        for line in code_lines(HOOK.read_text(encoding="utf-8")):
            with self.subTest(line=line):
                self.assertIsNone(FORBIDDEN_HOOK_COMMANDS.search(line))

    @unittest.skipUnless(BASH.is_file(), "Git Bash/POSIX Bash is required")
    def test_session_start_leaves_home_untouched_with_or_without_a_stray_hold(self):
        with tempfile.TemporaryDirectory(prefix="simonk main fence ") as raw:
            base = Path(raw)
            repo = base / "source with spaces"
            fixture_hook = repo / ".claude" / "hooks" / "session-start.sh"
            fixture_hook.parent.mkdir(parents=True)
            shutil.copyfile(HOOK, fixture_hook)
            (repo / "perspectives.md").write_text("notes\n", encoding="utf-8")
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
            for stray_hold in (False, True):
                if stray_hold:
                    (repo / "distribution").mkdir(exist_ok=True)
                    (repo / "distribution" / "main-source-only.hold").write_text("x\n", encoding="utf-8")
                for project_dir in (repo, other_project):
                    with self.subTest(project=project_dir.name, stray_hold=stray_hold):
                        env["CLAUDE_PROJECT_DIR"] = posix(project_dir)
                        result = subprocess.run(
                            [str(BASH), "--noprofile", "--norc", posix(fixture_hook)],
                            cwd=base, env=env, text=True, encoding="utf-8",
                            capture_output=True, timeout=10,
                        )
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertIn("SessionStart is read-only (D-87)", result.stdout)
                        self.assertIn("Nothing was written.", result.stdout)
                        self.assertEqual(project_dir == repo, "[perspectives]" in result.stdout)
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

    def test_hold_and_release_workflow_are_retired(self):
        # D-87: removing the hold and the code it fenced in one commit means a revert
        # brings both back together; a stray hold file or reader must not reappear.
        self.assertFalse(HOLD.exists())
        self.assertFalse((WORKFLOWS / "release.yml").exists())
        readers = sorted(
            path.relative_to(ROOT).as_posix()
            for path in [*WORKFLOWS.glob("*.yml"), *(ROOT / ".claude" / "hooks").iterdir()]
            if path.is_file() and HOLD.name in path.read_text(encoding="utf-8"))
        self.assertEqual(readers, [])

    def test_no_workflow_creates_a_github_release(self):
        # Releases reach users as dist commits (1.<N>.0); a GitHub Release from main
        # would collide with that numbering.
        makers = sorted(path.name for path in WORKFLOWS.glob("*.yml")
                        if RELEASE_MAKERS.search(path.read_text(encoding="utf-8")))
        self.assertEqual(makers, [])


if __name__ == "__main__":
    unittest.main()
