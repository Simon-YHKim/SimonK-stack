"""Offline checks for a stale Codex PATH shim; no Orca or npm access."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import runpy
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("check_tooling.py")
ROUTING = SCRIPT.with_name("routing.py")


def _state_env(path):
    return {"LOCALAPPDATA" if os.name == "nt" else "XDG_STATE_HOME": str(path)}


class CodexPathChecks(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("check_tooling", SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_help_does_not_probe_orca_registry_or_write_snapshot(self):
        for flag in ("--help", "-h"):
            with self.subTest(flag=flag):
                output = io.StringIO()
                with mock.patch.object(sys, "argv", [str(SCRIPT), flag]):
                    with mock.patch("subprocess.run") as child:
                        with mock.patch("os.makedirs") as write:
                            with contextlib.redirect_stdout(output):
                                with self.assertRaises(SystemExit) as done:
                                    runpy.run_path(str(SCRIPT), run_name="__main__")
                self.assertEqual(done.exception.code, 0)
                self.assertIn("--local-codex", output.getvalue())
                child.assert_not_called()
                write.assert_not_called()

    def test_unknown_option_fails_closed_without_probes(self):
        output = io.StringIO()
        with mock.patch.object(sys, "argv", [str(SCRIPT), "--unknown"]):
            with mock.patch("subprocess.run") as child:
                with contextlib.redirect_stderr(output):
                    with self.assertRaises(SystemExit) as done:
                        runpy.run_path(str(SCRIPT), run_name="__main__")
        self.assertEqual(done.exception.code, 2)
        self.assertIn("--unknown", output.getvalue())
        child.assert_not_called()

    def test_adjacent_npm_package_exposes_newer_version_than_path_shim(self):
        with tempfile.TemporaryDirectory() as temporary:
            bin_dir = Path(temporary)
            package = bin_dir / "node_modules" / "@openai" / "codex" / "package.json"
            package.parent.mkdir(parents=True)
            package.write_text(json.dumps({"name": "@openai/codex", "version": "0.159.0"}),
                               encoding="utf-8")
            with mock.patch.object(self.module.shutil, "which", return_value=str(bin_dir / "codex.cmd")):
                with mock.patch.object(self.module, "_version", return_value=("0.155.0", "codex-cli")):
                    row = self.module.check_codex_local()
        self.assertEqual(row["installed"], "0.155.0")
        self.assertEqual(row["local_package"], "0.159.0")
        self.assertEqual(row["state"], "뒤처짐")

    def test_full_preflight_blocks_stale_shim_when_registry_is_unavailable(self):
        with mock.patch.object(self.module, "_version", return_value=("0.155.0", "codex-cli")):
            with mock.patch.object(self.module, "_npm_latest", return_value=None):
                with mock.patch.object(self.module, "_local_codex_package_version",
                                       return_value="0.159.0"):
                    rows = self.module.check_clis()
        self.assertEqual(rows[0]["state"], "뒤처짐")
        self.assertEqual(rows[0]["local_package"], "0.159.0")

    def test_other_package_or_missing_package_cannot_claim_stale_codex(self):
        with tempfile.TemporaryDirectory() as temporary:
            bin_dir = Path(temporary)
            package = bin_dir / "node_modules" / "@openai" / "codex" / "package.json"
            package.parent.mkdir(parents=True)
            package.write_text(json.dumps({"name": "not-codex", "version": "9.0.0"}),
                               encoding="utf-8")
            with mock.patch.object(self.module.shutil, "which", return_value=str(bin_dir / "codex.cmd")):
                self.assertIsNone(self.module._local_codex_package_version())
                package.unlink()
                self.assertIsNone(self.module._local_codex_package_version())

    def test_failed_version_command_cannot_turn_error_text_into_a_version(self):
        with mock.patch.object(self.module, "_run", return_value=(1, "codex-cli 0.159.0", "update blocked")):
            version, _ = self.module._version(["codex", "--version"])
        self.assertIsNone(version)

    def test_prerelease_comparison_is_unknown_not_newer_than_stable(self):
        self.assertIsNone(self.module._cmp("0.159.0-beta.1", "0.159.0"))

    def test_local_mode_does_not_succeed_when_version_or_package_is_unknown(self):
        for row in ({"tool": "codex", "installed": None, "local_package": None,
                     "state": self.module.UNKNOWN},
                    {"tool": "codex", "installed": "0.159.0", "local_package": None,
                     "state": "설치본만 확인"}):
            with self.subTest(state=row["state"]):
                with mock.patch.object(self.module, "check_codex_local", return_value=row):
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        exit_code = self.module.report_local_codex()
                self.assertEqual(exit_code, 2)
                self.assertEqual(json.loads(output.getvalue())["state"], row["state"])

    def test_local_mode_succeeds_for_matching_stable_versions(self):
        with mock.patch.object(self.module, "_version", return_value=("0.159.0", "codex-cli")):
            with mock.patch.object(self.module, "_local_codex_package_version",
                                   return_value="0.159.0"):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    exit_code = self.module.report_local_codex()
        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(output.getvalue())["state"], "로컬 이상")

    def test_local_mode_never_queries_registry_or_orca(self):
        with mock.patch.object(self.module, "check_codex_local", return_value={
                "tool": "codex", "installed": "0.155.0", "local_package": "0.159.0",
                "state": "뒤처짐"}):
            with mock.patch.object(self.module, "check_orca_skills",
                                   side_effect=AssertionError("Orca must not run")):
                with mock.patch.object(self.module, "_npm_latest",
                                       side_effect=AssertionError("npm view must not run")):
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        exit_code = self.module.report_local_codex()
        self.assertEqual(exit_code, 1)
        self.assertEqual(json.loads(output.getvalue())["state"], "뒤처짐")

    def test_legacy_g11_points_to_side_effect_minimal_local_probe(self):
        spec = importlib.util.spec_from_file_location("vibe_routing_for_g11", ROUTING)
        routing = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(routing)
        guard = next(description for guard_id, description, _ in routing.GUARDS
                     if guard_id == "G11")
        self.assertIn("`python -B scripts/check_tooling.py --local-codex`", guard)
        self.assertNotIn("`python scripts/check_tooling.py`", guard)

    def test_orca_snapshot_stays_outside_skill_bundle_and_pending_persists(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            signed_state = root / "signed-skill" / "state"
            external = root / "host-state"
            output = [(0, "alpha: first", ""), (0, "alpha: updated", "")]
            with mock.patch.dict(os.environ, _state_env(external)):
                with mock.patch.object(self.module, "SKILL_ROOT", str(root / "signed-skill")):
                    with mock.patch.object(self.module, "_run", side_effect=output):
                        first = self.module.check_orca_skills()
                        second = self.module.check_orca_skills()
            snapshot = external / "SimonKStack" / "vibe" / "orca-skills.json"
            self.assertEqual(first["state"], "스냅샷 생성")
            self.assertEqual(second["state"], "미확인 변경")
            self.assertTrue(second["pending"])
            self.assertFalse(signed_state.exists())
            self.assertEqual(json.loads(snapshot.read_text(encoding="utf-8"))["skills"],
                             {"alpha": "updated"})

    def test_simultaneous_reports_preserve_both_pending_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "SimonKStack" / "vibe" / "orca-skills.json"
            self.module._write_snapshot(str(snapshot), {"alpha": "old", "beta": "old"}, {})
            first_writing = threading.Event()
            second_writing = threading.Event()
            original_write = self.module._write_snapshot
            results = {}

            def delayed_write(*args, **kwargs):
                if threading.current_thread().name == "first":
                    first_writing.set()
                    second_writing.wait(0.5)
                elif threading.current_thread().name == "second":
                    second_writing.set()
                return original_write(*args, **kwargs)

            listings = {"first": "alpha: new\nbeta: old",
                        "second": "alpha: old\nbeta: new"}

            def report():
                results[threading.current_thread().name] = self.module.check_orca_skills()

            def listing(*_args, **_kwargs):
                return 0, listings[threading.current_thread().name], ""

            with mock.patch.dict(os.environ, _state_env(root)):
                with mock.patch.object(self.module, "_run", side_effect=listing):
                    with mock.patch.object(self.module, "_write_snapshot", side_effect=delayed_write):
                        first = threading.Thread(target=report, name="first")
                        second = threading.Thread(target=report, name="second")
                        first.start()
                        self.assertTrue(first_writing.wait(2))
                        second.start()
                        first.join(3)
                        second.join(3)
            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertEqual(set(json.loads(snapshot.read_text(encoding="utf-8"))["pending"]["changed"]),
                             {"alpha", "beta"})
            self.assertEqual(results["first"]["state"], "미확인 변경")
            self.assertEqual(results["second"]["state"], "미확인 변경")

    def test_ack_requires_exact_reviewed_pending_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "SimonKStack" / "vibe" / "orca-skills.json"
            self.module._write_snapshot(str(snapshot), {"alpha": "old", "beta": "old"}, {})
            listings = [(0, "alpha: new\nbeta: old", ""),
                        (0, "alpha: new\nbeta: new", "")]
            with mock.patch.dict(os.environ, _state_env(root)):
                with mock.patch.object(self.module, "_run", side_effect=listings):
                    first = self.module.check_orca_skills()
                    second = self.module.check_orca_skills()
                self.assertNotEqual(first["pending_digest"], second["pending_digest"])
                before = snapshot.read_bytes()
                with self.assertRaises(ValueError):
                    self.module.ack_skills(first["pending_digest"])
                self.assertEqual(snapshot.read_bytes(), before)
                self.assertIn("확인 처리", self.module.ack_skills(second["pending_digest"]))
            self.assertEqual(json.loads(snapshot.read_text(encoding="utf-8"))["pending"], {})

    def test_repeat_sighting_keeps_review_digest_stable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "SimonKStack" / "vibe" / "orca-skills.json"
            self.module._write_snapshot(str(snapshot), {"alpha": "old"}, {})
            with mock.patch.dict(os.environ, _state_env(root)):
                with mock.patch.object(self.module, "_run", return_value=(0, "alpha: new", "")):
                    first = self.module.check_orca_skills()
                    second = self.module.check_orca_skills()
                self.assertEqual(first["pending_digest"], second["pending_digest"])
                self.assertIn("확인 처리", self.module.ack_skills(first["pending_digest"]))

    def test_ack_cli_without_review_digest_fails_before_state_access(self):
        output = io.StringIO()
        with mock.patch.object(sys, "argv", [str(SCRIPT), "--ack-skills"]):
            with mock.patch("subprocess.run") as child:
                with mock.patch("os.makedirs") as write:
                    with contextlib.redirect_stderr(output):
                        with self.assertRaises(SystemExit) as done:
                            runpy.run_path(str(SCRIPT), run_name="__main__")
        self.assertEqual(done.exception.code, 2)
        self.assertIn("digest", output.getvalue())
        child.assert_not_called()
        write.assert_not_called()

    def test_ack_replay_after_success_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "SimonKStack" / "vibe" / "orca-skills.json"
            self.module._write_snapshot(str(snapshot), {"alpha": "old"}, {})
            with mock.patch.dict(os.environ, _state_env(root)):
                with mock.patch.object(self.module, "_run", return_value=(0, "alpha: new", "")):
                    digest = self.module.check_orca_skills()["pending_digest"]
                self.module.ack_skills(digest)
                with self.assertRaises(ValueError):
                    self.module.ack_skills(digest)

    def test_new_pending_generation_prevents_same_second_aba_ack(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "SimonKStack" / "vibe" / "orca-skills.json"
            self.module._write_snapshot(str(snapshot), {"alpha": "old"}, {})
            listings = [(0, "alpha: new", ""), (0, "alpha: old", ""),
                        (0, "alpha: new", "")]
            with mock.patch.dict(os.environ, _state_env(root)):
                with mock.patch.object(self.module.time, "strftime",
                                       return_value="2026-10-01T14:40:00"):
                    with mock.patch.object(self.module, "_run", side_effect=listings):
                        first = self.module.check_orca_skills()
                        self.module.ack_skills(first["pending_digest"])
                        self.module.check_orca_skills()
                        second = self.module.check_orca_skills()
                self.assertNotEqual(first["pending_digest"], second["pending_digest"])
                with self.assertRaises(ValueError):
                    self.module.ack_skills(first["pending_digest"])

    def test_legacy_pending_receives_generation_on_next_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "SimonKStack" / "vibe" / "orca-skills.json"
            snapshot.parent.mkdir(parents=True)
            snapshot.write_text(json.dumps({
                "skills": {"alpha": "new"},
                "pending": {"first_seen": "2026-09-30T12:00:00", "seen_count": 1,
                            "added": [], "removed": [], "changed": ["alpha"]}}),
                encoding="utf-8")
            with mock.patch.dict(os.environ, _state_env(root)):
                with mock.patch.object(self.module, "_run", return_value=(0, "alpha: new", "")):
                    result = self.module.check_orca_skills()
                self.assertEqual(result["state"], "미확인 변경")
                self.assertRegex(result["pending_digest"], r"^[a-f0-9]{64}$")
                self.assertIn("확인 처리", self.module.ack_skills(result["pending_digest"]))
            self.assertEqual(json.loads(snapshot.read_text(encoding="utf-8"))["pending"], {})

    def test_report_unknown_state_is_not_a_successful_preflight(self):
        with mock.patch.object(self.module, "check_clis", return_value=[]):
            with mock.patch.object(self.module, "check_orca_skills", return_value={
                    "state": self.module.UNKNOWN, "detail": "lock unavailable",
                    "added": [], "removed": [], "changed": []}):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(self.module.report(as_json=True), 1)

    def test_late_old_listing_cannot_replace_newer_serialized_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "SimonKStack" / "vibe" / "orca-skills.json"
            self.module._write_snapshot(str(snapshot), {"alpha": "old"}, {})
            first_listing = threading.Event()
            second_done = threading.Event()

            def listing(*_args, **_kwargs):
                if threading.current_thread().name == "first":
                    first_listing.set()
                    second_done.wait(0.5)
                    return 0, "alpha: old", ""
                return 0, "alpha: new", ""

            def report():
                self.module.check_orca_skills()
                if threading.current_thread().name == "second":
                    second_done.set()

            with mock.patch.dict(os.environ, _state_env(root)):
                with mock.patch.object(self.module, "_run", side_effect=listing):
                    first = threading.Thread(target=report, name="first")
                    second = threading.Thread(target=report, name="second")
                    first.start()
                    self.assertTrue(first_listing.wait(2))
                    second.start()
                    first.join(3)
                    second.join(3)
            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertEqual(json.loads(snapshot.read_text(encoding="utf-8"))["skills"],
                             {"alpha": "new"})

    def test_migration_cannot_publish_between_report_absence_check_and_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            legacy = root / "legacy.json"
            legacy.write_text(json.dumps({"skills": {"alpha": "legacy"}, "pending": {}}),
                              encoding="utf-8")
            snapshot = root / "host-state" / "SimonKStack" / "vibe" / "orca-skills.json"
            report_writing = threading.Event()
            migration_done = threading.Event()
            original_write = self.module._write_snapshot
            results = {}

            def delayed_write(*args, **kwargs):
                if threading.current_thread().name == "report":
                    report_writing.set()
                    migration_done.wait(0.5)
                return original_write(*args, **kwargs)

            def report():
                results["report"] = self.module.check_orca_skills()

            def migrate():
                results["migration"] = self.module.migrate_snapshot(str(legacy))
                migration_done.set()

            with mock.patch.dict(os.environ, _state_env(root / "host-state")):
                with mock.patch.object(self.module, "_run", return_value=(0, "alpha: current", "")):
                    with mock.patch.object(self.module, "_write_snapshot", side_effect=delayed_write):
                        first = threading.Thread(target=report, name="report")
                        second = threading.Thread(target=migrate, name="migration")
                        first.start()
                        self.assertTrue(report_writing.wait(2))
                        second.start()
                        first.join(3)
                        second.join(3)
            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertEqual(results["migration"], 1)
            self.assertEqual(results["report"]["state"], "스냅샷 생성")
            self.assertEqual(json.loads(snapshot.read_text(encoding="utf-8"))["skills"],
                             {"alpha": "current"})
            self.assertEqual(json.loads(legacy.read_text(encoding="utf-8"))["skills"],
                             {"alpha": "legacy"})

    def test_lock_excludes_a_separate_process(self):
        with tempfile.TemporaryDirectory() as temporary:
            snapshot = Path(temporary) / "orca-skills.json"
            child_code = """
import importlib.util
import sys
spec = importlib.util.spec_from_file_location('check_tooling_child', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with module._snapshot_lock(sys.argv[2]):
    print('LOCKED', flush=True)
    sys.stdin.readline()
"""
            child = subprocess.Popen([sys.executable, "-B", "-c", child_code,
                                      str(SCRIPT), str(snapshot)], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True, encoding="utf-8")
            try:
                self.assertEqual(child.stdout.readline().strip(), "LOCKED")
                acquired = threading.Event()

                def contender():
                    with self.module._snapshot_lock(str(snapshot)):
                        acquired.set()

                thread = threading.Thread(target=contender, daemon=True)
                thread.start()
                self.assertFalse(acquired.wait(0.15))
                child.stdin.write("release\n")
                child.stdin.flush()
                self.assertEqual(child.wait(timeout=3), 0)
                thread.join(3)
                self.assertTrue(acquired.is_set())
            finally:
                if child.poll() is None:
                    child.stdin.write("release\n")
                    child.stdin.flush()
                    child.wait(timeout=3)
                child.stdin.close()
                child.stdout.close()
                child.stderr.close()

    def test_legacy_snapshot_migration_preserves_source_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            legacy = root / "old-bundle" / "state" / "orca-skills.json"
            legacy.parent.mkdir(parents=True)
            legacy.write_text(json.dumps({"generated_at": "2026-10-01T00:00:00",
                                          "skills": {"alpha": "first"}, "pending": {}}),
                              encoding="utf-8")
            original_hash = hashlib.sha256(legacy.read_bytes()).hexdigest()
            with mock.patch.dict(os.environ, _state_env(root / "host-state")):
                first = self.module.migrate_snapshot(str(legacy))
                second = self.module.migrate_snapshot(str(legacy))
            target = root / "host-state" / "SimonKStack" / "vibe" / "orca-skills.json"
            self.assertEqual(first, 0)
            self.assertEqual(second, 1)
            self.assertEqual(legacy.read_bytes(), target.read_bytes())
            self.assertEqual(hashlib.sha256(legacy.read_bytes()).hexdigest(), original_hash)

    def test_snapshot_refuses_state_root_inside_signed_skill(self):
        with tempfile.TemporaryDirectory() as temporary:
            skill = Path(temporary) / "signed-skill"
            with mock.patch.dict(os.environ, _state_env(skill / "state")):
                with mock.patch.object(self.module, "SKILL_ROOT", str(skill)):
                    with mock.patch.object(self.module, "_run", return_value=(0, "alpha: first", "")):
                        result = self.module.check_orca_skills()
            self.assertEqual(result["state"], self.module.UNKNOWN)
            self.assertFalse(skill.exists())

    def test_invalid_existing_snapshot_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "SimonKStack" / "vibe" / "orca-skills.json"
            snapshot.parent.mkdir(parents=True)
            snapshot.write_text("{broken", encoding="utf-8")
            with mock.patch.dict(os.environ, _state_env(root)):
                with mock.patch.object(self.module, "_run", return_value=(0, "alpha: first", "")):
                    result = self.module.check_orca_skills()
            self.assertEqual(result["state"], self.module.UNKNOWN)
            self.assertEqual(snapshot.read_text(encoding="utf-8"), "{broken")

    def test_migration_publish_failure_leaves_no_partial_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            legacy = root / "legacy.json"
            legacy.write_text(json.dumps({"skills": {"alpha": "first"}, "pending": {}}),
                              encoding="utf-8")
            target_dir = root / "host-state" / "SimonKStack" / "vibe"
            with mock.patch.dict(os.environ, _state_env(root / "host-state")):
                with mock.patch.object(self.module.os, "link", side_effect=OSError("denied")):
                    result = self.module.migrate_snapshot(str(legacy))
            self.assertEqual(result, 1)
            self.assertFalse((target_dir / "orca-skills.json").exists())
            self.assertEqual(list(target_dir.glob(".orca-skills-*")), [])


if __name__ == "__main__":
    unittest.main()
