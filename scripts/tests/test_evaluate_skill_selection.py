"""Offline recorded-selection scoring; fixtures are not model observations."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "evaluate_skill_selection", ROOT / "scripts/evaluate_skill_selection.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class SelectionEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.cases = {"schema_version": 1, "cases": [
            {"id": "one", "prompt": "작업 조정", "acceptable": [["vibe"], ["vibe", "helper"]],
             "forbidden": ["vibe-bot"], "kind": "positive"},
            {"id": "two", "prompt": "$debug", "acceptable": [["debug"]],
             "forbidden": ["vibe"], "kind": "explicit"}]}
        records = [{"case_id": "one", "selected": ["vibe"], "evidence": "fixture only"},
                   {"case_id": "two", "selected": ["debug"], "evidence": "fixture only"}]
        self.results = {"schema_version": 1,
                        "evaluator": {"host": "fixture", "model": "fixture-model",
                                      "effort": "high", "observation_kind": "static-review"},
                        "conditions": [{"id": arm, "catalog_sha256": char * 64,
                                        "records": copy.deepcopy(records)}
                                       for arm, char in [("before", "a"), ("after", "b")]]}

    def grade(self):
        return M.evaluate(self.cases, self.results)

    def test_absent_results_are_pending_not_passed(self):
        out = M.evaluate(self.cases)
        self.assertEqual(out["status"], "pending")
        self.assertEqual(out["conditions"]["after"]["scored_count"], 0)
        self.assertFalse(out["native_compatibility_verified"])

    def test_complete_recorded_comparison_preserves_provenance_without_authentication(self):
        out = self.grade()
        self.assertEqual(out["status"], "recorded_comparison_passed")
        self.assertEqual(out["evaluator"], self.results["evaluator"])
        self.assertEqual(out["conditions"]["before"]["catalog_sha256"], "a" * 64)
        self.assertEqual(out["conditions"]["after"]["correct_count"], 2)
        self.assertEqual(out["conditions"]["after"]["total_count"], 2)
        self.assertEqual(out["regressions"], [])
        for flag in ("native_compatibility_verified", "evidence_authenticity_verified",
                     "catalog_binding_verified"):
            self.assertFalse(out[flag])

    def test_native_label_never_self_certifies_native_compatibility(self):
        self.results["evaluator"]["observation_kind"] = "native-session"
        self.assertFalse(self.grade()["native_compatibility_verified"])

    def test_exact_set_matches_order_independent_alternative(self):
        self.results["conditions"][1]["records"][0]["selected"] = ["helper", "vibe"]
        self.assertEqual(self.grade()["status"], "recorded_comparison_passed")

    def test_extra_skill_is_not_a_correct_superset(self):
        self.results["conditions"][1]["records"][0]["selected"] = ["vibe", "unasked"]
        out = self.grade()
        self.assertEqual(out["status"], "recorded_comparison_failed")
        self.assertEqual(out["regressions"], ["one"])

    def test_namespaces_and_aliases_are_not_normalized(self):
        self.results["conditions"][1]["records"][0]["selected"] = ["simonk-core:vibe"]
        self.assertEqual(self.grade()["regressions"], ["one"])

    def test_forbidden_selection_fails(self):
        self.results["conditions"][1]["records"][0]["selected"] = ["vibe", "vibe-bot"]
        out = self.grade()
        self.assertFalse(out["conditions"]["after"]["records"][0]["correct"])
        self.assertEqual(out["conditions"]["after"]["records"][0]["forbidden_selected"], ["vibe-bot"])

    def test_no_selection_is_observed_wrong_not_missing(self):
        self.results["conditions"][1]["records"][0]["selected"] = []
        out = self.grade()
        self.assertEqual(out["conditions"]["after"]["scored_count"], 2)
        self.assertEqual(out["status"], "recorded_comparison_failed")

    def test_no_skill_control_accepts_explicit_empty_set(self):
        self.cases["cases"][0].update(acceptable=[[]], kind="negative")
        for arm in self.results["conditions"]:
            arm["records"][0]["selected"] = []
        self.assertEqual(self.grade()["status"], "recorded_comparison_passed")

    def test_baseline_miss_can_improve_to_full_pass(self):
        self.results["conditions"][0]["records"][0]["selected"] = []
        self.assertEqual(self.grade()["status"], "recorded_comparison_passed")

    def test_persistent_wrong_answers_are_not_hidden_by_zero_regressions(self):
        for arm in self.results["conditions"]:
            arm["records"][0]["selected"] = []
        out = self.grade()
        self.assertEqual(out["regressions"], [])
        self.assertEqual(out["status"], "recorded_comparison_failed")

    def test_missing_arm_is_incomplete(self):
        self.results["conditions"].pop(0)
        out = self.grade()
        self.assertEqual(out["status"], "incomplete")
        self.assertEqual(out["conditions"]["before"]["missing_case_ids"], ["one", "two"])

    def test_missing_case_is_not_graded_as_failure_or_full_pass(self):
        self.results["conditions"][1]["records"].pop()
        out = self.grade()
        self.assertEqual(out["status"], "incomplete")
        self.assertEqual(out["conditions"]["after"]["scored_count"], 1)
        self.assertEqual(out["regressions"], [])

    def test_case_duplicate_and_bad_schema_rejected(self):
        bad_inputs = [[], {}, {"schema_version": True, "cases": self.cases["cases"]},
                      {"schema_version": 1, "cases": []},
                      {"schema_version": 1, "cases": self.cases["cases"] * 2}]
        for bad in bad_inputs:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                M.evaluate(bad)

    def test_invalid_case_fields_rejected(self):
        for key, value in [("id", ""), ("prompt", " "), ("acceptable", []),
                           ("acceptable", [["vibe", "vibe"]]),
                           ("acceptable", [["with space"]]), ("forbidden", "vibe"),
                           ("kind", "other"), ("kind", None)]:
            changed = copy.deepcopy(self.cases)
            changed["cases"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                M.evaluate(changed)

    def test_conflicting_acceptable_and_forbidden_rejected(self):
        self.cases["cases"][0]["forbidden"] = ["vibe"]
        with self.assertRaises(ValueError):
            self.grade()

    def test_bad_evaluator_rejected(self):
        for key, value in [("host", ""), ("model", None), ("effort", " "),
                           ("observation_kind", "trusted")]:
            bad = copy.deepcopy(self.results)
            bad["evaluator"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                M.evaluate(self.cases, bad)

    def test_duplicate_unknown_condition_and_hash_rejected(self):
        for mutate in [lambda r: r["conditions"].append(r["conditions"][0]),
                       lambda r: r["conditions"][0].update(id="later"),
                       lambda r: r["conditions"][0].update(catalog_sha256="not-a-hash")]:
            bad = copy.deepcopy(self.results)
            mutate(bad)
            with self.assertRaises(ValueError):
                M.evaluate(self.cases, bad)

    def test_duplicate_unknown_case_records_rejected(self):
        for mutate in [lambda records: records.append(records[0]),
                       lambda records: records[0].update(case_id="unknown")]:
            bad = copy.deepcopy(self.results)
            mutate(bad["conditions"][0]["records"])
            with self.assertRaises(ValueError):
                M.evaluate(self.cases, bad)

    def test_invalid_selection_or_blank_evidence_rejected(self):
        for key, value in [("selected", ["vibe", "vibe"]), ("selected", "vibe"),
                           ("selected", [None]), ("selected", [" vibe"]),
                           ("evidence", " "), ("evidence", None)]:
            bad = copy.deepcopy(self.results)
            bad["conditions"][0]["records"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                M.evaluate(self.cases, bad)

    def test_unknown_fields_cannot_smuggle_verification_claims(self):
        self.results["native_compatibility_verified"] = True
        with self.assertRaises(ValueError):
            self.grade()

    def test_evaluation_does_not_modify_inputs(self):
        before = copy.deepcopy((self.cases, self.results))
        self.grade()
        self.assertEqual((self.cases, self.results), before)

    def test_cli_pending_success_failure_and_input_errors_are_json(self):
        with tempfile.TemporaryDirectory(prefix="selection-eval-test-") as folder:
            case_path = Path(folder) / "cases.json"
            result_path = Path(folder) / "results.json"
            case_path.write_text(json.dumps(self.cases), encoding="utf-8")
            result_path.write_text(json.dumps(self.results), encoding="utf-8")
            variants = [(["--cases", str(case_path)], 2, "pending"),
                        (["--cases", str(case_path), "--results", str(result_path)],
                         0, "recorded_comparison_passed"),
                        (["--cases", str(case_path) + ".missing"], 1, "invalid_input")]
            for args, expected_code, expected_status in variants:
                with self.subTest(args=args), contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(M.main(args), expected_code)
                    self.assertEqual(json.loads(output.getvalue())["status"], expected_status)
            self.results["conditions"][1]["records"][0]["selected"] = []
            result_path.write_text(json.dumps(self.results), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(M.main(variants[1][0]), 1)
                self.assertEqual(json.loads(output.getvalue())["status"], "recorded_comparison_failed")

    def test_loader_rejects_duplicate_keys_and_oversized_input(self):
        with tempfile.TemporaryDirectory(prefix="selection-input-test-") as folder:
            target = Path(folder) / "input.json"
            for content in ['{"schema_version":1,"schema_version":1}', " " * (1024 * 1024 + 1)]:
                target.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    M.load_json(target)

    def test_cli_argument_errors_use_json(self):
        for args in ([], ["--unknown"], ["--help"]):
            with self.subTest(args=args), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(M.main(args), 1)
                self.assertEqual(json.loads(output.getvalue())["status"], "invalid_input")

    def test_documentation_distinguishes_recorded_scores_from_live_verification(self):
        doc = (ROOT / "docs/skill-selection-validation.md").read_text(encoding="utf-8")
        for expected in ("Grok", "$0", "static-review", "native_compatibility_verified",
                         "catalog_sha256", "--cases", "81", "namespace"):
            self.assertIn(expected, doc)


if __name__ == "__main__":
    unittest.main()
