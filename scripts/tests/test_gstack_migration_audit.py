"""Read-only migration audit preserves host and local policy distinctions."""

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("gstack_migration_audit", ROOT / "scripts/gstack_migration_audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class GstackMigrationAuditTests(unittest.TestCase):
    def test_declared_name_requires_single_frontmatter_name(self):
        self.assertEqual(audit.declared_name("---\nname: qa\n---\n## QA\n"), "qa")
        for body in ("name: qa\n", "---\nname: qa\nname: ship\n---\n",
                     "---\nname: ../qa\n---\n"):
            with self.subTest(body=body), self.assertRaises(ValueError):
                audit.declared_name(body)

    def test_generated_index_uses_declared_names_not_folder_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            claude = root / "qa"
            codex = root / ".agents" / "skills" / "gstack-qa"
            special = root / ".agents" / "skills" / "gstack-upgrade"
            for folder, name in ((claude, "qa"), (codex, "qa"), (special, "gstack-upgrade")):
                folder.mkdir(parents=True)
                (folder / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
            self.assertEqual(set(audit.generated_index(root, "claude")), {"qa"})
            self.assertEqual(set(audit.generated_index(root, "codex")), {"qa", "gstack-upgrade"})

    def test_generated_duplicate_names_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for folder in (root / "qa", root / "gstack-qa"):
                folder.mkdir()
                (folder / "SKILL.md").write_text("---\nname: qa\n---\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate generated"):
                audit.generated_index(root, "claude")

    def test_generated_digest_changes_with_document_bytes(self):
        first = audit.generated_digest({"qa": ("qa/SKILL.md", "---\nname: qa\n---\n")})
        second = audit.generated_digest({"qa": ("qa/SKILL.md", "---\nname: qa\n---\n## Updated\n")})
        moved = audit.generated_digest({"qa": ("gstack-qa/SKILL.md", "---\nname: qa\n---\n")})
        self.assertEqual(len(first), 64)
        self.assertNotEqual(first, second)
        self.assertNotEqual(first, moved)

    def test_generated_root_link_counter_finds_forward_and_backslash_paths(self):
        docs = {
            "qa": ("qa/SKILL.md", "Read E:/probe/qa/sections/start.md\n"),
            "ship": ("ship/SKILL.md", "Read E:\\probe\\ship\\sections\\end.md\n"),
            "review": ("review/SKILL.md", "No local link\n"),
        }
        self.assertEqual(audit.generated_root_links(docs, Path("E:/probe")),
                         {"skills": 2, "occurrences": 2})

    def test_compare_pair_reports_missing_policy_and_format_without_claiming_failure(self):
        legacy = ("---\nname: investigate\n---\n"
                  "## Skill routing\n## Candidate session scope commands\n"
                  "## 완료 보고 (HTML) — 표준\n")
        generated = "---\nname: investigate\n---\n" + "## Modern\n" * 501
        result = audit.compare_pair("investigate", legacy, generated)
        self.assertEqual(result["policy_gaps"], ["skill_routing", "session_scope", "completion_report"])
        self.assertTrue(result["body_over_500_lines"])
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(audit.compare_pair("investigate", legacy, None)["status"], "missing_generated")

    def test_audit_verifies_receipt_before_candidate_reads(self):
        with patch.object(audit.plugin_bundle, "verify_bundle", side_effect=ValueError("bad receipt")), \
             patch.object(audit.release, "read_file") as read_file:
            with self.assertRaises(ValueError):
                audit.audit_candidate(Path("package"), "0" * 64, Path("generated"))
            read_file.assert_not_called()

    def test_audit_reports_host_mapping_gaps_from_verified_candidate(self):
        skill = "plugins/SimonKStack/skills/qa/SKILL.md"
        body = ("---\nname: qa\n---\n## 완료 보고 (HTML) — 표준\n"
                "~/.claude/skills/gstack/bin/gstack-skill-start\n").encode()
        receipt = {"files": [{"path": skill, "size": len(body),
                              "sha256": audit.release.digest(body)}]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = source / skill
            target.parent.mkdir(parents=True)
            target.write_bytes(body)
            generated = root / "generated"
            (generated / "qa").mkdir(parents=True)
            (generated / "qa" / "SKILL.md").write_text(
                "---\nname: qa\n---\n## Modern\n", encoding="utf-8")
            with patch.object(audit.plugin_bundle, "verify_bundle", return_value=receipt):
                report = audit.audit_candidate(source, "0" * 64, generated)
        self.assertEqual(report["skills_checked"], 1)
        self.assertEqual(report["matched"], {"claude": 1, "codex": 0})
        self.assertEqual(report["missing"], {"claude": [], "codex": ["qa"]})
        self.assertEqual(report["policy_gap_counts"]["completion_report"], 1)
        self.assertEqual(report["status"], "migration_review_required")
        self.assertFalse(report["runtime_closure_verified"])

    def test_absolute_generated_root_link_prevents_static_mapping_pass(self):
        skill = "plugins/SimonKStack/skills/qa/SKILL.md"
        body = b"---\nname: qa\n---\n~/.claude/skills/gstack/bin/gstack-skill-start\n"
        receipt = {"files": [{"path": skill, "size": len(body),
                              "sha256": audit.release.digest(body)}]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = source / skill
            target.parent.mkdir(parents=True)
            target.write_bytes(body)
            generated = root / "generated"
            (generated / "qa").mkdir(parents=True)
            (generated / ".agents" / "skills" / "gstack-qa").mkdir(parents=True)
            (generated / "qa" / "SKILL.md").write_text(
                f"---\nname: qa\n---\nRead {generated.as_posix()}/qa/sections/demo.md\n",
                encoding="utf-8")
            (generated / ".agents" / "skills" / "gstack-qa" / "SKILL.md").write_text(
                "---\nname: qa\n---\nNo absolute generated root\n", encoding="utf-8")
            with patch.object(audit.plugin_bundle, "verify_bundle", return_value=receipt):
                report = audit.audit_candidate(source, "0" * 64, generated)
        self.assertEqual(report["generated_root_links"]["claude"],
                         {"skills": 1, "occurrences": 1})
        self.assertEqual(report["generated_root_links"]["codex"],
                         {"skills": 0, "occurrences": 0})
        self.assertEqual(report["status"], "migration_review_required")

    def test_empty_legacy_set_is_not_a_migration_pass(self):
        skill = "plugins/SimonKStack/skills/qa/SKILL.md"
        body = b"---\nname: qa\n---\n## QA\n"
        receipt = {"files": [{"path": skill, "size": len(body),
                              "sha256": audit.release.digest(body)}]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = source / skill
            target.parent.mkdir(parents=True)
            target.write_bytes(body)
            generated = root / "generated"
            generated.mkdir()
            with patch.object(audit.plugin_bundle, "verify_bundle", return_value=receipt):
                report = audit.audit_candidate(source, "0" * 64, generated)
        self.assertEqual(report["status"], "no_legacy_gstack_refs")
        self.assertEqual(report["skills_checked"], 0)
        self.assertFalse(report["runtime_closure_verified"])

    def test_wrong_generated_digest_blocks_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generated = root / "generated"
            (generated / "qa").mkdir(parents=True)
            (generated / "qa" / "SKILL.md").write_text(
                "---\nname: qa\n---\n", encoding="utf-8")
            with patch.object(audit.plugin_bundle, "verify_bundle", return_value={"files": []}):
                with self.assertRaisesRegex(ValueError, "Generated document digest mismatch"):
                    audit.audit_candidate(root / "package", "0" * 64, generated,
                                          {"claude": "0" * 64, "codex": "0" * 64})


if __name__ == "__main__":
    unittest.main()
