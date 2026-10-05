"""Regression traps for the retired killer. Never inspect or stop real processes."""
import builtins
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "kill_worker.py"


class Denied(Exception):
    pass


class FakeProcess:
    def __init__(self, trace, unreadable=False):
        self.pid, self.trace, self.unreadable = 867000, trace, unreadable
        self.alive = True

    def parents(self):
        self.trace.append("parents")
        return []

    def environ(self):
        self.trace.append("environment")
        if self.unreadable:
            raise Denied("fixture only")
        return {"ORCA_TERMINAL_HANDLE": "term-fixture-A"}

    def children(self, recursive=False):
        self.trace.append("children")
        return []

    def name(self):
        return "fixture-only"

    def create_time(self):
        return 1.0

    def terminate(self):
        self.trace.append("terminate")
        self.alive = False

    def kill(self):
        self.trace.append("kill")


class RetiredKillerTests(unittest.TestCase):
    def setUp(self):
        self.trace = []
        self.process = FakeProcess(self.trace)
        guard = patch("subprocess.Popen", side_effect=AssertionError("No external processes"))
        guard.start()
        self.addCleanup(guard.stop)
        signal_guard = patch("os.kill", side_effect=AssertionError("No real process signals"))
        signal_guard.start()
        self.addCleanup(signal_guard.stop)
        self.original_import = builtins.__import__

    def process_iter(self, *args):
        self.trace.append("process_iter")
        return iter([self.process] if self.process.alive else [])

    def native(self, *args):
        self.trace.append("native:" + "/".join(args[:2]))
        return True, {"workers": [{"dispatchId": "ctx-fixture-B", "agentTerminalHandle": "term-fixture-B"}]}

    def import_trap(self, name, *args, **kwargs):
        if name == "psutil":
            self.trace.append("import:psutil")
            return SimpleNamespace(process_iter=self.process_iter, Process=lambda: self.process,
                AccessDenied=Denied, NoSuchProcess=Denied, ZombieProcess=Denied,
                wait_procs=lambda procs, timeout: (procs, []))
        if name == "routing":
            self.trace.append("import:routing")
            return SimpleNamespace(run_orca_json=self.native)
        return self.original_import(name, *args, **kwargs)

    def load(self):
        spec = importlib.util.spec_from_file_location("fixture_retired_killer", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def invoke(self, args, direct=False):
        self.process.alive = True
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch("builtins.__import__", side_effect=self.import_trap), patch.object(sys, "path", list(sys.path)), \
                patch.object(sys, "argv", [str(SCRIPT), *args]), \
                patch.dict(os.environ, {"ORCA_TERMINAL_HANDLE": "fixture-own-terminal"}), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            if direct:
                with self.assertRaises(SystemExit) as stopped:
                    runpy.run_path(str(SCRIPT), run_name="__main__")
                code = stopped.exception.code
            else:
                code = self.load().main()
        return code, stdout.getvalue(), stderr.getvalue()

    def assert_blocked(self, args, direct=False):
        self.trace.clear()
        code, out, _ = self.invoke(args, direct)
        self.assertEqual(self.trace, [], "Retired entry must not inspect, import or mutate native/process state")
        self.assertEqual(code, 2)
        body = json.loads(out)
        self.assertFalse(body["ok"])
        self.assertEqual(body["error"], "LEGACY_WORKER_TERMINATION_DISABLED")
        self.assertIs(body["termination_verified"], False)
        return body

    def test_mismatched_handle_and_dispatch_cannot_kill_or_fence(self):
        self.assert_blocked(["--dispatch", "ctx-fixture-B", "--handle", "term-fixture-A", "--kill", "--fence"])

    def test_legacy_flags_cannot_restore_termination(self):
        for args in (["--handle", "term-fixture-A", "--kill"],
                     ["--dispatch", "ctx-fixture-B", "--kill"],
                     ["--dispatch", "ctx-fixture-B", "--fence"], ["--kill"], ["--fence"]):
            with self.subTest(args=args):
                self.assert_blocked(args)

    def test_dry_legacy_requests_do_not_scan_or_claim_safety(self):
        for args in ([], ["--handle", "term-fixture-A"], ["--dispatch", "ctx-fixture-B"]):
            with self.subTest(args=args):
                self.assert_blocked(args)

    def test_unreadable_process_is_never_zero_process_success(self):
        self.process.unreadable = True
        self.assert_blocked(["--handle", "term-fixture-A", "--kill", "--fence", "--dispatch", "ctx-fixture-B"])

    def test_import_has_no_home_path_injection_or_process_dependencies(self):
        with patch("builtins.__import__", side_effect=self.import_trap), patch.object(sys, "path", list(sys.path)):
            original = list(sys.path)
            self.load()
            self.assertEqual(sys.path, original)
        self.assertEqual(self.trace, [])

    def test_direct_script_entry_is_also_inert(self):
        self.assert_blocked(["--dispatch", "ctx-fixture-B", "--handle", "term-fixture-A", "--kill", "--fence"], direct=True)

    def test_failure_does_not_echo_untrusted_target_values(self):
        code, out, _ = self.invoke(["--handle", "fixture-private-value", "--kill"])
        self.assertEqual(code, 2)
        self.assertNotIn("fixture-private-value", out)
        self.assertEqual(self.trace, [])

    def test_help_needs_no_native_modules_or_process_state(self):
        code, out, _ = self.invoke(["--help"], direct=True)
        self.assertEqual(code, 0)
        self.assertIn("retired", out.lower())
        self.assertEqual(self.trace, [])

    def test_mixed_help_is_not_a_successful_legacy_request(self):
        for args in (["--help", "--kill"], ["--handle", "term-fixture-A", "-h"], ["-h", "--help"]):
            with self.subTest(args=args):
                self.assert_blocked(args)

    def test_force_and_environment_do_not_override_retirement(self):
        with patch.dict(os.environ, {"VIBE_ALLOW_LEGACY_TERMINATION": "1"}):
            self.assert_blocked(["--force", "--kill", "--handle", "term-fixture-A"])


if __name__ == "__main__":
    unittest.main()
