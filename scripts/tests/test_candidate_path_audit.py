"""The candidate path audit is a conservative, read-only static check."""

import importlib.util
from contextlib import redirect_stderr
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("candidate_path_audit", ROOT / "scripts/candidate_path_audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class CandidatePathAuditTests(unittest.TestCase):
    def test_source_checkout_commands_are_reported_without_command_text(self):
        skill = "plugins/SimonKCore/skills/example/SKILL.md"
        text = ("Run `bash skills-src/example/scripts/run.sh --token SENSITIVE`.\n"
                "bash ./skills-src/example/scripts/check.sh\n"
                "python -B -m unittest discover -s skills-src/vibe/scripts\n")
        rows = audit.inspect_unportable_commands(skill, text)
        self.assertEqual(rows, [
            {"skill": skill, "line": 1, "reason": "source_checkout_command"},
            {"skill": skill, "line": 2, "reason": "source_checkout_command"},
            {"skill": skill, "line": 3, "reason": "source_checkout_command"},
        ])
        self.assertNotIn("SENSITIVE", repr(rows))

    def test_explicit_source_repo_placeholder_and_prose_are_not_runtime_commands(self):
        skill = "plugins/SimonKCore/skills/example/SKILL.md"
        text = ("Do not assume `skills-src/` exists.\n"
                "python -m unittest discover -s '<stack-source-root>/skills-src/vibe/scripts'\n")
        self.assertEqual(audit.inspect_unportable_commands(skill, text), [])

    def test_project_relative_skill_commands_are_reported(self):
        skill = "plugins/SimonKStack/skills/data-retention-planner/SKILL.md"
        text = ("bash skills/data-retention-planner/scripts/scan-retention.sh\n"
                "node ./skills/data-retention-planner/scripts/gen-purge-plan.mjs\n"
                "bash '<skill-dir>/scripts/scan-retention.sh'\n")
        self.assertEqual(audit.inspect_unportable_commands(skill, text), [
            {"skill": skill, "line": 1, "reason": "project_relative_skill_command"},
            {"skill": skill, "line": 2, "reason": "project_relative_skill_command"},
        ])

    def test_verified_candidate_includes_unportable_command_findings(self):
        skill = "plugins/SimonKCore/skills/example/SKILL.md"
        body = b"bash skills-src/example/scripts/run.sh\n"
        receipt = {"files": [{"path": skill, "size": len(body),
                              "sha256": audit.release.digest(body)}]}
        with patch.object(audit.release, "no_links", side_effect=lambda path: path), \
             patch.object(audit.plugin_bundle, "verify_bundle", return_value=receipt), \
             patch.object(audit.release, "safe_member", side_effect=lambda root, path: root / path), \
             patch.object(audit.release, "read_file", return_value=body):
            report = audit.audit_candidate(Path("fixture"), "0" * 64)
        self.assertEqual(report["status"], "incomplete")
        self.assertEqual(report["unportable_commands"], [
            {"skill": skill, "line": 1, "reason": "source_checkout_command"}])
        self.assertEqual(report["external_runtime_counts"], {
            "skill_documents": 0, "literal_references": 0, "distinct_targets": 0})

    def test_gstack_runtime_hint_is_reported_once_without_exposing_commands(self):
        skill = "plugins/SimonKStack/skills/qa/SKILL.md"
        text = ("~/.claude/skills/gstack/bin/gstack-config get telemetry --token SENSITIVE\n"
                ".claude/skills/gstack/bin/gstack-skill-start --skill qa\n")
        rows = audit.inspect_external_runtime_hints(skill, text)
        self.assertEqual(rows, [{"skill": skill, "reason": "gstack_bin_reference"}])
        self.assertNotIn("SENSITIVE", repr(rows))

    def test_verified_candidate_separates_static_paths_from_external_runtime(self):
        skill = "plugins/SimonKStack/skills/qa/SKILL.md"
        body = b"~/.claude/skills/gstack/bin/gstack-skill-start --skill qa\n"
        receipt = {"files": [{"path": skill, "size": len(body),
                              "sha256": audit.release.digest(body)}]}
        with patch.object(audit.release, "no_links", side_effect=lambda path: path), \
             patch.object(audit.plugin_bundle, "verify_bundle", return_value=receipt), \
             patch.object(audit.release, "safe_member", side_effect=lambda root, path: root / path), \
             patch.object(audit.release, "read_file", return_value=body):
            report = audit.audit_candidate(Path("fixture"), "0" * 64)
        self.assertEqual(report["status"], "external_runtime_pending")
        self.assertEqual(report["external_runtime_hints"], [
            {"skill": skill, "reason": "gstack_bin_reference"}])
        self.assertEqual(report["external_runtime_counts"], {
            "skill_documents": 1, "literal_references": 1, "distinct_targets": 1})
        self.assertFalse(report["runtime_closure_verified"])

    def test_external_runtime_counts_repeat_refs_without_exposing_target_names(self):
        skill = "plugins/SimonKStack/skills/qa/SKILL.md"
        body = (b"~/.claude/skills/gstack/bin/gstack-config get telemetry\n"
                b".claude/skills/gstack/bin/gstack-config get update_check\n"
                b"~/.claude/skills/gstack/bin/gstack-slug\n"
                b"~/.claude/skills/gstack/bin/gstack-secretmarker12345\n")
        receipt = {"files": [{"path": skill, "size": len(body),
                              "sha256": audit.release.digest(body)}]}
        with patch.object(audit.release, "no_links", side_effect=lambda path: path), \
             patch.object(audit.plugin_bundle, "verify_bundle", return_value=receipt), \
             patch.object(audit.release, "safe_member", side_effect=lambda root, path: root / path), \
             patch.object(audit.release, "read_file", return_value=body):
            report = audit.audit_candidate(Path("fixture"), "0" * 64)
        self.assertEqual(report["external_runtime_counts"], {
            "skill_documents": 1, "literal_references": 4, "distinct_targets": 3})
        self.assertEqual(report["status"], "external_runtime_pending")
        self.assertNotIn("secretmarker12345", repr(report))

    def test_external_runtime_hint_prevents_success_exit(self):
        with patch.object(audit, "audit_candidate", return_value={
            "status": "external_runtime_pending", "unresolved": [],
            "unportable_commands": [], "external_runtime_hints": [
                {"skill": "plugins/SimonKStack/skills/qa/SKILL.md",
                 "reason": "gstack_bin_reference"}]}), redirect_stderr(io.StringIO()):
            with patch("sys.stdout", new_callable=io.StringIO):
                code = audit.main(["--package", "fixture", "--expected-digest", "0" * 64])
        self.assertEqual(code, 1)

    def test_pinned_gstack_source_reports_regular_target_without_claiming_runtime(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / "bin/gstack-config"
            target.parent.mkdir()
            target.write_bytes(b"fixture helper\n")
            source = {"status": "unsupported_git_modes", "tree_oid": "1" * 40,
                      "raw_manifest_sha256": "2" * 64, "package_contract_compatible": False}
            records = [{"path": "bin/gstack-config", "mode": "100755"}]
            with patch.object(audit.gstack_inventory, "audit_source", return_value=source), \
                 patch.object(audit.gstack_inventory, "_tree_records", return_value=records):
                report = audit.inspect_pinned_gstack_targets(root, "3" * 40, {"gstack-config"})
        self.assertEqual(report["status"], "direct_targets_present")
        self.assertEqual(report["present"], 1)
        self.assertEqual(report["missing"], 0)
        self.assertEqual(report["nonregular"], 0)
        self.assertEqual(len(report["target_manifest_sha256"]), 64)
        self.assertFalse(report["source_package_compatible"])
        self.assertFalse(report["runtime_closure_verified"])
        self.assertNotIn("gstack-config", repr(report))

    def test_pinned_gstack_source_missing_or_nonregular_targets_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = {"status": "unsupported_git_modes", "tree_oid": "1" * 40,
                      "raw_manifest_sha256": "2" * 64, "package_contract_compatible": False}
            with patch.object(audit.gstack_inventory, "audit_source", return_value=source), \
                 patch.object(audit.gstack_inventory, "_tree_records", return_value=[]):
                missing = audit.inspect_pinned_gstack_targets(root, "3" * 40, {"gstack-config"})
            with patch.object(audit.gstack_inventory, "audit_source", return_value=source), \
                 patch.object(audit.gstack_inventory, "_tree_records", return_value=[
                     {"path": "bin/gstack-config", "mode": "120000"}]):
                nonregular = audit.inspect_pinned_gstack_targets(root, "3" * 40, {"gstack-config"})
        self.assertEqual((missing["status"], missing["missing"], missing["present"]),
                         ("direct_targets_incomplete", 1, 0))
        self.assertEqual((nonregular["status"], nonregular["nonregular"], nonregular["present"]),
                         ("direct_targets_incomplete", 1, 0))

    def test_pinned_gstack_source_rejects_invalid_targets_before_clone_read(self):
        with patch.object(audit.gstack_inventory, "audit_source") as source:
            with self.assertRaisesRegex(ValueError, "Invalid direct helper"):
                audit.inspect_pinned_gstack_targets(Path("fixture"), "3" * 40,
                                                    {"../credential"})
            source.assert_not_called()

    def test_pinned_gstack_source_inventory_failure_prevents_helper_read(self):
        with patch.object(audit.gstack_inventory, "audit_source",
                          side_effect=ValueError("dirty source")), \
             patch.object(audit.gstack_inventory, "_tree_records") as tree:
            with self.assertRaisesRegex(ValueError, "dirty source"):
                audit.inspect_pinned_gstack_targets(Path("fixture"), "3" * 40,
                                                    {"gstack-config"})
            tree.assert_not_called()

    def test_pinned_gstack_source_change_during_read_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / "bin/gstack-config"
            target.parent.mkdir()
            target.write_bytes(b"fixture helper\n")
            before = {"status": "unsupported_git_modes", "tree_oid": "1" * 40,
                      "raw_manifest_sha256": "2" * 64, "package_contract_compatible": False}
            after = {**before, "raw_manifest_sha256": "4" * 64}
            with patch.object(audit.gstack_inventory, "audit_source",
                              side_effect=[before, after]), \
                 patch.object(audit.gstack_inventory, "_tree_records", return_value=[
                     {"path": "bin/gstack-config", "mode": "100755"}]):
                with self.assertRaisesRegex(ValueError, "changed during direct helper inspection"):
                    audit.inspect_pinned_gstack_targets(root, "3" * 40, {"gstack-config"})

    def test_pinned_gstack_source_requires_both_arguments(self):
        with self.assertRaisesRegex(ValueError, "must be supplied together"):
            audit.audit_candidate(Path("fixture"), "0" * 64,
                                  gstack_source=Path("source"))

    def test_gstack_source_evidence_does_not_upgrade_candidate_runtime(self):
        skill = "plugins/SimonKStack/skills/qa/SKILL.md"
        body = b"~/.claude/skills/gstack/bin/gstack-config get telemetry\n"
        receipt = {"files": [{"path": skill, "size": len(body),
                              "sha256": audit.release.digest(body)}]}
        evidence = {"status": "direct_targets_present", "present": 1,
                    "runtime_closure_verified": False}
        with patch.object(audit.release, "no_links", side_effect=lambda path: path), \
             patch.object(audit.plugin_bundle, "verify_bundle", return_value=receipt), \
             patch.object(audit.release, "safe_member", side_effect=lambda root, path: root / path), \
             patch.object(audit.release, "read_file", return_value=body), \
             patch.object(audit, "inspect_pinned_gstack_targets", return_value=evidence):
            report = audit.audit_candidate(Path("fixture"), "0" * 64,
                                           gstack_source=Path("source"), gstack_commit="1" * 40)
        self.assertEqual(report["gstack_source_evidence"], evidence)
        self.assertEqual(report["status"], "external_runtime_pending")
        self.assertFalse(report["runtime_closure_verified"])

    def test_sibling_skill_reference_is_resolved_inside_same_plugin(self):
        skill = "plugins/SimonKAIHub/skills/rag-builder/SKILL.md"
        target = "plugins/SimonKAIHub/skills/llm-eval/scripts/gate.mjs"
        rows = audit.inspect_skill_references(skill, "Use `../llm-eval/scripts/gate.mjs`.", {skill, target})
        self.assertEqual(rows, [{"reference": "../llm-eval/scripts/gate.mjs",
                                 "resolved": target, "status": "present"}])

    def test_markdown_links_cover_references_and_assets_without_double_counting(self):
        skill = "plugins/SimonKCore/skills/example/SKILL.md"
        parent = "plugins/SimonKCore/skills/example/"
        text = ("Read [contract](references/plan.md#scope) and "
                "![diagram](assets/flow.svg), then `scripts/check.py`. "
                "Repeat [contract](references/plan.md#other). "
                "Ignore [web](https://example.com/doc.md) and "
                "[placeholder](references/<name>.md).")
        available = {skill, parent + "references/plan.md",
                     parent + "assets/flow.svg", parent + "scripts/check.py"}
        rows = audit.inspect_skill_references(skill, text, available)
        self.assertEqual([(row["reference"], row["status"]) for row in rows], [
            ("references/plan.md", "present"),
            ("assets/flow.svg", "present"),
            ("scripts/check.py", "present"),
        ])

    def test_missing_or_escaping_markdown_links_fail_static_path_audit(self):
        skill = "plugins/SimonKStack/skills/example/SKILL.md"
        text = "Read [missing](references/needed.md) and [escape](../../../../secret.md)."
        rows = audit.inspect_skill_references(skill, text, {skill})
        self.assertEqual([(row["reference"], row["status"]) for row in rows], [
            ("references/needed.md", "unresolved"),
            ("../../../../secret.md", "outside-plugin"),
        ])

    def test_missing_paths_reported_once_without_treating_placeholders_as_files(self):
        skill = "plugins/SimonKMarket/skills/referral-program-builder/SKILL.md"
        text = ("Run `scripts/check-referral-integrity.sh` and use "
                "`templates/k-factor-queries.sql`; repeat `scripts/check-referral-integrity.sh`. "
                "Ignore `scripts/<project>.sh`, `scripts/*.sh`, "
                "`scripts/key?token=abc` and ` `.")
        rows = audit.inspect_skill_references(skill, text, {skill})
        self.assertEqual([(row["reference"], row["status"]) for row in rows], [
            ("scripts/check-referral-integrity.sh", "unresolved"),
            ("templates/k-factor-queries.sql", "unresolved"),
        ])

    def test_unresolved_reference_suggests_same_plugin_file_without_resolving_it(self):
        skill = "plugins/SimonKAIHub/skills/rag-builder/SKILL.md"
        sibling = "plugins/SimonKAIHub/skills/llm-eval/scripts/gate.mjs"
        other_plugin = "plugins/SimonKCore/skills/example/scripts/gate.mjs"
        rows = audit.inspect_skill_references(skill, "Use `scripts/gate.mjs`.",
                                              {skill, sibling, other_plugin})
        self.assertEqual(rows, [{"reference": "scripts/gate.mjs",
                                 "resolved": "plugins/SimonKAIHub/skills/rag-builder/scripts/gate.mjs",
                                 "status": "unresolved", "possible_targets": [sibling]}])

    def test_outside_plugin_reference_gets_no_alternative_hint(self):
        skill = "plugins/SimonKCore/skills/stack-update/SKILL.md"
        target = "plugins/SimonKCore/skills/other/scripts/install.sh"
        rows = audit.inspect_skill_references(skill, "`../../../../scripts/install.sh`",
                                              {skill, target})
        self.assertEqual(rows[0]["status"], "outside-plugin")
        self.assertNotIn("possible_targets", rows[0])

    def test_reference_cannot_escape_own_plugin_or_claim_root_helper(self):
        skill = "plugins/SimonKCore/skills/stack-update/SKILL.md"
        rows = audit.inspect_skill_references(
            skill, "`../../../../scripts/install.sh` and `scripts/install.sh --force`",
            {skill, "scripts/install.sh"})
        self.assertEqual([(row["reference"], row["status"]) for row in rows], [
            ("../../../../scripts/install.sh", "outside-plugin"),
            ("scripts/install.sh", "unresolved"),
        ])

    def test_example_worktree_directories_are_not_asset_refs(self):
        skill = "plugins/SimonKCore/skills/simon-worktree/SKILL.md"
        self.assertEqual(audit.inspect_skill_references(skill, "`../myapp-auth`", {skill}), [])

    def test_directory_prefix_does_not_substitute_for_the_named_file(self):
        skill = "plugins/SimonKCore/skills/example/SKILL.md"
        ref = "plugins/SimonKCore/skills/example/scripts/entry.py"
        rows = audit.inspect_skill_references(skill, "`scripts/entry.py`", {skill, ref + "/nested"})
        self.assertEqual(rows[0]["status"], "unresolved")

    def test_receipt_verification_precedes_skill_reads(self):
        with patch.object(audit.release, "no_links", side_effect=lambda path: path), \
             patch.object(audit.plugin_bundle, "verify_bundle", side_effect=ValueError("bad digest")), \
             patch.object(audit.release, "read_file") as read_file:
            with self.assertRaisesRegex(ValueError, "bad digest"):
                audit.audit_candidate(Path("fixture"), "0" * 64)
            read_file.assert_not_called()

    def test_changed_skill_bytes_fail_closed_after_receipt_verification(self):
        skill = "plugins/SimonKCore/skills/example/SKILL.md"
        receipt = {"files": [{"path": skill, "size": 3, "sha256": "0" * 64}]}
        with patch.object(audit.release, "no_links", side_effect=lambda path: path), \
             patch.object(audit.plugin_bundle, "verify_bundle", return_value=receipt), \
             patch.object(audit.release, "safe_member", side_effect=lambda root, path: root / path), \
             patch.object(audit.release, "read_file", return_value=b"bad"):
            with self.assertRaisesRegex(ValueError, "changed after candidate verification"):
                audit.audit_candidate(Path("fixture"), "0" * 64)

    def test_cli_verification_failure_does_not_echo_untrusted_details(self):
        output = io.StringIO()
        with patch.object(audit, "audit_candidate", side_effect=ValueError("secret in receipt")), \
             redirect_stderr(output):
            code = audit.main(["--package", "fixture", "--expected-digest", "0" * 64])
        self.assertEqual(code, 2)
        self.assertNotIn("secret", output.getvalue())


if __name__ == "__main__":
    unittest.main()
