"""D-76 release version and dist staging, using only disposable Git repos and folders."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import dist_release as dist

OWNERS = sorted(dist.OWNERS)


def git(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
    return subprocess.check_output(
        ["git", "-c", "core.autocrlf=false", "-c", "commit.gpgSign=false", "-c", "core.hooksPath=" + os.devnull,
         "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "-C", str(root), *args],
        text=True, encoding="utf-8", stderr=subprocess.PIPE, timeout=30, env=env)


def record(**changes):
    value = {"schema_version": 1, "scope": dist.DIST_SCOPE, "version": "1.10.0",
             "content_digest": "a" * 64, "bundle_digest": "b" * 64, "source_commit": "c" * 40,
             "source_digest": "d" * 64, "pins": {owner: "e" * 40 for owner in OWNERS},
             "codex_overlay_digest": "f" * 64, "codex_subset_digest": "0" * 64, "run": None}
    value.update(changes)
    return value


class VersionSchemeTests(unittest.TestCase):
    def test_only_plain_semver_cores_are_release_versions(self):
        self.assertEqual(dist.parse_version("1.561.0"), (1, 561, 0))
        for bad in ("0.1.0-vibe.018825543742", "1.2.3-rc.1", "1.2.3+c0ffee", "1.01.0", "01.2.3",
                    "1.2", "v1.2.3", "1.2.3 ", "", None, 1, ["1.2.3"]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                dist.parse_version(bad)

    def test_versions_rise_with_the_count_and_compare_numerically(self):
        self.assertEqual(dist.release_version(561), "1.561.0")
        previous = dist.parse_version(dist.release_version(1))
        for count in (2, 9, 10, 99, 100, 999, 1000, 12345):
            current = dist.parse_version(dist.release_version(count))
            self.assertGreater(current, previous)  # 1.10.0 > 1.9.0, unlike string order
            previous = current
        for bad in (0, -1, True, 1.0, "3"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                dist.release_version(bad)

    def test_first_release_sorts_above_legacy_and_every_old_base(self):
        first = dist.parse_version(dist.release_version(1))
        legacy = json.loads((ROOT / dist.LEGACY_MANIFEST).read_text(encoding="utf-8"))["version"]
        for old in (legacy, "0.1.0", "0.3.0", "0.99.99"):
            self.assertGreater(first, dist.parse_version(old))


class ComputeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dist-release-test-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        (self.repo / "distribution").mkdir(parents=True)
        git(self.repo, "init", "-q")
        self.inputs = self.repo / "distribution/plugin-inputs.v1.json"
        self.write_pins("1" * 40)
        self.commit("first")

    def write_pins(self, sha):
        self.inputs.write_text(json.dumps({"schema_version": 1, "plugins": {
            owner: {"name": "simonk-" + owner.removeprefix("SimonK").lower(), "commit": sha}
            for owner in OWNERS}}), encoding="utf-8", newline="\n")

    def commit(self, message):
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", message)

    def test_same_commit_same_version_and_pin_only_change_raises_it(self):
        first = dist.compute(self.repo)
        self.assertEqual(first["version"], "1.1.0")
        self.assertEqual(first["commit_count"], 1)
        self.assertEqual(first["commit"], git(self.repo, "rev-parse", "HEAD").strip())
        self.assertEqual(dist.compute(self.repo), first)  # rebuild of one commit: same version
        self.write_pins("2" * 40)  # pin-only change
        self.commit("chore: bump one plugin pin")
        second = dist.compute(self.repo)
        self.assertEqual(second["version"], "1.2.0")
        self.assertGreater(dist.parse_version(second["version"]), dist.parse_version(first["version"]))

    def test_merged_side_branch_still_raises_the_version(self):
        git(self.repo, "checkout", "-qb", "side")
        for n in range(3):
            (self.repo / f"side{n}.txt").write_text("x", encoding="utf-8")
            self.commit(f"side {n}")
        git(self.repo, "checkout", "-q", "-")
        (self.repo / "main.txt").write_text("y", encoding="utf-8")
        self.commit("main")
        before = dist.compute(self.repo)["commit_count"]
        git(self.repo, "merge", "-q", "--no-ff", "-m", "merge side", "side")
        self.assertGreater(dist.compute(self.repo)["commit_count"], before)

    def test_shallow_clone_is_refused(self):
        self.commit_twice()
        clone = Path(self.temp.name) / "shallow"
        git(self.temp.name, "clone", "-q", "--depth", "1", self.repo.as_uri(), str(clone))
        with self.assertRaisesRegex(ValueError, "Shallow"):
            dist.compute(clone)

    def commit_twice(self):
        for n in range(2):
            (self.repo / f"more{n}.txt").write_text("z", encoding="utf-8")
            self.commit(f"more {n}")

    def test_legacy_root_plugin_version_is_a_floor(self):
        manifest = self.repo / dist.LEGACY_MANIFEST
        manifest.parent.mkdir()
        manifest.write_text(json.dumps({"name": "simonk-stack", "version": "0.1.0"}), encoding="utf-8")
        self.commit("legacy root plugin")
        result = dist.compute(self.repo)
        self.assertEqual(result["legacy_floor"], "0.1.0")
        manifest.write_text(json.dumps({"name": "simonk-stack", "version": "1.5.0"}), encoding="utf-8")
        self.commit("legacy root plugin above the scheme")
        with self.assertRaisesRegex(ValueError, "legacy"):
            dist.compute(self.repo)

    def test_cli_prints_the_version_json(self):
        import io
        from unittest.mock import patch
        with patch.object(sys, "stdout", io.StringIO()) as stdout:
            self.assertEqual(dist.main(["version", "--repo", str(self.repo)]), 0)
        self.assertEqual(json.loads(stdout.getvalue())["version"], "1.1.0")


class DecideTests(unittest.TestCase):
    def test_first_release_publishes(self):
        self.assertEqual(dist.decide(None, record())["action"], "publish")

    def test_identical_content_is_skipped_at_any_version(self):
        for version in ("1.9.0", "1.10.0", "1.11.0"):
            with self.subTest(version=version):
                decision = dist.decide(record(), record(version=version, bundle_digest="9" * 64))
                self.assertEqual((decision["action"], decision["reason"]), ("skip", "identical-content"))

    def test_new_content_needs_a_higher_version(self):
        self.assertEqual(dist.decide(record(), record(version="1.11.0", content_digest="1" * 64))["action"],
                         "publish")
        for version in ("1.10.0", "1.9.0", "0.99.0"):
            with self.subTest(version=version):
                decision = dist.decide(record(), record(version=version, content_digest="1" * 64))
                self.assertEqual((decision["action"], decision["reason"]), ("refuse", "not-newer-than-dist"))

    def test_rollback_reships_older_content_under_a_higher_version(self):
        good = record(version="1.10.0", content_digest="1" * 64)
        bad = record(version="1.20.0", content_digest="2" * 64)
        self.assertEqual(dist.decide(good, bad)["action"], "publish")
        rollback = record(version="1.25.0", content_digest="1" * 64)  # reverted on main
        self.assertEqual(dist.decide(bad, rollback)["action"], "publish")
        stale = record(version="1.15.0", content_digest="1" * 64)  # late old run
        self.assertEqual(dist.decide(bad, stale)["action"], "refuse")

    def test_records_are_exact(self):
        for change in ({"version": "1.10.0-rc.1"}, {"content_digest": "A" * 64}, {"source_commit": "c" * 39},
                       {"pins": {"SimonKCore": "e" * 40}}, {"run": "http://insecure"}, {"schema_version": True},
                       {"scope": "other"}, {"extra": 1}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                dist.decide(None, record(**change))
        with self.assertRaises(ValueError):
            dist.decide({"version": "1.1.0"}, record())

    def test_cli_refuse_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as raw:
            previous, current = Path(raw, "prev.json"), Path(raw, "cur.json")
            previous.write_bytes(dist.encoded(record(version="1.20.0", content_digest="2" * 64)))
            current.write_bytes(dist.encoded(record(version="1.15.0")))
            import io
            from unittest.mock import patch
            with patch.object(sys, "stdout", io.StringIO()):
                self.assertEqual(dist.main(["decide", "--previous", str(previous), "--current", str(current)]), 1)
                self.assertEqual(dist.main(["decide", "--current", str(current)]), 0)


class StageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dist-stage-test-")
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.candidate, self.dist = base / "candidate", base / "dist"
        self.dist.mkdir()
        (self.dist / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
        self.members = {
            "plugins/SimonKCore/.claude-plugin/plugin.json": (b'{"version":"1.10.0"}\n', "100644"),
            "plugins/SimonKCore/skills/careful/bin/check-careful.sh": (b"#!/bin/bash\necho ok\n", "100755"),
            "plugins/SimonKStack/skills/freeze/SKILL.md": (b"---\nname: freeze\n---\n", "100644"),
        }
        files = []
        for path, (data, mode) in sorted(self.members.items()):
            target = self.candidate / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            files.append({"path": path, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
                          "mode": mode, "origin": "source", "input_path": path})
        receipt = {"files": files, "source_digest": "d" * 64,
                   "inputs": {"schema_version": 1, "plugins": {o: {"name": o, "commit": "e" * 40} for o in OWNERS}},
                   "release": {"version": "1.10.0", "content_digest": "a" * 64}}
        data = dist.encoded(receipt)
        (self.candidate / "bundle.json").write_bytes(data)
        self.bundle_digest = hashlib.sha256(data).hexdigest()
        self.record = dist.release_record(self.candidate, self.bundle_digest, "c" * 40, "f" * 64, "0" * 64,
                                          "https://github.com/example/run/1")

    def test_record_reads_the_verified_candidate(self):
        self.assertEqual(self.record["version"], "1.10.0")
        self.assertEqual(self.record["content_digest"], "a" * 64)
        self.assertEqual(self.record["pins"], {o: "e" * 40 for o in OWNERS})
        with self.assertRaisesRegex(ValueError, "bundle digest"):
            dist.release_record(self.candidate, "1" * 64, "c" * 40, "f" * 64, "0" * 64)

    def test_stage_replaces_content_and_lists_executables(self):
        (self.dist / "plugins/SimonKOld").mkdir(parents=True)
        (self.dist / "plugins/SimonKOld/stale.md").write_text("old", encoding="utf-8")
        (self.dist / dist.RECORD).write_text("{}", encoding="utf-8")
        result = dist.stage(self.candidate, self.dist, self.record)
        self.assertEqual(result, {"files": 3, "executables": [
            "plugins/SimonKCore/skills/careful/bin/check-careful.sh"]})
        self.assertFalse((self.dist / "plugins/SimonKOld").exists())
        for path, (data, _) in self.members.items():
            self.assertEqual((self.dist / path).read_bytes(), data)
        self.assertEqual((self.dist / ".gitattributes").read_bytes(), b"* -text\n")
        self.assertEqual(json.loads((self.dist / dist.RECORD).read_bytes()), self.record)
        self.assertEqual((self.dist / ".git").read_text(encoding="utf-8"), "gitdir: elsewhere\n")
        self.assertFalse((self.dist / "bundle.json").exists())  # receipts stay in the artifact

    def test_stage_never_wipes_a_main_checkout_or_unknown_tree(self):
        (self.dist / ".git").unlink()
        (self.dist / ".git").mkdir()
        with self.assertRaisesRegex(ValueError, "linked Git worktree"):
            dist.stage(self.candidate, self.dist, self.record)
        (self.dist / ".git").rmdir()
        (self.dist / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
        (self.dist / "README.md").write_text("not dist", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unexpected top-level"):
            dist.stage(self.candidate, self.dist, self.record)
        self.assertTrue((self.dist / "README.md").exists())

    def test_stage_rejects_changed_bytes_and_escaping_paths(self):
        (self.candidate / "plugins/SimonKStack/skills/freeze/SKILL.md").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "differs"):
            dist.stage(self.candidate, self.dist, self.record)
        for bad in ("../x", "plugins/../x", "/plugins/a/b", "plugins\\a\\b", "skills/a/b", "plugins/a", "C:/x"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                dist._member(bad)


if __name__ == "__main__":
    unittest.main()
