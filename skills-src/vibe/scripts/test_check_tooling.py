"""Offline checks for a stale Codex PATH shim; no Orca or npm access."""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("check_tooling.py")
ROUTING = SCRIPT.with_name("routing.py")


class CodexPathChecks(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("check_tooling", SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

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


if __name__ == "__main__":
    unittest.main()
