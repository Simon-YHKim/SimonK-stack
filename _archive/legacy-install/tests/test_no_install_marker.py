"""D-68: a skills-src folder marked .simonk-no-install never reaches an install target.

Offline and confined to a temporary directory. install.sh (TEST_MODE) and
setup-repo.sh (vendor mode) run whole, with git/bun stubbed. The SessionStart
copy loop (held on main by D-33) and the vendored hook loop are sliced from the
real scripts and executed against fixtures, so the guarded code itself runs.
"""
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
MARKER = ".simonk-no-install"
RETIRED = "investigate"
SENTINEL = "gstack copy sentinel\n"
BASH = (Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"
        if os.name == "nt" else Path(shutil.which("bash") or "/missing/bash"))


def posix(path):
    path = Path(path).absolute()
    if os.name == "nt":
        return "/" + path.drive[0].lower() + path.as_posix()[2:]
    return str(path)


def between(text, start, end):
    head = text.index(start)
    return text[head:text.index(end, head)]


def skill_dirs(root):
    return {p.name for p in root.iterdir() if (p / "SKILL.md").is_file()}


class RetiredSourceTests(unittest.TestCase):
    def test_retired_source_is_kept_marked_and_documented(self):
        self.assertTrue((ROOT / "skills-src" / RETIRED / "SKILL.md").is_file())
        marked = sorted(p.parent.name for p in (ROOT / "skills-src").glob("*/" + MARKER))
        self.assertEqual(marked, [RETIRED])
        entry = between((ROOT / "skills-src/VENDORED.md").read_text(encoding="utf-8"),
                        "- `investigate`", "\n- `land-and-deploy`")
        for needle in ("D-68", MARKER, "재개 조건", "30일", "deny", "상주"):
            self.assertIn(needle, entry)


@unittest.skipUnless(BASH.is_file(), "Git Bash/POSIX Bash is required")
class NoInstallMarkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="simonk no install ")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.home = self.base / "home"
        (self.home / ".claude/skills").mkdir(parents=True)

    def bash(self, program, *args, cwd=None, **extra):
        env = dict(os.environ, HOME=posix(self.home), USERPROFILE=str(self.home), **extra)
        return subprocess.run([str(BASH), "--noprofile", "--norc", "-s", "--", *args],
                              input=program, text=True, encoding="utf-8", capture_output=True,
                              cwd=cwd or self.base, env=env, timeout=300)

    def script(self, relative):
        path = ROOT / relative
        # stdin keeps CRLF working copies runnable; BASH_ARGV0 keeps $0 = the real script.
        stubs = "git() { return 97; }; bun() { return 98; }\n"
        return "BASH_ARGV0=" + shlex.quote(path.as_posix()) + "\n" + stubs + path.read_text(encoding="utf-8")

    def put(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def fixture_repo(self):
        repo = self.base / "fixture repo"
        self.put(repo / "skills-src" / RETIRED / "SKILL.md", "---\nname: investigate\n---\nold\n")
        self.put(repo / "skills-src" / RETIRED / MARKER, "D-68\n")
        self.put(repo / "skills-src/plain/SKILL.md", "---\nname: plain\n---\nnew\n")
        return repo

    def test_install_sh_force_never_replaces_the_marked_name(self):
        target = self.base / "target"
        self.put(target / RETIRED / "SKILL.md", SENTINEL)
        result = self.bash(self.script("scripts/install.sh"), "--force",
                           SIMONK_SKILLS_TARGET=posix(target),
                           SIMONK_PLUGIN_CACHE=posix(self.base / "cache"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("skip (no-install marker, D-68): " + RETIRED, result.stdout)
        self.assertEqual((target / RETIRED / "SKILL.md").read_text(encoding="utf-8"), SENTINEL)
        self.assertEqual(sorted(p.name for p in (target / RETIRED).iterdir()), ["SKILL.md"])
        expected = skill_dirs(ROOT / "skills")
        self.assertIn(RETIRED, expected)  # root skills/ still holds it; the guard is what skips it
        self.assertEqual(skill_dirs(target), expected)
        self.assertEqual((target / "debug/SKILL.md").read_bytes(), (ROOT / "skills/debug/SKILL.md").read_bytes())

    def test_setup_repo_vendor_mode_skips_the_marked_name(self):
        project = self.base / "project"
        project.mkdir()
        result = self.bash(self.script("scripts/setup-repo.sh"), posix(project))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("skip (no-install marker, D-68): " + RETIRED, result.stdout)
        copied = skill_dirs(project / ".claude/skills")
        expected = (skill_dirs(ROOT / "skills-src") | skill_dirs(ROOT / ".claude/skills")) - {RETIRED}
        self.assertEqual(copied, expected)
        hook = (project / ".claude/hooks/session-start.sh").read_text(encoding="utf-8")
        self.assertIn('[ -e "$d/.simonk-no-install" ] && continue', hook)

    def test_session_start_copy_loop_skips_marked_folder_even_when_forced(self):
        repo = self.fixture_repo()
        self.put(repo / "skills-src/retired-new/SKILL.md", "---\nname: retired-new\n---\nx\n")
        self.put(repo / "skills-src/retired-new" / MARKER, "D-68\n")
        installed = self.home / ".claude/skills"
        self.put(installed / RETIRED / "SKILL.md", SENTINEL)
        self.put(installed / "plain/SKILL.md", "old\n")
        loop = between((ROOT / ".claude/hooks/session-start.sh").read_text(encoding="utf-8"),
                       "count_new=0\n", 'log "Skills: new=')
        program = ("set -euo pipefail\nlog() { echo \"$*\"; }\n"
                   "REPO_DIR=" + shlex.quote(posix(repo)) + "\n"
                   'CHANGED_SET=" investigate plain retired-new "\n' + loop
                   + 'echo "new=$count_new updated=$count_updated skipped=$count_skipped"\n')
        result = self.bash(program, SIMON_STACK_FORCE_SYNC="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("new=0 updated=1 skipped=0", result.stdout)
        self.assertEqual((installed / RETIRED / "SKILL.md").read_text(encoding="utf-8"), SENTINEL)
        self.assertFalse((installed / "retired-new").exists())
        self.assertIn("new", (installed / "plain/SKILL.md").read_text(encoding="utf-8"))

    def test_vendored_hook_loop_skips_marked_folder(self):
        repo = self.fixture_repo()
        loop = between((ROOT / "scripts/setup-repo.sh").read_text(encoding="utf-8"),
                       "# --- simon-stack skills from THIS repo ---", "# --- INDEX + instincts")
        program = "set -euo pipefail\nREPO_DIR=" + shlex.quote(posix(repo)) + "\n" + loop
        result = self.bash(program)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(skill_dirs(self.home / ".claude/skills"), {"plain"})


if __name__ == "__main__":
    unittest.main()
