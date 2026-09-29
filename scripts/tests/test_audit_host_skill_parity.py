"""Fail-closed static skill parity checks for the two host packages."""
import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_host_skill_parity as parity


def sha(data):
    return hashlib.sha256(data).hexdigest()


class HostSkillParityTests(unittest.TestCase):
    def setUp(self):
        self.zoom = parity.ZOOM_PATH
        self.normal = "plugins/SimonKCore/skills/vibe/SKILL.md"
        self.excluded = parity.EXPECTED_EXCLUDED
        self.original_zoom = b"---\nname: zoom-out\ndisable-model-invocation: true\n---\nMap\n"
        self.projected_zoom = self.original_zoom.replace(parity.MANUAL_FLAG, b"")
        self.claude = {self.normal: sha(b"vibe"), self.zoom: sha(self.original_zoom)}
        self.claude.update({path: sha(path.encode()) for path in self.excluded})
        self.codex = {self.normal: sha(b"vibe"), self.zoom: sha(self.projected_zoom)}
        self.reference = "plugins/SimonKCore/skills/vibe/references/orchestration.md"
        self.claude_payload = {**self.claude, self.reference: sha(b"shared contract")}
        self.codex_payload = {**self.codex, self.reference: sha(b"shared contract"),
                              parity.codex_overlay.ZOOM_POLICY_PATH:
                              sha(parity.codex_overlay.ZOOM_POLICY)}

    def compare(self):
        return parity.compare(self.claude, self.codex,
                              self.original_zoom, self.projected_zoom,
                              self.claude_payload, self.codex_payload)

    def test_only_d29_exclusions_and_manual_zoom_projection_pass(self):
        report = self.compare()
        self.assertEqual(report["status"], "static_content_parity")
        self.assertEqual(report["identical_skills"], 1)
        self.assertEqual(report["identical_payload_files"], 2)
        self.assertEqual(report["projected_skills"], [self.zoom])
        self.assertEqual(report["excluded_skills"], sorted(self.excluded))
        self.assertFalse(report["host_behavior_verified"])

    def test_changed_shared_skill_fails(self):
        self.codex[self.normal] = sha(b"weakened")
        self.codex_payload[self.normal] = self.codex[self.normal]
        with self.assertRaisesRegex(ValueError, "Shared skill bytes differ"):
            self.compare()

    def test_changed_shared_reference_fails(self):
        self.codex_payload[self.reference] = sha(b"weakened contract")
        with self.assertRaisesRegex(ValueError, "Shared skill payload differs"):
            self.compare()

    def test_missing_shared_reference_fails(self):
        del self.codex_payload[self.reference]
        with self.assertRaisesRegex(ValueError, "Shared skill payload differs"):
            self.compare()

    def test_extra_shared_script_fails(self):
        self.codex_payload["plugins/SimonKCore/skills/vibe/scripts/extra.py"] = sha(b"extra")
        with self.assertRaisesRegex(ValueError, "Shared skill payload differs"):
            self.compare()

    def test_zoom_policy_must_be_exact_projection(self):
        self.codex_payload[parity.codex_overlay.ZOOM_POLICY_PATH] = sha(b"implicit invocation")
        with self.assertRaisesRegex(ValueError, "Shared skill payload differs"):
            self.compare()

    def test_unexpected_exclusion_fails(self):
        del self.codex[self.normal]
        with self.assertRaisesRegex(ValueError, "D-29 excluded skill set differs"):
            self.compare()

    def test_excluded_safety_skill_readded_fails(self):
        path = next(iter(self.excluded))
        self.codex[path] = self.claude[path]
        with self.assertRaisesRegex(ValueError, "D-29 excluded skill set differs"):
            self.compare()

    def test_extra_codex_skill_fails(self):
        self.codex["plugins/SimonKCore/skills/extra/SKILL.md"] = sha(b"extra")
        with self.assertRaisesRegex(ValueError, "Codex skill set adds"):
            self.compare()

    def test_zoom_projection_must_be_exact_single_frontmatter_removal(self):
        self.projected_zoom += b" altered"
        self.codex[self.zoom] = sha(self.projected_zoom)
        with self.assertRaisesRegex(ValueError, "Zoom-out projection differs"):
            self.compare()

    def test_zoom_marker_outside_frontmatter_fails(self):
        self.original_zoom = b"---\nname: zoom-out\n---\n" + parity.MANUAL_FLAG
        self.projected_zoom = self.original_zoom.replace(parity.MANUAL_FLAG, b"")
        self.claude[self.zoom] = sha(self.original_zoom)
        self.codex[self.zoom] = sha(self.projected_zoom)
        with self.assertRaisesRegex(ValueError, "Zoom-out marker must be in frontmatter"):
            self.compare()

    def test_zoom_receipt_hash_mismatch_fails(self):
        self.codex[self.zoom] = sha(b"other")
        with self.assertRaisesRegex(ValueError, "Zoom-out receipt differs"):
            self.compare()


if __name__ == "__main__":
    unittest.main()
