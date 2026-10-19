"""claude.ai app skill ZIP regressions; every file is written inside a temp directory."""
import importlib.util
import json
import os
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

    def test_output_folder_inside_the_skill_is_never_packaged(self):
        d = self.skill("self-out", "name: self-out\ndescription: Use when x.\n",
                       extra={"a.md": "a\n", "stale.zip.tmp": "partial"})
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(d)
        mod.build(d, "dist")  # the reported case: --out dist, run from inside the skill
        first = (d / "dist" / "self-out.zip").read_bytes()
        report = mod.build(d, "dist")
        self.assertEqual(report["files"], ["SKILL.md", "a.md"])
        self.assertEqual(first, (d / "dist" / "self-out.zip").read_bytes())

        same = self.skill("same-out", "name: same-out\ndescription: Use when x.\n", extra={"a.md": "a\n"})
        mod.build(same, same)  # --out is the skill folder itself
        self.assertEqual(mod.build(same, same)["files"], ["SKILL.md", "a.md"])

    def test_yaml_comments_are_ignored(self):
        d = self.skill(
            "note-skill",
            "# leading comment\n"
            "name: note-skill  # the folder name\n"
            "# between keys\n"
            "description: Use when x. # trailing\n"
            "allowed-tools:\n  # tools the skill may call\n  - Read\n  - Bash  # shell\n"
            "notes: |\n  # literal content, not a comment\n  second line\n"
            "# after the block\n"
            "version: '1.0' # quoted, then a comment\n"
            "topic: C#, F# # languages\n",
        )
        report = mod.build(d, self.out)
        self.assertEqual(report["description_chars"], len("Use when x."))
        skill_md = self.read_zip("note-skill")["note-skill/SKILL.md"]
        self.assertTrue(skill_md.startswith("---\nname: note-skill\ndescription: Use when x.\nmetadata:\n"))
        self.assertIn('  allowed-tools: "Read, Bash"\n', skill_md)
        self.assertIn('  notes: "# literal content, not a comment\\nsecond line"\n', skill_md)
        self.assertIn('  version: "1.0"\n', skill_md)
        self.assertIn('  topic: "C#, F#"\n', skill_md)
        for gone in ("leading comment", "between keys", "after the block", "trailing", "languages"):
            self.assertNotIn(gone, skill_md)

        quoted = self.skill("hash-skill", 'name: hash-skill\ndescription: "Use when #tags matter." # c\n')
        self.assertEqual(mod.build(quoted, self.out)["description_chars"], len("Use when #tags matter."))
        multi = self.skill("multi-skill", 'name: multi-skill\ndescription: "Use when\n  #tag shows up."\n')
        mod.build(multi, self.out)  # a '#' line inside an open quote is text; dropping it would unbalance the quote
        self.assertIn('description: "Use when\n  #tag shows up."\n', self.read_zip("multi-skill")["multi-skill/SKILL.md"])

    def test_executable_helpers_keep_their_exec_bit(self):
        d = self.skill(
            "exec-skill", "name: exec-skill\ndescription: Use when x.\n",
            extra={"scripts/run.sh": "#!/bin/sh\necho hi\n", "scripts/tool.py": "print(1)\n", "notes.md": "n\n"},
        )
        if os.name != "nt":  # an exec bit only exists on POSIX; SKILL.md stays 0644 regardless
            os.chmod(d / "scripts" / "tool.py", 0o755)
            os.chmod(d / "SKILL.md", 0o755)
        tool_mode = 0o644 if os.name == "nt" else 0o755
        report = mod.build(d, self.out)
        with zipfile.ZipFile(self.out / "exec-skill.zip") as z:
            infos = z.infolist()
        self.assertEqual({i.create_system for i in infos}, {3})
        modes = {i.filename.split("/", 1)[1]: i.external_attr >> 16 for i in infos}
        self.assertEqual(modes, {
            "SKILL.md": 0o100644, "notes.md": 0o100644,
            "scripts/run.sh": 0o100755, "scripts/tool.py": 0o100000 | tool_mode,
        })
        self.assertEqual(sorted(report["executables"]),
                         sorted(["scripts/run.sh"] + (["scripts/tool.py"] if tool_mode == 0o755 else [])))

    def test_secret_files_are_never_packaged(self):
        secrets = {
            ".env": "TOKEN=sk-live-123\n", ".env.local": "K=v\n", "config/.env": "X=1\n",
            "keys/server.pem": "pem\n", "keys/api.key": "k\n", "certs/a.p12": "p\n", "certs/b.pfx": "p\n",
            "id_rsa": "k\n", "ssh/id_ed25519.pub": "k\n", ".npmrc": "t\n", "home/.netrc": "t\n", ".pypirc": "t\n",
        }
        keep = {"scripts/env.py": "print(1)\n", "environment.md": "e\n", "keys/README.md": "r\n"}
        d = self.skill("secret-skill", "name: secret-skill\ndescription: Use when x.\n", extra={**secrets, **keep})
        report = mod.build(d, self.out, include=["*"])
        self.assertEqual(sorted(self.read_zip("secret-skill")),
                         sorted(f"secret-skill/{p}" for p in ["SKILL.md", *keep]))
        self.assertEqual(sorted(report["excluded_secrets"]), sorted(secrets))
        self.assertNotIn("sk-live-123", json.dumps(report))
        with self.assertRaises(mod.BuildError):
            mod.build(d, self.out, include=[".env"])

    def test_compatibility_is_written_as_one_string(self):
        cases = {
            "flow-compat": ("compatibility: [claude-code, codex]\ntags: [a, 'b c']\n", "claude-code, codex"),
            "block-compat": ("compatibility:\n  - claude-code\n  - grok\n", "claude-code, grok"),
            "plain-compat": ("compatibility: Requires Python 3.11\n", "Requires Python 3.11"),
        }
        for name, (fm, want) in cases.items():
            with self.subTest(name=name):
                mod.build(self.skill(name, f"name: {name}\ndescription: Use when x.\n{fm}"), self.out)
                skill_md = self.read_zip(name)[f"{name}/SKILL.md"]
                self.assertIn(f"\ncompatibility: {json.dumps(want)}\n", skill_md)
                self.assertEqual(top_keys(skill_md)[:3], ["name", "description", "compatibility"])
        self.assertIn('  tags: "a, b c"\n', self.read_zip("flow-compat")["flow-compat/SKILL.md"])
        for name, value in {"long-compat": "x" * 501, "empty-compat": "[]"}.items():
            with self.subTest(name=name):
                with self.assertRaises(mod.BuildError):
                    mod.build(self.skill(name, f"name: {name}\ndescription: Use when x.\ncompatibility: {value}\n"),
                              self.out)

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
