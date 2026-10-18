"""claude.ai app skill ZIP regressions; every file is written inside a temp directory."""
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "claude_app_skill_zip.py"
spec = importlib.util.spec_from_file_location("claude_app_skill_zip", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

APP_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}


def top_keys(skill_md):
    fm, _ = mod.split_frontmatter(skill_md)
    return [e[0] for e in mod.parse_entries(fm)]


class AppSkillZipTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.out = self.root / "out"

    def skill(self, name, frontmatter, body="# body\n", extra=None):
        d = self.root / "src" / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"---\n{frontmatter}---\n{body}", encoding="utf-8")
        for rel, text in (extra or {}).items():
            p = d / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        return d

    def read_zip(self, name):
        with zipfile.ZipFile(self.out / f"{name}.zip") as z:
            return {i.filename: z.read(i).decode("utf-8") for i in z.infolist()}

    def test_moves_unknown_keys_into_metadata_and_drops_evals(self):
        d = self.skill(
            "demo-skill",
            'name: demo-skill\ndescription: "Use when \\"demo\\" is asked."\n'
            "allowed-tools: Read, Bash\nversion: 1.0.0\nauthor: simon-stack\n",
            extra={"references/a.md": "ref\n", "evals/cases.json": "[]", "x.bak": "old"},
        )
        report = mod.build(d, self.out)
        files = self.read_zip("demo-skill")
        self.assertEqual(sorted(files), ["demo-skill/SKILL.md", "demo-skill/references/a.md"])
        skill_md = files["demo-skill/SKILL.md"]
        self.assertEqual(top_keys(skill_md), ["name", "description", "metadata"])
        self.assertIn('  version: "1.0.0"\n', skill_md)
        self.assertIn('  author: "simon-stack"\n', skill_md)
        self.assertIn('  allowed-tools: "Read, Bash"\n', skill_md)
        self.assertTrue(skill_md.endswith("---\n# body\n"))
        self.assertEqual(report["moved_to_metadata"], ["allowed-tools", "version", "author"])

    def test_appends_to_existing_metadata_block(self):
        d = self.skill("meta-skill", "name: meta-skill\ndescription: Use when x.\nmetadata:\n    owner: s\nversion: '2'\n")
        mod.build(d, self.out)
        skill_md = self.read_zip("meta-skill")["meta-skill/SKILL.md"]
        self.assertIn("metadata:\n    owner: s\n    version: \"2\"\n---\n", skill_md)

    def test_metadata_key_clash_is_refused(self):
        d = self.skill("clash-skill", "name: clash-skill\ndescription: Use when x.\nmetadata:\n  version: a\nversion: b\n")
        with self.assertRaises(mod.BuildError):
            mod.build(d, self.out)

    def test_rejects_bad_name_long_description_and_xml(self):
        cases = {
            "wrong-name": "name: other\ndescription: Use when x.\n",
            "long-desc": "name: long-desc\ndescription: " + "a" * 1025 + "\n",
            "xml-desc": "name: xml-desc\ndescription: Use when <b>bold</b>.\n",
            "claude-thing": "name: claude-thing\ndescription: Use when x.\n",
        }
        for name, fm in cases.items():
            with self.subTest(name=name):
                with self.assertRaises(mod.BuildError):
                    mod.build(self.skill(name, fm), self.out)

    def test_folded_description_counts_joined_text(self):
        d = self.skill("folded-skill", "name: folded-skill\ndescription: >\n  Use when one.\n  Then two.\n")
        report = mod.build(d, self.out)
        self.assertEqual(report["description_chars"], len("Use when one. Then two."))

    def test_override_skill_md_include_subset_and_strict(self):
        d = self.skill(
            "big-skill", "name: big-skill\ndescription: Use when x.\nversion: 9\n",
            body="Read ${CLAUDE_SKILL_DIR}/references/keep.md\n",
            extra={"references/keep.md": "keep\n", "references/drop.md": "drop\n"},
        )
        with self.assertRaises(mod.BuildError):
            mod.build(d, self.out, strict=True)
        app_md = self.root / "app-SKILL.md"
        app_md.write_text("---\nname: big-skill\ndescription: Use when x in the app.\n---\nRead references/keep.md\n",
                          encoding="utf-8")
        report = mod.build(d, self.out, skill_md=app_md, include=["references/keep.md"], strict=True)
        self.assertEqual(report["files"], ["SKILL.md", "references/keep.md"])
        self.assertEqual(report["claude_code_only"], {})
        self.assertIn("in the app", self.read_zip("big-skill")["big-skill/SKILL.md"])
        with self.assertRaises(mod.BuildError):
            mod.build(d, self.out, skill_md=app_md, include=["references/none.md"])

    def test_output_is_deterministic(self):
        d = self.skill("same-skill", "name: same-skill\ndescription: Use when x.\n", extra={"b.md": "b\n", "a.md": "a\n"})
        mod.build(d, self.out)
        first = (self.out / "same-skill.zip").read_bytes()
        mod.build(d, self.out)
        self.assertEqual(first, (self.out / "same-skill.zip").read_bytes())

    def test_repo_skills_for_the_app_profile_build_cleanly(self):
        for name in ("karpathy-guidelines", "simon-design-first"):
            with self.subTest(name=name):
                report = mod.build(REPO / "skills-src" / name, self.out, strict=True)
                skill_md = self.read_zip(name)[f"{name}/SKILL.md"]
                self.assertLessEqual(set(top_keys(skill_md)), APP_KEYS)
                self.assertNotIn("evals/cases.json", report["files"])

    def test_cli_reports_json_and_error_exit(self):
        d = self.skill("cli-skill", "name: cli-skill\ndescription: Use when x.\n")
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(mod.main([str(d), "--out", str(self.out)]), 0)
        self.assertEqual(json.loads(buf.getvalue())["name"], "cli-skill")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(mod.main([str(self.root / "missing"), "--out", str(self.out)]), 2)


if __name__ == "__main__":
    unittest.main()
