"""Regression tests for the persona report's fail-closed evidence gate."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[2] / "skills-src/persona-simulation/scripts/check_findings.py"


class PersonaFindingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def report(self, name="persona-sim-current.html", content=""):
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def run_check(self, *args):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), *map(str, args)],
            cwd=self.root, text=True, capture_output=True, check=False,
        )

    def test_missing_report_fails(self):
        self.assertEqual(self.run_check().returncode, 1)

    def test_expected_report_cannot_be_replaced_by_stale_report(self):
        self.report("persona-sim-old.html", "PERSONA-SCOPE: first-run and core-loop, 12 people")
        self.assertEqual(self.run_check("--expect", "persona-sim-current.html").returncode, 1)

    def test_directory_and_invalid_utf8_fail(self):
        folder = self.root / "persona-sim-dir.html"
        folder.mkdir()
        self.assertEqual(self.run_check(folder).returncode, 1)
        bad = self.root / "persona-sim-bad.html"
        bad.write_bytes(b"\xff\xfe")
        self.assertEqual(self.run_check(bad).returncode, 1)

    def test_zero_findings_requires_scope_for_this_report(self):
        report = self.report(content="<main>No findings.</main>")
        self.assertEqual(self.run_check("--expect", report).returncode, 1)
        report.write_text("<main>PERSONA-SCOPE: first-run + core-loop; 12 people</main>", encoding="utf-8")
        self.assertEqual(self.run_check("--expect", report).returncode, 0)

    def test_grounded_finding_passes(self):
        report = self.report(content="<article>BLOCKER <code>src/app/entry.tsx:84</code> button height 36</article>")
        self.assertEqual(self.run_check("--expect", report).returncode, 0)

    def test_two_grounded_findings_pass_on_one_line(self):
        report = self.report(content=(
            "<main><article>BLOCKER <code>entry.tsx:84</code></article>"
            "<article>DROPOUT <code>flow.tsx:17</code></article></main>"
        ))
        self.assertEqual(self.run_check("--expect", report).returncode, 0)

    def test_expected_report_does_not_borrow_old_reports_scope(self):
        self.report("persona-sim-old.html", "PERSONA-SCOPE: first-run and core-loop, 12 people")
        current = self.report(content="<main>No findings.</main>")
        self.assertEqual(self.run_check("--expect", current).returncode, 1)

    def test_missing_or_preceding_evidence_does_not_pass(self):
        report = self.report(content="<article>BLOCKER No source location</article>")
        self.assertEqual(self.run_check("--expect", report).returncode, 1)
        report.write_text("<code>entry.tsx:84</code><article>BLOCKER No source location</article>", encoding="utf-8")
        self.assertEqual(self.run_check("--expect", report).returncode, 1)

    def test_one_line_html_does_not_borrow_next_findings_evidence(self):
        report = self.report(content=(
            "<main><article>BLOCKER no source</article>"
            "<article>DROPOUT <code>entry.tsx:84</code></article></main>"
        ))
        self.assertEqual(self.run_check("--expect", report).returncode, 1)

    def test_attribute_evidence_is_not_visible_report_evidence(self):
        report = self.report(content='<article data-cite="entry.tsx:84">BLOCKER no visible source</article>')
        self.assertEqual(self.run_check("--expect", report).returncode, 1)

    def test_head_and_script_do_not_supply_scope_or_evidence(self):
        report = self.report(content=(
            "<html><head><title>PERSONA-SCOPE: fabricated</title></head>"
            "<body><script>BLOCKER entry.tsx:84</script><main>No findings.</main></body></html>"
        ))
        self.assertEqual(self.run_check("--expect", report).returncode, 1)

    def test_multiple_reports_each_require_own_scope_or_findings(self):
        first = self.report("persona-sim-one.html", "PERSONA-SCOPE: first-run, 10 people")
        second = self.report("persona-sim-two.html", "<main>No findings.</main>")
        self.assertEqual(self.run_check(first, second).returncode, 1)


if __name__ == "__main__":
    unittest.main()
