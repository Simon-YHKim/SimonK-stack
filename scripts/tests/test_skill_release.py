"""Offline package boundaries; only disposable fixture repositories/targets."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts/skill_release.py"


@unittest.skipUnless(os.name == "nt", "Guarded package I/O is Windows-only")
class SkillReleaseTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(HELPER.is_file(), "The source-owned release helper is not implemented")
        spec = importlib.util.spec_from_file_location("skill_release", HELPER)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.temp = tempfile.TemporaryDirectory(prefix="vibe-release-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.config = {"schema_version": 1, "scope": "source-owned-overlay-v1",
                       "owners": {"alpha": "SimonKCore", "beta": "SimonKStack"},
                       "development_only": ["review"], "preserve_unowned": True,
                       "plugin_only_out_of_scope": ["third-party"],
                       "external_dependencies": [{"name": "Python", "status": "not_verified"}]}
        self.put("skills-src/alpha/SKILL.md", "---\nname: alpha\ndescription: fixture\n---\nAlpha\n")
        self.put("skills-src/alpha/scripts/run.py", "print('offline fixture')\n")
        self.put("skills-src/beta/SKILL.md", "---\nname: beta\ndescription: fixture\n---\nBeta\n")
        self.put(".claude/skills/review/SKILL.md", "---\nname: review\n---\nDevelopment only\n")
        self.put("LICENSE", "Fixture license\n")
        self.put("NOTICE", "Fixture notice\n")
        self.put("skills-src/VENDORED.md", "Fixture upstream attribution\n")
        self.git("init", "-q")
        self.git("add", "--", "skills-src", ".claude", "LICENSE", "NOTICE")
        self.git("update-index", "--chmod=+x", "skills-src/alpha/scripts/run.py")
        self.bundle = self.base / "package"
        self.target = self.base / "materialized"

    def put(self, relative, content):
        p = self.repo / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                       capture_output=True, timeout=15)

    def build(self):
        return self.m.build_release(self.repo, self.config, self.bundle)

    def test_build_records_every_tracked_member_and_portable_mode(self):
        result = self.build()
        manifest = self.m.verify_release(self.bundle, result["release_digest"])
        self.assertEqual(manifest["scope"], "source-owned-overlay-v1")
        self.assertFalse(manifest["full_plugin_build"])
        self.assertFalse(manifest["runtime_closure_verified"])
        self.assertEqual(set(manifest["owners"]), {"alpha", "beta"})
        expected = {"skills-src/alpha/SKILL.md", "skills-src/alpha/scripts/run.py",
                    "skills-src/beta/SKILL.md", "skills-src/VENDORED.md", "LICENSE", "NOTICE"}
        self.assertEqual({f["source_path"] for f in manifest["files"]}, expected)
        for f in manifest["files"]:
            data = (self.repo / f["source_path"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), f["sha256"])
            self.assertEqual(data, (self.bundle / f["package_path"]).read_bytes())
        executable = next(f for f in manifest["files"] if f["source_path"].endswith("run.py"))
        self.assertEqual(executable["mode"], "100755")

    def test_repeated_builds_are_deterministic_and_existing_output_is_not_replaced(self):
        first = self.build()
        second = self.m.build_release(self.repo, self.config, self.base / "package2")
        self.assertEqual(first["release_digest"], second["release_digest"])
        before = (self.bundle / "release.json").read_bytes()
        with self.assertRaises(ValueError):
            self.build()
        self.assertEqual(before, (self.bundle / "release.json").read_bytes())

    def test_preview_creates_nothing_and_apply_rechecks_same_release(self):
        release = self.build()["release_digest"]
        preview = self.m.materialize(self.bundle, self.target, release)
        self.assertEqual(preview["status"], "preview")
        self.assertFalse(self.target.exists())
        out = self.m.materialize(self.bundle, self.target, release, apply=True)
        self.assertEqual(out["status"], "materialized_verified")
        self.assertTrue((self.target / "alpha/scripts/run.py").is_file())
        self.assertFalse((self.target / "review").exists())
        extra = self.target / "third-party"
        extra.mkdir()
        (extra / "SKILL.md").write_bytes(b"unowned fixture")
        again = self.m.materialize(self.bundle, self.target, release, apply=True)
        self.assertEqual(again["status"], "existing_verified")
        self.assertEqual((extra / "SKILL.md").read_bytes(), b"unowned fixture")

    def test_changed_or_extra_package_members_are_rejected_before_target_creation(self):
        for kind in ("changed", "missing", "extra"):
            with self.subTest(kind=kind):
                bundle = self.base / kind
                release = self.m.build_release(self.repo, self.config, bundle)["release_digest"]
                member = bundle / "plugins/SimonKCore/skills/alpha/scripts/run.py"
                if kind == "changed":
                    member.write_bytes(b"tampered")
                elif kind == "missing":
                    member.unlink()
                else:
                    (member.parent / "unexpected.py").write_bytes(b"extra")
                with self.assertRaises(ValueError):
                    self.m.materialize(bundle, self.base / (kind + "-target"), release, apply=True)
                self.assertFalse((self.base / (kind + "-target")).exists())

    def test_expected_digest_and_modified_target_fail_without_overwrite(self):
        release = self.build()["release_digest"]
        with self.assertRaises(ValueError):
            self.m.materialize(self.bundle, self.target, "0" * 64, apply=True)
        self.m.materialize(self.bundle, self.target, release, apply=True)
        file = self.target / "alpha/scripts/run.py"
        file.write_bytes(b"user change")
        with self.assertRaises(ValueError):
            self.m.materialize(self.bundle, self.target, release, apply=True)
        self.assertEqual(file.read_bytes(), b"user change")

    def test_unmanaged_existing_target_is_preserved(self):
        release = self.build()["release_digest"]
        self.target.mkdir()
        sentinel = self.target / "unowned.txt"
        sentinel.write_bytes(b"preserve")
        with self.assertRaises(ValueError):
            self.m.materialize(self.bundle, self.target, release, apply=True)
        self.assertEqual(sentinel.read_bytes(), b"preserve")
        self.assertEqual(list(self.target.iterdir()), [sentinel])

    def test_ownership_missing_unknown_and_case_collisions_fail_before_write(self):
        for change in ("missing", "unknown", "case", "escape"):
            conf = copy.deepcopy(self.config)
            if change == "missing":
                del conf["owners"]["beta"]
            elif change == "unknown":
                conf["owners"]["alpha"] = "UnknownPlugin"
            elif change == "case":
                conf["owners"]["Alpha"] = "SimonKCore"
            else:
                conf["owners"]["../escape"] = "SimonKCore"
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.m.build_release(self.repo, conf, self.bundle)
            self.assertFalse(self.bundle.exists())

    def test_untracked_new_skill_and_tracked_sensitive_file_are_not_silently_packaged(self):
        self.put("skills-src/new-skill/SKILL.md", "---\nname: new-skill\ndescription: fixture\n---\nNew skill\n")
        with self.assertRaises(ValueError):
            self.build()
        self.config["owners"]["new-skill"] = "SimonKCore"
        self.git("add", "skills-src/new-skill")
        self.put("skills-src/alpha/.env", "FIXTURE_ONLY=not-a-secret\n")
        self.git("add", "-f", "skills-src/alpha/.env")
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse(self.bundle.exists())

    def test_declared_dependencies_and_development_scope_survive_build(self):
        release = self.build()["release_digest"]
        m = self.m.verify_release(self.bundle, release)
        self.assertEqual(m["development_only"], ["review"])
        self.assertEqual(m["plugin_only_out_of_scope"], ["third-party"])
        self.assertEqual(m["external_dependencies"], self.config["external_dependencies"])
        self.assertTrue(m["preserve_unowned"])

    def test_schema_version_requires_an_integer_not_bool_or_float(self):
        for version in (True, 1.0, "1", None):
            conf = copy.deepcopy(self.config)
            conf["schema_version"] = version
            with self.subTest(version=repr(version)), self.assertRaises(ValueError):
                self.m.validate_config(conf)

    def test_dependencies_have_exact_bounded_string_fields_and_unique_names(self):
        cases = [None, ["Python"], [{}], [{"name": "Python"}],
                 [{"name": "Python", "status": "not_verified", "verified": True}],
                 [{"name": "", "status": "not_verified"}],
                 [{"name": "Python", "status": False}],
                 [{"name": "Python", "status": ""}],
                 [{"name": "x" * 4097, "status": "not_verified"}],
                 [{"name": "Python", "status": "x" * 4097}],
                 [{"name": "Python", "status": "not_verified"},
                  {"name": "python", "status": "not_verified"}]]
        for deps in cases:
            conf = copy.deepcopy(self.config)
            conf["external_dependencies"] = deps
            with self.subTest(dependencies=repr(deps)[:70]), self.assertRaises(ValueError):
                self.m.validate_config(conf)

    def test_scope_name_collections_reject_bad_types_with_validation_error(self):
        for field, value in (("owners", {"alpha": []}), ("development_only", [[]]),
                             ("plugin_only_out_of_scope", [None])):
            conf = copy.deepcopy(self.config)
            conf[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.m.validate_config(conf)

    def test_json_loader_and_encoder_reject_nonfinite_numbers(self):
        path = self.base / "nonfinite.json"
        for literal in ("NaN", "Infinity", "-Infinity", "1e999", "-1e999"):
            path.write_text('{"nested": [{"number": ' + literal + '}]}', encoding="utf-8")
            with self.subTest(literal=literal), self.assertRaises(ValueError):
                self.m.load_json(path)
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(encoded=repr(value)), self.assertRaises(ValueError):
                self.m.encoded({"number": value})

    def test_manifest_source_state_cannot_claim_a_different_provenance(self):
        self.build()
        path = self.bundle / "release.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        for state in (None, False, "commit-attested", ""):
            changed = copy.deepcopy(manifest)
            changed["source_state"] = state
            data = (json.dumps(changed, sort_keys=True, indent=2) + "\n").encode("utf-8")
            path.write_bytes(data)
            with self.subTest(state=state), self.assertRaises(ValueError):
                self.m.verify_release(self.bundle, hashlib.sha256(data).hexdigest())
            self.assertFalse(self.target.exists())

    def test_noncanonical_release_json_is_rejected_during_verification(self):
        self.build()
        path = self.bundle / "release.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        data = json.dumps(manifest, separators=(",", ":")).encode("utf-8")
        path.write_bytes(data)
        with self.assertRaises(ValueError):
            self.m.verify_release(self.bundle, hashlib.sha256(data).hexdigest())

    def test_release_json_nonfinite_values_are_rejected_with_new_digest(self):
        self.build()
        path = self.bundle / "release.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        for value in (float("nan"), float("inf"), float("-inf")):
            changed = copy.deepcopy(manifest)
            changed["external_dependencies"][0]["status"] = value
            data = json.dumps(changed).encode("utf-8")
            path.write_bytes(data)
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                self.m.verify_release(self.bundle, hashlib.sha256(data).hexdigest())

    def test_manual_workflow_eol_gate_checks_only_declared_text(self):
        workflow = (ROOT / ".github/workflows/skill-release-windows-manual.yml").read_text(encoding="utf-8")
        pattern = re.search(r"if \(\$eols -match '([^']+)'", workflow).group(1)
        self.assertIsNone(re.search(pattern, "i/crlf w/crlf attr/-text\tskills-src/alpha/capture.raw"))
        self.assertIsNone(re.search(pattern, "i/lf w/lf attr/text eol=lf\tskills-src/alpha/SKILL.md"))
        for eol in ("crlf", "mixed"):
            self.assertIsNotNone(re.search(pattern, f"i/lf w/{eol} attr/text eol=lf\tskills-src/alpha/SKILL.md"))
        self.assertRegex(workflow, r"(?m)^on:\n  workflow_dispatch:\n\npermissions:\n  contents: read\n")
        self.assertIn("persist-credentials: false", workflow)
        self.assertNotRegex(workflow, r"(?m)^  (push|pull_request|schedule):")

    def test_fresh_checkouts_preserve_binary_bytes_and_execute_installer_directly(self):
        attributes = ROOT / ".gitattributes"
        self.assertTrue(attributes.is_file(), "Fresh-checkout byte policy is missing")
        self.put(".gitattributes", attributes.read_text(encoding="utf-8"))
        self.put("scripts/install.sh", (ROOT / "scripts/install.sh").read_text(encoding="utf-8"))
        self.put("scripts/skill_release.py", HELPER.read_text(encoding="utf-8"))
        self.put("distribution/skills-release.v1.json", json.dumps(self.config))
        binary = b"fixture\x00\r\nbytes\xff\r\n"
        self.put("skills-src/alpha/assets/image.bin", "")
        (self.repo / "skills-src/alpha/assets/image.bin").write_bytes(binary)
        raw = b"raw fixture\r\nunchanged bytes\r\n"
        (self.repo / "skills-src/alpha/assets/capture.raw").write_bytes(raw)
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")
        results = []
        for autocrlf in ("true", "false"):
            clone = self.base / ("checkout-" + autocrlf)
            subprocess.run(["git", "clone", "--no-local", "--no-checkout", str(self.repo), str(clone)],
                           check=True, capture_output=True, timeout=30)
            subprocess.run(["git", "-C", str(clone), "config", "core.autocrlf", autocrlf], check=True)
            subprocess.run(["git", "-C", str(clone), "checkout", "-q", "HEAD"], check=True, timeout=30)
            status = subprocess.run(["git", "-C", str(clone), "status", "--porcelain"],
                                    check=True, capture_output=True).stdout
            self.assertEqual(status, b"")
            self.assertNotIn(b"\r", (clone / "scripts/install.sh").read_bytes())
            self.assertEqual((clone / "skills-src/alpha/assets/image.bin").read_bytes(), binary)
            self.assertEqual((clone / "skills-src/alpha/assets/capture.raw").read_bytes(), raw)
            package = self.base / ("release-" + autocrlf)
            cli = [sys.executable, "-B", str(clone / "scripts/skill_release.py")]
            built = subprocess.run([*cli, "build", "--repo", str(clone), "--ownership",
                                    str(clone / "distribution/skills-release.v1.json"), "--output", str(package)],
                                   check=True, capture_output=True, text=True, encoding="utf-8", timeout=30)
            release = json.loads(built.stdout)["release_digest"]
            target = self.base / ("installed-" + autocrlf)
            env = dict(os.environ, SIMONK_PYTHON=sys.executable, PYTHONUTF8="1")
            args = ["C:/Program Files/Git/bin/bash.exe", str(clone / "scripts/install.sh"),
                    "--offline-package", str(package), "--target", str(target), "--expected-digest", release]
            for flags, expected in (([], "preview"), (["--apply"], "materialized_verified"),
                                    (["--apply"], "existing_verified")):
                executed = subprocess.run([*args, *flags], check=True, capture_output=True, text=True,
                                          encoding="utf-8", env=env, timeout=30)
                self.assertEqual(json.loads(executed.stdout)["status"], expected)
            results.append((release, {p.relative_to(package).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                      for p in package.rglob("*") if p.is_file()}))
        self.assertEqual(results[0], results[1])

    def test_source_link_is_rejected_without_reading_its_target(self):
        external = self.base / "external"
        external.mkdir()
        (external / "SKILL.md").write_bytes(b"do not read")
        linked = self.repo / "skills-src/linked"
        if os.name == "nt":
            p = subprocess.run(["cmd", "/c", "mklink", "/J", str(linked), str(external)],
                               capture_output=True, timeout=10)
            self.assertEqual(p.returncode, 0)
        else:
            linked.symlink_to(external, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse(self.bundle.exists())

    def test_publish_failure_never_creates_or_changes_destination(self):
        release = self.build()["release_digest"]
        with patch.object(self.m, "publish_new", side_effect=OSError("fixture interruption")):
            with self.assertRaises(OSError):
                self.m.materialize(self.bundle, self.target, release, apply=True)
        self.assertFalse(self.target.exists())
        self.m.materialize(self.bundle, self.target, release, apply=True)
        self.assertTrue((self.target / "alpha/SKILL.md").is_file())

    def test_reserved_targets_are_rejected_even_in_preview(self):
        release = self.build()["release_digest"]
        for target in (self.repo, self.repo.parent, Path.home(),
                       self.base / ".claude/skills", self.base / "SimonK-Plugins/new"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                self.m.materialize(self.bundle, target, release)

    def shell(self, *args):
        script = ROOT / "scripts/install.sh"
        bash = "C:/Program Files/Git/bin/bash.exe" if os.name == "nt" else "bash"
        env = dict(os.environ, SIMONK_PYTHON=sys.executable, PYTHONUTF8="1")
        # stdin avoids MSYS multiline -c argument truncation; argv0 stays the real script.
        prefix = "BASH_ARGV0=" + shlex.quote(script.as_posix()) + "\n"
        prefix += "git() { echo LEGACY_SENTINEL >&2; return 97; }; bun() { return 98; }\n"
        return subprocess.run([bash, "-s", "--", *args],
                              input=prefix + script.read_text(encoding="utf-8"),
                              text=True, encoding="utf-8", capture_output=True, env=env, timeout=25)

    def test_actual_installer_offline_entry_previews_applies_and_never_hits_legacy(self):
        release = self.build()["release_digest"]
        args = ["--offline-package", self.bundle.as_posix(), "--target", self.target.as_posix(),
                "--expected-digest", release]
        preview = self.shell(*args)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertEqual(json.loads(preview.stdout)["status"], "preview")
        self.assertFalse(self.target.exists())
        applied = self.shell(*args, "--apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertEqual(json.loads(applied.stdout)["status"], "materialized_verified")
        self.assertNotIn("LEGACY_SENTINEL", preview.stderr + applied.stderr)

    def test_legacy_options_cannot_leak_into_offline_install(self):
        release = self.build()["release_digest"]
        for flag in ("--force", "--no-backup", "--unknown"):
            p = self.shell("--offline-package", self.bundle.as_posix(), "--target",
                           self.target.as_posix(), "--expected-digest", release, flag)
            self.assertNotEqual(p.returncode, 0)
            self.assertNotIn("LEGACY_SENTINEL", p.stderr)
            self.assertFalse(self.target.exists())

    def test_tracked_private_key_filename_and_nonportable_names_fail_before_write(self):
        for filename in ("private.key", "certificate.pem", "bad?name.txt"):
            with self.subTest(filename=filename):
                rel = "skills-src/alpha/" + filename
                if os.name == "nt" and "?" in filename:
                    with self.assertRaises(ValueError):
                        self.m.relative(rel)
                    continue
                self.put(rel, "fixture, not an actual key")
                self.git("add", "--", rel)
                with self.assertRaises(ValueError):
                    self.build()
                self.assertFalse(self.bundle.exists())
                self.git("rm", "-f", "--", rel)  # Only this test's disposable tracked fixture.

    @unittest.skipUnless(os.name == "nt", "Windows package I/O")
    def test_unicode_non_bmp_destination_roundtrip(self):
        self.bundle = self.base / ("package-" + "\U0001f680" * 3)
        self.target = self.base / ("skills-" + "\U0001f680" * 3)
        release = self.build()["release_digest"]
        result = self.m.materialize(self.bundle, self.target, release, apply=True)
        self.assertEqual(result["status"], "materialized_verified")

    @unittest.skipUnless(os.name == "nt", "Windows does not apply POSIX executable bits")
    def test_windows_does_not_reopen_written_members_for_chmod(self):
        with patch.object(Path, "chmod", side_effect=AssertionError("Unsafe path reopen")):
            release = self.build()["release_digest"]
            self.m.materialize(self.bundle, self.target, release, apply=True)

    def short_path(self, path):
        import ctypes
        from ctypes import wintypes
        get_short = ctypes.WinDLL("kernel32", use_last_error=True).GetShortPathNameW
        get_short.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        get_short.restype = wintypes.DWORD
        result = ctypes.create_unicode_buffer(32768)
        self.assertGreater(get_short(str(path), result, len(result)), 0)
        short = Path(result.value)
        if str(short).casefold() == str(path).casefold():
            self.skipTest("Fixture volume does not expose an 8.3 alias")
        return short

    @unittest.skipUnless(os.name == "nt", "Windows short-path aliases")
    def test_short_alias_cannot_bypass_protected_target_or_input_overlap(self):
        self.bundle = self.base / "long-source-package"
        release = self.build()["release_digest"]
        protected = self.base / ".claude"
        protected.mkdir()
        for real in (protected, self.bundle):
            with self.subTest(parent=real.name):
                alias = self.short_path(real)
                with self.assertRaises(ValueError):
                    self.m.materialize(self.bundle, alias / "nested-target", release, apply=True)
                self.assertFalse((real / "nested-target").exists())

    @unittest.skipUnless(os.name == "nt", "Windows short-path aliases")
    def test_short_input_alias_cannot_bypass_long_target_overlap(self):
        self.bundle = self.base / "long-source-package"
        release = self.build()["release_digest"]
        with self.assertRaises(ValueError):
            self.m.materialize(self.short_path(self.bundle), self.bundle / "nested-target", release, apply=True)
        self.assertFalse((self.bundle / "nested-target").exists())

    @unittest.skipUnless(os.name == "nt", "Windows namespace guard")
    def test_network_and_device_paths_are_rejected_before_filesystem_inspection(self):
        for path in ("\\\\fixture.invalid\\share\\file", "\\\\?\\C:\\fixture", "\\\\.\\C:\\fixture"):
            with self.subTest(path=path), patch.object(Path, "lstat", side_effect=AssertionError("Must not inspect")):
                with self.assertRaises(ValueError):
                    self.m.no_links(path)

    def test_unsupported_platform_fails_closed_before_io(self):
        with patch.object(self.m.os, "name", "posix"), self.assertRaises(ValueError):
            self.m.local_path("fixture")

    @unittest.skipUnless(os.name == "nt", "Windows handle link count")
    def test_hardlink_alias_is_rejected_before_reading(self):
        protected = self.base / ".claude"
        protected.mkdir()
        source = protected / "fixture.txt"
        source.write_bytes(b"PROTECTED_FIXTURE_NOT_A_SECRET")
        alias = self.repo / "skills-src/alpha/hardlink.txt"
        os.link(source, alias)
        self.git("add", "--", "skills-src/alpha/hardlink.txt")
        with self.assertRaises(ValueError):
            self.m.read_file(alias)
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse(self.bundle.exists())

    def test_manifest_path_tamper_rejected_even_with_new_caller_digest(self):
        self.build()
        path = self.bundle / "release.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["files"][0]["install_path"] = "../outside"
        data = self.m.encoded(manifest)
        path.write_bytes(data)
        with self.assertRaises(ValueError):
            self.m.materialize(self.bundle, self.target, hashlib.sha256(data).hexdigest(), apply=True)
        self.assertFalse(self.target.exists())

    def test_package_changed_during_copy_is_not_published(self):
        release = self.build()["release_digest"]
        original = self.m.read_file
        reads = 0

        def changing(path):
            nonlocal reads
            if Path(path) == self.bundle / "plugins/SimonKCore/skills/alpha/scripts/run.py":
                reads += 1
                if reads == 2:
                    Path(path).write_bytes(b"fixture race")
            return original(path)

        with patch.object(self.m, "read_file", side_effect=changing), self.assertRaises(ValueError):
            self.m.materialize(self.bundle, self.target, release, apply=True)
        self.assertFalse(self.target.exists())

    def test_concurrent_destination_creator_is_not_overwritten(self):
        release = self.build()["release_digest"]
        original = self.m.publish_new

        def racing(stage, target):
            target.mkdir()
            (target / "other-owner").write_bytes(b"preserve")
            return original(stage, target)

        with patch.object(self.m, "publish_new", side_effect=racing), self.assertRaises(ValueError):
            self.m.materialize(self.bundle, self.target, release, apply=True)
        self.assertEqual((self.target / "other-owner").read_bytes(), b"preserve")

    def test_different_release_cannot_replace_existing_target(self):
        release = self.build()["release_digest"]
        self.m.materialize(self.bundle, self.target, release, apply=True)
        before = (self.target / "alpha/scripts/run.py").read_bytes()
        self.put("skills-src/alpha/scripts/run.py", "print('new source')\n")
        other = self.base / "new-package"
        newer = self.m.build_release(self.repo, self.config, other)["release_digest"]
        with self.assertRaises(ValueError):
            self.m.materialize(other, self.target, newer, apply=True)
        self.assertEqual((self.target / "alpha/scripts/run.py").read_bytes(), before)

    def test_unreadable_extra_subtree_is_not_treated_as_absent(self):
        release = self.build()["release_digest"]
        extra = self.bundle / "unreadable-extra"
        extra.mkdir()
        (extra / "unexpected.txt").write_bytes(b"extra")
        original = os.scandir

        def deny(path):
            if str(path) == str(extra):
                raise PermissionError("fixture unreadable subtree")
            return original(path)

        with patch.object(self.m.os, "scandir", side_effect=deny), self.assertRaises((ValueError, OSError)):
            self.m.verify_release(self.bundle, release)

    @unittest.skipUnless(os.name == "nt", "Real Windows junction race")
    def test_directory_swap_cannot_read_protected_fixture_bytes(self):
        source = self.base / "source"
        protected = self.base / "protected-fixture"
        source.mkdir()
        protected.mkdir()
        (source / "file.txt").write_bytes(b"safe fixture")
        (protected / "file.txt").write_bytes(b"PROTECTED_FIXTURE_ONLY")
        original = self.m.no_links
        swapped = False

        def swap(path):
            nonlocal swapped
            result = original(path)
            if Path(path) == source / "file.txt" and not swapped:
                swapped = True
                source.rename(self.base / "parked")
                p = subprocess.run(["cmd", "/c", "mklink", "/J", str(source), str(protected)],
                                   capture_output=True, timeout=10)
                self.assertEqual(p.returncode, 0)
            return result

        with patch.object(self.m, "no_links", side_effect=swap), self.assertRaises((ValueError, OSError)):
            self.m.read_file(source / "file.txt")

    @unittest.skipUnless(os.name == "nt", "Real Windows parent publication race")
    def test_publish_parent_swap_cannot_write_protected_fixture(self):
        parent = self.base / "publish-parent"
        protected = self.base / "protected-parent"
        parent.mkdir()
        protected.mkdir()
        stage = parent / "stage"
        stage.mkdir()
        (stage / "verified.txt").write_bytes(b"safe")
        (protected / "stage").mkdir()
        (protected / "stage/injected.txt").write_bytes(b"unverified")
        original = self.m.no_links
        swapped = False

        def swap(path):
            nonlocal swapped
            result = original(path)
            if Path(path) == parent and not swapped:
                swapped = True
                parent.rename(self.base / "parked-parent")
                p = subprocess.run(["cmd", "/c", "mklink", "/J", str(parent), str(protected)],
                                   capture_output=True, timeout=10)
                self.assertEqual(p.returncode, 0)
            return result

        with patch.object(self.m, "no_links", side_effect=swap), self.assertRaises((ValueError, OSError)):
            self.m.publish_new(stage, parent / "published")
        self.assertFalse((protected / "published").exists())


if __name__ == "__main__":
    unittest.main()
