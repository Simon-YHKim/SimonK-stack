"""Read-only host topology checks for a staged /vibe candidate."""

import os
import json
import io
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import vibe_host_preflight as preflight


class DirectoryLinkCompatibilityTests(unittest.TestCase):
    def test_windows_junction_tag_is_recognized_without_path_is_junction(self):
        class Junction:
            def lstat(self):
                return SimpleNamespace(st_mode=stat.S_IFDIR,
                                       st_reparse_tag=0xA0000003)

        self.assertTrue(preflight._is_directory_link(Junction()))

    @unittest.skipUnless(os.name == "nt", "Windows junction fixture")
    def test_real_windows_junction_is_recognized(self):
        with tempfile.TemporaryDirectory(prefix="vibe-junction-") as temporary:
            root = Path(temporary)
            target = root / "target"
            target.mkdir()
            link = root / "link"
            subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                           check=True, capture_output=True, text=True)
            self.assertTrue(preflight._is_directory_link(link))
            self.assertEqual(preflight._direct_target(link), target)


class VibeHostPreflightTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="vibe-host-preflight-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.candidate = self.root / "candidate"
        self.old_candidate = self.root / "old-candidate"
        self.claude = self.root / "claude"
        self.codex = self.root / "codex"
        self.agents = self.root / "agents"
        for host, names, package in (
            (self.claude, preflight.CLAUDE_NAMES, "candidate-safety"),
            (self.codex, preflight.CODEX_NAMES, "codex-subset-safety"),
        ):
            (host / "skills").mkdir(parents=True)
            for name in names:
                source = self.candidate / package / "plugins/SimonKCore/skills" / name
                source.mkdir(parents=True)
                (source / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: Candidate {name}\n---\ncandidate {name}\n",
                    encoding="utf-8")
                old = self.old_candidate / package / "plugins/SimonKCore/skills" / name
                old.mkdir(parents=True)
                (old / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: Installed {name}\n---\ninstalled {name}\n",
                    encoding="utf-8")
                try:
                    os.symlink(old, host / "skills" / name, target_is_directory=True)
                except OSError as exc:
                    self.fail(f"directory symlinks unavailable: {exc}")
        for package in ("candidate-safety", "codex-subset-safety"):
            for plugin in ("SimonKCore", "SimonKDesign", "SimonKStack", "SimonKMarket", "SimonKAIHub"):
                plugin_root = self.candidate / package / "plugins" / plugin
                (plugin_root / "skills").mkdir(parents=True, exist_ok=True)
                manifest = plugin_root / ".claude-plugin/plugin.json"
                manifest.parent.mkdir(parents=True)
                manifest.write_text(json.dumps({"name": plugin.lower(), "version": "0.3.0-test"}),
                                    encoding="utf-8")
                if package == "codex-subset-safety":
                    codex_manifest = plugin_root / ".codex-plugin/plugin.json"
                    codex_manifest.parent.mkdir(parents=True)
                    codex_manifest.write_text(json.dumps({"name": plugin.lower(),
                                                          "version": "0.3.0-test"}),
                                              encoding="utf-8")
        (self.agents / "skills").mkdir(parents=True)
        os.symlink(self.claude / "skills" / "vibe",
                   self.agents / "skills" / "vibe", target_is_directory=True)

    def scan(self):
        return preflight.scan(self.candidate, self.old_candidate,
                              self.claude, self.codex, self.agents)

    def native_snapshot(self, enabled=True):
        names = [name.lower() for name in preflight.PLUGIN_NAMES]
        return {
            "claude": [{"id": f"{name}@{name}", "version": "0.3.0-test",
                        "enabled": enabled} for name in names],
            "codex": {"installed": [{"pluginId": f"{name}@{name}",
                                      "version": "0.3.0-test", "installed": True,
                                      "enabled": enabled} for name in names],
                      "available": []},
        }

    def test_native_plugin_snapshot_reports_all_five_missing_on_both_hosts(self):
        report = preflight.scan(self.candidate, self.old_candidate, self.claude,
                                self.codex, self.agents,
                                native_snapshot={"claude": [], "codex": {"installed": [], "available": []}})
        self.assertEqual(report["native_plugin_coverage"]["claude"]["missing"], 5)
        self.assertEqual(report["native_plugin_coverage"]["codex"]["missing"], 5)
        self.assertEqual(report["rollout_gate"], "blocked")

    def test_native_plugin_metadata_match_is_not_installation_approval(self):
        report = preflight.scan(self.candidate, self.old_candidate, self.claude,
                                self.codex, self.agents, native_snapshot=self.native_snapshot())
        self.assertEqual(report["native_plugin_coverage"]["claude"]["matched"], 5)
        self.assertEqual(report["native_plugin_coverage"]["codex"]["matched"], 5)
        self.assertFalse(report["full_skill_set_verified"])
        self.assertFalse(report["installation_ready"])

    def test_codex_registry_is_compared_with_codex_manifest_version(self):
        manifest = (self.candidate / "codex-subset-safety/plugins/SimonKCore/"
                    ".codex-plugin/plugin.json")
        manifest.write_text(json.dumps({"name": "simonkcore", "version": "0.4.0-codex"}),
                            encoding="utf-8")
        snapshot = self.native_snapshot()
        snapshot["codex"]["installed"][0]["version"] = "0.4.0-codex"
        report = preflight.scan(self.candidate, self.old_candidate, self.claude,
                                self.codex, self.agents, native_snapshot=snapshot)
        self.assertEqual(report["native_plugin_coverage"]["codex"]["matched"], 5)

    def test_disabled_and_duplicate_native_entries_fail_closed(self):
        disabled = preflight.scan(self.candidate, self.old_candidate, self.claude,
                                  self.codex, self.agents,
                                  native_snapshot=self.native_snapshot(enabled=False))
        self.assertEqual(disabled["native_plugin_coverage"]["claude"]["disabled"], 5)
        self.assertEqual(disabled["native_plugin_coverage"]["codex"]["disabled"], 5)
        duplicate = self.native_snapshot()
        duplicate["claude"].append(dict(duplicate["claude"][0]))
        report = preflight.scan(self.candidate, self.old_candidate, self.claude,
                                self.codex, self.agents, native_snapshot=duplicate)
        self.assertEqual(report["native_plugin_coverage"]["claude"]["ambiguous"], 1)
        self.assertEqual(report["rollout_gate"], "blocked")

    def test_version_drift_and_wrong_marketplace_are_not_matches(self):
        snapshot = self.native_snapshot()
        snapshot["claude"][0]["version"] = "0.2.0-old"
        snapshot["codex"]["installed"][0]["pluginId"] = "simonkcore@untrusted-marketplace"
        report = preflight.scan(self.candidate, self.old_candidate, self.claude,
                                self.codex, self.agents, native_snapshot=snapshot)
        self.assertEqual(report["native_plugin_coverage"]["claude"]["drifted"], 1)
        self.assertEqual(report["native_plugin_coverage"]["codex"]["missing"], 1)
        self.assertFalse(report["installation_ready"])

    def test_malformed_native_snapshot_blocks_even_when_links_are_valid(self):
        report = preflight.scan(self.candidate, self.old_candidate, self.claude,
                                self.codex, self.agents,
                                native_snapshot={"claude": [], "codex": ["not-a-registry"]})
        self.assertEqual(report["status"], "blocked")
        self.assertIn("NATIVE_SNAPSHOT_INVALID", report["issues"])
        self.assertEqual(report["native_plugin_coverage"]["status"], "invalid_snapshot")

    def test_non_object_native_manifest_blocks_with_json_result(self):
        manifest = (self.candidate / "candidate-safety/plugins/SimonKCore/"
                    ".claude-plugin/plugin.json")
        manifest.write_text("[]", encoding="utf-8")
        report = self.scan_with_native_snapshot()
        self.assertEqual(report["status"], "blocked")
        self.assertIn("NATIVE_SNAPSHOT_INVALID", report["issues"])

    def scan_with_native_snapshot(self):
        return preflight.scan(self.candidate, self.old_candidate, self.claude,
                              self.codex, self.agents,
                              native_snapshot=self.native_snapshot())

    def test_explicit_null_native_stdin_cannot_be_treated_as_unobserved(self):
        argv = ["--candidate-root", str(self.candidate), "--expected-current-root",
                str(self.old_candidate), "--claude-root", str(self.claude),
                "--codex-root", str(self.codex), "--agents-root", str(self.agents),
                "--native-json-stdin"]
        output = io.StringIO()
        with patch.object(sys, "stdin", io.StringIO("null")), redirect_stdout(output):
            code = preflight.main(argv)
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "blocked")

    def test_valid_old_links_are_snapshotted_without_install_approval(self):
        report = self.scan()
        self.assertEqual(report["status"], "host_snapshot_complete", report)
        self.assertEqual(report["checked_links"], 8)
        self.assertEqual(report["different_skills"], 7)
        self.assertEqual(report["scope"], "seven_flat_core_links_and_one_agents_alias")
        self.assertFalse(report["full_skill_set_verified"])
        self.assertEqual(report["rollout_gate"], "blocked")
        self.assertEqual(report["flat_coverage"]["claude"]["drifted"], 5)
        self.assertEqual(report["flat_coverage"]["codex"]["drifted"], 2)
        self.assertFalse(report["installation_ready"])
        self.assertFalse(report["profile_changed"])
        self.assertFalse(report["candidate_bytes_verified"])
        self.assertTrue((self.claude / "skills/vibe/SKILL.md").read_text().endswith(
            "installed vibe\n"))

    def test_report_does_not_expose_profile_or_candidate_paths(self):
        report = self.scan_with_native_snapshot()

        def strings(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    yield key
                    yield from strings(item)
            elif isinstance(value, list):
                for item in value:
                    yield from strings(item)
            elif isinstance(value, str):
                yield value

        report_values = "\n".join(strings(report))
        for root in (self.candidate, self.old_candidate, self.claude,
                     self.codex, self.agents):
            self.assertNotIn(str(root), report_values)

    def test_ordinary_skill_directory_is_rejected(self):
        link = self.claude / "skills" / "vibe"
        link.unlink()
        link.mkdir()
        (link / "SKILL.md").write_text("user owned\n", encoding="utf-8")
        report = self.scan()
        self.assertEqual(report["status"], "blocked")
        self.assertIn("NOT_LINK", report["issues"])

    def test_alias_must_point_to_claude_flat_skill(self):
        alias = self.agents / "skills" / "vibe"
        alias.unlink()
        os.symlink(self.codex / "skills" / "vibe", alias, target_is_directory=True)
        report = self.scan()
        self.assertEqual(report["status"], "blocked")
        self.assertIn("ALIAS_TARGET_MISMATCH", report["issues"])

    def test_link_to_unexpected_old_candidate_is_rejected(self):
        link = self.codex / "skills" / "vibe"
        link.unlink()
        unexpected = self.root / "unexpected" / "vibe"
        unexpected.mkdir(parents=True)
        (unexpected / "SKILL.md").write_text("old but unknown\n", encoding="utf-8")
        os.symlink(unexpected, link, target_is_directory=True)
        report = self.scan()
        self.assertEqual(report["status"], "blocked")
        self.assertIn("LINK_TARGET_MISMATCH", report["issues"])

    def test_missing_candidate_file_blocks_snapshot(self):
        missing = self.candidate / "candidate-safety/plugins/SimonKCore/skills/vibe/SKILL.md"
        missing.unlink()
        report = self.scan()
        self.assertEqual(report["status"], "blocked")
        self.assertIn("CANDIDATE_SKILL_MISSING", report["issues"])

    def test_flat_metadata_match_does_not_authorize_installation(self):
        for host, names, package in (
            (self.claude, preflight.CLAUDE_NAMES, "candidate-safety"),
            (self.codex, preflight.CODEX_NAMES, "codex-subset-safety"),
        ):
            for name in names:
                candidate = self.candidate / package / "plugins/SimonKCore/skills" / name / "SKILL.md"
                shutil.copyfile(candidate, self.old_candidate / package /
                                "plugins/SimonKCore/skills" / name / "SKILL.md")
        report = self.scan()
        self.assertEqual(report["flat_coverage"]["claude"]["matched"], 5)
        self.assertEqual(report["flat_coverage"]["codex"]["matched"], 2)
        self.assertEqual(report["rollout_gate"], "blocked")
        self.assertFalse(report["full_skill_set_verified"])

    def test_partial_candidate_pins_fail_before_host_scan(self):
        report = preflight.scan(self.candidate, self.old_candidate,
                                self.claude, self.codex, self.agents,
                                candidate_pins={"source": "a" * 64})
        self.assertEqual(report["status"], "blocked")
        self.assertIn("CANDIDATE_VERIFICATION_FAILED", report["issues"])
        self.assertFalse(report["candidate_bytes_verified"])
        self.assertFalse(report["profile_changed"])

    def test_verified_candidate_bytes_do_not_authorize_installation(self):
        pins = {name: char * 64 for name, char in (
            ("source", "a"), ("candidate-safety", "b"),
            ("codex-overlay-safety", "c"), ("codex-subset-safety", "d"))}
        with patch.object(preflight, "_verify_candidate_receipts",
                          return_value={"status": "verified", "packages": 4}):
            report = preflight.scan(self.candidate, self.old_candidate,
                                    self.claude, self.codex, self.agents,
                                    candidate_pins=pins)
        self.assertTrue(report["candidate_bytes_verified"])
        self.assertEqual(report["candidate_verification"]["packages"], 4)
        self.assertFalse(report["installation_ready"])
        self.assertEqual(report["rollout_gate"], "blocked")

    def test_four_receipts_and_provenance_must_match_the_supplied_pins(self):
        pins = {name: char * 64 for name, char in (
            ("source", "a"), ("candidate-safety", "b"),
            ("codex-overlay-safety", "c"), ("codex-subset-safety", "d"))}
        with (patch("skill_release.verify_release") as source,
              patch("plugin_bundle.verify_bundle") as claude,
              patch("codex_overlay.verify_overlay") as overlay,
              patch("codex_safe_subset.verify_subset") as subset):
            claude.return_value = {"source_digest": pins["source"]}
            overlay.return_value = {"candidate_digest": pins["candidate-safety"]}
            subset.return_value = {"source_overlay_digest": pins["codex-overlay-safety"]}
            result = preflight._verify_candidate_receipts(self.candidate, pins)
            self.assertEqual(result, {"status": "verified", "packages": 4})
            source.assert_called_once_with(self.candidate / "source", pins["source"])
            claude.assert_called_once_with(self.candidate / "candidate-safety",
                                           pins["candidate-safety"])
            overlay.assert_called_once_with(self.candidate / "codex-overlay-safety",
                                            pins["codex-overlay-safety"])
            subset.assert_called_once_with(
                self.candidate / "codex-subset-safety", pins["codex-subset-safety"],
                source=self.candidate / "codex-overlay-safety",
                source_digest=pins["codex-overlay-safety"])

            overlay.return_value = {"candidate_digest": "e" * 64}
            self.assertEqual(preflight._verify_candidate_receipts(self.candidate, pins)["status"],
                             "invalid")
            overlay.return_value = {"candidate_digest": pins["candidate-safety"]}
            claude.side_effect = ValueError("tampered bytes")
            self.assertEqual(preflight._verify_candidate_receipts(self.candidate, pins)["status"],
                             "invalid")

    def test_invalid_candidate_bytes_stop_before_host_inventory(self):
        pins = {name: char * 64 for name, char in (
            ("source", "a"), ("candidate-safety", "b"),
            ("codex-overlay-safety", "c"), ("codex-subset-safety", "d"))}
        with (patch("skill_release.verify_release", side_effect=ValueError("tampered")),
              patch.object(preflight, "_flat_coverage", side_effect=AssertionError("host read"))):
            report = preflight.scan(self.candidate, self.old_candidate,
                                    self.claude, self.codex, self.agents,
                                    candidate_pins=pins)
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["issues"], ["CANDIDATE_VERIFICATION_FAILED"])
        self.assertFalse(report["profile_changed"])

    def test_unavailable_local_verifier_fails_closed(self):
        pins = {name: char * 64 for name, char in (
            ("source", "a"), ("candidate-safety", "b"),
            ("codex-overlay-safety", "c"), ("codex-subset-safety", "d"))}
        with patch.dict(sys.modules, {"skill_release": None}):
            result = preflight._verify_candidate_receipts(self.candidate, pins)
        self.assertEqual(result, {"status": "invalid", "packages": 0})


if __name__ == "__main__":
    unittest.main()
