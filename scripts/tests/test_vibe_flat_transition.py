"""Isolated flat-link switch and recovery; never touch a user profile."""

import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import vibe_flat_transition as transition


class FlatTransitionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="vibe-flat-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.current = self.root / "old"
        self.candidate = self.root / "new"
        self.claude = self.root / "claude"
        self.codex = self.root / "codex"
        self.agents = self.root / "agents"
        for host, names, package in (
            (self.claude, ("model-router", "multi-terminal-dispatcher", "simonk", "vibe", "vibe-bot"),
             "candidate-safety"),
            (self.codex, ("vibe", "vibe-bot"), "codex-subset-safety"),
        ):
            (host / "skills").mkdir(parents=True)
            for name in names:
                old = self.current / package / "plugins/SimonKCore/skills" / name
                new = self.candidate / package / "plugins/SimonKCore/skills" / name
                old.mkdir(parents=True)
                new.mkdir(parents=True)
                (old / "SKILL.md").write_text(f"old {name}\n", encoding="utf-8")
                (new / "SKILL.md").write_text(f"new {name}\n", encoding="utf-8")
                os.symlink(old, host / "skills" / name, target_is_directory=True)
        (self.agents / "skills").mkdir(parents=True)
        os.symlink(self.claude / "skills/vibe", self.agents / "skills/vibe",
                   target_is_directory=True)
        self.pins = {name: char * 64 for name, char in (
            ("source", "a"), ("candidate-safety", "b"),
            ("codex-overlay-safety", "c"), ("codex-subset-safety", "d"))}
        self.native = {"claude": [], "codex": {"installed": []}}
        self.report = {"status": "host_snapshot_complete", "issues": [],
                       "checked_links": 8, "candidate_bytes_verified": True,
                       "native_plugin_coverage": {"status": "metadata_matched"}}

    def plan(self):
        with patch.object(transition.preflight, "scan", return_value=self.report):
            return transition.prepare_plan(
                self.candidate, self.current, self.claude, self.codex, self.agents,
                self.pins, self.native)

    def test_rehearsal_switches_seven_links_and_restores_every_old_link(self):
        plan = self.plan()
        alias = os.readlink(self.agents / "skills/vibe")
        with patch.object(transition.preflight, "scan", return_value=self.report):
            transition.apply_isolated(plan, self.root, self.native)
        for entry in plan["entries"]:
            link = Path(entry["link"])
            self.assertEqual(transition.preflight._direct_target(link), Path(entry["new_target"]))
            self.assertTrue(Path(entry["archive"]).is_symlink())
        self.assertEqual(os.readlink(self.agents / "skills/vibe"), alias)
        transition.rollback_isolated(plan, self.root)
        for entry in plan["entries"]:
            link = Path(entry["link"])
            self.assertEqual(transition.preflight._direct_target(link), Path(entry["old_target"]))
            self.assertFalse(os.path.lexists(entry["archive"]))
            self.assertTrue(Path(entry["quarantine"]).is_symlink())
        self.assertEqual(os.readlink(self.agents / "skills/vibe"), alias)
        transition.rollback_isolated(plan, self.root)

    def test_changed_old_link_refuses_before_any_move(self):
        plan = self.plan()
        link = self.claude / "skills/model-router"
        link.unlink()
        alien = self.root / "alien"
        alien.mkdir()
        os.symlink(alien, link, target_is_directory=True)
        with patch.object(transition.preflight, "scan", return_value=self.report):
            with self.assertRaises(transition.TransitionError):
                transition.apply_isolated(plan, self.root, self.native)
        self.assertEqual(transition.preflight._direct_target(link), alien)
        self.assertFalse(os.path.lexists(plan["entries"][0]["archive"]))

    def test_mid_switch_failure_restores_old_links_without_deleting_new_link(self):
        plan = self.plan()
        real_symlink = os.symlink
        calls = 0

        def fail_second(target, link, *, target_is_directory):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("injected link failure")
            return real_symlink(target, link, target_is_directory=target_is_directory)

        with (patch.object(transition.preflight, "scan", return_value=self.report),
              patch.object(transition.os, "symlink", side_effect=fail_second)):
            with self.assertRaises(transition.TransitionError):
                transition.apply_isolated(plan, self.root, self.native)
        for entry in plan["entries"]:
            self.assertEqual(transition.preflight._direct_target(Path(entry["link"])),
                             Path(entry["old_target"]))
        self.assertTrue(Path(plan["entries"][0]["quarantine"]).is_symlink())

    def test_forged_manifest_or_non_isolated_root_cannot_switch(self):
        plan = self.plan()
        plan["entries"][0]["link"] = str(self.root / "not-a-skill")
        with self.assertRaises(transition.TransitionError):
            transition.apply_isolated(plan, self.root, self.native)
        plan = self.plan()
        with self.assertRaises(transition.TransitionError):
            transition.apply_isolated(plan, self.claude, self.native)
        self.assertEqual(transition.preflight._direct_target(self.claude / "skills/vibe"),
                         self.current / "candidate-safety/plugins/SimonKCore/skills/vibe")

    def test_native_registration_must_be_observed_before_switch(self):
        report = dict(self.report)
        report["native_plugin_coverage"] = {"status": "gaps"}
        with patch.object(transition.preflight, "scan", return_value=report):
            with self.assertRaises(transition.TransitionError):
                transition.prepare_plan(self.candidate, self.current, self.claude,
                                        self.codex, self.agents, self.pins, self.native)

    def test_reparse_skills_parent_blocks_switch_before_move(self):
        plan = self.plan()
        skills = self.claude / "skills"
        saved = self.claude / "skills-saved"
        os.rename(skills, saved)
        os.symlink(saved, skills, target_is_directory=True)
        with patch.object(transition.preflight, "scan", return_value=self.report):
            with self.assertRaises(transition.TransitionError):
                transition.apply_isolated(plan, self.root, self.native)
        self.assertEqual(transition.preflight._direct_target(saved / "vibe"),
                         self.current / "candidate-safety/plugins/SimonKCore/skills/vibe")

    def test_reparse_quarantine_parent_blocks_rollback(self):
        plan = self.plan()
        with patch.object(transition.preflight, "scan", return_value=self.report):
            transition.apply_isolated(plan, self.root, self.native)
        parent = Path(plan["entries"][0]["quarantine"]).parent
        saved = parent.with_name(parent.name + "-saved")
        os.rename(parent, saved)
        os.symlink(saved, parent, target_is_directory=True)
        with self.assertRaises(transition.TransitionError):
            transition.rollback_isolated(plan, self.root)
        self.assertEqual(transition.preflight._direct_target(Path(plan["entries"][0]["link"])),
                         Path(plan["entries"][0]["new_target"]))

    @unittest.skipUnless(os.name == "nt", "Windows junction rehearsal")
    def test_existing_windows_junction_survives_switch_and_rollback(self):
        link = self.claude / "skills/vibe"
        old = self.current / "candidate-safety/plugins/SimonKCore/skills/vibe"
        link.unlink()
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(old)],
                       check=True, capture_output=True, text=True)
        self.assertEqual(link.lstat().st_reparse_tag, stat.IO_REPARSE_TAG_MOUNT_POINT)
        plan = self.plan()
        with patch.object(transition.preflight, "scan", return_value=self.report):
            transition.apply_isolated(plan, self.root, self.native)
        transition.rollback_isolated(plan, self.root)
        self.assertEqual(link.lstat().st_reparse_tag, stat.IO_REPARSE_TAG_MOUNT_POINT)
        self.assertEqual(transition.preflight._direct_target(link), old)

    def test_tampered_new_link_blocks_whole_rollback_before_any_move(self):
        plan = self.plan()
        with patch.object(transition.preflight, "scan", return_value=self.report):
            transition.apply_isolated(plan, self.root, self.native)
        first = Path(plan["entries"][0]["link"])
        first.unlink()
        alien = self.root / "alien"
        alien.mkdir()
        os.symlink(alien, first, target_is_directory=True)
        with self.assertRaises(transition.TransitionError):
            transition.rollback_isolated(plan, self.root)
        for entry in plan["entries"][1:]:
            self.assertEqual(transition.preflight._direct_target(Path(entry["link"])),
                             Path(entry["new_target"]))

    def test_interrupted_switch_recovers_from_persisted_plan(self):
        plan = self.plan()
        real_symlink = os.symlink
        calls = 0

        def interrupt_second(target, link, *, target_is_directory):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise KeyboardInterrupt("simulated process interruption")
            return real_symlink(target, link, target_is_directory=target_is_directory)

        with (patch.object(transition.preflight, "scan", return_value=self.report),
              patch.object(transition.os, "symlink", side_effect=interrupt_second)):
            with self.assertRaises(KeyboardInterrupt):
                transition.apply_isolated(plan, self.root, self.native)
        journal = self.root / "vibe-flat-transition.json"
        self.assertTrue(journal.is_file())
        self.assertEqual(json.loads(journal.read_text(encoding="utf-8"))["plan_digest"],
                         plan["plan_digest"])
        transition.recover_isolated(self.root)
        for entry in plan["entries"]:
            self.assertEqual(transition.preflight._direct_target(Path(entry["link"])),
                             Path(entry["old_target"]))
        self.assertTrue(Path(plan["entries"][0]["quarantine"]).is_symlink())
        transition.recover_isolated(self.root)

    def test_tampered_journal_cannot_move_links_during_recovery(self):
        plan = self.plan()
        with patch.object(transition.preflight, "scan", return_value=self.report):
            transition.apply_isolated(plan, self.root, self.native)
        journal = self.root / "vibe-flat-transition.json"
        forged = json.loads(journal.read_text(encoding="utf-8"))
        forged["entries"][-1]["old_target"] = str(self.root / "alien")
        journal.write_text(json.dumps(forged), encoding="utf-8")
        with self.assertRaises(transition.TransitionError):
            transition.recover_isolated(self.root)
        for entry in plan["entries"]:
            self.assertEqual(transition.preflight._direct_target(Path(entry["link"])),
                             Path(entry["new_target"]))

    def test_apply_rejects_existing_journal_before_first_move(self):
        plan = self.plan()
        (self.root / "vibe-flat-transition.json").write_text("stale", encoding="utf-8")
        with patch.object(transition.preflight, "scan", return_value=self.report):
            with self.assertRaises(transition.TransitionError):
                transition.apply_isolated(plan, self.root, self.native)
        for entry in plan["entries"]:
            self.assertEqual(transition.preflight._direct_target(Path(entry["link"])),
                             Path(entry["old_target"]))

    def test_recovery_rejects_missing_and_linked_journal(self):
        plan = self.plan()
        with self.assertRaises(transition.TransitionError):
            transition.recover_isolated(self.root)
        outsider = self.root / "outsider.json"
        outsider.write_text(json.dumps(plan), encoding="utf-8")
        os.symlink(outsider, self.root / "vibe-flat-transition.json")
        with self.assertRaises(transition.TransitionError):
            transition.recover_isolated(self.root)
        for entry in plan["entries"]:
            self.assertEqual(transition.preflight._direct_target(Path(entry["link"])),
                             Path(entry["old_target"]))

    def test_recovery_rejects_duplicate_json_keys(self):
        plan = self.plan()
        with patch.object(transition.preflight, "scan", return_value=self.report):
            transition.apply_isolated(plan, self.root, self.native)
        journal = self.root / "vibe-flat-transition.json"
        journal.write_text(journal.read_text(encoding="utf-8")[:-1] + ',"scope":"forged"}',
                           encoding="utf-8")
        with self.assertRaises(transition.TransitionError):
            transition.recover_isolated(self.root)
        for entry in plan["entries"]:
            self.assertEqual(transition.preflight._direct_target(Path(entry["link"])),
                             Path(entry["new_target"]))


if __name__ == "__main__":
    unittest.main()
