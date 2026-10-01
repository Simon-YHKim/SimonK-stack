"""Protect /vibe discovery when a host shortens skill descriptions."""

import re
import unittest
from pathlib import Path


SKILL_PATH = Path(__file__).resolve().parents[2] / "skills-src" / "vibe" / "SKILL.md"
OBSERVED_CODEX_PREFIX_CHARS = 48


class VibeDescriptionBudgetTests(unittest.TestCase):
    def test_shortened_description_keeps_command_and_orchestrator_identity(self):
        frontmatter = SKILL_PATH.read_text(encoding="utf-8").split("---", 2)[1]
        match = re.search(r"^description:\s*'(.+)'$", frontmatter, re.MULTILINE)
        self.assertIsNotNone(match)
        prefix = match.group(1)[:OBSERVED_CODEX_PREFIX_CHARS].lower()
        self.assertIn("/vibe", prefix)
        self.assertIn("simonkstack", prefix)
        self.assertRegex(prefix, r"rout|orchestrat")


if __name__ == "__main__":
    unittest.main()
