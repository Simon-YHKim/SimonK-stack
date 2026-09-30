"""Executable contract checks for the app orchestrator's host routing boundary."""

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills-src" / "app-dev-orchestrator" / "SKILL.md"
CASES = SKILL.parent / "evals" / "cases.json"


class AppDevHostParityTests(unittest.TestCase):
    def test_central_model_and_effort_authority(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("## Host parity and routing authority", text)
        self.assertIn("`/vibe` 중앙 planner", text)
        self.assertIn("모델·effort", text)
        self.assertNotIn("Opus 4.6 자동 사용", text)
        self.assertIn("authorization-gated deployment plan", text.splitlines()[2])

    def test_codex_subset_does_not_claim_claude_hooks(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("Codex D-29", text)
        self.assertIn("`careful`, `guard`, `freeze`, `investigate`, `unfreeze`", text)
        self.assertIn("호스트 정책 집행과 동등하다고 주장하지 않는다", text)

    def test_host_parity_evals_track_skill_version(self):
        text = SKILL.read_text(encoding="utf-8")
        version = re.search(r"(?m)^version: (.+)$", text)
        self.assertIsNotNone(version)
        cases = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(cases["version"], version.group(1))
        self.assertTrue({"claude-new-app-central-route", "codex-new-app-safe-subset"}
                        <= {case["id"] for case in cases["cases"]})


if __name__ == "__main__":
    unittest.main()
