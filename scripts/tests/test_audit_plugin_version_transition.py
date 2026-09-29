"""Non-generating transition checks over synthetic verified-receipt shapes."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_plugin_version_transition as transition
import skill_release as release


def manifest() -> dict:
    return {"inputs": {"plugins": {owner: {} for owner in release.OWNERS}},
            "files": [{"path": f"plugins/{owner}/skills/example/SKILL.md",
                       "sha256": "a" * 64, "mode": "100644"}
                      for owner in sorted(release.OWNERS)]}


class TransitionTests(unittest.TestCase):
    def setUp(self):
        self.before = manifest()
        self.after = deepcopy(self.before)
        self.versions = {owner: "1.0.0-vibe.old" for owner in release.OWNERS}
        self.metadata = {owner: {relative: ("d" * 64, "100644")
                                 for relative in (transition.plugin_bundle.PLUGIN,
                                                  transition.plugin_bundle.MARKET)}
                         for owner in release.OWNERS}

    def compare(self, *, versions=None, metadata=None):
        return transition.compare(self.before, self.after, self.versions,
                                  versions or self.versions, self.metadata,
                                  metadata or self.metadata)

    def test_identical_payload_and_versions_are_stable(self):
        result = self.compare()
        self.assertEqual(result["status"], "consistent")
        self.assertTrue(all(row["state"] == "stable" for row in result["plugins"]))

    def test_same_version_with_changed_payload_is_collision(self):
        self.after["files"][0]["sha256"] = "b" * 64
        result = self.compare()
        self.assertEqual(result["status"], "collision")
        self.assertEqual(sum(row["state"] == "collision" for row in result["plugins"]), 1)

    def test_changed_payload_and_version_is_updated(self):
        self.after["files"][0]["mode"] = "100755"
        new_versions = {**self.versions, "SimonKAIHub": "1.0.1-vibe.new"}
        result = self.compare(versions=new_versions)
        self.assertEqual(result["status"], "consistent")
        self.assertEqual(result["plugins"][0]["state"], "updated")

    def test_manifest_only_version_change_is_churn(self):
        new_versions = {owner: "1.0.1-vibe.new" for owner in release.OWNERS}
        result = self.compare(versions=new_versions)
        self.assertEqual(result["status"], "churn")
        self.assertTrue(all(row["state"] == "churn" for row in result["plugins"]))

    def test_added_file_counts_as_payload_change(self):
        self.after["files"].append({"path": "plugins/SimonKCore/skills/example/references/guide.md",
                                    "sha256": "c" * 64, "mode": "100644"})
        result = self.compare()
        row = next(row for row in result["plugins"] if row["owner"] == "SimonKCore")
        self.assertEqual(row["state"], "collision")
        self.assertEqual(row["changed_paths"], ["skills/example/references/guide.md"])

    def test_version_only_manifest_bytes_do_not_count_as_payload(self):
        for owner in release.OWNERS:
            self.after["files"].append({"path": f"plugins/{owner}/{transition.plugin_bundle.PLUGIN}",
                                        "sha256": "d" * 64, "mode": "100644"})
        result = self.compare()
        self.assertEqual(result["status"], "consistent")

    def test_nonversion_manifest_change_is_collision(self):
        changed_metadata = deepcopy(self.metadata)
        changed_metadata["SimonKDesign"][transition.plugin_bundle.PLUGIN] = ("e" * 64, "100644")
        result = self.compare(metadata=changed_metadata)
        row = next(row for row in result["plugins"] if row["owner"] == "SimonKDesign")
        self.assertEqual(row["state"], "collision")
        self.assertEqual(row["changed_paths"], [transition.plugin_bundle.PLUGIN])

    def test_owner_mismatch_is_rejected(self):
        del self.after["inputs"]["plugins"]["SimonKMarket"]
        with self.assertRaisesRegex(ValueError, "owner sets differ"):
            self.compare()


if __name__ == "__main__":
    unittest.main()
