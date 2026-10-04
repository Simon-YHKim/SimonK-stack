"""The plugin quality gate must work under Windows' legacy console locale."""
from __future__ import annotations

import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


GATE = Path(__file__).with_name("run_ci.py")


def load_gate():
    spec = importlib.util.spec_from_file_location("plugin_skill_ci_encoding", GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SkillCiEncodingTests(unittest.TestCase):
    def setUp(self):
        self.gate = load_gate()

    def test_child_commands_select_utf8_independent_of_parent_locale(self):
        with tempfile.TemporaryDirectory(prefix="plugin-skill-ci-encoding-") as temporary:
            skill = Path(temporary)
            (skill / "evals").mkdir()
            (skill / "evals" / "cases.json").write_text("[]", encoding="utf-8")
            with patch.object(self.gate, "run", return_value=(0, "{}")) as runner:
                ok, failures = self.gate.check_skill(skill)
            self.assertTrue(ok, failures)
            self.assertEqual(runner.call_count, 2)
            for call in runner.call_args_list:
                self.assertEqual(call.args[0][:3], [sys.executable, "-X", "utf8"])

    def test_child_output_decodes_utf8(self):
        code, output = self.gate.run([sys.executable, "-X", "utf8", "-c", "print('한글 —')"])
        self.assertEqual(code, 0)
        self.assertIn("한글 —", output)

    def test_invalid_child_encoding_fails_closed(self):
        child = subprocess.CompletedProcess(["fixture"], 0, stdout=b"\xff", stderr=b"")
        with patch.object(self.gate.subprocess, "run", return_value=child):
            code, output = self.gate.run(["fixture"])
        self.assertNotEqual(code, 0)
        self.assertIn("UTF-8", output)

    def test_summary_prints_to_cp949_console(self):
        with tempfile.TemporaryDirectory(prefix="plugin-skill-ci-summary-") as temporary:
            skills = Path(temporary)
            skill = skills / "fixture"
            skill.mkdir()
            (skill / "SKILL.md").write_text("fixture", encoding="utf-8")
            stream = io.TextIOWrapper(io.BytesIO(), encoding="cp949", errors="strict")
            with patch.object(self.gate, "SKILLS", skills), \
                 patch.object(self.gate, "check_skill", return_value=(True, [])), \
                 patch.object(sys, "stdout", stream):
                code = self.gate.main()
            stream.flush()
        self.assertEqual(code, 0)
        self.assertIn("RESULT: PASS", stream.buffer.getvalue().decode("cp949"))


if __name__ == "__main__":
    unittest.main()
