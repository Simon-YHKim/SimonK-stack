"""Codex general-skill projection must not expose unported safety policies."""
import base64
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import codex_overlay

OWNERS = ("SimonKAIHub", "SimonKCore", "SimonKDesign", "SimonKMarket", "SimonKStack")
BASES = {"SimonKAIHub": "AI 제품/기능 빌드 오케스트레이션 플러그인 (fixture)",
         "SimonKCore": "SimonK 플러그인 공유 인프라 (위임·모델라우팅·fixture)",
         "SimonKDesign": "디자인 fixture 플러그인",
         "SimonKMarket": "마켓 fixture 플러그인",
         "SimonKStack": "제품/서비스 빌드 오케스트레이션 플러그인"}
CORE_TEXT = BASES["SimonKCore"] + ". Codex판에는 Claude Code 전용인 careful·unfreeze 안전 스킬이 없다."
STACK_TEXT = (BASES["SimonKStack"]
              + ". Codex판에는 Claude Code 전용인 freeze·guard·investigate 안전 스킬이 없다.")


def _sha(data):
    return hashlib.sha256(data).hexdigest()


@unittest.skipUnless(os.name == "nt", "Pinned package I/O is Windows-only")
class CodexSafeSubsetTests(unittest.TestCase):
    def setUp(self):
        helper = ROOT / "scripts/codex_safe_subset.py"
        self.assertTrue(helper.is_file(), "Codex safe-subset builder is missing")
        spec = importlib.util.spec_from_file_location("codex_safe_subset", helper)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.r = self.module.r
        self.temp = tempfile.TemporaryDirectory(prefix="vibe-codex-subset-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "verified-v2-overlay"
        self.output = self.root / "general-subset"
        self.source_digest = self.make_source(self.source)

    def put(self, relative, data, root=None):
        target = (self.source if root is None else root) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def make_source(self, root, version="1.10.0", bases=None):
        """A v2-overlay-shaped fixture; the version changes only version-bearing bytes."""
        bases = dict(BASES, **(bases or {}))
        root.mkdir()
        self.put("overlay.json", f'{{"fixture":"{version}"}}\n'.encode(), root)
        self.put("bundle.json", f'{{"release":"{version}"}}\n'.encode(), root)
        for owner in OWNERS:
            description = bases[owner]
            if owner in self.module.bundle.DESCRIPTION_NOTICES:
                description += ". " + self.module.bundle.DESCRIPTION_NOTICES[owner]
            name = "simonk-" + owner.removeprefix("SimonK").lower()
            claude = {"name": name, "version": version, "description": description,
                      "author": {"name": "Simon Kim"}, "skills": ["./skills/vibe/"]}
            self.put(f"plugins/{owner}/.claude-plugin/plugin.json", self.r.encoded(claude), root)
            self.put(f"plugins/{owner}/.claude-plugin/marketplace.json",
                     self.r.encoded({"name": "fixture", "plugins": [{"name": name, "version": version}]}),
                     root)
            self.put(codex_overlay.overlay_path(owner), codex_overlay.codex_manifest(owner, claude), root)
        self.put("plugins/SimonKCore/skills/vibe/SKILL.md", b"---\nname: vibe\n---\nGeneral\n", root)
        for owner, name in (("SimonKCore", "careful"), ("SimonKStack", "guard"),
                            ("SimonKStack", "freeze"), ("SimonKStack", "investigate"),
                            ("SimonKCore", "unfreeze")):
            self.put(f"plugins/{owner}/skills/{name}/SKILL.md",
                     f"---\nname: {name}\n---\nClaude hook only\n".encode(), root)
            self.put(f"plugins/{owner}/skills/{name}/scripts/helper.py", b"print('fixture')\n", root)
        for owner in ("SimonKCore", "SimonKStack"):
            self.put(f"plugins/{owner}/.simonk-runtime/safety_runtime.py",
                     b"print('safety fixture')\n", root)
        return _sha((root / "overlay.json").read_bytes())

    def build(self, source=None, digest=None, output=None):
        with patch.object(codex_overlay, "verify_overlay", return_value={"installation_ready": False}):
            return self.module.build_subset(self.source if source is None else source,
                                            self.source_digest if digest is None else digest,
                                            self.output if output is None else output)

    def manifest(self, root, owner):
        return json.loads((root / codex_overlay.overlay_path(owner)).read_bytes())

    def test_excludes_safety_skills_dependent_unfreeze_and_runtime(self):
        before = {p.relative_to(self.source).as_posix(): p.read_bytes()
                  for p in self.source.rglob("*") if p.is_file()}
        result = self.build()
        with patch.object(codex_overlay, "verify_overlay", return_value={"installation_ready": False}):
            receipt = self.module.verify_subset(self.output, result["subset_digest"],
                                                self.source, self.source_digest)
        self.assertEqual(receipt["schema_version"], 2)
        self.assertEqual(receipt["decision_ref"], "D-29")
        self.assertEqual(len(receipt["excluded_skills"]), 5)
        # 5 skills x 2 files, 2 safety runtimes, 5 owners x .claude-plugin/{plugin,marketplace}.json
        self.assertEqual(len(receipt["excluded_members"]), 22)
        self.assertIn("simonk-core:unfreeze", receipt["excluded_skills"])
        self.assertTrue(any(".simonk-runtime" in row["path"]
                            for row in receipt["excluded_members"]))
        self.assertFalse(receipt["installation_ready"])
        self.assertFalse(receipt["host_compatibility_verified"])
        rewritten = {codex_overlay.overlay_path(owner) for owner in ("SimonKCore", "SimonKStack")}
        for relative, data in before.items():
            self.assertEqual((self.source / relative).read_bytes(), data)
            excluded = any(relative.startswith(prefix) for prefix in self.module.EXCLUDED_PREFIXES)
            self.assertEqual((self.output / relative).exists(), not excluded)
            if not excluded and relative not in rewritten:
                self.assertEqual((self.output / relative).read_bytes(), data)

    def test_claude_manifests_and_runtimes_are_not_shipped(self):
        result = self.build()
        for owner in OWNERS:
            self.assertFalse((self.output / f"plugins/{owner}/.claude-plugin").exists())
            self.assertTrue((self.output / codex_overlay.overlay_path(owner)).is_file())
        shipped = {p.relative_to(self.output).as_posix() for p in self.output.rglob("*") if p.is_file()}
        self.assertFalse(any("/.claude-plugin/" in path or "/.simonk-runtime/" in path
                             for path in shipped))
        receipt = self.module.verify_subset(self.output, result["subset_digest"])
        excluded = {row["path"] for row in receipt["excluded_members"]}
        for owner in OWNERS:
            self.assertIn(f"plugins/{owner}/.claude-plugin/plugin.json", excluded)
            self.assertIn(f"plugins/{owner}/.claude-plugin/marketplace.json", excluded)
        # A source without a Claude manifest cannot prove the omission.
        (self.source / "plugins/SimonKDesign/.claude-plugin/plugin.json").unlink()
        with self.assertRaises(ValueError):
            self.build(output=self.root / "second")
        self.assertFalse((self.root / "second").exists())

    def test_core_and_stack_describe_the_codex_edition(self):
        result = self.build()
        for owner, text in (("SimonKCore", CORE_TEXT), ("SimonKStack", STACK_TEXT)):
            manifest = self.manifest(self.output, owner)
            self.assertEqual(manifest["description"], text)
            self.assertEqual(manifest["interface"]["shortDescription"], text)
            self.assertEqual(manifest["interface"]["longDescription"], text)
            raw = (self.output / codex_overlay.overlay_path(owner)).read_text(encoding="utf-8")
            for claude_only in ("Windows", "claude plugin install", "레거시"):
                self.assertNotIn(claude_only, raw)
            source = self.manifest(self.source, owner)
            source["description"] = source["interface"]["shortDescription"] = text
            source["interface"]["longDescription"] = text
            self.assertEqual(manifest, source)  # nothing else changes
        for owner in ("SimonKAIHub", "SimonKDesign", "SimonKMarket"):
            path = codex_overlay.overlay_path(owner)
            self.assertEqual((self.output / path).read_bytes(), (self.source / path).read_bytes())
        receipt = self.module.verify_subset(self.output, result["subset_digest"])
        replaced = receipt["replaced_members"]
        self.assertEqual([row["path"] for row in replaced],
                         [codex_overlay.overlay_path(o) for o in ("SimonKCore", "SimonKStack")])
        for row in replaced:
            original = (self.source / row["path"]).read_bytes()
            self.assertEqual(base64.b64decode(row["original_base64"]), original)
            self.assertEqual((row["original_sha256"], row["original_size"]),
                             (_sha(original), len(original)))
            shipped = (self.output / row["path"]).read_bytes()
            self.assertEqual((row["sha256"], row["size"]), (_sha(shipped), len(shipped)))
        self.assertEqual(self.module.CODEX_NOTICES, {
            "SimonKCore": "Codex판에는 Claude Code 전용인 careful·unfreeze 안전 스킬이 없다.",
            "SimonKStack": "Codex판에는 Claude Code 전용인 freeze·guard·investigate 안전 스킬이 없다."})
        self.assertEqual(set(self.module.CODEX_NOTICES), set(self.module.bundle.DESCRIPTION_NOTICES))

    def test_rewrite_is_rederived_and_drift_fails_closed(self):
        self.build()
        # Re-pinned forgery: ship the Claude text again with every hash updated.
        path = codex_overlay.overlay_path("SimonKStack")
        original = (self.source / path).read_bytes()
        (self.output / path).write_bytes(original)
        receipt = json.loads((self.output / "subset.json").read_bytes())
        for row in receipt["included_members"] + receipt["replaced_members"]:
            if row["path"] == path:
                row["sha256"], row["size"] = _sha(original), len(original)
        manifests = {codex_overlay.overlay_path(o):
                     (self.output / codex_overlay.overlay_path(o)).read_bytes() for o in OWNERS}
        receipt["content_digest"] = self.module.content_digest(receipt["included_members"], manifests)
        forged = self.r.encoded(receipt)
        (self.output / "subset.json").write_bytes(forged)
        with self.assertRaisesRegex(ValueError, "rewrite differs"):
            self.module.verify_subset(self.output, _sha(forged))
        # A source whose description drifted from the projected notice is refused.
        drifted = self.root / "drifted"
        digest = self.make_source(drifted)
        manifest = self.manifest(drifted, "SimonKCore")
        manifest["description"] = manifest["interface"]["shortDescription"] = BASES["SimonKCore"]
        manifest["interface"]["longDescription"] = BASES["SimonKCore"]
        (drifted / codex_overlay.overlay_path("SimonKCore")).write_bytes(self.r.encoded(manifest))
        with self.assertRaisesRegex(ValueError, "Claude-only notice"):
            self.build(drifted, digest, self.root / "drifted-subset")
        self.assertFalse((self.root / "drifted-subset").exists())
        with self.assertRaises(ValueError):  # owners without safety skills are never rewritten
            self.module.codex_edition("SimonKDesign", (drifted / codex_overlay.overlay_path(
                "SimonKDesign")).read_bytes())

    def test_content_digest_ignores_the_release_version_but_not_content(self):
        first = self.build()
        later_source = self.root / "later-overlay"
        later = self.build(later_source, self.make_source(later_source, version="1.11.0"),
                           self.root / "later-subset")
        self.assertNotEqual(first["subset_digest"], later["subset_digest"])
        self.assertEqual(first["content_digest"], later["content_digest"])
        receipt = self.module.verify_subset(self.root / "later-subset", later["subset_digest"])
        self.assertEqual(receipt["content_digest"], later["content_digest"])
        self.assertEqual(self.manifest(self.root / "later-subset", "SimonKCore")["version"], "1.11.0")
        # Any shipped byte, including a description, is new content.
        changed_source = self.root / "changed-overlay"
        digest = self.make_source(changed_source)
        self.put("plugins/SimonKCore/skills/vibe/SKILL.md", b"---\nname: vibe\n---\nGeneral 2\n",
                 changed_source)
        changed = self.build(changed_source, digest, self.root / "changed-subset")
        self.assertNotEqual(changed["content_digest"], first["content_digest"])
        described_source = self.root / "described-overlay"
        digest = self.make_source(described_source, bases={"SimonKAIHub": "다른 설명"})
        described = self.build(described_source, digest, self.root / "described-subset")
        self.assertNotEqual(described["content_digest"], first["content_digest"])

    def test_cli_reports_the_content_digest_and_accepts_expected_digest(self):
        with patch.object(codex_overlay, "verify_overlay", return_value={"installation_ready": False}), \
                patch.object(sys, "stdout", io.StringIO()) as stdout:
            code = self.module.main(["build", "--source-overlay", str(self.source),
                                     "--overlay-digest", self.source_digest,
                                     "--output", str(self.output)])
        self.assertEqual(code, 0)
        built = json.loads(stdout.getvalue())
        self.assertRegex(built["content_digest"], r"\A[0-9a-f]{64}\Z")
        with patch.object(sys, "stdout", io.StringIO()) as stdout:
            code = self.module.main(["verify", "--package", str(self.output),
                                     "--expected-digest", built["subset_digest"]])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["content_digest"], built["content_digest"])
        with patch.object(sys, "stdout", io.StringIO()):
            self.assertEqual(self.module.main(["verify", "--package", str(self.output),
                                               "--subset-digest", "0" * 64]), 2)

    def test_reintroduced_safety_skill_and_changed_retained_file_fail(self):
        result = self.build()
        for unsafe in ("plugins/SimonKStack/skills/freeze/SKILL.md",
                       "plugins/SimonKCore/.claude-plugin/plugin.json"):
            with self.subTest(unsafe=unsafe):
                target = self.output / unsafe
                target.parent.mkdir(parents=True)
                target.write_text("unsafe", encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.module.verify_subset(self.output, result["subset_digest"])
                target.unlink()
                target.parent.rmdir()
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



class CodexCatalogTests(unittest.TestCase):
    """Hub D-88: Codex reads .agents/plugins/marketplace.json before the Claude
    catalog. Stage 1 kept it empty so Codex never installed the Claude build with
    its five safety skills; stage 2 points it at the verified Codex subset that
    dist carries under codex/plugins/ (never at plugins/, the Claude build)."""

    def test_codex_catalog_serves_only_the_dist_codex_subset(self):
        import json
        path = ROOT / ".agents" / "plugins" / "marketplace.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["name"], "simonk-stack")
        self.assertNotIn("version", data)
        self.assertIn("Codex edition", data["interface"]["displayName"])
        expected = {"simonk-core": "SimonKCore", "simonk-stack": "SimonKStack",
                    "simonk-aihub": "SimonKAIHub", "simonk-design": "SimonKDesign",
                    "simonk-market": "SimonKMarket"}
        self.assertEqual([item["name"] for item in data["plugins"]], list(expected))
        for item in data["plugins"]:
            with self.subTest(plugin=item["name"]):
                self.assertEqual(set(item), {"name", "source"})
                self.assertEqual(item["source"], {
                    "source": "git-subdir",
                    "url": "https://github.com/Simon-YHKim/SimonK-stack.git",
                    "path": f"codex/plugins/{expected[item['name']]}",
                    "ref": "dist",
                })
        # Codex picks the first catalog that exists, in this order.
        self.assertFalse((ROOT / ".agents" / "plugins" / "api_marketplace.json").exists())


if __name__ == "__main__":
    unittest.main()
