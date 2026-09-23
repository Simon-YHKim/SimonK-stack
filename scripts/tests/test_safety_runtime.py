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
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SOURCE_RUNTIME = ROOT / "skills-src/freeze/bin/safety_runtime.py"
RESOURCES = (
    "careful/bin/check-careful.sh",
    "careful/bin/hook-extract.sh",
    "freeze/bin/check-freeze.sh",
)
BASH = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"


@unittest.skipUnless(os.name == "nt" and BASH.is_file(), "Windows Git Bash is required")
class SafetyRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(SOURCE_RUNTIME.is_file(), "candidate safety runtime is missing")
        self.temp = tempfile.TemporaryDirectory(prefix="simonk safety runtime ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.runtime = self.base / ".simonk-runtime"
        self.runtime.mkdir()
        shutil.copyfile(SOURCE_RUNTIME, self.runtime / "safety_runtime.py")
        for relative in RESOURCES:
            source = ROOT / "skills-src" / relative
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

    def test_invalid_identity_and_payload_use_policy_specific_fallback(self):
        cases = (
            '{"session_id":',
            {"session_id": "${CLAUDE_SESSION_ID}", "cwd": str(self.worktree), "tool_input": {}},
            {"session_id": "bad/session", "cwd": str(self.worktree), "tool_input": {}},
            {"session_id": "session-A", "cwd": "relative", "tool_input": {}},
        )
        for payload in cases:
            with self.subTest(payload=payload):
                careful, _ = self.check("careful", payload=payload)
                freeze, _ = self.check("freeze", payload=payload)
                self.assertEqual(careful, "ask")
                self.assertEqual(freeze, "deny")
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
        self.assertEqual(careful, "ask")
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
        self.assertEqual(careful, "ask")
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
        self.assertEqual(careful, "ask")
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
        decision, _ = self.check("careful", payload=self.payload(command="git status"))
        self.assertEqual(decision, "ask")

    def test_shared_extract_hardlink_is_rejected_by_careful_too(self):
        helper = self.runtime / "careful/bin/hook-extract.sh"
        saved = helper.with_name("saved-extract.sh")
        helper.replace(saved)
        os.link(saved, helper)
        decision, _ = self.check("careful", payload=self.payload(command="git status"))
        self.assertEqual(decision, "ask")

    def test_missing_helper_or_bash_failure_uses_policy_fallback_without_path_dump(self):
        secret_marker = "private-path-marker"
        (self.runtime / "careful/bin/check-careful.sh").unlink()
        payload = self.payload(command="echo " + secret_marker)
        decision, result = self.check("careful", payload=payload)
        self.assertEqual(decision, "ask")
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
        self.assertEqual(careful, "ask")
        self.assertEqual(freeze, "deny")

        helper = self.runtime / "careful/bin/check-careful.sh"
        helper.write_text("#!/usr/bin/env bash\nhead -c 70000 /dev/zero | tr '\\0' x\n",
                          encoding="utf-8")
        decision, _ = self.check("careful", payload=self.payload(command="git status"))
        self.assertEqual(decision, "ask")

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
        self.assertEqual(decision, "ask")
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

    def test_atomic_collision_does_not_delete_preexisting_file(self):
        spec = importlib.util.spec_from_file_location("candidate_safety_runtime", SOURCE_RUNTIME)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        previous_no_bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            spec.loader.exec_module(module)
        finally:
            sys.dont_write_bytecode = previous_no_bytecode
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


if __name__ == "__main__":
    unittest.main()
