"""Offline Codex hook wire-format tests; no hook registration or tool execution."""

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from codex_hook_input import HookInputError, parse_pre_tool_use  # noqa: E402


def payload(tool_name, command, **extra):
    event = {
        "session_id": "session-123",
        "cwd": "C:/work/project",
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": {"command": command},
        **extra,
    }
    return json.dumps(event).encode("utf-8")


class CodexHookInputTests(unittest.TestCase):
    def test_bash_uses_command_and_does_not_execute_it(self):
        event = parse_pre_tool_use(payload("Bash", "touch should-not-exist; rm -rf /"))
        self.assertEqual(event.tool_name, "Bash")
        self.assertEqual(event.command, "touch should-not-exist; rm -rf /")
        self.assertEqual(event.targets, ())
        self.assertFalse(Path("should-not-exist").exists())

    def test_apply_patch_extracts_add_update_delete_and_move_targets(self):
        patch = (
            "*** Begin Patch\n"
            "*** Add File: src/new file.py\n+"
            "+value\n"
            "*** Update File: src/old.py\n"
            "*** Move to: src/renamed.py\n"
            "@@\n"
            "-old\n+"
            "+new\n"
            "*** Delete File: src/gone.py\n"
            "*** End Patch\n"
        )
        event = parse_pre_tool_use(payload("apply_patch", patch))
        self.assertEqual(event.targets, (
            "src/new file.py", "src/old.py", "src/renamed.py", "src/gone.py"
        ))

    def test_patch_rejects_partial_unknown_and_ambiguous_targets(self):
        bad = (
            "*** Begin Patch\n*** Update File: src/a.py\n@@\n-old\n+new\n",
            "*** Begin Patch\n*** Copy File: src/a.py\n*** End Patch",
            "*** Begin Patch\n*** Add File: \n+x\n*** End Patch",
            "*** Begin Patch\n*** Move to: src/a.py\n*** End Patch",
            "*** Begin Patch\n*** Add File: src/a.py\n+x\n*** Add File: SRC/A.PY\n+y\n*** End Patch",
            "*** Begin Patch\n*** Add File: src/a.py\n*** End Patch\n*** Add File: src/b.py",
            "*** Begin Patch\n*** Add File: src/a.py\n+x\n*** Weird Header\n*** End Patch",
            "*** Begin Patch\n*** Add File: src/a.py\x00\n+x\n*** End Patch",
            "*** Begin Patch\n*** Add File: src/a.py\r*** Add File: src/b.py\n+x\n*** End Patch",
            "*** Begin Patch\n*** Add File: src/a.py\u2028*** Add File: src/b.py\n+x\n*** End Patch",
        )
        for patch in bad:
            with self.subTest(patch=patch):
                with self.assertRaises(HookInputError):
                    parse_pre_tool_use(payload("apply_patch", patch))

    def test_json_and_required_fields_fail_closed_for_parser(self):
        bad = (
            b"{}",
            b'{"session_id":"x","session_id":"y"}',
            b'{"session_id": NaN}',
            payload("Edit", "*** Begin Patch\n*** End Patch"),
            payload("Bash", ""),
            payload("Bash", "safe", hook_event_name="PostToolUse"),
            json.dumps({"session_id": "session-123", "cwd": "C:/work/project",
                        "hook_event_name": "PreToolUse", "tool_name": "Bash",
                        "tool_input": {"command": 4}}).encode("utf-8"),
        )
        for item in bad:
            with self.subTest(item=item[:60]):
                with self.assertRaises(HookInputError):
                    parse_pre_tool_use(item)

    def test_input_is_bounded(self):
        with self.assertRaises(HookInputError):
            parse_pre_tool_use(b" " * (1024 * 1024 + 1))


if __name__ == "__main__":
    unittest.main()
