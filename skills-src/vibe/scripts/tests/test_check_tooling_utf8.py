"""check_tooling.py: UTF-8 stdio and a side-effect-free --help.

Runs a TEMP COPY of the script so its state directory lives in the temp dir.
PATH holds only fixture stand-ins for codex/npm/orca/claude/agy/grok that
append to a marker file; no real agent CLI, network or real state is touched.
"""
import ast
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "check_tooling.py"
TOOLS = ("codex", "npm", "orca", "claude", "agy", "grok")
SIDE_EFFECT_CALLS = {"report", "ack_skills", "check_clis", "check_orca_skills",
                     "_run", "_version", "_npm_latest", "_write_snapshot", "makedirs"}


def _write_stand_in(bin_dir, name):
    # The tool name is written literally: PATH holds only bin_dir, so external
    # helpers such as `basename` are not available to the POSIX stand-in.
    extra = name == "orca"
    if os.name == "nt":
        body = "@echo off\r\necho called %s>>\"%%VIBE_TOOLING_MARKER%%\"\r\n" % name
        if extra:
            body += "echo demo-skill: fixture only\r\n"
        (bin_dir / (name + ".cmd")).write_bytes(body.encode("ascii"))
    else:
        body = "#!/bin/sh\necho \"called %s\" >> \"$VIBE_TOOLING_MARKER\"\n" % name
        if extra:
            body += "echo 'demo-skill: fixture only'\n"
        path = bin_dir / name
        path.write_bytes(body.encode("ascii"))
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


class CheckToolingUtf8Tests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="vibe-check-tooling-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        scripts = self.root / "skill" / "scripts"
        scripts.mkdir(parents=True)
        self.copy = scripts / "check_tooling.py"
        shutil.copyfile(SCRIPT, self.copy)
        self.state = self.root / "skill" / "state"
        self.marker = self.root / "marker.txt"
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        for name in TOOLS:
            _write_stand_in(bin_dir, name)
        env = dict(os.environ)
        for key in ("PYTHONUTF8", "PYTHONLEGACYWINDOWSSTDIO", "PYTHONPATH"):
            env.pop(key, None)
        env.update({"PATH": str(bin_dir), "PYTHONIOENCODING": "ascii",
                    "VIBE_TOOLING_MARKER": str(self.marker)})
        self.env = env

    def run_copy(self, *args):
        proc = subprocess.run([sys.executable, "-B", str(self.copy), *args],
                              cwd=str(self.root), env=self.env, capture_output=True,
                              timeout=120)
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")

    def test_ascii_pipe_really_rejects_korean(self):
        # Control: proves the environment above would crash an unfixed print.
        proc = subprocess.run([sys.executable, "-B", "-c", "print(chr(0xD234))"],
                              cwd=str(self.root), env=self.env, capture_output=True,
                              timeout=60)
        self.assertNotEqual(proc.returncode, 0)

    def test_help_prints_docstring_without_side_effects(self):
        for flag in ("--help", "-h"):
            code, out, err = self.run_copy(flag)
            self.assertEqual(code, 0, err)
            self.assertIn("툴체인 최신화 점검", out)
            self.assertIn("--ack-skills", out)
            self.assertNotIn("Traceback", err)
            self.assertFalse(self.state.exists(), flag)
            self.assertFalse(self.marker.exists(), flag)

    def test_control_full_report_uses_stand_ins_and_utf8(self):
        # Control: the default path does call tools and write state, so the
        # absence of both in the help test is meaningful.
        code, out, err = self.run_copy()
        self.assertEqual(code, 0, err)
        self.assertNotIn("Traceback", err)
        self.assertIn("툴체인", out)
        self.assertTrue(self.marker.exists())
        called = self.marker.read_bytes().decode("ascii", "replace")
        for tool in ("codex", "npm", "orca"):
            self.assertIn("called " + tool, called)
        self.assertTrue((self.state / "orca-skills.json").is_file())

    def test_entrypoint_reconfigures_before_first_print_and_help_first(self):
        tree = ast.parse(SCRIPT.read_bytes().decode("utf-8"))
        mains = [node for node in tree.body if isinstance(node, ast.If)
                 and isinstance(node.test, ast.Compare)
                 and isinstance(node.test.left, ast.Name)
                 and node.test.left.id == "__name__"]
        self.assertEqual(len(mains), 1)
        calls = sorted((n for n in ast.walk(mains[0]) if isinstance(n, ast.Call)),
                       key=lambda n: (n.lineno, n.col_offset))

        def name(call):
            func = call.func
            return func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")

        first_reconfigure = next(c.lineno for c in calls if name(c) == "reconfigure")
        first_print = next(c.lineno for c in calls if name(c) == "print")
        self.assertLess(first_reconfigure, first_print)
        help_line = min(n.lineno for n in ast.walk(mains[0])
                        if isinstance(n, ast.Constant) and n.value == "--help")
        side_effects = [c.lineno for c in calls if name(c) in SIDE_EFFECT_CALLS]
        self.assertTrue(side_effects)
        self.assertLess(help_line, min(side_effects))
        # Nothing at module level may run before the entrypoint.
        for node in tree.body:
            if node is mains[0]:
                continue
            ok = isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.Assign))
            ok = ok or (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))
            self.assertTrue(ok, ast.dump(node)[:120])


if __name__ == "__main__":
    unittest.main()
