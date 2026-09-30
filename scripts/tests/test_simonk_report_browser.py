"""Exercise the filled report in an isolated local Chrome profile, without models."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/tests/report_browser_smoke.mjs"
TEMPLATE = ROOT / "skills-src/simonk-report/templates/report.html"
NODE = shutil.which("node")
CHROME = Path(os.environ.get("CHROME_BIN") or (
    "C:/Program Files/Google/Chrome/Application/chrome.exe" if sys.platform == "win32"
    else "/usr/bin/google-chrome"
))


@unittest.skipUnless(NODE and CHROME.is_file(), "Local Node.js and Chrome are required")
class ReportBrowserTests(unittest.TestCase):
    def test_filled_report_interactions_and_offline_print(self):
        with tempfile.TemporaryDirectory(prefix="simonk-report-browser-") as temp:
            prefix = Path(temp) / "report"
            result = subprocess.run(
                [NODE, str(SCRIPT), str(TEMPLATE), str(prefix)],
                cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=45,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            receipt = json.loads(Path(f"{prefix}-result.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["status"], "passed")
            self.assertEqual(receipt["checks"], 18)
            self.assertEqual(receipt["exceptions"], [])
            self.assertGreater(receipt["pdf_bytes"], 1000)
            self.assertNotIn("{{", Path(f"{prefix}-fixture.html").read_text(encoding="utf-8"))
            for suffix in receipt["screenshots"]:
                screenshot = Path(f"{prefix}-{suffix}.png")
                self.assertGreater(screenshot.stat().st_size, 1000)
                self.assertEqual(screenshot.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()
