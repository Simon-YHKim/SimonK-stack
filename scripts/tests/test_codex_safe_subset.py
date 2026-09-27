"""Codex general-skill projection must not expose unported safety policies."""
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import codex_overlay


@unittest.skipUnless(os.name == "nt", "Pinned package I/O is Windows-only")
class CodexSafeSubsetTests(unittest.TestCase):
    def setUp(self):
        helper = ROOT / "scripts/codex_safe_subset.py"
        self.assertTrue(helper.is_file(), "Codex safe-subset builder is missing")
        spec = importlib.util.spec_from_file_location("codex_safe_subset", helper)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory(prefix="vibe-codex-subset-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "verified-v2-overlay"
        self.source.mkdir()
        self.output = self.root / "general-subset"
        self.put("overlay.json", b'{"fixture":true}\n')
        self.put("bundle.json", b'{"fixture":true}\n')
        self.put("plugins/SimonKCore/.codex-plugin/plugin.json", b'{"name":"simonk-core"}\n')
        self.put("plugins/SimonKStack/.codex-plugin/plugin.json", b'{"name":"simonk-stack"}\n')
        self.put("plugins/SimonKCore/skills/vibe/SKILL.md", b"---\nname: vibe\n---\nGeneral\n")
        for owner, name in (("SimonKCore", "careful"), ("SimonKStack", "guard"),
                            ("SimonKStack", "freeze"), ("SimonKStack", "investigate"),
                            ("SimonKCore", "unfreeze")):
            self.put(f"plugins/{owner}/skills/{name}/SKILL.md",
                     f"---\nname: {name}\n---\nClaude hook only\n".encode())
            self.put(f"plugins/{owner}/skills/{name}/scripts/helper.py", b"print('fixture')\n")
        for owner in ("SimonKCore", "SimonKStack"):
            self.put(f"plugins/{owner}/.simonk-runtime/safety_runtime.py",
                     b"print('safety fixture')\n")
        self.source_digest = hashlib.sha256((self.source / "overlay.json").read_bytes()).hexdigest()

    def put(self, relative, data):
        target = self.source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def build(self):
        with patch.object(codex_overlay, "verify_overlay", return_value={"installation_ready": False}):
            return self.module.build_subset(self.source, self.source_digest, self.output)

    def test_excludes_safety_skills_dependent_unfreeze_and_runtime(self):
        before = {p.relative_to(self.source).as_posix(): p.read_bytes()
                  for p in self.source.rglob("*") if p.is_file()}
        result = self.build()
        with patch.object(codex_overlay, "verify_overlay", return_value={"installation_ready": False}):
            receipt = self.module.verify_subset(self.output, result["subset_digest"],
                                                self.source, self.source_digest)
        self.assertEqual(receipt["decision_ref"], "D-29")
        self.assertEqual(len(receipt["excluded_skills"]), 5)
        self.assertEqual(len(receipt["excluded_members"]), 12)
        self.assertIn("simonk-core:unfreeze", receipt["excluded_skills"])
        self.assertTrue(any(".simonk-runtime" in row["path"]
                            for row in receipt["excluded_members"]))
        self.assertFalse(receipt["installation_ready"])
        self.assertFalse(receipt["host_compatibility_verified"])
        for relative, data in before.items():
            self.assertEqual((self.source / relative).read_bytes(), data)
            excluded = any(relative.startswith(prefix) for prefix in self.module.EXCLUDED_PREFIXES)
            self.assertEqual((self.output / relative).exists(), not excluded)

    def test_reintroduced_safety_skill_and_changed_retained_file_fail(self):
        result = self.build()
        unsafe = self.output / "plugins/SimonKStack/skills/freeze/SKILL.md"
        unsafe.parent.mkdir(parents=True)
        unsafe.write_text("unsafe", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.module.verify_subset(self.output, result["subset_digest"])
        unsafe.unlink()
        retained = self.output / "plugins/SimonKCore/skills/vibe/SKILL.md"
        retained.write_bytes(retained.read_bytes() + b"changed")
        with self.assertRaises(ValueError):
            self.module.verify_subset(self.output, result["subset_digest"])

    def test_missing_safety_source_or_wrong_pin_never_publishes(self):
        (self.source / "plugins/SimonKStack/skills/guard/SKILL.md").unlink()
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse(self.output.exists())
        with self.assertRaises(ValueError):
            self.module.build_subset(self.source, "0" * 64, self.output)
        self.assertFalse(self.output.exists())

    def test_existing_output_is_never_overwritten(self):
        self.output.mkdir()
        sentinel = self.output / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.build()
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_receipt_pin_and_source_provenance_are_separate(self):
        result = self.build()
        receipt = self.module.verify_subset(self.output, result["subset_digest"])
        self.assertEqual(receipt["source_overlay_digest"], self.source_digest)
        with patch.object(codex_overlay, "verify_overlay", return_value={"installation_ready": False}):
            with self.assertRaises(ValueError):
                self.module.verify_subset(self.output, result["subset_digest"], self.source,
                                          "0" * 64)
        receipt_file = self.output / "subset.json"
        receipt_file.write_bytes(receipt_file.read_bytes() + b" ")
        with self.assertRaises(ValueError):
            self.module.verify_subset(self.output, result["subset_digest"])


if __name__ == "__main__":
    unittest.main()
