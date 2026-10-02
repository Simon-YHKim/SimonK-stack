"""Offline adversarial fixtures for QA acceptance, never live application tests."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("qa_gate.py")
spec = importlib.util.spec_from_file_location("qa_gate", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class AcceptanceGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.artifacts = self.root / "artifacts"
        self.artifacts.mkdir()
        self.target = {"revision": "build-sha-123", "environment": "test"}
        self.evidence = self.artifact("checks.txt", b"1 assertion passed\n")
        self.contract = {
            "schema_version": 1,
            "created_at": "2026-01-01T00:00:00Z",
            "target": copy.deepcopy(self.target),
            "requirements": [{
                "id": "R-1", "source_type": "spec", "source": "spec.md#label",
                "expected": "The heading uses the approved label.",
                "risk": "low", "category": "functional",
                "negative_testing": "not_applicable",
                "negative_reason": "Static label, no input or state transition.",
                "checks": [{"id": "C-1", "kind": "positive", "level": "unit",
                            "expected": "The label equals the specification."}],
            }],
        }
        self.results = {"schema_version": 1, "contract_sha256": "",
                        "target": copy.deepcopy(self.target),
                        "checks": [self.check("C-1")]}
        self.approval = None

    def artifact(self, name, data):
        (self.artifacts / name).write_bytes(data)
        return {"path": name, "sha256": hashlib.sha256(data).hexdigest()}

    def check(self, identifier, level="unit"):
        return {"id": identifier, "status": "passed", "level": level,
                "mocked": level == "unit", "command": "test-runner --case " + identifier,
                "exit_code": 0, "observed_at": "2026-01-01T00:01:00Z",
                "actual": "Expected assertion observed in the fixture.",
                "counts": {"passed": 1, "failed": 0, "skipped": 0},
                "evidence": [copy.deepcopy(self.evidence)]}

    def write_inputs(self):
        contract = self.root / "contract.json"
        contract.write_text(json.dumps(self.contract), encoding="utf-8")
        self.digest = hashlib.sha256(contract.read_bytes()).hexdigest()
        self.results["contract_sha256"] = self.digest
        (self.root / "results.json").write_text(json.dumps(self.results), encoding="utf-8")
        if self.approval is not None:
            self.approval["contract_sha256"] = self.digest
            (self.root / "approval.json").write_text(json.dumps(self.approval), encoding="utf-8")

    def audit(self, write=True, **overrides):
        if write:
            self.write_inputs()
        args = dict(contract_path=self.root / "contract.json",
                    results_path=self.root / "results.json", evidence_root=self.artifacts,
                    contract_sha256=self.digest, revision=self.target["revision"],
                    environment=self.target["environment"],
                    approval_path=self.root / "approval.json" if self.approval else None)
        args.update(overrides)
        return gate.audit(**args)

    def blocked(self, fragment=None, **kwargs):
        code, report = self.audit(**kwargs)
        self.assertNotEqual(code, 0, report)
        self.assertFalse(report["release_authorized"])
        if fragment:
            self.assertIn(fragment, " ".join(report["issues"]).lower())

    def high_risk(self, category="authorization"):
        req = self.contract["requirements"][0]
        req.update(risk="high", category=category, negative_testing="required")
        req.pop("negative_reason")
        extra = "recovery" if category in {"payment", "deletion", "migration"} else "boundary"
        req["checks"] += [
            {"id": "C-deny", "kind": "negative", "level": "integration",
             "expected": "Other tenant cannot read the order; no data is returned."},
            {"id": "C-edge", "kind": extra, "level": "integration",
             "expected": "Boundary or recovery invariant holds without side effects."},
        ]
        self.results["checks"] += [self.check("C-deny", "integration"),
                                    self.check("C-edge", "integration")]
        self.approval = {"schema_version": 1, "contract_sha256": "",
                         "target": copy.deepcopy(self.target), "decision": "approved",
                         "reviewer_type": "human", "reviewer": "Fixture reviewer",
                         "observed_at": "2026-01-01T00:02:00Z",
                         "evidence": [self.artifact("review.txt", b"Fixture scoped review\n")]}

    def test_low_risk_valid_passes_without_human_gate(self):
        code, report = self.audit()
        self.assertEqual(code, 0, report)
        self.assertEqual(report["decision"], "pass")
        self.assertFalse(report["release_authorized"])

    def test_missing_and_extra_checks_block(self):
        saved = copy.deepcopy(self.results["checks"])
        for checks in [[], saved + [self.check("unexpected")]]:
            with self.subTest(checks=checks):
                self.results["checks"] = checks
                self.blocked()

    def test_duplicate_requirement_and_check_ids_block(self):
        original = copy.deepcopy(self.contract)
        self.contract["requirements"] *= 2
        self.blocked("duplicate")
        self.contract = copy.deepcopy(original)
        self.contract["requirements"][0]["checks"] *= 2
        self.blocked("duplicate")
        self.contract = copy.deepcopy(original)
        self.results["checks"] *= 2
        self.blocked("duplicate")

    def test_all_nonpassed_states_block(self):
        for status in ["failed", "blocked", "not_run", "skipped", "not_applicable", "PASS"]:
            with self.subTest(status=status):
                self.results["checks"][0]["status"] = status
                self.blocked()

    def test_claimed_pass_does_not_override_failed_process(self):
        for exit_code in [1, -1, None, True, "0"]:
            with self.subTest(exit_code=exit_code):
                self.results["checks"][0]["exit_code"] = exit_code
                self.blocked()

    def test_minimal_failed_or_unexecuted_check_is_blocked_not_invalid(self):
        for status in ["failed", "blocked", "not_run", "skipped"]:
            with self.subTest(status=status):
                self.results["checks"] = [{"id": "C-1", "status": status}]
                code, report = self.audit()
                self.assertEqual(code, 1, report)
                self.assertEqual(report["decision"], "blocked")

    def test_passed_check_conditionally_requires_every_evidence_field(self):
        original = copy.deepcopy(self.results["checks"][0])
        for field in ["level", "mocked", "command", "exit_code", "observed_at", "actual", "counts", "evidence"]:
            with self.subTest(field=field):
                self.results["checks"] = [copy.deepcopy(original)]
                self.results["checks"][0].pop(field)
                code, report = self.audit()
                self.assertEqual(code, 2, report)
                self.assertEqual(report["decision"], "invalid")
                self.assertFalse(report["release_authorized"])

    def test_zero_failed_skipped_and_boolean_counts_block(self):
        for counts in [{"passed": 0, "failed": 0, "skipped": 0},
                       {"passed": 3, "failed": 1, "skipped": 0},
                       {"passed": 3, "failed": 0, "skipped": 1},
                       {"passed": True, "failed": 0, "skipped": 0}]:
            with self.subTest(counts=counts):
                self.results["checks"][0]["counts"] = counts
                self.blocked()

    def test_contract_hash_must_be_pinned_outside_results(self):
        self.blocked(contract_sha256="a" * 64)

    def test_results_must_bind_to_exact_contract_bytes(self):
        self.write_inputs()
        self.results["contract_sha256"] = "f" * 64
        (self.root / "results.json").write_text(json.dumps(self.results), encoding="utf-8")
        self.blocked(write=False, fragment="contract")

    def test_both_targets_must_match_trusted_checkout_context(self):
        for field in ["revision", "environment"]:
            with self.subTest(field=field):
                old = self.results["target"][field]
                self.results["target"][field] = "stale"
                self.blocked("target")
                self.results["target"][field] = old
                self.blocked(**{field: "another-build"})

    def test_precontract_future_and_naive_time_block(self):
        for stamp in ["2025-12-31T23:59:59Z", "2999-01-01T00:00:00Z",
                      "2026-01-01T00:01:00", "yesterday"]:
            with self.subTest(stamp=stamp):
                self.results["checks"][0]["observed_at"] = stamp
                self.blocked()

    def test_missing_empty_and_tampered_artifacts_block(self):
        path = self.artifacts / "checks.txt"
        for data in [b"", b"changed"]:
            with self.subTest(data=data):
                path.write_bytes(data)
                self.blocked()
        path.unlink()
        self.blocked()

    def test_path_escape_absolute_and_windows_ads_block(self):
        for path in ["../contract.json", "/etc/passwd", "C:/outside.txt",
                     "C:\\outside.txt", "checks.txt:stream", "//host/share.txt"]:
            with self.subTest(path=path):
                self.results["checks"][0]["evidence"][0]["path"] = path
                self.blocked()

    def test_symlink_outside_evidence_root_blocks(self):
        outside = self.root / "outside.txt"
        outside.write_bytes(b"outside")
        link = self.artifacts / "link.txt"
        try:
            link.symlink_to(outside)
        except OSError:
            self.skipTest("OS does not permit creating test symlinks")
        self.results["checks"][0]["evidence"] = [{"path": "link.txt", "sha256": hashlib.sha256(b"outside").hexdigest()}]
        self.blocked()

    def test_missing_assertion_or_execution_evidence_blocks(self):
        original = copy.deepcopy(self.results["checks"][0])
        for field, value in [("actual", ""), ("command", ""), ("evidence", []), ("mocked", "false")]:
            with self.subTest(field=field):
                self.results["checks"][0] = copy.deepcopy(original)
                self.results["checks"][0][field] = value
                self.blocked()

    def test_untrusted_requirement_or_empty_scope_blocks(self):
        self.contract["requirements"][0]["source_type"] = "implementation"
        self.blocked()
        self.contract["requirements"] = []
        self.blocked()

    def test_negative_exemption_requires_reason(self):
        self.contract["requirements"][0]["negative_reason"] = ""
        self.blocked()

    def test_exemption_reason_is_conditionally_required(self):
        req = self.contract["requirements"][0]
        req.pop("negative_reason")
        code, report = self.audit()
        self.assertEqual(code, 2, report)
        self.assertIn("negative_reason", " ".join(report["issues"]))
        req["negative_testing"] = "required"
        req["checks"].append({"id": "C-negative", "kind": "negative", "level": "unit",
                              "expected": "Invalid input is rejected."})
        self.results["checks"].append(self.check("C-negative"))
        code, report = self.audit()
        self.assertEqual(code, 0, report)

    def test_low_risk_required_negative_cannot_be_omitted(self):
        self.contract["requirements"][0]["negative_testing"] = "required"
        self.contract["requirements"][0].pop("negative_reason")
        self.blocked()

    def test_high_risk_valid_with_separate_scoped_review(self):
        self.high_risk()
        code, report = self.audit()
        self.assertEqual(code, 0, report)

    def test_high_risk_cannot_be_downgraded(self):
        self.high_risk()
        self.contract["requirements"][0]["risk"] = "low"
        self.blocked()

    def test_high_risk_missing_negative_boundary_or_review_blocks(self):
        self.high_risk()
        req = self.contract["requirements"][0]
        saved = copy.deepcopy(req["checks"])
        for kind in ["negative", "boundary"]:
            with self.subTest(kind=kind):
                req["checks"] = [c for c in saved if c["kind"] != kind]
                self.blocked()
        req["checks"] = saved
        self.approval = None
        self.blocked("review")

    def test_screenshot_or_mock_cannot_prove_permission_boundary(self):
        self.high_risk()
        self.results["checks"][1]["mocked"] = True
        self.blocked()
        self.results["checks"][1]["mocked"] = False
        self.contract["requirements"][0]["checks"][1]["level"] = "visual"
        self.results["checks"][1]["level"] = "visual"
        self.blocked()

    def test_human_review_must_match_contract_and_be_human(self):
        self.high_risk()
        self.approval["reviewer_type"] = "agent"
        self.blocked()
        self.approval["reviewer_type"] = "human"
        self.approval["target"]["revision"] = "older-build"
        self.blocked()

    def test_payment_deletion_migration_require_recovery(self):
        for category in ["payment", "deletion", "migration"]:
            with self.subTest(category=category):
                self.setUp()
                self.high_risk(category)
                code, report = self.audit()
                self.assertEqual(code, 0, report)
                self.contract["requirements"][0]["checks"][2]["kind"] = "boundary"
                self.blocked()

    def test_unknown_fields_and_duplicate_json_keys_fail_closed(self):
        self.results["human_reviewed"] = True
        self.blocked()
        self.results.pop("human_reviewed")
        self.write_inputs()
        (self.root / "results.json").write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
        self.blocked(write=False, fragment="duplicate")

    def test_commands_are_inert_text(self):
        marker = self.root / "MUST_NOT_EXIST"
        self.results["checks"][0]["command"] = f'python -c "open({str(marker)!r}, chr(119)).write(chr(120))"'
        code, report = self.audit()
        self.assertEqual(code, 0, report)
        self.assertFalse(marker.exists())

    def test_empty_and_stale_human_review_artifacts_block(self):
        self.high_risk()
        self.approval["evidence"] = []
        self.blocked("review")
        self.approval["evidence"] = [self.artifact("review.txt", b"Scoped review")]
        self.approval["observed_at"] = "2025-12-31T23:59:59Z"
        self.blocked("review")

    def test_forged_approval_contract_hash_blocks(self):
        self.high_risk()
        self.write_inputs()
        self.approval["contract_sha256"] = "e" * 64
        (self.root / "approval.json").write_text(json.dumps(self.approval), encoding="utf-8")
        self.blocked(write=False, fragment="review")

    def test_contract_creation_in_future_and_boolean_version_block(self):
        self.contract["created_at"] = "2999-01-01T00:00:00Z"
        self.blocked()
        self.contract["created_at"] = "2026-01-01T00:00:00Z"
        self.contract["schema_version"] = True
        self.blocked()

    def test_invalid_json_and_nonfinite_numbers_fail_closed(self):
        self.write_inputs()
        for data in ["{bad", '{"counts":NaN}', "[]"]:
            with self.subTest(data=data):
                (self.root / "results.json").write_text(data, encoding="utf-8")
                code, report = self.audit(write=False)
                self.assertEqual(code, 2, report)

    def test_cli_exit_status_and_no_input_mutation(self):
        self.write_inputs()
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        args = [sys.executable, "-B", str(SCRIPT), "--contract", str(self.root / "contract.json"),
                "--results", str(self.root / "results.json"), "--evidence-root", str(self.artifacts),
                "--contract-sha256", self.digest, "--revision", self.target["revision"],
                "--environment", self.target["environment"]]
        process = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(process.returncode, 0, process.stderr + process.stdout)
        self.assertEqual(json.loads(process.stdout)["decision"], "pass")
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()})
        self.results["checks"] = []
        self.write_inputs()
        process = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(process.returncode, 1, process.stdout)
        process = subprocess.run(args[:-2], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(process.returncode, 2)


if __name__ == "__main__":
    unittest.main()
