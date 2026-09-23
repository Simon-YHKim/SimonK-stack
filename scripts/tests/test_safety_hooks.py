"""Leaf hook subprocess tests; no model calls, host activation or user installs.

Only stdin JSON is inspected: destructive command strings are NEVER executed.
Flat materialization is not proof of split-plugin or session lifecycle closure.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
RUNTIMES = ("careful/bin/check-careful.sh", "careful/bin/hook-extract.sh",
            "freeze/bin/check-freeze.sh")
PIN = "b9706f3635b6a545f46fae607ae9d6bcbfb69b91"
BASH = (Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"
        if os.name == "nt" else Path(shutil.which("bash") or "/missing/bash"))


@unittest.skipUnless(BASH.is_file(), "Git Bash/POSIX Bash is required")
class SafetyHookTests(unittest.TestCase):
    def setUp(self):
        for relative in RUNTIMES:
            self.assertTrue((ROOT / "skills-src" / relative).is_file(),
                            "Missing source hook runtime: " + relative)
        self.temp = tempfile.TemporaryDirectory(prefix="simonk hook test ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.flat = self.base / "flat skills"
        self.cwd = self.base / "project with spaces"
        self.inside = self.cwd / "src"
        self.inside.mkdir(parents=True)
        (self.cwd / "src-other").mkdir()
        self.state = self.base / "plugin state"
        self.state.mkdir()
        self.home = self.base / "isolated home"
        self.home.mkdir()
        for relative in RUNTIMES:
            target = self.flat / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / "skills-src" / relative, target)
        # No inherited shell startup hooks, Git configuration or provider keys.
        self.env = {k: v for k, v in os.environ.items()
                    if k.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP"}}
        self.env.update(HOME=self.posix(self.home), USERPROFILE=str(self.home),
                        CLAUDE_PLUGIN_DATA=self.posix(self.state),
                        CLAUDE_PLUGIN_ROOT=self.posix(self.base / "SimonKStack"),
                        GSTACK_HOME=self.posix(self.base / "analytics only"),
                        GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_CONFIG_SYSTEM=os.devnull, GIT_TERMINAL_PROMPT="0",
                        LC_ALL="C", BASH_ENV="", ENV="")
        if os.name == "nt":
            self.basic_path = str(BASH.parent.parent / "usr/bin")
            node = shutil.which("node")
            self.assertIsNotNone(node, "Node parser is required for Windows tests")
            self.env["PATH"] = os.pathsep.join((self.basic_path, str(Path(node).parent)))
        else:
            self.basic_path = "/usr/bin:/bin"
            self.env["PATH"] = os.environ["PATH"]

    @staticmethod
    def posix(path):
        path = Path(path).absolute()
        if os.name == "nt":
            return "/" + path.drive[0].lower() + path.as_posix()[2:]
        return str(path)

    def hook(self, skill, payload, *, env=None, flat=None):
        runtime = (flat or self.flat) / skill / "bin" / ("check-" + skill + ".sh")
        p = subprocess.run([str(BASH), "--noprofile", "--norc", self.posix(runtime)],
                           input=payload if isinstance(payload, str) else json.dumps(payload),
                           text=True, encoding="utf-8", capture_output=True,
                           cwd=self.cwd, env=env or self.env, timeout=15)
        self.assertEqual(p.returncode, 0, p.stderr)
        result = json.loads(p.stdout)  # Exactly one valid JSON object, not log+JSON.
        if result:
            self.assertEqual(set(result), {"hookSpecificOutput"})
            self.assertEqual(result["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertTrue(result["hookSpecificOutput"]["permissionDecisionReason"])
        return result.get("hookSpecificOutput", {}).get("permissionDecision", "allow")

    def freeze(self):
        # Execute the current SKILL.md writer with only an owned fixture path.
        # This is not skill invocation/host hook activation.
        writer = ('set -eu; FREEZE_DIR=$(cd "$1" && pwd); '
                  'FREEZE_DIR="${FREEZE_DIR%/}/"; '
                  'STATE_DIR="${CLAUDE_PLUGIN_DATA:-$HOME/.gstack}"; '
                  'mkdir -p "$STATE_DIR"; '
                  'printf "%s\\n" "$FREEZE_DIR" > "$STATE_DIR/freeze-dir.txt"')
        subprocess.run([str(BASH), "--noprofile", "--norc", "-c", writer, "writer", "src"],
                       check=True, capture_output=True, cwd=self.cwd, env=self.env, timeout=15)

    def test_careful_safe_command(self):
        self.assertEqual(self.hook("careful", {"tool_input": {"command": "git status --short"}}), "allow")

    def test_careful_warns_documented_families(self):
        commands = ["rm -rf /var/data", "DROP TABLE users;", "TRUNCATE orders;",
                    "git push -f origin topic", "git reset --hard HEAD~3",
                    "git checkout .", "git restore .", "kubectl delete pod x",
                    "docker rm -f x", "docker system prune -a"]
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(self.hook("careful", {"tool_input": {"command": command}}), "ask")

    def test_careful_catastrophic_command_keeps_documented_ask_policy(self):
        self.assertEqual(self.hook("careful", {"tool_input": {"command": "rm -rf /"}}), "ask")

    def test_careful_build_exception_does_not_hide_compound_or_quoted_command(self):
        self.assertEqual(self.hook("careful", {"tool_input": {"command": "rm -rf node_modules"}}), "allow")
        for command in ('echo "quoted"; rm -rf /var/data', "rm -rf /\nrm -rf node_modules",
                        "rm${IFS}-rf${IFS}/"):
            self.assertEqual(self.hook("careful", {"tool_input": {"command": command}}), "ask")

    def test_hook_never_executes_input_command(self):
        sentinel = self.cwd / "must-not-exist"
        command = "touch must-not-exist; rm -rf /var/data"
        self.assertEqual(self.hook("careful", {"tool_input": {"command": command}}), "ask")
        self.assertFalse(sentinel.exists())

    def test_malformed_nonempty_json_is_not_allowed(self):
        self.freeze()
        self.assertEqual(self.hook("careful", '{"tool_input":'), "ask")
        self.assertEqual(self.hook("freeze", '{"tool_input":'), "deny")

    def test_missing_empty_or_wrong_type_required_field_is_not_allowed(self):
        self.freeze()
        for payload in ("", "{}", '{"tool_input":{}}', '{"tool_input":null}',
                        '{"tool_input":{"command":7,"file_path":7}}',
                        '{"tool_input":{"command":"","file_path":""}}'):
            with self.subTest(payload=payload):
                self.assertEqual(self.hook("careful", payload), "ask")
                self.assertEqual(self.hook("freeze", payload), "deny")

    def test_malformed_present_state_is_not_inactive(self):
        for content in ("", "   \n", "relative-boundary\n"):
            (self.state / "freeze-dir.txt").write_text(content, encoding="utf-8")
            with self.subTest(content=content):
                self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": "outside.py"}}), "deny")
        (self.state / "freeze-dir.txt").unlink()
        (self.state / "freeze-dir.txt").mkdir()
        self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": "outside.py"}}), "deny")

    def test_missing_parent_traversal_cannot_ride_boundary_prefix(self):
        self.freeze()
        for path in ("src/missing/../../outside.py", "src/missing/deep/new.py"):
            self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": path}}), "deny")

    def test_file_path_control_characters_are_not_silently_stripped(self):
        self.freeze()
        for suffix in ("\n", "\r", "\t", "\0", "\x7f"):
            with self.subTest(code=ord(suffix)):
                self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": "src/new.py" + suffix}}), "deny")

    def test_root_boundary_does_not_introduce_double_slashes(self):
        # Only state in this owned fixture is written; /usr/bin is not modified.
        (self.state / "freeze-dir.txt").write_text("/\n", encoding="utf-8")
        self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": "/usr/bin/never-created-by-hook"}}), "allow")

    def test_final_symlink_to_outside_is_denied(self):
        self.freeze()
        outside = self.cwd / "outside.py"
        outside.write_text("fixture", encoding="utf-8")
        link = self.inside / "linked.py"
        try:
            link.symlink_to(outside)
        except OSError as exc:
            self.skipTest("OS cannot create this owned symlink fixture: " + type(exc).__name__)
        self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": "src/linked.py"}}), "deny")

    def test_missing_helper_is_not_allowed(self):
        (self.flat / RUNTIMES[1]).unlink()  # Disposable fixture, never source/user files.
        self.freeze()
        self.assertEqual(self.hook("careful", {"tool_input": {"command": "git status"}}), "ask")
        self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": "src/new.py"}}), "deny")

    def test_missing_parsers_are_not_allowed(self):
        self.freeze()
        # Override parser functions only in this owned subprocess startup file.
        startup = self.base / "no parsers.sh"
        startup.write_text("python3() { return 127; }\nnode() { return 127; }\n", encoding="utf-8")
        env = {**self.env, "BASH_ENV": self.posix(startup)}
        self.assertEqual(self.hook("careful", {"tool_input": {"command": "git status"}}, env=env), "ask")
        self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": "src/new.py"}}, env=env), "deny")

    def test_inactive_freeze_allows(self):
        self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": "other.py"}}), "allow")

    def test_active_freeze_inside_outside_and_prefix_collision(self):
        self.freeze()
        for path, decision in (("src/new.py", "allow"), ("other.py", "deny"),
                               ("src-other/new.py", "deny"), ("src/../other.py", "deny")):
            with self.subTest(path=path):
                self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": path}}), decision)

    def test_writer_plugin_state_takes_precedence_over_unrelated_gstack_home(self):
        self.freeze()
        self.assertNotEqual(self.env["GSTACK_HOME"], self.env["CLAUDE_PLUGIN_DATA"])
        self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": "outside.py"}}), "deny")

    def test_absolute_posix_path_and_cwd_mount_alias_agree(self):
        self.freeze()
        self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": self.posix(self.inside / "new.py")}}), "allow")
        self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": "src/new.py"}}), "allow")
        # Also exercise the inverse /c-state versus cwd /tmp alias, if present.
        (self.state / "freeze-dir.txt").write_text(self.posix(self.inside) + "/\n", encoding="utf-8")
        self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": "src/new.py"}}), "allow")

    def test_careful_unexpected_runtime_failure_returns_ask_json(self):
        startup = self.base / "stdin failure.sh"
        startup.write_text("cat() { return 13; }\n", encoding="utf-8")
        self.assertEqual(self.hook("careful", {"tool_input": {"command": "git status"}},
                                  env={**self.env, "BASH_ENV": self.posix(startup)}), "ask")

    def test_careful_matcher_failure_is_not_a_nonmatch(self):
        startup = self.base / "matcher failure.sh"
        startup.write_text("grep() { return 2; }\n", encoding="utf-8")
        self.assertEqual(self.hook("careful", {"tool_input": {"command": "rm -rf /var/data"}},
                                  env={**self.env, "BASH_ENV": self.posix(startup)}), "ask")

    def test_python_only_parser_preserves_decisions(self):
        self.freeze()
        startup = self.base / "python only.sh"
        startup.write_text("python3() { " + shlex.quote(self.posix(Path(sys.executable))) +
                           ' "$@"; }\nnode() { return 127; }\n', encoding="utf-8")
        env = {**self.env, "BASH_ENV": self.posix(startup)}
        self.assertEqual(self.hook("careful", {"tool_input": {"command": "git status"}}, env=env), "allow")
        self.assertEqual(self.hook("careful", {"tool_input": {"command": "rm -rf /var/data"}}, env=env), "ask")
        self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": "src/new.py"}}, env=env), "allow")
        self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": "outside.py"}}, env=env), "deny")

    def test_home_state_fallback_matches_current_writer(self):
        self.freeze()
        fallback = self.home / ".gstack"
        fallback.mkdir()
        shutil.copyfile(self.state / "freeze-dir.txt", fallback / "freeze-dir.txt")
        env = dict(self.env)
        del env["CLAUDE_PLUGIN_DATA"]
        self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": "outside.py"}}, env=env), "deny")

    def test_removing_fixture_state_unfreezes(self):
        self.freeze()
        (self.state / "freeze-dir.txt").unlink()
        self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": "outside.py"}}), "allow")

    def test_failing_state_read_is_deny_not_silent_exit(self):
        self.freeze()
        startup = self.base / "unreadable state.sh"
        startup.write_text("head() { return 13; }\n", encoding="utf-8")
        self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": "src/new.py"}},
                                  env={**self.env, "BASH_ENV": self.posix(startup)}), "deny")

    def test_decision_reason_escapes_quotes(self):
        self.freeze()
        self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": 'outside"file.py'}}), "deny")

    def test_analytics_contain_patterns_not_commands(self):
        marker = "private-payload-marker"
        self.hook("careful", {"tool_input": {"command": "rm -rf /var/" + marker}})
        log = self.base / "analytics only/analytics/skill-usage.jsonl"
        records = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(records[0]["pattern"], "rm_recursive")
        self.assertNotIn(marker, log.read_text(encoding="utf-8"))
        self.assertFalse((self.home / ".gstack").exists())

    def test_license_records_pinned_upstream_and_local_adaptations(self):
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn(PIN, license_text)
        self.assertIn("Copyright (c) 2026 Garry Tan", license_text)
        self.assertIn("CLAUDE_PLUGIN_DATA", license_text)
        self.assertIn("ask", license_text)

    @unittest.skipUnless(os.name == "nt", "Guarded materializer is Windows-only")
    def test_package_materialization_runs_the_real_leaf_bytes(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import skill_release as release
        repo = self.base / "source fixture"
        (repo / ".claude/skills").mkdir(parents=True)
        for skill in ("careful", "freeze"):
            shutil.copytree(ROOT / "skills-src" / skill, repo / "skills-src" / skill)
        for name in ("LICENSE", "NOTICE", "skills-src/VENDORED.md"):
            shutil.copyfile(ROOT / name, repo / name)
        git = shutil.which("git")
        for args in (("init", "-q"), ("add", "--", "skills-src", "LICENSE", "NOTICE")):
            subprocess.run([git, "-C", str(repo), *args], check=True, capture_output=True,
                           env=self.env, timeout=15)
        config = {"schema_version": 1, "scope": release.SCOPE,
                  "owners": {"careful": "SimonKCore", "freeze": "SimonKStack"},
                  "development_only": [], "preserve_unowned": True,
                  "plugin_only_out_of_scope": [], "external_dependencies": []}
        package, target = self.base / "leaf package", self.base / "materialized skills"
        receipt = release.build_release(repo, config, package)
        manifest = release.verify_release(package, receipt["release_digest"])
        outcome = release.materialize(package, target, receipt["release_digest"], apply=True)
        self.assertFalse(outcome["runtime_closure_verified"])
        for relative in RUNTIMES:
            original = (ROOT / "skills-src" / relative).read_bytes()
            self.assertEqual((target / relative).read_bytes(), original)
            record = next(f for f in manifest["files"] if f["source_path"] == "skills-src/" + relative)
            self.assertEqual(record["sha256"], hashlib.sha256(original).hexdigest())
        self.freeze()
        self.assertEqual(self.hook("careful", {"tool_input": {"command": "git reset --hard"}}, flat=target), "ask")
        self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": "src/new.py"}}, flat=target), "allow")
        self.assertEqual(self.hook("freeze", {"tool_input": {"file_path": "outside.py"}}, flat=target), "deny")


if __name__ == "__main__":
    unittest.main()
