"""Offline Codex deny-policy candidate; never installs a hook or executes input."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from codex_guarded_policy import judge_pre_tool_use  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
CAREFUL = ROOT / "skills-src/careful/bin/check-careful.sh"
GIT_BASH = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"


def event(cwd, tool, command):
    return json.dumps({
        "session_id": "session-123", "cwd": str(cwd),
        "hook_event_name": "PreToolUse", "tool_name": tool,
        "tool_input": {"command": command},
    }).encode("utf-8")


def decision(result):
    if result == {}:
        return "allow"
    output = result["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecisionReason"]
    return output["permissionDecision"]


class CodexGuardedPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="simonk codex guard ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "project with spaces"
        self.boundary = self.project / "inside"
        self.outside = self.project / "outside"
        self.boundary.mkdir(parents=True)
        self.outside.mkdir()

    @staticmethod
    def patch(*paths):
        lines = ["*** Begin Patch"]
        for path in paths:
            lines.extend((f"*** Add File: {path}", "+fixture"))
        lines.append("*** End Patch")
        return "\n".join(lines)

    def test_patch_inside_allowed_and_outside_denied(self):
        inside = event(self.project, "apply_patch", self.patch("inside/new.py"))
        outside = event(self.project, "apply_patch", self.patch("outside/new.py"))
        self.assertEqual(decision(judge_pre_tool_use(inside, boundary=self.boundary)), "allow")
        self.assertEqual(decision(judge_pre_tool_use(outside, boundary=self.boundary)), "deny")

    def test_multi_target_move_and_prefix_collision_cannot_escape(self):
        sibling = self.project / "inside-other"
        sibling.mkdir()
        for paths in (("inside/a.py", "outside/b.py"),
                      ("inside/../outside/b.py",),
                      ("inside-other/b.py",)):
            with self.subTest(paths=paths):
                request = event(self.project, "apply_patch", self.patch(*paths))
                self.assertEqual(decision(judge_pre_tool_use(request, boundary=self.boundary)), "deny")
        move = ("*** Begin Patch\n*** Update File: inside/a.py\n"
                "*** Move to: outside/a.py\n@@\n-old\n+new\n*** End Patch")
        self.assertEqual(decision(judge_pre_tool_use(
            event(self.project, "apply_patch", move), boundary=self.boundary)), "deny")

    def test_final_symlink_escape_is_denied(self):
        target = self.outside / "actual.py"
        target.write_text("fixture", encoding="utf-8")
        link = self.boundary / "link.py"
        try:
            link.symlink_to(target)
        except OSError as exc:
            self.skipTest("symlink fixture unavailable: " + type(exc).__name__)
        request = event(self.project, "apply_patch", self.patch("inside/link.py"))
        self.assertEqual(decision(judge_pre_tool_use(request, boundary=self.boundary)), "deny")

    def test_parent_symlink_escape_is_denied(self):
        link = self.boundary / "linked-dir"
        try:
            link.symlink_to(self.outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest("symlink fixture unavailable: " + type(exc).__name__)
        request = event(self.project, "apply_patch", self.patch("inside/linked-dir/new.py"))
        self.assertEqual(decision(judge_pre_tool_use(request, boundary=self.boundary)), "deny")

    def test_missing_parent_bad_boundary_and_invalid_payload_deny(self):
        request = event(self.project, "apply_patch", self.patch("inside/missing/new.py"))
        self.assertEqual(decision(judge_pre_tool_use(request, boundary=self.boundary)), "deny")
        valid = event(self.project, "apply_patch", self.patch("inside/new.py"))
        self.assertEqual(decision(judge_pre_tool_use(valid, boundary=self.outside / "gone")), "deny")
        self.assertEqual(decision(judge_pre_tool_use(b"{", boundary=self.boundary)), "deny")

    def test_without_freeze_boundary_patch_is_not_claimed_to_be_frozen(self):
        request = event(self.project, "apply_patch", self.patch("outside/new.py"))
        self.assertEqual(judge_pre_tool_use(request), {})

    def test_cli_emits_only_supported_deny_json(self):
        script = ROOT / "scripts/codex_guarded_policy.py"
        request = event(self.project, "apply_patch", self.patch("outside/new.py"))
        process = subprocess.run(
            [sys.executable, "-B", str(script), "--boundary", str(self.boundary)],
            input=request, capture_output=True, timeout=10,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stderr, b"")
        output = json.loads(process.stdout)
        self.assertEqual(set(output), {"hookSpecificOutput"})
        self.assertEqual(decision(output), "deny")

    @unittest.skipUnless(GIT_BASH.is_file() and CAREFUL.is_file(), "Git Bash safety leaf required")
    def test_bash_leaf_ask_becomes_supported_codex_deny(self):
        safe = event(self.project, "Bash", "git status --short")
        danger = event(self.project, "Bash", "git reset --hard HEAD~1")
        kwargs = {"bash": GIT_BASH, "careful_script": CAREFUL}
        self.assertEqual(decision(judge_pre_tool_use(safe, **kwargs)), "allow")
        self.assertEqual(decision(judge_pre_tool_use(danger, **kwargs)), "deny")

    @unittest.skipUnless(GIT_BASH.is_file() and CAREFUL.is_file(), "Git Bash safety leaf required")
    def test_bash_input_is_never_executed_and_missing_leaf_denies(self):
        sentinel = self.project / "must-not-exist"
        command = "touch must-not-exist; rm -rf /var/data"
        request = event(self.project, "Bash", command)
        self.assertEqual(decision(judge_pre_tool_use(
            request, bash=GIT_BASH, careful_script=CAREFUL)), "deny")
        self.assertFalse(sentinel.exists())
        self.assertEqual(decision(judge_pre_tool_use(
            request, bash=GIT_BASH, careful_script=self.root / "missing.sh")), "deny")

    @unittest.skipUnless(GIT_BASH.is_file(), "Git Bash required")
    def test_invalid_or_oversized_leaf_output_denies(self):
        fake = self.root / "fake leaf.sh"
        request = event(self.project, "Bash", "git status")
        for body in ("printf 'not-json\\n'", "head -c 70000 /dev/zero"):
            with self.subTest(body=body):
                fake.write_text("#!/usr/bin/env bash\n" + body + "\n", encoding="utf-8")
                self.assertEqual(decision(judge_pre_tool_use(
                    request, bash=GIT_BASH, careful_script=fake)), "deny")

    @unittest.skipUnless(GIT_BASH.is_file(), "Git Bash required")
    def test_leaf_child_does_not_inherit_parent_credential_environment(self):
        fake = self.root / "fake env leaf.sh"
        fake.write_text(
            '#!/usr/bin/env bash\n'
            'if [ -n "${SIMONK_TEST_CREDENTIAL:-}" ]; then printf "not-json\\n"; '
            'else printf "{}\\n"; fi\n', encoding="utf-8",
        )
        request = event(self.project, "Bash", "git status")
        with patch.dict(os.environ, {"SIMONK_TEST_CREDENTIAL": "fixture-only"}):
            self.assertEqual(decision(judge_pre_tool_use(
                request, bash=GIT_BASH, careful_script=fake)), "allow")


if __name__ == "__main__":
    unittest.main()
