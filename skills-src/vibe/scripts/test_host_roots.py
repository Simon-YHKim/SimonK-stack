"""host_roots observes split-home roots without writing or guessing."""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import host_roots  # noqa: E402

NOW = datetime(2026, 10, 21, 6, 0, tzinfo=timezone.utc)


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")


def skill(root, name):
    write(root / name / "SKILL.md", f"---\nname: {name}\ndescription: Use when {name}\n---\n")


class HostRootsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        self.claude = self.home / ".claude"
        skill(self.claude / "skills", "career")

    def tearDown(self):
        self.tmp.cleanup()

    def plugin(self, name, *, skills=True, manifest=None):
        install = self.claude / "plugins" / "cache" / "mk" / name / "1.0.0"
        install.mkdir(parents=True)
        if skills:
            skill(install / "skills", f"{name}-skill")
        if manifest is not None:
            write(install / ".claude-plugin" / "plugin.json", manifest)
        return install

    def settings(self, enabled, path=None):
        write(path or self.claude / "settings.json", {"model": "x", "enabledPlugins": enabled})

    def installed(self, plugins, version=2):
        write(self.claude / "plugins" / "installed_plugins.json", {"version": version, "plugins": plugins})

    def observe(self, host="claude", **kw):
        return host_roots.observe(host, self.home, env={}, now=NOW, **kw)

    def test_enabled_plugin_roots_follow_user_skills_in_settings_order(self):
        a = self.plugin("alpha")
        b = self.plugin("beta")
        self.settings({"beta@mk": True, "alpha@mk": True})
        self.installed({"alpha@mk": [{"scope": "user", "installPath": str(a)}],
                        "beta@mk": [{"scope": "user", "installPath": str(b)}]})
        out = self.observe()
        self.assertEqual(out["roots"], [str(self.claude / "skills"), str(b / "skills"), str(a / "skills")])
        self.assertEqual(out["root_args"][:2], ["--root", str(self.claude / "skills")])
        self.assertEqual(out["observed_at"], "2026-10-21T06:00:00+00:00")
        self.assertEqual(len(out["sources"]), 2)
        self.assertTrue(all(len(s["sha256"]) == 64 for s in out["sources"]))

    def test_disabled_missing_record_and_missing_dirs_are_skipped_not_guessed(self):
        a = self.plugin("alpha")
        no_skills = self.plugin("bare", skills=False)
        self.settings({"alpha@mk": False, "ghost@mk": True, "bare@mk": True, "gone@mk": True,
                       "text@mk": "true"})
        self.installed({"alpha@mk": [{"scope": "user", "installPath": str(a)}],
                        "bare@mk": [{"scope": "user", "installPath": str(no_skills)}],
                        "gone@mk": [{"scope": "user", "installPath": str(self.home / "nowhere")}]})
        out = self.observe()
        self.assertEqual(out["roots"], [str(self.claude / "skills")])
        reasons = {s["plugin"]: s["reason"] for s in out["skipped"] if "plugin" in s}
        self.assertEqual(reasons, {"alpha@mk": "disabled", "ghost@mk": "no_install_record",
                                   "bare@mk": "no_skills_dir", "gone@mk": "install_path_missing",
                                   "text@mk": "disabled"})

    def test_relative_install_path_is_not_resolved(self):
        self.settings({"rel@mk": True})
        self.installed({"rel@mk": [{"scope": "user", "installPath": "plugins/cache/rel"}]})
        out = self.observe()
        self.assertIn({"plugin": "rel@mk", "reason": "install_path_missing"}, out["skipped"])

    def test_malformed_host_json_fails_closed(self):
        write(self.claude / "settings.json", "{not json")
        with self.assertRaises(host_roots.HostRootsError):
            self.observe()
        self.settings({"a@mk": True})
        self.installed({}, version=1)
        with self.assertRaisesRegex(host_roots.HostRootsError, "unsupported schema"):
            self.observe()
        write(self.claude / "settings.json", {"enabledPlugins": ["a@mk"]})
        with self.assertRaisesRegex(host_roots.HostRootsError, "enabledPlugins"):
            self.observe()
        write(self.claude / "settings.json", '{"enabledPlugins": {"a@mk": NaN}}')
        with self.assertRaisesRegex(host_roots.HostRootsError, "nonfinite"):
            self.observe()

    def test_oversized_json_fails_closed(self):
        write(self.claude / "settings.json", " " * (host_roots.MAX_JSON_BYTES + 1))
        with self.assertRaisesRegex(host_roots.HostRootsError, "larger than"):
            self.observe()

    def test_missing_settings_still_reports_user_skills(self):
        out = self.observe()
        self.assertEqual(out["roots"], [str(self.claude / "skills")])
        self.assertEqual(out["sources"], [])
        self.assertTrue(any("No plugin is enabled" in n for n in out["notes"]))

    def test_same_physical_root_is_deduplicated(self):
        a = self.plugin("alpha")
        self.settings({"alpha@mk": True, "alias@mk": True})
        self.installed({"alpha@mk": [{"scope": "user", "installPath": str(a)}],
                        "alias@mk": [{"scope": "user", "installPath": str(a)}]})
        out = self.observe()
        self.assertEqual(out["roots"], [str(self.claude / "skills"), str(a / "skills")])
        self.assertIn("duplicate_physical_root", [s.get("reason") for s in out["skipped"]])

    def test_project_settings_override_and_scope_selection(self):
        project = Path(self.tmp.name) / "repo"
        user_copy = self.plugin("alpha")
        local_copy = self.claude / "plugins" / "cache" / "mk" / "alpha" / "2.0.0"
        skill(local_copy / "skills", "alpha-local")
        beta = self.plugin("beta")
        self.settings({"alpha@mk": True, "beta@mk": True})
        self.settings({"beta@mk": False}, project / ".claude" / "settings.json")
        self.settings({"gamma@mk": True}, project / ".claude" / "settings.local.json")
        self.installed({"alpha@mk": [{"scope": "user", "installPath": str(user_copy)},
                                     {"scope": "local", "installPath": str(local_copy),
                                      "projectPath": str(project)}],
                        "beta@mk": [{"scope": "user", "installPath": str(beta)}],
                        "gamma@mk": [{"scope": "project", "installPath": str(beta),
                                      "projectPath": str(Path(self.tmp.name) / "other")}]})
        out = self.observe(project=project)
        self.assertEqual(out["roots"], [str(self.claude / "skills"), str(local_copy / "skills")])
        reasons = {s["plugin"]: s["reason"] for s in out["skipped"] if "plugin" in s}
        self.assertEqual(reasons, {"beta@mk": "disabled", "gamma@mk": "no_applicable_install_record"})
        # Without --project only user-scope records apply.
        out = self.observe()
        self.assertEqual(out["roots"], [str(self.claude / "skills"), str(user_copy / "skills"),
                                        str(beta / "skills")])

    def test_ambiguous_records_are_skipped(self):
        a = self.plugin("alpha")
        self.settings({"alpha@mk": True})
        self.installed({"alpha@mk": [{"scope": "user", "installPath": str(a)},
                                     {"scope": "user", "installPath": str(a)}]})
        out = self.observe()
        self.assertIn({"plugin": "alpha@mk", "reason": "ambiguous_install_record"}, out["skipped"])

    def test_manifest_declared_skills_stay_inside_plugin(self):
        ok = self.plugin("decl", skills=False, manifest={"name": "decl", "skills": ["./extra/one/"]})
        skill(ok / "extra", "one")
        bad = self.plugin("escape", manifest={"name": "escape", "skills": "../../.."})
        broken = self.plugin("broken", manifest="{oops")
        self.settings({"decl@mk": True, "escape@mk": True, "broken@mk": True})
        self.installed({"decl@mk": [{"scope": "user", "installPath": str(ok)}],
                        "escape@mk": [{"scope": "user", "installPath": str(bad)}],
                        "broken@mk": [{"scope": "user", "installPath": str(broken)}]})
        out = self.observe()
        self.assertEqual(out["roots"], [str(self.claude / "skills"), str(ok / "extra")])
        reasons = {s["plugin"]: s["reason"] for s in out["skipped"] if "plugin" in s}
        self.assertEqual(reasons["escape@mk"], "manifest_skills_outside_plugin")
        self.assertTrue(reasons["broken@mk"].startswith("manifest_invalid"))

    def test_synced_claude_ai_plugins_are_never_scanned(self):
        skill(self.claude / "plugins" / "synced" / "org" / "engineering" / "skills", "standup")
        out = self.observe()
        self.assertFalse(any("synced" in r for r in out["roots"]))
        self.assertTrue(any("plugins/synced" in n for n in out["notes"]))

    def test_codex_roots_follow_orchestrate_default_order(self):
        skill(self.home / ".codex" / "skills", "a")
        skill(self.home / ".agents" / "skills", "b")
        skill(self.home / ".codex" / "skills" / ".system", "c")
        out = self.observe("codex")
        self.assertEqual(out["roots"], [str(self.home / ".codex" / "skills"),
                                        str(self.home / ".agents" / "skills"),
                                        str(self.home / ".codex" / "skills" / ".system")])
        with self.assertRaises(host_roots.HostRootsError):
            self.observe("codex", project=self.home)

    def test_env_overrides_config_dirs(self):
        alt = Path(self.tmp.name) / "alt-claude"
        skill(alt / "skills", "x")
        out = host_roots.observe("claude", self.home, env={"CLAUDE_CONFIG_DIR": str(alt)}, now=NOW)
        self.assertEqual(out["roots"], [str(alt / "skills")])
        altc = Path(self.tmp.name) / "alt-codex"
        skill(altc / "skills", "y")
        out = host_roots.observe("codex", self.home, env={"CODEX_HOME": str(altc)}, now=NOW)
        self.assertEqual(out["roots"][0], str(altc / "skills"))

    def test_candidate_first_prepends_bundle_roots_or_fails_closed(self):
        bundle = Path(self.tmp.name) / "bundle"
        core = bundle / "plugins" / "SimonKCore" / "skills"
        skill(core, "vibe")
        fake = {"roots": [{"path": str(core), "status": "scanned"}]}
        orch = mock.MagicMock()
        orch.candidate_inventory.return_value = fake
        with mock.patch.dict(sys.modules, {"orchestrate": orch}):
            out = self.observe(candidate_first=True)
        self.assertEqual(out["roots"][:2], [str(core), str(self.claude / "skills")])
        self.assertTrue(any("receipt check" in n for n in out["notes"]))
        orch.candidate_inventory.return_value = None
        with mock.patch.dict(sys.modules, {"orchestrate": orch}):
            out = self.observe(candidate_first=True)
        self.assertIn({"root": "candidate", "reason": "not_in_candidate"}, out["skipped"])
        orch.candidate_inventory.side_effect = ValueError("Candidate discovery member drift")
        with mock.patch.dict(sys.modules, {"orchestrate": orch}):
            with self.assertRaisesRegex(host_roots.HostRootsError, "not intact"):
                self.observe(candidate_first=True)

    def test_cli_is_read_only_and_reports_errors_as_exit_2(self):
        before = sorted(p.relative_to(self.home) for p in self.home.rglob("*"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = host_roots.main(["--host", "claude", "--home", str(self.home)])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(buf.getvalue())["roots"], [str(self.claude / "skills")])
        self.assertEqual(sorted(p.relative_to(self.home) for p in self.home.rglob("*")), before)
        write(self.claude / "settings.json", "[]")
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = host_roots.main(["--host", "claude", "--home", str(self.home)])
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(buf.getvalue())["error"], "HostRootsError")


if __name__ == "__main__":
    unittest.main()
