"""Flat-skill migration audit reads only explicit direct directories."""

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_flat_skill_packages as audit


class FlatSkillPackageAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="flat-skill-audit-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.bundle = self.base / "bundle"
        self.bundle.mkdir()
        self.root = self.base / "installed"
        self.root.mkdir()
        self.skill = self.root / "sample"
        self.skill.mkdir()
        (self.skill / "SKILL.md").write_bytes(b"name: sample\n")
        (self.skill / "references").mkdir()
        (self.skill / "references" / "guide.md").write_bytes(b"guide\n")
        self.manifest = {
            "owners": {"sample": "SimonKCore"},
            "files": [
                {"path": "plugins/SimonKCore/skills/sample/SKILL.md",
                 "sha256": audit.release.digest(b"name: sample\n")},
                {"path": "plugins/SimonKCore/skills/sample/references/guide.md",
                 "sha256": audit.release.digest(b"guide\n")},
            ],
        }

    def run_audit(self, *, excluded=()):
        with patch.object(audit.plugin_bundle, "verify_bundle", return_value=self.manifest) as verify:
            result = audit.audit(self.bundle, "a" * 64, [self.root], excluded)
        verify.assert_called_once_with(self.bundle, "a" * 64)
        return result

    def test_full_package_match_including_reference(self):
        result = self.run_audit()
        self.assertEqual(result["summary"]["matched"], 1)
        row = result["rows"][0]
        self.assertEqual(row["status"], "matched")
        self.assertEqual(row["files"], 2)
        self.assertEqual(row["changed"], [])

    def test_added_removed_and_changed_members_are_separate(self):
        (self.skill / "SKILL.md").write_bytes(b"name: altered\n")
        (self.skill / "references" / "guide.md").unlink()
        (self.skill / "local.txt").write_bytes(b"keep me")
        row = self.run_audit()["rows"][0]
        self.assertEqual(row["status"], "drifted")
        self.assertEqual(row["changed"], ["SKILL.md"])
        self.assertEqual(row["missing_files"], ["references/guide.md"])
        self.assertEqual(row["extra_files"], ["local.txt"])
        self.assertNotIn("keep me", repr(row))

    def test_link_is_reported_without_reading_its_target(self):
        target = self.base / "sensitive"
        target.mkdir()
        (target / "SKILL.md").write_bytes(b"secret-content")
        for item in (self.skill / "references" / "guide.md", self.skill / "SKILL.md"):
            item.unlink()
        (self.skill / "references").rmdir()
        self.skill.rmdir()
        try:
            os.symlink(target, self.skill, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlink unavailable: {exc}")
        with patch.object(audit.release, "read_file", side_effect=AssertionError("target read")):
            report = self.run_audit()
        row = report["rows"][0]
        self.assertEqual(row["status"], "linked_preserved")
        self.assertFalse(report["package_evaluated"])
        self.assertNotIn("secret-content", repr(row))

    def test_excluded_direct_skill_is_not_read(self):
        with patch.object(audit.release, "read_file", side_effect=AssertionError("excluded read")):
            row = self.run_audit(excluded=[self.skill])["rows"][0]
        self.assertEqual(row["status"], "excluded")

    def test_unrelated_installed_skill_is_not_scanned(self):
        unrelated = self.root / "unrelated"
        unrelated.mkdir()
        (unrelated / "SKILL.md").write_bytes(b"private")
        result = self.run_audit()
        self.assertEqual([row["name"] for row in result["rows"]], ["sample"])
        self.assertFalse(result["unrelated_skills_read"])

    def test_nested_link_fails_closed(self):
        other = self.base / "outside.txt"
        other.write_bytes(b"secret")
        link = self.skill / "references" / "outside.txt"
        try:
            os.symlink(other, link)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlink unavailable: {exc}")
        row = self.run_audit()["rows"][0]
        self.assertEqual(row["status"], "unsafe")
        self.assertNotIn("secret", repr(row))

    def test_excessive_directory_entries_fail_closed(self):
        (self.skill / "empty").mkdir()
        with patch.object(audit, "MAX_SKILL_ENTRIES", 2):
            row = self.run_audit()["rows"][0]
        self.assertEqual(row["status"], "unsafe")
        self.assertEqual(row["reason"], "ValueError")


if __name__ == "__main__":
    unittest.main()
