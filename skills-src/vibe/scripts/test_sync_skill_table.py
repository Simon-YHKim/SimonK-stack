"""The legacy routing table is generated on demand, not loaded with /vibe."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("sync_skill_table.py")
SKILL_ROOT = SCRIPT.parent.parent
TABLE = "<!-- ROUTING:BEGIN -->\nlegacy-row\n<!-- ROUTING:END -->"


class SyncSkillTableTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="vibe-table-test-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.scripts = self.root / "scripts"
        self.scripts.mkdir()
        (self.root / "references").mkdir()
        shutil.copyfile(SCRIPT, self.scripts / SCRIPT.name)
        (self.scripts / "routing.py").write_text(
            "def emit_md():\n    return " + repr(TABLE) + "\n", encoding="utf-8")
        self.skill = self.root / "SKILL.md"
        self.skill.write_text("# Main skill\nRead references/legacy-routing.md only for legacy policy.\n",
                              encoding="utf-8")
        self.reference = self.root / "references" / "legacy-routing.md"
        self.reference.write_text("# Legacy policy\n\n" + TABLE + "\n", encoding="utf-8")

    def run_sync(self, *args):
        return subprocess.run([sys.executable, "-B", str(self.scripts / SCRIPT.name), *args],
                              cwd=self.root, capture_output=True, text=True, encoding="utf-8",
                              timeout=10)

    def test_check_uses_reference_and_does_not_need_markers_in_skill(self):
        original = self.skill.read_bytes()
        result = self.run_sync("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.skill.read_bytes(), original)

    def test_drift_is_reported_then_only_reference_is_regenerated(self):
        self.reference.write_text("# Legacy policy\n\n" + TABLE.replace("legacy-row", "stale-row") + "\n",
                                  encoding="utf-8")
        original_skill = self.skill.read_bytes()
        original_reference = self.reference.read_bytes()
        check = self.run_sync("--check")
        self.assertEqual(check.returncode, 1, check.stdout + check.stderr)
        self.assertEqual(self.reference.read_bytes(), original_reference)
        update = self.run_sync()
        self.assertEqual(update.returncode, 0, update.stdout + update.stderr)
        self.assertIn(TABLE, self.reference.read_text(encoding="utf-8"))
        self.assertEqual(self.skill.read_bytes(), original_skill)

    def test_real_skill_keeps_legacy_table_in_direct_reference(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertFalse("<!-- ROUTING:BEGIN" in skill)
        self.assertIn("(references/legacy-routing.md)", skill)
        self.assertTrue((SKILL_ROOT / "references" / "legacy-routing.md").is_file())
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--check"],
                                cwd=SKILL_ROOT, capture_output=True, text=True,
                                encoding="utf-8", timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
