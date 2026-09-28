"""version_gap.py: fixture-only checks plus one check of the real vibe folder.

Fixtures live in temp dirs. No network, no real agent CLI, no writes outside
temp. test_real_vibe_skill_versions_agree reads skills-src/vibe read-only and
fails while SKILL.md, evals/cases.json and CHANGELOG.md disagree.
"""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
REAL_SKILL = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
import version_gap  # noqa: E402

CHANGELOG = "# Changelog\n\n## {v} - 2026-01-01\n\n- fixture\n"


def make_skill(root, skill="1.2.3", cases="1.2.3", changelog=None, name="fixture"):
    root = Path(root)
    (root / "evals").mkdir(parents=True, exist_ok=True)
    (root / "SKILL.md").write_bytes(
        ("---\nname: %s\ndescription: 'Synthetic fixture: not a real skill'\n"
         "version: %s\n---\n\n# fixture\n" % (name, skill)).encode("utf-8"))
    (root / "evals" / "cases.json").write_bytes(json.dumps(
        {"skill": name, "version": cases, "cases": []}).encode("utf-8"))
    text = changelog if changelog is not None else CHANGELOG.format(v=skill)
    (root / "CHANGELOG.md").write_bytes(text.encode("utf-8"))
    return root


def snapshot(root):
    return sorted((str(p.relative_to(root)), p.stat().st_mtime_ns,
                   p.read_bytes() if p.is_file() else b"")
                  for p in Path(root).rglob("*"))


def run_main(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = version_gap.main(list(argv))
    return code, out.getvalue()


class VersionGapFixtureTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="vibe-version-gap-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()

    def check(self, skill_dir):
        code, out = run_main("check", "--skill", str(skill_dir))
        return code, json.loads(out)

    def test_check_consistent(self):
        skill = make_skill(self.root / "a")
        code, result = self.check(skill)
        self.assertEqual(code, 0, result)
        self.assertEqual((result["skill_md"], result["cases"], result["changelog"]),
                         ("1.2.3", "1.2.3", "1.2.3"))
        self.assertIs(result["consistent"], True)

    def test_check_inconsistent(self):
        skill = make_skill(self.root / "a", skill="1.2.4", changelog=CHANGELOG.format(v="1.2.3"))
        code, result = self.check(skill)
        self.assertEqual(code, 1, result)
        self.assertIs(result["consistent"], False)
        self.assertEqual(result["skill_md"], "1.2.4")
        self.assertEqual(result["errors"], [])

    def test_check_unreleased_heading_above_is_allowed(self):
        text = ("# Changelog\n\n## Unreleased\n\n- pending\n\n"
                "## 1.2.3 - 2026-01-01\n\n- x\n\n## 1.2.2 - 2025-12-31\n")
        code, result = self.check(make_skill(self.root / "a", changelog=text))
        self.assertEqual(code, 0, result)
        self.assertEqual(result["changelog"], "1.2.3")

    def test_check_keep_a_changelog_brackets(self):
        text = "# Changelog\n\n## [Unreleased]\n\n## [1.2.3] - 2026-01-01\n"
        code, result = self.check(make_skill(self.root / "a", changelog=text))
        self.assertEqual(code, 0, result)

    def test_check_other_heading_above_first_version_is_unreadable(self):
        text = "# Changelog\n\n## Notes\n\n## 1.2.3 - 2026-01-01\n"
        code, result = self.check(make_skill(self.root / "a", changelog=text))
        self.assertEqual(code, 2, result)
        self.assertIsNone(result["changelog"])

    def test_check_missing_or_unreadable_inputs(self):
        for member in ("SKILL.md", "evals/cases.json", "CHANGELOG.md"):
            skill = make_skill(self.root / member.replace("/", "_"))
            (skill / member).unlink()
            code, result = self.check(skill)
            self.assertEqual(code, 2, member)
            self.assertIs(result["consistent"], False)
            self.assertEqual(len(result["errors"]), 1, result)
        skill = make_skill(self.root / "noheading", changelog="# Changelog\n\n- none\n")
        self.assertEqual(self.check(skill)[0], 2)
        skill = make_skill(self.root / "badjson")
        (skill / "evals" / "cases.json").write_bytes(b"{not json")
        self.assertEqual(self.check(skill)[0], 2)
        skill = make_skill(self.root / "nover", skill="")
        self.assertEqual(self.check(skill)[0], 2)

    def test_check_bom_and_crlf_everywhere(self):
        skill = make_skill(self.root / "a")
        for member in ("SKILL.md", "evals/cases.json", "CHANGELOG.md"):
            raw = (skill / member).read_bytes().replace(b"\n", b"\r\n")
            (skill / member).write_bytes(b"\xef\xbb\xbf" + raw)
        code, result = self.check(skill)
        self.assertEqual(code, 0, result)
        self.assertEqual(result["skill_md"], "1.2.3")

    def test_check_semver_suffixes(self):
        for version, heading in (("1.2.3-rc.1", "## 1.2.3-rc.1 - 2026-01-01"),
                                 ("1.2.3+build.5", "## [1.2.3+build.5]")):
            text = "# Changelog\n\n%s\n" % heading
            skill = make_skill(self.root / version.replace("+", "_"), skill=version,
                               cases=version, changelog=text)
            code, result = self.check(skill)
            self.assertEqual(code, 0, result)
            self.assertEqual(result["changelog"], version)

    def test_check_heading_variants_are_version_headings(self):
        # release-please / conventional-changelog link headings, `v`/`V`,
        # colon and up to three leading spaces.
        for index, heading in enumerate((
                "## [1.2.3](https://example.invalid/compare/v1.2.2...v1.2.3) (2026-01-01)",
                "## V1.2.3", "## 1.2.3: title", "   ## 1.2.3")):
            text = "# Changelog\n\n## [Unreleased](https://example.invalid)\n\n%s\n" % heading
            code, result = self.check(make_skill(self.root / str(index), changelog=text))
            self.assertEqual(code, 0, (heading, result))

    def test_check_four_part_version_is_not_semver(self):
        text = "# Changelog\n\n## 1.2.3.4\n\n## 1.2.3\n"
        code, result = self.check(make_skill(self.root / "a", changelog=text))
        self.assertEqual(code, 2, result)

    def test_check_skips_comments_and_nested_fences(self):
        text = ("# Changelog\n\n<!--\n## 9.9.9 - template\n-->\n\n"
                "````md\n```\n~~~\n## 9.9.8\n```\n````\n\n## 1.2.3 - 2026-01-01\n")
        code, result = self.check(make_skill(self.root / "a", changelog=text))
        self.assertEqual(code, 0, result)
        self.assertEqual(result["changelog"], "1.2.3")

    def test_check_unreleased_only_is_unreadable(self):
        text = "# Changelog\n\n## Unreleased\n\n- pending\n"
        code, result = self.check(make_skill(self.root / "a", changelog=text))
        self.assertEqual(code, 2, result)
        self.assertIsNone(result["changelog"])

    def test_check_malformed_frontmatter_is_unreadable(self):
        bodies = {
            "unclosed": b"---\nname: fixture\nversion: 1.2.3\n# body\n",
            "leading_blank": b"\n---\nname: fixture\nversion: 1.2.3\n---\n",
            "nested": b"---\nname: fixture\nmetadata:\n  version: 1.2.3\n---\n",
            "not_semver": b"---\nname: fixture\nversion: 1.2\n---\n",
            "open_quote": b"---\nname: fixture\nversion: \"1.2.3\n---\n",
            "duplicate": b"---\nname: fixture\nversion: 1.2.3\nversion: 9.9.9\n---\n",
            "not_utf8": b"---\nname: fixture\ndescription: \xc7\xd1\nversion: 1.2.3\n---\n",
        }
        for label, body in bodies.items():
            skill = make_skill(self.root / label)
            (skill / "SKILL.md").write_bytes(body)
            code, result = self.check(skill)
            self.assertEqual(code, 2, label)
            self.assertIsNone(result["skill_md"], label)
        skill = make_skill(self.root / "comment")
        (skill / "SKILL.md").write_bytes(b"---\nname: fixture\nversion: '1.2.3' # pin\n---\n")
        self.assertEqual(self.check(skill)[0], 0)

    def test_gap_prerelease_precedence(self):
        source = make_skill(self.root / "src", skill="2.13.0-rc.1")
        running = make_skill(self.root / "run", skill="2.13.0")
        code, out = run_main("gap", "--running", str(running), "--source", str(source))
        self.assertEqual(code, 1)
        self.assertIn("실행본이 소스보다 앞선다", out)
        code, out = run_main("gap", "--running", str(source), "--source", str(running))
        self.assertEqual(code, 1)
        self.assertIn("설치 갱신 필요", out)

    def test_check_and_gap_never_write(self):
        source = make_skill(self.root / "src")
        running = make_skill(self.root / "run", skill="1.0.0")
        before = snapshot(self.root)
        self.check(source)
        run_main("gap", "--running", str(running), "--source", str(source), "--json")
        self.assertEqual(snapshot(self.root), before)

    def test_gap_equal(self):
        source = make_skill(self.root / "src")
        running = make_skill(self.root / "run")
        code, out = run_main("gap", "--running", str(running), "--source", str(source))
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "fixture 실행본과 소스 버전 일치 (1.2.3)")

    def test_gap_differ(self):
        source = make_skill(self.root / "src", skill="2.13.0")
        running = make_skill(self.root / "run", skill="2.11.6")
        code, out = run_main("gap", "--running", str(running), "--source", str(source))
        self.assertEqual(code, 1)
        self.assertEqual(out.strip(), "fixture 실행본 2.11.6 ≠ 소스 2.13.0 (설치 갱신 필요)")

    def test_gap_running_ahead_of_source(self):
        source = make_skill(self.root / "src", skill="1.0.0")
        running = make_skill(self.root / "run", skill="1.1.0")
        code, out = run_main("gap", "--running", str(running), "--source", str(source))
        self.assertEqual(code, 1)
        self.assertIn("실행본이 소스보다 앞선다", out)

    def test_gap_unreadable(self):
        source = make_skill(self.root / "src")
        code, out = run_main("gap", "--running", str(self.root / "missing"),
                             "--source", str(source))
        self.assertEqual(code, 2)
        self.assertIn("버전 읽기 실패", out)

    def test_gap_json(self):
        source = make_skill(self.root / "src", skill="2.0.0")
        running = make_skill(self.root / "run", skill="1.9.9")
        code, out = run_main("gap", "--running", str(running), "--source", str(source), "--json")
        result = json.loads(out)
        self.assertEqual(code, 1)
        self.assertIs(result["equal"], False)
        self.assertEqual((result["running"]["version"], result["source"]["version"]),
                         ("1.9.9", "2.0.0"))
        self.assertEqual(result["skill"], "fixture")

    def test_gap_resolves_linked_install_for_display(self):
        source = make_skill(self.root / "src")
        link = self.root / "installed"
        try:
            os.symlink(source, link, target_is_directory=True)
        except (OSError, NotImplementedError):
            try:
                import _winapi
                _winapi.CreateJunction(str(source), str(link))
            except (ImportError, AttributeError, OSError):
                self.skipTest("no symlink or junction support here")
        self.addCleanup(lambda: link.exists() and (os.rmdir(link) if os.name == "nt"
                                                   else link.unlink()))
        code, out = run_main("gap", "--running", str(link), "--source", str(source), "--json")
        result = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(result["running"]["path"], str(link))
        self.assertEqual(result["running"]["resolved"], str(source.resolve()))
        self.assertTrue(source.joinpath("SKILL.md").is_file())

    def test_cli_prints_utf8_under_ascii_stdio(self):
        source = make_skill(self.root / "src", skill="2.13.0")
        running = make_skill(self.root / "run", skill="2.11.6")
        env = dict(os.environ)
        env.pop("PYTHONUTF8", None)
        env["PYTHONIOENCODING"] = "ascii"
        proc = subprocess.run([sys.executable, "-B", str(SCRIPTS / "version_gap.py"), "gap",
                               "--running", str(running), "--source", str(source)],
                              cwd=str(self.root), env=env, capture_output=True, timeout=60)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(proc.stdout.decode("utf-8").strip(),
                         "fixture 실행본 2.11.6 ≠ 소스 2.13.0 (설치 갱신 필요)")
        proc = subprocess.run([sys.executable, "-B", str(SCRIPTS / "version_gap.py"), "check",
                               "--skill", str(source)],
                              cwd=str(self.root), env=env, capture_output=True, timeout=60)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(json.loads(proc.stdout.decode("utf-8"))["skill_md"], "2.13.0")


class RealVibeSkillTests(unittest.TestCase):
    def test_real_vibe_skill_versions_agree(self):
        # Expected to fail until SKILL.md, evals/cases.json and CHANGELOG.md
        # carry the same version. Do not weaken this test to make it pass.
        code, result = version_gap.check(REAL_SKILL)
        self.assertEqual(code, 0, json.dumps(result, ensure_ascii=False))
        self.assertIs(result["consistent"], True)


if __name__ == "__main__":
    unittest.main()
