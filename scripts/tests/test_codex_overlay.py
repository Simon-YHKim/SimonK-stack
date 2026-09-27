"""Codex compatibility projection of an immutable five-plugin candidate."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import plugin_bundle as bundle


@unittest.skipUnless(os.name == "nt", "Pinned package I/O is Windows-only")
class CodexOverlayTests(unittest.TestCase):
    def setUp(self):
        helper = ROOT / "scripts/codex_overlay.py"
        self.assertTrue(helper.is_file(), "Codex overlay builder is not implemented")
        spec = importlib.util.spec_from_file_location("codex_overlay", helper)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory(prefix="vibe-codex-overlay-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.candidate = self.base / "candidate"
        self.candidate.mkdir()
        self.output = self.base / "overlay"
        self.receipt = {"bases": {}, "files": []}
        for owner in sorted(bundle.r.OWNERS):
            name = "simonk-" + owner.removeprefix("SimonK").lower()
            manifest = {"name": name, "version": "1.2.3-vibe.abcdef123456",
                        "description": name + " skills", "author": {"name": "Simon Kim"},
                        "license": "MIT", "skills": ["./skills/example/"]}
            self.put(f"plugins/{owner}/.claude-plugin/plugin.json", bundle.r.encoded(manifest))
            self.put(f"plugins/{owner}/skills/example/SKILL.md",
                     b"---\nname: example\ndescription: fixture\n---\nFixture\n")
            self.receipt["bases"][owner] = {}
        self.zoom_path = "plugins/SimonKStack/skills/zoom-out/SKILL.md"
        self.zoom_source = (b"---\nname: zoom-out\ndescription: Manual-only map\n"
                            b"disable-model-invocation: true\n---\nMap\n")
        self.put(self.zoom_path, self.zoom_source)
        self.put("bundle.json", b'{"fixture":true}\n')
        self.candidate_digest = self.hash((self.candidate / "bundle.json").read_bytes())

    @staticmethod
    def hash(data):
        return hashlib.sha256(data).hexdigest()

    def put(self, relative, data):
        path = self.candidate / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        if relative != "bundle.json":
            self.receipt["files"].append({"path": relative, "sha256": self.hash(data),
                                           "size": len(data), "mode": "100644"})

    def test_build_preserves_candidate_and_generates_five_valid_manifests(self):
        before = {f["path"]: (self.candidate / f["path"]).read_bytes()
                  for f in self.receipt["files"]}
        with patch.object(bundle, "verify_bundle", return_value=self.receipt):
            result = self.module.build_overlay(self.candidate, self.candidate_digest, self.output)
            checked = self.module.verify_overlay(self.output, result["overlay_digest"])
        self.assertEqual(len(checked["generated"]), 7)
        self.assertFalse(checked["installation_ready"])
        self.assertFalse(checked["host_compatibility_verified"])
        self.assertEqual(result["candidate_digest"], self.candidate_digest)
        for relative, original in before.items():
            if relative != self.zoom_path:
                self.assertEqual((self.output / relative).read_bytes(), original)
            self.assertEqual((self.candidate / relative).read_bytes(), original)
        projected = (self.output / self.zoom_path).read_bytes()
        self.assertNotIn(b"disable-model-invocation: true", projected)
        self.assertIn(b"name: zoom-out", projected)
        policy = (self.output / "plugins/SimonKStack/skills/zoom-out/agents/openai.yaml").read_text()
        self.assertIn("allow_implicit_invocation: false", policy)
        self.assertIn(self.zoom_path, checked["generated"])
        for owner in sorted(bundle.r.OWNERS):
            manifest = json.loads((self.output / "plugins" / owner /
                                   ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["name"], "simonk-" + owner.removeprefix("SimonK").lower())
            self.assertEqual(manifest["skills"], "./skills/")
            self.assertEqual(manifest["author"]["name"], "Simon Kim")
            self.assertNotIn("hooks", manifest)

    def test_existing_output_is_never_overwritten(self):
        self.output.mkdir()
        sentinel = self.output / "keep.txt"
        sentinel.write_text("keep", encoding="utf-8")
        with patch.object(bundle, "verify_bundle", return_value=self.receipt):
            with self.assertRaises(ValueError):
                self.module.build_overlay(self.candidate, self.candidate_digest, self.output)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_tampered_generated_or_extra_member_fails_verification(self):
        with patch.object(bundle, "verify_bundle", return_value=self.receipt):
            result = self.module.build_overlay(self.candidate, self.candidate_digest, self.output)
            target = self.output / "plugins/SimonKCore/.codex-plugin/plugin.json"
            target.write_bytes(target.read_bytes() + b" ")
            with self.assertRaises(ValueError):
                self.module.verify_overlay(self.output, result["overlay_digest"])
            target.write_bytes(target.read_bytes()[:-1])
            extra = self.output / "plugins/SimonKCore/untracked.txt"
            extra.write_text("extra", encoding="utf-8")
            with self.assertRaises(ValueError):
                self.module.verify_overlay(self.output, result["overlay_digest"])

    def test_wrong_candidate_digest_stops_before_publication(self):
        with patch.object(bundle, "verify_bundle", return_value=self.receipt):
            with self.assertRaises(ValueError):
                self.module.build_overlay(self.candidate, "0" * 64, self.output)
        self.assertFalse(self.output.exists())

    def test_zoom_out_policy_or_projected_skill_tamper_fails(self):
        with patch.object(bundle, "verify_bundle", return_value=self.receipt):
            result = self.module.build_overlay(self.candidate, self.candidate_digest, self.output)
            for relative in (self.zoom_path,
                             "plugins/SimonKStack/skills/zoom-out/agents/openai.yaml"):
                with self.subTest(relative=relative):
                    target = self.output / relative
                    before = target.read_bytes()
                    target.write_bytes(before + b" ")
                    with self.assertRaises(ValueError):
                        self.module.verify_overlay(self.output, result["overlay_digest"])
                    target.write_bytes(before)


if __name__ == "__main__":
    unittest.main()
