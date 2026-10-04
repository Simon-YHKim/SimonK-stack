"""Windows user-home installer (scripts/windows) against disposable homes only.

Every case passes -UserHome/-CodexHome/-ReleasesDir/-RepoRoot inside a temporary
directory, so the real ~/.claude, ~/.codex and Releases folders are never read or
written. No package build, model call or network access happens here.
"""
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts" / "windows"
PWSH = shutil.which("pwsh")
CORE = Path("candidate-safety/plugins/SimonKCore/skills")
# Junction name -> (home-relative link, candidate-relative target)
LINKS = {
    "claude-vibe": (".claude/skills/vibe", CORE / "vibe"),
    "claude-vibe-bot": (".claude/skills/vibe-bot", CORE / "vibe-bot"),
    "claude-model-router": (".claude/skills/model-router", CORE / "model-router"),
    "claude-simonk": (".claude/skills/simonk", CORE / "simonk"),
    "claude-multi-terminal-dispatcher": (".claude/skills/multi-terminal-dispatcher", CORE / "multi-terminal-dispatcher"),
    "claude-qa": (".claude/skills/qa", Path("candidate-safety/plugins/SimonKStack/skills/qa")),
    "codex-vibe": (".codex/skills/vibe", Path("codex-subset-safety/plugins/SimonKCore/skills/vibe")),
    "codex-vibe-bot": (".codex/skills/vibe-bot", Path("codex-subset-safety/plugins/SimonKCore/skills/vibe-bot")),
}
OLD = "20260101-vibe-100-aaaaaaa"
NEW = "20260102-vibe-110-bbbbbbb"


def skill_md(name, version):
    return f"---\nname: {name}\nversion: {version}\n---\nfixture {name}\n".encode()


@unittest.skipUnless(PWSH and os.name == "nt", "Windows PowerShell 7 is required")
class WindowsUpdateLocalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="winstall-test-", ignore_cleanup_errors=True)
        self.addCleanup(temporary.cleanup)
        self.root = Path(os.path.realpath(temporary.name))
        self.home = self.root / "home"
        self.codex = self.home / ".codex"
        self.releases = self.root / "releases"
        self.repo = self.root / "repo"
        self.archive_root = self.home / ".claude" / "flat-link-archive"
        (self.home / ".claude" / "skills").mkdir(parents=True)
        (self.codex / "skills").mkdir(parents=True)
        self.releases.mkdir()
        self.make_repo()
        self.make_candidate(OLD, self.commit_a, "1.0.0")
        self.make_candidate(NEW, "b" * 40, "1.1.0")
        for name, (link, rel) in LINKS.items():
            self.junction(self.home / link, self.candidate(OLD) / rel)
        self.config = self.codex / "config.toml"
        self.config.write_bytes(
            ('model = "fixture"\n\n[[skills.config]]\n# fixture comment\n'
             f'path = "{self.vibe_path(OLD)}"\nenabled = false\n').encode())
        for skill in ("careful", "freeze"):
            target = self.home / ".claude" / "skills" / skill
            target.mkdir()
            (target / "SKILL.md").write_bytes(skill_md(skill, "0.2.0"))

    # ------------------------------------------------------------ fixtures

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True,
                              text=True, encoding="utf-8").stdout.strip()

    def commit(self, message):
        self.git("add", "-A")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def write(self, relative, data):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def make_repo(self):
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "core.autocrlf", "false")
        for skill in ("vibe", "vibe-bot", "model-router", "simonk", "multi-terminal-dispatcher", "qa"):
            self.write(f"skills-src/{skill}/SKILL.md", skill_md(skill, "1.0.0"))
        for skill in ("careful", "freeze"):
            self.write(f"skills-src/{skill}/SKILL.md", skill_md(skill, "0.2.0"))
        self.write("distribution/skills-release.v1.json", b"{}\n")
        self.write("distribution/plugin-inputs.v1.json", json.dumps(
            {"schema_version": 1, "plugins": {"SimonKCore": {"name": "simonk-core", "commit": "c" * 40}}}).encode())
        self.write("docs/INSTALL.md", b"# fixture\n")
        self.commit_a = self.commit("fixture A")

    def candidate(self, tag):
        return self.releases / f"{tag}-candidate"

    def vibe_path(self, tag):
        return str(self.candidate(tag) / CORE / "vibe" / "SKILL.md").replace("\\", "/")

    def make_candidate(self, tag, main, version):
        for name, (link, rel) in LINKS.items():
            folder = self.candidate(tag) / rel
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "SKILL.md").write_bytes(skill_md(rel.name, version))
        (self.releases / f"{tag}-receipts.json").write_text(json.dumps({"main": main}), encoding="utf-8")

    @staticmethod
    def junction(link, target):
        import _winapi
        link.parent.mkdir(parents=True, exist_ok=True)
        _winapi.CreateJunction(str(target), str(link))

    def targets(self):
        return {name: os.path.realpath(self.home / link) for name, (link, _) in LINKS.items()}

    def expected(self, tag):
        return {name: os.path.realpath(self.candidate(tag) / rel) for name, (_, rel) in LINKS.items()}

    def run_script(self, script, *args, timeout=180):
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        result = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", str(SCRIPTS / script), *args],
                                capture_output=True, text=True, encoding="utf-8", errors="replace",
                                timeout=timeout, cwd=self.root, env=env)
        self.assertTrue(result.stdout.strip(), result.stderr)
        return result.returncode, json.loads(result.stdout)

    def junctions(self, *args):
        return self.run_script("install-junctions.ps1", "-UserHome", str(self.home), "-CodexHome", str(self.codex),
                               "-ReleasesDir", str(self.releases), *args)

    def update(self, *args):
        return self.run_script("update-local.ps1", "-RepoRoot", str(self.repo), "-Ref", "HEAD", "-NoFetch",
                               "-UserHome", str(self.home), "-CodexHome", str(self.codex),
                               "-ReleasesDir", str(self.releases), "-PhysicalSkills", "careful,freeze", *args)

    # ------------------------------------------------------------ cases

    def test_all_scripts_parse_without_errors(self):
        check = self.root / "parse.ps1"
        check.write_text("param([string] $Dir)\n$n = 0\n"
                         "foreach ($f in Get-ChildItem -LiteralPath $Dir -File) { $t = $null; $e = $null\n"
                         "    $null = [Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$t, [ref]$e)\n"
                         "    $n += $e.Count }\n$n\n", encoding="utf-8")
        result = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", str(check), str(SCRIPTS)],
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.stdout.strip(), "0", result.stderr)
        names = sorted(p.name for p in SCRIPTS.iterdir())
        self.assertEqual(names, ["SimonKLocalInstall.psm1", "build-candidate.ps1", "install-junctions.ps1",
                                 "install-physical.ps1", "update-local.ps1"])

    def test_junction_preview_changes_nothing(self):
        before, config = self.targets(), self.config.read_bytes()
        rc, data = self.junctions("-Tag", NEW)
        self.assertEqual((rc, data["status"], data["old_tag"]), (0, "preview", OLD), data)
        self.assertEqual({e["action"] for e in data["entries"]}, {"swap"})
        self.assertEqual(len(data["entries"]), 8)
        self.assertEqual(data["config"]["action"], "replace")
        self.assertEqual(self.targets(), before)
        self.assertEqual(self.config.read_bytes(), config)
        self.assertFalse(self.archive_root.exists())

    def test_junction_apply_switches_links_config_and_archives_old_links(self):
        rc, data = self.junctions("-Tag", NEW, "-Apply")
        self.assertEqual((rc, data["status"]), (0, "installed"), data)
        self.assertEqual(self.targets(), self.expected(NEW))
        text = self.config.read_text(encoding="utf-8")
        self.assertEqual(text.count(self.vibe_path(NEW)), 1)
        self.assertNotIn(self.vibe_path(OLD), text)
        archive = self.archive_root / f"vibe-{NEW}"
        manifest = json.loads((archive / "manifest.json").read_text(encoding="utf-8-sig"))
        self.assertEqual((manifest["state"], manifest["old_tag"]), ("installed", OLD))
        self.assertTrue((archive / "codex-config.toml.before").is_file())
        for name, (_, rel) in LINKS.items():
            self.assertEqual(os.path.realpath(archive / name), os.path.realpath(self.candidate(OLD) / rel))
        rc, again = self.junctions("-Tag", NEW)
        self.assertEqual((rc, again["status"]), (0, "unchanged"), again)

    def test_first_install_archives_plain_folder_creates_links_and_appends_config(self):
        for link, _ in LINKS.values():
            os.rmdir(self.home / link)  # removes only the junction itself
        plain = self.home / ".claude" / "skills" / "vibe"
        plain.mkdir()
        (plain / "SKILL.md").write_bytes(b"old physical copy")
        self.config.write_bytes(b'model = "fixture"')
        rc, data = self.junctions("-Tag", NEW, "-Apply")
        self.assertEqual((rc, data["status"], data["mode"]), (0, "installed", "first-install"), data)
        actions = {e["name"]: e["action"] for e in data["entries"]}
        self.assertEqual(actions.pop("claude-vibe"), "archive-directory")
        self.assertEqual(set(actions.values()), {"create"})
        self.assertEqual(self.targets(), self.expected(NEW))
        archive = self.archive_root / f"vibe-{NEW}"
        self.assertEqual((archive / "claude-vibe" / "SKILL.md").read_bytes(), b"old physical copy")
        text = self.config.read_text(encoding="utf-8")
        self.assertTrue(text.startswith('model = "fixture"\n\n[[skills.config]]\n'), text)
        self.assertEqual(text.count(self.vibe_path(NEW)), 1)
        self.assertTrue(text.endswith("enabled = false\n"))

    def test_changed_topology_is_refused_before_any_move(self):
        stray = self.root / "stray-qa"
        stray.mkdir()
        (stray / "SKILL.md").write_bytes(b"stray")
        qa = self.home / ".claude" / "skills" / "qa"
        os.rmdir(qa)  # removes only the junction itself
        self.junction(qa, stray)
        before, config = self.targets(), self.config.read_bytes()
        rc, data = self.junctions("-Tag", NEW, "-Apply")
        self.assertEqual((rc, data["error"]), (2, "TOPOLOGY_CHANGED"), data)
        self.assertEqual(self.targets(), before)
        self.assertEqual(self.config.read_bytes(), config)
        self.assertFalse(self.archive_root.exists())

    def test_open_vibe_run_is_refused_and_closed_runs_pass(self):
        db = self.home / "AppData" / "Local" / "SimonK" / "vibe" / "runs.sqlite3"
        db.parent.mkdir(parents=True)
        db.write_bytes(b"")
        tool = self.candidate(OLD) / CORE / "vibe" / "scripts" / "run_state.py"
        tool.parent.mkdir()
        snapshot = {"runs": [{"run_id": "fixture-run", "closed": 0}], "accounts": [], "attempts": [],
                    "budget": {"halted": False}}
        tool.write_text(f"import json\nprint(json.dumps({snapshot!r}))\n", encoding="utf-8")
        before = self.targets()
        rc, data = self.junctions("-Tag", NEW, "-Apply")
        self.assertEqual((rc, data["error"]), (2, "VIBE_RUN_OPEN"), data)
        self.assertIn("fixture-run", data["detail"])
        self.assertEqual(self.targets(), before)
        snapshot["runs"][0]["closed"] = 2
        tool.write_text(f"import json\nprint(json.dumps({snapshot!r}))\n", encoding="utf-8")
        rc, data = self.junctions("-Tag", NEW)
        self.assertEqual((rc, data["status"], data["run_guard"]["blocked"]), (0, "preview", False), data)

    def test_failure_after_links_rolls_everything_back(self):
        config = self.config.read_bytes()
        os.chmod(self.config, stat.S_IREAD)
        self.addCleanup(os.chmod, self.config, stat.S_IREAD | stat.S_IWRITE)
        before = self.targets()
        rc, data = self.junctions("-Tag", NEW, "-Apply")
        self.assertEqual(rc, 2, data)
        self.assertEqual(self.targets(), before)
        self.assertEqual(self.config.read_bytes(), config)
        archive = self.archive_root / f"vibe-{NEW}"
        manifest = json.loads((archive / "manifest.json").read_text(encoding="utf-8-sig"))
        self.assertEqual(manifest["state"], "rolled-back")
        self.assertEqual(len(list(archive.glob("*-failed-new-link"))), 8)
        # A retry after the cause is fixed goes to a fresh archive; the rolled-back one is kept.
        os.chmod(self.config, stat.S_IREAD | stat.S_IWRITE)
        rc, data = self.junctions("-Tag", NEW, "-Apply")
        self.assertEqual((rc, data["status"]), (0, "installed"), data)
        self.assertEqual(Path(data["archive"]).name, f"vibe-{NEW}-2")
        self.assertEqual(self.targets(), self.expected(NEW))
        self.assertTrue((archive / "manifest.json").is_file())

    def test_physical_sync_replaces_only_differing_skills(self):
        careful = self.home / ".claude" / "skills" / "careful"
        freeze = self.home / ".claude" / "skills" / "freeze"
        old_bytes = skill_md("careful", "0.1.0").replace(b"\n", b"\r\n")
        (careful / "SKILL.md").write_bytes(old_bytes)
        freeze_mtime = (freeze / "SKILL.md").stat().st_mtime_ns
        common = ("-RepoRoot", str(self.repo), "-Ref", "HEAD", "-NoFetch", "-UserHome", str(self.home),
                  "-Skills", "careful,freeze", "-ArchiveTag", "t1")
        rc, data = self.run_script("install-physical.ps1", *common)
        self.assertEqual(rc, 0, data)
        actions = {s["skill"]: (s["state"], s["action"]) for s in data["skills"]}
        self.assertEqual(actions, {"careful": ("differs", "replace"), "freeze": ("same", "none")})
        self.assertEqual((careful / "SKILL.md").read_bytes(), old_bytes)
        rc, data = self.run_script("install-physical.ps1", *common, "-Apply")
        self.assertEqual((rc, data["status"]), (0, "installed"), data)
        self.assertEqual((careful / "SKILL.md").read_bytes(), skill_md("careful", "0.2.0"))
        self.assertEqual((self.archive_root / "careful-t1" / "SKILL.md").read_bytes(), old_bytes)
        self.assertEqual((freeze / "SKILL.md").stat().st_mtime_ns, freeze_mtime)
        self.assertFalse((self.archive_root / "freeze-t1").exists())

    def test_update_local_is_current_when_only_docs_changed(self):
        self.write("docs/INSTALL.md", b"# fixture\n\nnew paragraph\n")
        self.commit("docs only")
        before = self.targets()
        rc, data = self.update()
        self.assertEqual((rc, data["status"]), (0, "current"), data)
        self.assertEqual(data["junctions"]["reason"], "candidate_inputs_unchanged")
        self.assertEqual(data["junctions"]["linked_bytes_equal_main"], "8/8")
        self.assertTrue(data["verify"]["ok"], data["verify"])
        self.assertTrue(data["verify"]["codex_config"]["matches_junction"])
        self.assertEqual(self.targets(), before)

    def test_update_local_plans_physical_only_when_unlinked_skill_changed(self):
        self.write("skills-src/careful/SKILL.md", skill_md("careful", "0.2.1"))
        self.commit("careful 0.2.1")
        rc, data = self.update()
        self.assertEqual((rc, data["status"]), (0, "preview"), data)
        self.assertEqual((data["junctions"]["action"], data["junctions"]["reason"]), ("none", "linked_skills_unchanged"))
        physical = {s["skill"]: s["action"] for s in data["physical"]}
        self.assertEqual(physical, {"careful": "replace", "freeze": "none"})
        self.assertEqual(data["candidate"]["action"], "none")

    def test_update_local_plans_build_and_low_memory_apply_changes_nothing(self):
        self.write("skills-src/vibe/SKILL.md", skill_md("vibe", "1.1.0"))
        sha = self.commit("vibe 1.1.0")
        rc, data = self.update()
        self.assertEqual((rc, data["status"]), (0, "preview"), data)
        # First (uncached) version lookup must return vibe, not the last grep hit (vibe-bot).
        self.assertEqual((data["main"]["vibe"], data["main"]["vibe_bot"]), ("1.1.0", "1.0.0"))
        self.assertEqual(data["junctions"]["action"], "update")
        self.assertEqual(data["candidate"]["action"], "build")
        self.assertRegex(data["candidate"]["tag"], r"^\d{8}-vibe-110-" + sha[:7] + "$")
        self.assertTrue(any(w.startswith("BLOCKED now: PLUGIN_PINS_REQUIRED") for w in data["would"]), data["would"])
        before, config = self.targets(), self.config.read_bytes()
        rc, data = self.update("-Apply", "-MinFreeMemoryGB", "1000000")
        self.assertEqual((rc, data["status"], data["error"]), (2, "blocked", "LOW_MEMORY"), data)
        self.assertEqual(self.targets(), before)
        self.assertEqual(self.config.read_bytes(), config)
        self.assertEqual(sorted(p.name for p in self.releases.iterdir() if p.name.endswith("-candidate")),
                         sorted([f"{OLD}-candidate", f"{NEW}-candidate"]))


if __name__ == "__main__":
    unittest.main()
