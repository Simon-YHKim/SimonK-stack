"""A pinned Gstack source inventory must not be mistaken for runtime closure."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import gstack_source_inventory as inventory


@unittest.skipUnless(os.name == "nt", "Guarded source I/O currently requires Windows")
class GstackSourceInventoryTests(unittest.TestCase):
    def git(self, root, *args, input_data=None):
        return subprocess.run(["git", "-C", str(root), *args], input=input_data,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              check=True).stdout.decode().strip()

    def fixture(self, root):
        self.git(root, "init", "-q")
        self.git(root, "config", "user.name", "Fixture")
        self.git(root, "config", "user.email", "fixture@example.invalid")
        self.git(root, "config", "core.symlinks", "false")
        (root / "bin").mkdir()
        (root / "bin" / "run.sh").write_bytes(b"#!/bin/sh\nexit 0\n")
        self.git(root, "add", "bin/run.sh")
        self.git(root, "commit", "-qm", "fixture")
        return self.git(root, "rev-parse", "HEAD")

    def test_clean_regular_tree_is_only_inventory_compatible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            head = self.fixture(root)
            result = inventory.audit_source(root, head)
        self.assertEqual(result["status"], "regular_tree")
        self.assertTrue(result["package_contract_compatible"])
        self.assertEqual(result["files"], 1)
        self.assertEqual(result["unsupported_members"], [])
        self.assertFalse(result["runtime_closure_verified"])
        self.assertFalse(result["installation_ready"])
        self.assertRegex(result["raw_manifest_sha256"], r"^[0-9a-f]{64}$")

    def test_git_symlink_mode_blocks_package_even_when_windows_materializes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            target = b"open-gstack-browser"
            blob = self.git(root, "hash-object", "-w", "--stdin", input_data=target)
            (root / "connect-chrome").write_bytes(target)
            self.git(root, "update-index", "--add", "--cacheinfo", "120000", blob,
                     "connect-chrome")
            self.git(root, "commit", "-qm", "link fixture")
            head = self.git(root, "rev-parse", "HEAD")
            result = inventory.audit_source(root, head)
        self.assertEqual(result["status"], "unsupported_git_modes")
        self.assertFalse(result["package_contract_compatible"])
        self.assertEqual(result["unsupported_members"],
                         [{"path": "connect-chrome", "mode": "120000"}])
        self.assertFalse(result["installation_ready"])

    def test_dirty_and_untracked_files_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            head = self.fixture(root)
            (root / "bin" / "run.sh").write_bytes(b"modified\n")
            with self.assertRaisesRegex(ValueError, "dirty|differ"):
                inventory.audit_source(root, head)
            self.git(root, "restore", "bin/run.sh")
            (root / "extra.txt").write_text("untracked", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "differ|dirty"):
                inventory.audit_source(root, head)

    def test_wrong_commit_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            with self.assertRaisesRegex(ValueError, "HEAD"):
                inventory.audit_source(root, "0" * 40)


if __name__ == "__main__":
    unittest.main()
