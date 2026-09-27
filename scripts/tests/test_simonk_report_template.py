"""Offline structural and syntax checks for the self-contained report template."""

from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import subprocess
import unittest


TEMPLATE = Path(__file__).resolve().parents[2] / "skills-src/simonk-report/templates/report.html"


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def find(self, **attrs):
        return [item for item in self.elements if all(item[1].get(k) == v for k, v in attrs.items())]


class ReportTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = TEMPLATE.read_text(encoding="utf-8")
        cls.doc = Elements()
        cls.doc.feed(cls.html)
        cls.ids = {attrs["id"] for _, attrs in cls.doc.elements if "id" in attrs}
        cls.css = re.search(r"<style>(.*?)</style>", cls.html, re.S).group(1)
        cls.script = re.search(r"<script>(.*?)</script>", cls.html, re.S).group(1)

    def test_offline_single_file(self):
        for tag, attrs in self.doc.elements:
            self.assertNotEqual(tag, "link")
            for key in ("src", "href"):
                self.assertFalse(attrs.get(key, "").startswith(("http:", "https:", "//")))
            if tag == "script":
                self.assertNotIn("src", attrs)
        self.assertNotRegex(self.css, r"@import|url\s*\(\s*['\"]?https?://")

    def test_tabs_and_no_script_readability(self):
        self.assertEqual(len(self.doc.find(role="tab")), 2)
        self.assertEqual(len(self.doc.find(role="tabpanel")), 2)
        self.assertIn("no-js", self.doc.find(lang="ko")[0][1].get("class", ""))
        for _, tab in self.doc.find(role="tab"):
            self.assertIn(tab["aria-controls"], self.ids)
        for _, panel in self.doc.find(role="tabpanel"):
            self.assertIn(panel["aria-labelledby"], self.ids)
            self.assertNotIn("hidden", panel)
        self.assertIn('.no-js [role="tablist"]', self.css)

    def test_memo_and_report_floor(self):
        self.assertEqual(len(self.doc.find(id="memo-panel")), 1)
        self.assertEqual(len(self.doc.find(id="memo-copy")), 1)
        self.assertEqual(len(self.doc.find(role="note")), 1)
        self.assertIn("@media (prefers-color-scheme: dark)", self.css)
        self.assertIn(":focus-visible", self.css)
        self.assertIn("@media print", self.css)
        for field in ("TASK_TITLE", "WRITTEN_KST", "SESSION", "GRADE", "WHAT", "WHY", "STATUS"):
            self.assertIn("{{" + field + "}}", self.html)
        self.assertIn("localStorage", self.script)
        self.assertIn("showText(text)", self.script)

    def test_mobile_controls_have_44px_targets(self):
        for selector in ('[role="tab"]', 'details.sec > summary', '.btn'):
            rule = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", self.css)
            self.assertIsNotNone(rule, selector)
            size = re.search(r"min-height\s*:\s*(\d+)px", rule.group(1))
            self.assertIsNotNone(size, selector)
            self.assertGreaterEqual(int(size.group(1)), 44, selector)

    @unittest.skipUnless(shutil.which("node"), "Node.js is unavailable")
    def test_inline_javascript_parses(self):
        result = subprocess.run(["node", "--check"], input=self.script, text=True,
                                encoding="utf-8", capture_output=True, timeout=10, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
