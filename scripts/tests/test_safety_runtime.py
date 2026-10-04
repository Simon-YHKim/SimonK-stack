"""Offline Windows integration tests for the candidate safety runtime adapter.

The fixtures are wholly disposable.  They never activate host hooks, inspect a
user skill directory, or use the real default state root.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[2]
SOURCE_RUNTIME = ROOT / "skills-src/freeze/bin/safety_runtime.py"
PACKAGED_PLUGIN = os.environ.get("SIMONK_SAFETY_CANDIDATE_PLUGIN_ROOT")
RESOURCES = (
    "careful/bin/check-careful.sh",
    "careful/bin/hook-extract.sh",
    "freeze/bin/check-freeze.sh",
)
BASH = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"
# The runtime's own fail-closed reasons (D-62 follow-up 5: careful no longer
# falls back to ask).
CAREFUL_RUNTIME_FAILURE = "[careful][RUNTIME FAILURE] Safety runtime failed, command not checked"
FREEZE_RUNTIME_FAILURE = "[freeze] Safety runtime unavailable; blocked, fail closed."
# A spent whole-check budget is its own deny reason: a timeout, safe to retry.
CAREFUL_TIMEOUT = "[careful][RUNTIME TIMEOUT] Safety check did not finish within "
FREEZE_TIMEOUT = "[freeze] Safety check timed out after "


@unittest.skipUnless(os.name == "nt" and BASH.is_file(), "Windows Git Bash is required")
class SafetyRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source_runtime = (Path(PACKAGED_PLUGIN) / ".simonk-runtime/safety_runtime.py"
                               if PACKAGED_PLUGIN else SOURCE_RUNTIME)
        resource_root = (Path(PACKAGED_PLUGIN) / ".simonk-runtime"
                         if PACKAGED_PLUGIN else ROOT / "skills-src")
        self.assertTrue(self.source_runtime.is_file(), "candidate safety runtime is missing")
        self.temp = tempfile.TemporaryDirectory(prefix="simonk safety runtime ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.runtime = self.base / ".simonk-runtime"
        self.runtime.mkdir()
        shutil.copyfile(self.source_runtime, self.runtime / "safety_runtime.py")
        for relative in RESOURCES:
            source = resource_root / relative
            self.assertTrue(source.is_file(), f"candidate safety resource is missing: {relative}")
            target = self.runtime / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

        self.project = self.base / "logical project"
        self.project.mkdir()
        self.worktree = self.base / "different worktree"
        self.inside = self.worktree / "src"
        self.inside.mkdir(parents=True)
        self.outside = self.worktree / "outside"
        self.outside.mkdir()
        self.project_b = self.base / "other project"
        self.project_b.mkdir()
        self.state_root = self.base / "owned state"
        self.home = self.base / "isolated home"
        self.home.mkdir()
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node is required by the unchanged leaf helper")
        kept = {k: v for k, v in os.environ.items()
                if k.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP"}}
        kept.update(
            SIMONK_SAFETY_STATE_ROOT=str(self.state_root),
            SIMONK_SAFETY_BASH=str(BASH),
            LOCALAPPDATA=str(self.base / "must not be used"),
            HOME=str(self.home),
            USERPROFILE=str(self.home),
            PATH=os.pathsep.join((str(Path(node).parent), str(BASH.parent.parent / "usr/bin"))),
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_CONFIG_SYSTEM=os.devnull,
            GIT_TERMINAL_PROMPT="0",
            BASH_ENV="",
            ENV="",
        )
        self.env = kept

    def run_cli(self, *args: str, payload=None, env=None, timeout: int = 12):
        stdin = None
        if payload is not None:
            stdin = payload if isinstance(payload, str) else json.dumps(payload)
        return subprocess.run(
            [sys.executable, "-B", str(self.runtime / "safety_runtime.py"), *map(str, args)],
            input=stdin,
            text=True,
            encoding="utf-8",
            capture_output=True,
            cwd=self.worktree,
            env=env or self.env,
            timeout=timeout,
        )

    @staticmethod
    def decision(result: subprocess.CompletedProcess[str]) -> str:
        data = json.loads(result.stdout)
        if not data:
            return "allow"
        hook = data["hookSpecificOutput"]
        if set(data) != {"hookSpecificOutput"} or hook["hookEventName"] != "PreToolUse":
            raise AssertionError(data)
        return hook["permissionDecision"]

    @staticmethod
    def reason(result: subprocess.CompletedProcess[str]) -> str:
        return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecisionReason"]

    def leaf_fixture(self, relative: str, decision: str, reason: str) -> None:
        """Replace a copied leaf with one that prints a fixed decision."""
        (self.runtime / relative).write_text(
            "#!/usr/bin/env bash\nprintf '%s\\n' '" + json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": reason,
                }
            }, separators=(",", ":")) + "'\n", encoding="utf-8")

    def payload(self, session="session-A", *, cwd=None, command=None, file_path=None):
        tool_input = {}
        if command is not None:
            tool_input["command"] = command
        if file_path is not None:
            tool_input["file_path"] = file_path
        return {"session_id": session, "cwd": str(cwd or self.worktree),
                "tool_input": tool_input}

    def set_boundary(self, *, project=None, session="session-A", boundary=None):
        result = self.run_cli("set", "--project", project or self.project,
                              "--session", session,
                              "--boundary", boundary or self.inside)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def check(self, policy, *, project=None, payload=None, env=None):
        result = self.run_cli("check", policy, "--project", project or self.project,
                              payload=payload, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return self.decision(result), result

    def state_file(self) -> Path:
        files = list((self.state_root / "states").glob("*.json"))
        self.assertEqual(len(files), 1)
        return files[0]

    def test_set_active_runs_real_freeze_leaf_inside_and_outside(self):
        self.set_boundary()
        inside, _ = self.check("freeze", payload=self.payload(file_path="src/new.py"))
        outside, _ = self.check("freeze", payload=self.payload(file_path="outside/new.py"))
        self.assertEqual(inside, "allow")
        self.assertEqual(outside, "deny")

    def test_clear_writes_exact_inactive_tombstone_and_allows(self):
        self.set_boundary()
        result = self.run_cli("clear", "--project", self.project, "--session", "session-A")
        self.assertEqual(result.returncode, 0, result.stderr)
        # /unfreeze documents this line; the plugin path must print it like freeze-state.sh does.
        self.assertIn("FREEZE_CLEARED", result.stdout)
        state = json.loads(self.state_file().read_text(encoding="utf-8"))
        self.assertEqual(set(state), {"project", "schema_version", "session", "status"})
        self.assertEqual(state["status"], "inactive")
        decision, _ = self.check("freeze", payload=self.payload(file_path="outside/new.py"))
        self.assertEqual(decision, "allow")

    def test_state_namespace_isolated_by_project_and_session(self):
        self.set_boundary(session="session-A")
        self.set_boundary(project=self.project_b, session="session-A")
        self.set_boundary(session="session-B")
        files = list((self.state_root / "states").glob("*.json"))
        self.assertEqual(len(files), 3)
        self.assertEqual(len({p.name for p in files}), 3)
        result = self.run_cli("clear", "--project", self.project, "--session", "session-A")
        self.assertEqual(result.returncode, 0, result.stderr)
        decision, _ = self.check("freeze", payload=self.payload("session-B", file_path="outside/x"))
        self.assertEqual(decision, "deny")

    def test_careful_works_without_freeze_state_and_never_executes_command(self):
        sentinel = self.worktree / "must-not-exist"
        safe, _ = self.check("careful", payload=self.payload(command="git status --short"))
        risky, _ = self.check(
            "careful", payload=self.payload(command="touch must-not-exist; rm -rf /var/data")
        )
        self.assertEqual(safe, "allow")
        self.assertEqual(risky, "ask")
        self.assertFalse(sentinel.exists())
        self.assertFalse(self.state_root.exists(), "careful check must not initialize freeze state")

    def test_careful_high_deny_passes_through_with_leaf_reason(self):
        # careful 0.2.2 HIGH tier: the real leaf denies; the runtime must not
        # downgrade it to ask or replace the leaf's reason.
        for command in ("rm -rf /", 'rm -rf "C:/"', "rm -rf ~"):
            with self.subTest(command=command):
                decision, result = self.check("careful", payload=self.payload(command=command))
                self.assertEqual(decision, "deny")
                self.assertTrue(self.reason(result).startswith("[careful][HIGH] "),
                                self.reason(result))

    def test_careful_leaf_internal_failure_deny_passes_through(self):
        # A sourced helper without the required functions is a careful HOOK
        # FAILURE (deny). The runtime keeps that deny and its reason.
        (self.runtime / "careful/bin/hook-extract.sh").write_text(
            "# fixture: outdated helper\n", encoding="utf-8")
        decision, result = self.check("careful", payload=self.payload(command="git status"))
        self.assertEqual(decision, "deny")
        self.assertIn("[careful][HOOK FAILURE]", self.reason(result))

    def test_fixture_leaf_decisions_pass_through_exactly(self):
        for relative, policy, decision in (
            ("careful/bin/check-careful.sh", "careful", "deny"),
            ("careful/bin/check-careful.sh", "careful", "ask"),
            ("careful/bin/check-careful.sh", "careful-powershell", "deny"),
            ("freeze/bin/check-freeze.sh", "freeze", "deny"),
        ):
            with self.subTest(policy=policy, decision=decision):
                if policy == "freeze":
                    self.set_boundary()
                self.leaf_fixture(relative, decision, "fixture reason " + decision)
                payload = (self.payload(file_path="src/new.py") if policy == "freeze"
                           else self.payload(command="git status"))
                got, result = self.check(policy, payload=payload)
                self.assertEqual(got, decision)
                self.assertEqual(self.reason(result), "fixture reason " + decision)

    def test_out_of_contract_leaf_decisions_fail_closed_as_deny(self):
        # freeze never asks and no leaf emits an explicit allow; either is
        # invalid output, which the runtime denies with its own reason.
        self.set_boundary()
        for relative, policy, decision, expected in (
            ("freeze/bin/check-freeze.sh", "freeze", "ask", FREEZE_RUNTIME_FAILURE),
            ("freeze/bin/check-freeze.sh", "freeze", "allow", FREEZE_RUNTIME_FAILURE),
            ("careful/bin/check-careful.sh", "careful", "allow", CAREFUL_RUNTIME_FAILURE),
            ("careful/bin/check-careful.sh", "careful", "block", CAREFUL_RUNTIME_FAILURE),
        ):
            with self.subTest(policy=policy, decision=decision):
                self.leaf_fixture(relative, decision, "fixture")
                payload = (self.payload(file_path="src/new.py") if policy == "freeze"
                           else self.payload(command="git status"))
                got, result = self.check(policy, payload=payload)
                self.assertEqual(got, "deny")
                self.assertTrue(self.reason(result).startswith(expected), self.reason(result))

    def shrink_budget(self, seconds: int) -> None:
        """Lower the copied runtime's whole-check budget for a timeout test."""
        path = self.runtime / "safety_runtime.py"
        text, count = re.subn(r"(?m)^CHECK_TIMEOUT = \d+$", f"CHECK_TIMEOUT = {seconds}",
                              path.read_text(encoding="utf-8"))
        self.assertEqual(count, 1, "CHECK_TIMEOUT constant not found")
        path.write_text(text, encoding="utf-8")

    def marker_processes(self, kill: bool = False) -> int:
        """Count, or stop, live processes whose command line names this test's folder.

        The folder name is random per test, so only processes started from this
        test's own copies match (the runtime's Python process too, but none runs
        between checks). Nothing else on the machine is counted or stopped.
        """
        script = ("$m = $env:SIMONK_TEST_MARKER; "
                  "$p = @(Get-CimInstance Win32_Process | Where-Object "
                  "{ $_.CommandLine -and $_.CommandLine.Contains($m) }); "
                  "if ($env:SIMONK_TEST_KILL -eq '1') { foreach ($x in $p) "
                  "{ Stop-Process -Id $x.ProcessId -Force -ErrorAction SilentlyContinue } }; "
                  "$p.Count")
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, timeout=60,
            env={**os.environ, "SIMONK_TEST_MARKER": self.base.name,
                 "SIMONK_TEST_KILL": "1" if kill else "0"})
        self.assertEqual(result.returncode, 0, result.stderr)
        return int(result.stdout.strip())

    def surviving_marker_processes(self, seconds: float = 5) -> int:
        """Marker process count once it reaches 0, or the last count after `seconds`."""
        deadline = time.monotonic() + seconds
        count = self.marker_processes()
        while count and time.monotonic() < deadline:
            time.sleep(0.5)
            count = self.marker_processes()
        return count

    def test_leaf_timeout_denies_with_timeout_reason_within_budget(self):
        # A leaf that never finishes is a timeout deny that says so and that
        # retrying is safe; the check returns soon after the budget and leaves
        # no leaf process behind (2026-10-05: six leaf shells were still
        # busy-looping 8 hours after this test, see the process-tree test).
        self.addCleanup(self.marker_processes, True)
        self.shrink_budget(1)
        self.set_boundary()
        for relative, policy, prefix in (
            ("careful/bin/check-careful.sh", "careful", CAREFUL_TIMEOUT),
            ("careful/bin/check-careful.sh", "careful-powershell", CAREFUL_TIMEOUT),
            ("freeze/bin/check-freeze.sh", "freeze", FREEZE_TIMEOUT),
        ):
            with self.subTest(policy=policy):
                (self.runtime / relative).write_text(
                    "#!/usr/bin/env bash\nwhile :; do :; done\n", encoding="utf-8")
                payload = (self.payload(file_path="src/new.py") if policy == "freeze"
                           else self.payload(command="git status"))
                started = time.monotonic()
                decision, result = self.check(policy, payload=payload)
                elapsed = time.monotonic() - started
                self.assertEqual(decision, "deny")
                self.assertTrue(self.reason(result).startswith(prefix + "1 s"),
                                self.reason(result))
                self.assertIn("retrying is safe", self.reason(result))
                self.assertLess(elapsed, 10)
        self.assertEqual(self.surviving_marker_processes(), 0, "a leaf outlived its timeout")

    def test_timeout_kills_the_whole_leaf_process_tree(self):
        # Git for Windows' bin/bash.exe is a launcher that runs usr/bin/bash.exe
        # as its child, so killing only the started process left the real
        # shell running. This leaf also starts a grandchild shell (it marks
        # the start in this test's folder) before looping: after the timeout
        # deny no process naming this test's folder may remain.
        self.addCleanup(self.marker_processes, True)
        self.shrink_budget(2)
        started = self.base / "grandchild-started"
        (self.runtime / "careful/bin/check-careful.sh").write_text(
            "#!/usr/bin/env bash\n"
            "\"$BASH\" --noprofile --norc -c ': > \"$1\"; while :; do :; done' grandchild "
            "\"${0%/.simonk-runtime/*}/grandchild-started\" &\n"
            "while :; do :; done\n", encoding="utf-8")
        self.assertEqual(self.marker_processes(), 0)
        decision, result = self.check("careful", payload=self.payload(command="git status"))
        self.assertEqual(decision, "deny")
        self.assertTrue(self.reason(result).startswith(CAREFUL_TIMEOUT + "2 s"),
                        self.reason(result))
        self.assertTrue(started.is_file(), "the grandchild never started; the test proves nothing")
        self.assertEqual(self.surviving_marker_processes(), 0,
                         "a leaf or its descendant outlived the timeout")

    def test_leaf_that_decides_still_leaves_no_process_behind(self):
        # A leaf that answers and exits while a background child it started
        # keeps running: the decision passes through and the child dies too.
        self.addCleanup(self.marker_processes, True)
        started = self.base / "grandchild-started"
        (self.runtime / "careful/bin/check-careful.sh").write_text(
            "#!/usr/bin/env bash\n"
            "started=\"${0%/.simonk-runtime/*}/grandchild-started\"\n"
            "\"$BASH\" --noprofile --norc -c ': > \"$1\"; while :; do :; done' grandchild "
            "\"$started\" &\n"
            "until [ -e \"$started\" ]; do :; done\n"
            "printf '{}\\n'\n", encoding="utf-8")
        decision, _ = self.check("careful", payload=self.payload(command="git status"))
        self.assertEqual(decision, "allow")
        self.assertTrue(started.is_file())
        self.assertEqual(self.surviving_marker_processes(), 0,
                         "a background child outlived its leaf")

    def test_spent_budget_times_out_before_starting_a_process(self):
        from unittest.mock import patch
        module = self.load_runtime_module()
        with patch.object(module.subprocess, "run") as run:
            with self.assertRaises(module.SafetyRuntimeTimeout):
                module._cygpath(BASH.parent.parent / "usr/bin/cygpath.exe", "C:\\",
                                time.monotonic() - 1)
        run.assert_not_called()

    def test_check_budget_stays_bounded(self):
        # 2026-10-04 measurement: the slowest whole check took 14.7 s under six
        # concurrent test suites. Far above 60 s a stuck check would stall every
        # command, and past the host's hook limit the hook would fail open.
        module = self.load_runtime_module()
        self.assertGreaterEqual(module.CHECK_TIMEOUT, 15)
        self.assertLessEqual(module.CHECK_TIMEOUT, 60)

    def test_careful_powershell_policy_runs_deny_only_powershell_leaf(self):
        # The payload carries no tool_name, so only the runtime's leaf argument
        # selects the PowerShell mode: MEDIUM Bash shapes must not ask there.
        sentinel = self.worktree / "must-not-exist"
        for command, expected in (
            ("Get-ChildItem -Force", "allow"),
            ("git reset --hard", "allow"),
            ("New-Item must-not-exist; Remove-Item -Recurse -Force C:\\", "deny"),
            ("Format-Volume -DriveLetter D", "deny"),
        ):
            with self.subTest(command=command):
                decision, result = self.check("careful-powershell",
                                              payload=self.payload(command=command))
                self.assertEqual(decision, expected)
                if expected == "deny":
                    self.assertTrue(self.reason(result).startswith("[careful][HIGH] PowerShell"),
                                    self.reason(result))
        careful, _ = self.check("careful", payload=self.payload(command="git reset --hard"))
        self.assertEqual(careful, "ask")
        self.assertFalse(sentinel.exists())
        self.assertFalse(self.state_root.exists())

    def test_missing_malformed_and_wrong_type_state_fail_closed(self):
        missing, _ = self.check("freeze", payload=self.payload(file_path="src/new.py"))
        self.assertEqual(missing, "deny")
        self.set_boundary()
        state_file = self.state_file()
        for content in ("", "{}", '{"schema_version":1,"status":"inactive","extra":1}'):
            state_file.write_text(content, encoding="utf-8")
            with self.subTest(content=content):
                decision, _ = self.check("freeze", payload=self.payload(file_path="src/new.py"))
                self.assertEqual(decision, "deny")
        state_file.unlink()
        state_file.mkdir()
        decision, _ = self.check("freeze", payload=self.payload(file_path="src/new.py"))
        self.assertEqual(decision, "deny")

    def test_invalid_identity_and_payload_use_fail_closed_fallback(self):
        cases = (
            '{"session_id":',
            {"session_id": "${CLAUDE_SESSION_ID}", "cwd": str(self.worktree), "tool_input": {}},
            {"session_id": "bad/session", "cwd": str(self.worktree), "tool_input": {}},
            {"session_id": "session-A", "cwd": "relative", "tool_input": {}},
        )
        for payload in cases:
            with self.subTest(payload=payload):
                for policy in ("careful", "careful-powershell"):
                    careful, result = self.check(policy, payload=payload)
                    self.assertEqual(careful, "deny")
                    self.assertTrue(self.reason(result).startswith(CAREFUL_RUNTIME_FAILURE))
                freeze, result = self.check("freeze", payload=payload)
                self.assertEqual(freeze, "deny")
                self.assertEqual(self.reason(result), FREEZE_RUNTIME_FAILURE)
        for session in ("", "bad/session", "${CLAUDE_SESSION_ID}"):
            result = self.run_cli("set", "--project", self.project, "--session", session,
                                  "--boundary", self.inside)
            self.assertNotEqual(result.returncode, 0)

    def test_duplicate_nonfinite_and_recursive_json_never_bypass_policy(self):
        duplicate = ("{\"session_id\":\"bad/session\",\"session_id\":\"session-A\","
                     + json.dumps("cwd") + ":" + json.dumps(str(self.worktree))
                     + ',"tool_input":{"command":"git status","file_path":"src/new.py"}}')
        careful, _ = self.check("careful", payload=duplicate)
        freeze, _ = self.check("freeze", payload=duplicate)
        self.assertEqual(careful, "deny")
        self.assertEqual(freeze, "deny")

        self.set_boundary()
        result = self.run_cli("clear", "--project", self.project, "--session", "session-A")
        self.assertEqual(result.returncode, 0, result.stderr)
        base = (json.dumps({"session_id": "session-A", "cwd": str(self.worktree)})[:-1]
                + ',"unknown":NaN,"tool_input":{"file_path":"src/new.py"}}')
        freeze, _ = self.check("freeze", payload=base)
        self.assertEqual(freeze, "deny", "non-finite JSON must not ride an inactive tombstone")

        nested = ("{\"session_id\":\"session-A\",\"cwd\":"
                  + json.dumps(str(self.worktree)) + ',"tool_input":{"x":'
                  + "[" * 100000 + "0" + "]" * 100000 + "}}")
        careful, _ = self.check("careful", payload=nested)
        freeze, _ = self.check("freeze", payload=nested)
        self.assertEqual(careful, "deny")
        self.assertEqual(freeze, "deny")

    def test_duplicate_state_keys_are_not_a_valid_inactive_tombstone(self):
        self.set_boundary()
        state = {
            "project": str(self.project.resolve()),
            "schema_version": 1,
            "session": "session-A",
        }
        raw = (json.dumps(state)[:-1]
               + ',"status":"active","status":"inactive"}')
        self.state_file().write_text(raw, encoding="utf-8")
        decision, _ = self.check("freeze", payload=self.payload(file_path="outside/new.py"))
        self.assertEqual(decision, "deny")

    def test_nul_in_hook_path_returns_a_decision_not_a_traceback(self):
        payload = self.payload(command="git status")
        payload["cwd"] = str(self.worktree) + "\0hidden"
        careful, result = self.check("careful", payload=payload)
        self.assertEqual(careful, "deny")
        self.assertTrue(self.reason(result).startswith(CAREFUL_RUNTIME_FAILURE))
        self.assertNotIn("Traceback", result.stderr)

    def test_hook_cwd_is_valid_but_independent_of_project_identity(self):
        self.set_boundary()
        self.assertFalse(self.worktree.is_relative_to(self.project))
        decision, _ = self.check("freeze", payload=self.payload(cwd=self.worktree,
                                                                  file_path="src/new.py"))
        self.assertEqual(decision, "allow")

    def test_missing_intermediate_parent_cannot_be_collapsed_before_leaf(self):
        self.set_boundary()
        decision, _ = self.check(
            "freeze", payload=self.payload(file_path="src/missing/../new.py")
        )
        self.assertEqual(decision, "deny")

    def test_state_hardlink_and_symlink_are_rejected_for_reads_and_writes(self):
        self.set_boundary()
        state_file = self.state_file()
        saved = self.base / "saved-state.json"
        state_file.replace(saved)
        os.link(saved, state_file)
        decision, _ = self.check("freeze", payload=self.payload(file_path="src/new.py"))
        self.assertEqual(decision, "deny")
        result = self.run_cli("clear", "--project", self.project, "--session", "session-A")
        self.assertNotEqual(result.returncode, 0)
        state_file.unlink()
        try:
            state_file.symlink_to(saved)
        except OSError as exc:
            self.skipTest("OS cannot create this owned symlink fixture: " + type(exc).__name__)
        decision, _ = self.check("freeze", payload=self.payload(file_path="src/new.py"))
        self.assertEqual(decision, "deny")
        result = self.run_cli("set", "--project", self.project, "--session", "session-A",
                              "--boundary", self.inside)
        self.assertNotEqual(result.returncode, 0)

    def test_state_root_ancestor_reparse_and_device_paths_are_rejected(self):
        real = self.base / "real state parent"
        real.mkdir()
        alias = self.base / "state alias"
        try:
            alias.symlink_to(real, target_is_directory=True)
        except OSError as exc:
            self.skipTest("OS cannot create this owned directory symlink: " + type(exc).__name__)
        env = {**self.env, "SIMONK_SAFETY_STATE_ROOT": str(alias / "nested")}
        result = self.run_cli("set", "--project", self.project, "--session", "session-A",
                              "--boundary", self.inside, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((real / "nested").exists())

        device_target = self.base / "device state"
        env = {**self.env, "SIMONK_SAFETY_STATE_ROOT": "\\\\?\\" + str(device_target)}
        result = self.run_cli("set", "--project", self.project, "--session", "session-A",
                              "--boundary", self.inside, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(device_target.exists())

    def test_resource_ancestor_reparse_falls_back(self):
        real = self.runtime / "careful-real"
        (self.runtime / "careful").replace(real)
        try:
            (self.runtime / "careful").symlink_to(real, target_is_directory=True)
        except OSError as exc:
            self.skipTest("OS cannot create this owned directory symlink: " + type(exc).__name__)
        decision, result = self.check("careful", payload=self.payload(command="git status"))
        self.assertEqual(decision, "deny")
        self.assertTrue(self.reason(result).startswith(CAREFUL_RUNTIME_FAILURE))

    def test_shared_extract_hardlink_is_rejected_by_careful_too(self):
        helper = self.runtime / "careful/bin/hook-extract.sh"
        saved = helper.with_name("saved-extract.sh")
        helper.replace(saved)
        os.link(saved, helper)
        decision, result = self.check("careful", payload=self.payload(command="git status"))
        self.assertEqual(decision, "deny")
        self.assertTrue(self.reason(result).startswith(CAREFUL_RUNTIME_FAILURE))

    def test_missing_helper_or_bash_failure_uses_fail_closed_fallback_without_path_dump(self):
        secret_marker = "private-path-marker"
        (self.runtime / "careful/bin/check-careful.sh").unlink()
        payload = self.payload(command="echo " + secret_marker)
        for policy in ("careful", "careful-powershell"):
            decision, result = self.check(policy, payload=payload)
            self.assertEqual(decision, "deny")
            self.assertTrue(self.reason(result).startswith(CAREFUL_RUNTIME_FAILURE))
            self.assertNotIn(secret_marker, result.stdout + result.stderr)
        self.set_boundary()
        env = {**self.env, "SIMONK_SAFETY_BASH": str(self.base / "missing/bash.exe")}
        decision, result = self.check("freeze", payload=self.payload(file_path="src/new.py"), env=env)
        self.assertEqual(decision, "deny")
        self.assertNotIn(str(self.base), result.stdout + result.stderr)

    def test_adapter_rejects_oversized_input_and_leaf_output(self):
        huge = "x" * (1024 * 1024 + 1)
        careful, _ = self.check("careful", payload=huge)
        freeze, _ = self.check("freeze", payload=huge)
        self.assertEqual(careful, "deny")
        self.assertEqual(freeze, "deny")

        helper = self.runtime / "careful/bin/check-careful.sh"
        helper.write_text("#!/usr/bin/env bash\nhead -c 70000 /dev/zero | tr '\\0' x\n",
                          encoding="utf-8")
        decision, result = self.check("careful", payload=self.payload(command="git status"))
        self.assertEqual(decision, "deny")
        self.assertTrue(self.reason(result).startswith(CAREFUL_RUNTIME_FAILURE))

    def test_leaf_cannot_inject_additional_hook_controls(self):
        helper = self.runtime / "careful/bin/check-careful.sh"
        helper.write_text(
            "#!/usr/bin/env bash\nprintf '%s\\n' "
            "'{}'\n".format(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": "fixture",
                    "updatedInput": {"command": "unexpected"},
                }
            }, separators=(",", ":"))),
            encoding="utf-8",
        )
        decision, result = self.check("careful", payload=self.payload(command="git status"))
        # Invalid leaf output is a runtime failure: deny, never the leaf's ask.
        self.assertEqual(decision, "deny")
        self.assertTrue(self.reason(result).startswith(CAREFUL_RUNTIME_FAILURE))
        parsed = json.loads(result.stdout)
        self.assertEqual(set(parsed["hookSpecificOutput"]),
                         {"hookEventName", "permissionDecision", "permissionDecisionReason"})

    def test_cp949_stdout_still_emits_ascii_safe_deny_json(self):
        helper = self.runtime / "careful/bin/check-careful.sh"
        leaf = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": "unicode fixture " + chr(0x1F600),
            }
        }
        helper.write_text("#!/usr/bin/env bash\nprintf '%s\\n' '"
                          + json.dumps(leaf, ensure_ascii=False, separators=(",", ":"))
                          + "'\n", encoding="utf-8")
        env = {**self.env, "PYTHONIOENCODING": "cp949"}
        result = self.run_cli("check", "careful", "--project", self.project,
                              payload=self.payload(command="git status"), env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.decision(result), "ask")

    def load_runtime_module(self):
        spec = importlib.util.spec_from_file_location("candidate_safety_runtime", self.source_runtime)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        previous_no_bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            spec.loader.exec_module(module)
        finally:
            sys.dont_write_bytecode = previous_no_bytecode
        return module

    def test_atomic_collision_does_not_delete_preexisting_file(self):
        module = self.load_runtime_module()
        parent = self.base / "collision state"
        parent.mkdir()
        target = parent / "state.json"
        collision = parent / ".state.json.collision.tmp"
        marker = b"preexisting marker"
        collision.write_bytes(marker)
        original = module.secrets.token_hex
        module.secrets.token_hex = lambda _length: "collision"
        try:
            with self.assertRaises(module.SafetyRuntimeError):
                module._atomic_write(target, {"fixture": True})
        finally:
            module.secrets.token_hex = original
        self.assertEqual(collision.read_bytes(), marker)
        self.assertFalse(target.exists())

    def test_atomic_state_shape_and_no_temporary_files(self):
        self.set_boundary()
        state = json.loads(self.state_file().read_text(encoding="utf-8"))
        self.assertEqual(set(state), {"boundary", "project", "schema_version", "session", "status"})
        self.assertEqual(state["schema_version"], 1)
        self.assertEqual(state["status"], "active")
        expected = hashlib.sha256(
            (os.path.normcase(str(self.project.resolve())) + "\0session-A").encode("utf-8")
        ).hexdigest() + ".json"
        self.assertEqual(self.state_file().name, expected)
        self.assertEqual(list((self.state_root / "states").glob(".*.tmp")), [])


class NonWindowsBranchTests(unittest.TestCase):
    """D-76 step 4: off Windows every check is a deliberate, explained deny.

    Runs on every OS (no Git Bash needed): os.name is patched on Windows, and a
    real POSIX host also runs the runtime as a subprocess.
    """

    def setUp(self) -> None:
        self.runtime_path = (Path(PACKAGED_PLUGIN) / ".simonk-runtime/safety_runtime.py"
                             if PACKAGED_PLUGIN else SOURCE_RUNTIME)
        spec = importlib.util.spec_from_file_location("candidate_safety_runtime_posix", self.runtime_path)
        self.module = importlib.util.module_from_spec(spec)
        previous = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            spec.loader.exec_module(self.module)
        finally:
            sys.dont_write_bytecode = previous

    def reason(self, policy):
        return self.module.NON_WINDOWS_REASONS["freeze" if policy == "freeze" else "careful"]

    def test_every_check_policy_denies_with_the_windows_only_reason(self):
        import io
        from unittest.mock import patch
        for policy in self.module.POLICIES:
            with self.subTest(policy=policy):
                with patch.object(self.module.os, "name", "posix"), \
                        patch.object(self.module.sys, "stdin", io.StringIO("not json")), \
                        patch.object(self.module.sys, "stdout", io.StringIO()) as stdout:
                    # Never reads stdin, state or the project: nothing there can change the answer.
                    code = self.module.main(["check", policy, "--project", "relative/never-read"])
                self.assertEqual(code, 0)
                self.assertEqual(json.loads(stdout.getvalue()), {"hookSpecificOutput": {
                    "hookEventName": "PreToolUse", "permissionDecision": "deny",
                    "permissionDecisionReason": self.reason(policy)}})

    def test_reasons_say_windows_only_fail_closed_and_the_way_out(self):
        careful, freeze = self.module.NON_WINDOWS_REASONS["careful"], self.module.NON_WINDOWS_REASONS["freeze"]
        for reason in (careful, freeze):
            self.assertIn("The SimonK safety runtime supports Windows only", reason)
            self.assertIn("blocked on purpose (fail closed)", reason)
            self.assertIn("start a new session", reason)
            self.assertNotIn("repair", reason)  # no repair makes it pass off Windows
        self.assertIn("without /careful and /guard", careful)
        self.assertIn("/plugin disable simonk-core@simonk-stack (for /careful)", careful)
        self.assertIn("/plugin disable simonk-stack@simonk-stack (for /guard)", careful)
        self.assertIn("without /freeze, /guard and /investigate", freeze)
        self.assertIn("/unfreeze cannot lift it here", freeze)
        self.assertIn("/plugin disable simonk-stack@simonk-stack", freeze)
        # The Windows runtime-failure reasons are unchanged.
        self.assertTrue(self.module._decision("careful")["hookSpecificOutput"]["permissionDecisionReason"]
                        .startswith(CAREFUL_RUNTIME_FAILURE))
        self.assertEqual(self.module._decision("freeze")["hookSpecificOutput"]["permissionDecisionReason"],
                         FREEZE_RUNTIME_FAILURE)

    def test_state_updates_still_fail_off_windows(self):
        import io
        from unittest.mock import patch
        for argv in (["set", "--project", "p", "--session", "s", "--boundary", "b"],
                     ["clear", "--project", "p", "--session", "s"]):
            with self.subTest(command=argv[0]):
                with patch.object(self.module.os, "name", "posix"), \
                        patch.object(self.module.sys, "stderr", io.StringIO()) as stderr:
                    self.assertEqual(self.module.main(argv), 2)
                self.assertEqual(stderr.getvalue(), "safety runtime state update failed\n")

    @unittest.skipIf(os.name == "nt", "Real POSIX subprocess")
    def test_real_posix_subprocess_denies(self):
        for policy in self.module.POLICIES:
            with self.subTest(policy=policy):
                result = subprocess.run([sys.executable, "-B", str(self.runtime_path), "check", policy,
                                         "--project", "/"], input="{}", text=True, capture_output=True,
                                        timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecisionReason"],
                                 self.reason(policy))


if __name__ == "__main__":
    unittest.main()
