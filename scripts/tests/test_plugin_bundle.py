"""Five-plugin candidates, using only disposable Git inputs and outputs."""
import base64
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import skill_release as release


@unittest.skipUnless(os.name == "nt", "Pinned package I/O is Windows-only")
class PluginBundleTests(unittest.TestCase):
    SAFETY_OWNERS = {
        "careful": "SimonKCore", "unfreeze": "SimonKCore",
        "freeze": "SimonKStack", "guard": "SimonKStack", "investigate": "SimonKStack",
    }
    SAFETY_DOCS = {
        "plugins/SimonKCore/skills/careful/SKILL.md",
        "plugins/SimonKCore/skills/unfreeze/SKILL.md",
        "plugins/SimonKStack/skills/freeze/SKILL.md",
        "plugins/SimonKStack/skills/guard/SKILL.md",
        "plugins/SimonKStack/skills/investigate/SKILL.md",
        "plugins/SimonKStack/skills/investigate/references/detail.md",
    }
    SAFETY_RESOURCES = {
        "careful/bin/check-careful.sh":
            "plugins/SimonKCore/skills/careful/bin/check-careful.sh",
        "careful/bin/hook-extract.sh":
            "plugins/SimonKCore/skills/careful/bin/hook-extract.sh",
        "freeze/bin/check-freeze.sh":
            "plugins/SimonKStack/skills/freeze/bin/check-freeze.sh",
        "safety_runtime.py":
            "plugins/SimonKStack/skills/freeze/bin/safety_runtime.py",
    }

    def setUp(self):
        helper = ROOT / "scripts/plugin_bundle.py"
        self.assertTrue(helper.is_file(), "Five-plugin candidate builder is not implemented")
        spec = importlib.util.spec_from_file_location("plugin_bundle", helper)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.temp = tempfile.TemporaryDirectory(prefix="vibe-plugin-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo, self.plugins = self.base / "source", self.base / "bases"
        self.repo.mkdir(); self.plugins.mkdir()
        self.config = {"schema_version": 1, "scope": release.SCOPE,
                       "owners": {"alpha": "SimonKCore", "beta": "SimonKStack"},
                       "development_only": [], "preserve_unowned": True,
                       "plugin_only_out_of_scope": [], "external_dependencies": []}
        self.inputs = {"schema_version": 1, "plugins": {}}
        for owner in sorted(release.OWNERS):
            root = self.plugins / owner
            root.mkdir()
            name = "simonk-" + owner.removeprefix("SimonK").lower()
            extra = "extra-" + name
            self.config["plugin_only_out_of_scope"].append(extra)
            self.put(root, f"skills/{extra}/SKILL.md", f"---\nname: {extra}\ndescription: fixture\n---\nExtra\n")
            names = [extra]
            for skill, home in self.config["owners"].items():
                if home == owner:
                    names.append(skill)
                    self.put(root, f"skills/{skill}/SKILL.md", f"---\nname: {skill}\ndescription: old\n---\nOld\n")
            manifest = {"name": name, "version": "1.2.3", "description": "fixture plugin",
                        "author": {"name": "Fixture"}, "license": "MIT",
                        "skills": [f"./skills/{s}/" for s in sorted(names)]}
            self.put(root, ".claude-plugin/plugin.json", json.dumps(manifest))
            self.put(root, ".claude-plugin/marketplace.json", json.dumps({
                "name": name, "owner": {"name": "Fixture"}, "version": "1.2.3",
                "plugins": [{"name": name, "source": "./", "version": "1.2.3"}]}))
            self.put(root, "LICENSE", "Original license\n")
            self.put(root, "NOTICE", "Original notice\n")
            self.put(root, "agents/.gitkeep", "")
            self.put(root, "commands/inspect.md", "Fixture command, never executed\n")
            self.git(root, "init", "-q")
            self.commit(root)
            sha = self.git(root, "rev-parse", "HEAD").strip()
            self.inputs["plugins"][owner] = {"name": name, "commit": sha}
        for skill in self.config["owners"]:
            policy = "disable-model-invocation: true\n" if skill == "beta" else ""
            self.put(self.repo, f"skills-src/{skill}/SKILL.md",
                     f"---\nname: {skill}\ndescription: new fixture\n{policy}---\nNew\n")
        self.put(self.repo, "skills-src/alpha/scripts/helper.py", "print('fixture only')\n")
        self.put(self.repo, "skills-src/VENDORED.md", "Source attribution\n")
        self.put(self.repo, "LICENSE", "Source license\n")
        self.put(self.repo, "NOTICE", "Source notice\n")
        self.git(self.repo, "init", "-q")
        self.git(self.repo, "add", ".")
        self.git(self.repo, "update-index", "--chmod=+x", "skills-src/alpha/scripts/helper.py")
        self.source = self.base / "source-package"
        self.source_digest = release.build_release(self.repo, self.config, self.source)["release_digest"]
        self.output = self.base / "candidate"

    def put(self, root, path, value):
        p = root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(value, encoding="utf-8", newline="\n")

    def git(self, root, *args):
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
        env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_SYSTEM="NUL",
                   GIT_CONFIG_GLOBAL="NUL", GIT_TERMINAL_PROMPT="0")
        command = ["git", "--no-optional-locks", "-c", "core.hooksPath=NUL",
                   "-c", "core.fsmonitor=false", "-c", "core.autocrlf=false",
                   "-c", "commit.gpgSign=false", "-C", str(root), *args]
        return subprocess.check_output(command, text=True, encoding="utf-8",
                                       stderr=subprocess.PIPE, timeout=15, env=env)

    def commit(self, root):
        self.git(root, "add", ".")
        self.git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "-qm", "test: fixture")

    def build(self, output=None):
        return self.m.build_bundle(self.source, self.source_digest, self.plugins,
                                   self.inputs, output or self.output)

    def enable_safety_fixture(self):
        """Add the reviewed real safety sources to the disposable alpha/beta fixture."""
        runtime = ROOT / "skills-src/freeze/bin/safety_runtime.py"
        self.assertTrue(runtime.is_file(), "Unit16 safety_runtime.py is not implemented")
        self.config["owners"].update(self.SAFETY_OWNERS)
        for skill in self.SAFETY_OWNERS:
            shutil.copytree(ROOT / "skills-src" / skill,
                            self.repo / "skills-src" / skill, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

        for owner in ("SimonKCore", "SimonKStack"):
            plugin = self.plugins / owner
            manifest_path = plugin / ".claude-plugin/plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for skill, home in self.SAFETY_OWNERS.items():
                if home != owner:
                    continue
                self.put(plugin, f"skills/{skill}/SKILL.md",
                         f"---\nname: {skill}\ndescription: old fixture\n---\nOld\n")
                manifest["skills"].append(f"./skills/{skill}/")
            manifest["skills"] = sorted(manifest["skills"])
            self.put(plugin, ".claude-plugin/plugin.json", json.dumps(manifest))
            self.repin(owner)

        self.git(self.repo, "add", ".")
        for source_path in self.SAFETY_RESOURCES.values():
            # package path plugins/<owner>/skills/... maps back to skills-src/...
            source_relative = Path("skills-src", *Path(source_path).parts[3:])
            tracked = self.git(ROOT, "ls-files", "-s", "--", source_relative.as_posix()).strip()
            if tracked.startswith("100755 "):
                self.git(self.repo, "update-index", "--chmod=+x", source_relative.as_posix())
        self.source = self.base / "safety-source-package"
        self.source_digest = release.build_release(self.repo, self.config, self.source)["release_digest"]
        self.output = self.base / "safety-candidate"

    def build_safety(self, output=None):
        return self.m.build_bundle(self.source, self.source_digest, self.plugins,
                                   self.inputs, output or self.output, safety_adapter=True)

    def rebuild_safety_source(self, label):
        self.git(self.repo, "add", "-A")
        self.source = self.base / ("safety-source-" + label)
        self.source_digest = release.build_release(self.repo, self.config, self.source)["release_digest"]
        self.output = self.base / ("safety-candidate-" + label)

    def repin_bundle(self, receipt):
        data = release.encoded(receipt)
        (self.output / "bundle.json").write_bytes(data)
        return release.digest(data)

    def repin(self, owner):
        root = self.plugins / owner
        self.commit(root)
        self.inputs["plugins"][owner]["commit"] = self.git(root, "rev-parse", "HEAD").strip()

    def forge(self, change):
        result = self.build()
        receipt = self.m.verify_bundle(self.output, result["bundle_digest"])
        change(receipt)
        data = release.encoded(receipt)
        (self.output / "bundle.json").write_bytes(data)
        with self.assertRaises(ValueError):
            self.m.verify_bundle(self.output, release.digest(data))

    def test_real_five_plugin_union_preserves_source_extras_and_components(self):
        result = self.build()
        receipt = self.m.verify_bundle(self.output, result["bundle_digest"])
        self.assertEqual(result["plugins"], 5)
        self.assertEqual(result["skills"], 7)
        self.assertFalse(receipt["runtime_closure_verified"])
        self.assertFalse(receipt["host_compatibility_verified"])
        self.assertFalse(receipt["installation_ready"])
        for owner, info in self.inputs["plugins"].items():
            plugin = self.output / "plugins" / owner
            manifest = json.loads((plugin / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
            expected = {n for n, home in receipt["owners"].items() if home == owner}
            self.assertEqual(manifest["skills"], [f"./skills/{n}/" for n in sorted(expected)])
            self.assertEqual(manifest["version"], "1.2.3-vibe." + self.source_digest[:12])
            market = json.loads((plugin / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
            self.assertEqual(market["plugins"][0]["version"], manifest["version"])
            self.assertEqual((plugin / "commands/inspect.md").read_bytes(),
                             (self.plugins / owner / "commands/inspect.md").read_bytes())
            self.assertEqual((plugin / "LICENSE").read_bytes(), b"Original license\n")
            self.assertEqual((plugin / ".simonk-source-attribution/LICENSE").read_bytes(), b"Source license\n")
        for skill, home in self.config["owners"].items():
            self.assertEqual((self.output / "plugins" / home / "skills" / skill / "SKILL.md").read_bytes(),
                             (self.repo / "skills-src" / skill / "SKILL.md").read_bytes())
        f = next(f for f in receipt["files"] if f["path"].endswith("scripts/helper.py"))
        self.assertEqual(f["mode"], "100755")

    def test_safety_adapter_is_explicit_v2_opt_in(self):
        self.enable_safety_fixture()
        v1_output = self.base / "plain-candidate"
        v1 = self.build(v1_output)
        v1_receipt = self.m.verify_bundle(v1_output, v1["bundle_digest"])
        self.assertEqual(v1_receipt["schema_version"], 1)
        self.assertEqual(v1_receipt["scope"], "five-plugin-candidate-v1")
        self.assertNotIn("safety_projection", v1_receipt)

        v2 = self.build_safety()
        receipt = self.m.verify_bundle(self.output, v2["bundle_digest"])
        self.assertEqual(receipt["schema_version"], 2)
        self.assertEqual(receipt["scope"], "five-plugin-candidate-safety-v2")
        self.assertEqual(receipt["safety_projection"]["version"], 1)
        self.assertFalse(receipt["runtime_closure_verified"])
        self.assertFalse(receipt["host_compatibility_verified"])
        self.assertFalse(receipt["installation_ready"])

    def test_cli_safety_adapter_flag_passes_explicit_true(self):
        import io
        inputs = self.base / "inputs.json"
        inputs.write_text(json.dumps(self.inputs), encoding="utf-8")
        expected = {"status": "fixture", "installation_ready": False}
        argv = ["build", "--source-package", str(self.source),
                "--source-digest", self.source_digest, "--plugin-parent", str(self.plugins),
                "--inputs", str(inputs), "--output", str(self.output), "--safety-adapter"]
        with patch.object(self.m, "build_bundle", return_value=expected) as build, \
                patch.object(sys, "stdout", io.StringIO()) as stdout:
            self.assertEqual(self.m.main(argv), 0)
        self.assertEqual(json.loads(stdout.getvalue()), expected)
        self.assertTrue(build.call_args.kwargs["safety_adapter"])

    def test_safety_projection_is_exact_and_changes_only_reviewed_members(self):
        self.enable_safety_fixture()
        plain_output = self.base / "plain-candidate"
        plain = self.build(plain_output)
        plain_receipt = self.m.verify_bundle(plain_output, plain["bundle_digest"])
        result = self.build_safety()
        receipt = self.m.verify_bundle(self.output, result["bundle_digest"])

        expected_inputs = self.SAFETY_DOCS | set(self.SAFETY_RESOURCES.values())
        self.assertEqual(set(receipt["safety_projection"]), {"version", "originals"})
        self.assertEqual(receipt["safety_projection"]["version"], 1)
        self.assertEqual(set(receipt["safety_projection"]["originals"]), expected_inputs)
        source_records = {f["package_path"]: f for f in receipt["source_manifest"]["files"]}
        for path, encoded in receipt["safety_projection"]["originals"].items():
            raw = base64.b64decode(encoded, validate=True)
            record = source_records[path]
            self.assertEqual((len(raw), release.digest(raw)), (record["size"], record["sha256"]))
            self.assertEqual(raw, (self.source / path).read_bytes())

        added = {f"plugins/{owner}/.simonk-runtime/{relative}"
                 for owner in ("SimonKCore", "SimonKStack")
                 for relative in self.SAFETY_RESOURCES}
        plain_files = release.files_under(plain_output) - {"bundle.json"}
        safety_files = release.files_under(self.output) - {"bundle.json"}
        self.assertEqual(safety_files - plain_files, added)
        self.assertEqual(plain_files - safety_files, set())
        changed = {path for path in plain_files
                   if (plain_output / path).read_bytes() != (self.output / path).read_bytes()}
        self.assertEqual(changed, self.SAFETY_DOCS)
        self.assertEqual(receipt["owners"], plain_receipt["owners"])
        for owner in ("SimonKCore", "SimonKStack"):
            for relative, original in self.SAFETY_RESOURCES.items():
                self.assertEqual(
                    (self.output / f"plugins/{owner}/.simonk-runtime/{relative}").read_bytes(),
                    (self.source / original).read_bytes())

    def test_projected_hooks_and_setup_commands_have_fixed_host_placeholders(self):
        self.enable_safety_fixture()
        result = self.build_safety()
        self.m.verify_bundle(self.output, result["bundle_digest"])
        runtime = "${CLAUDE_PLUGIN_ROOT}/.simonk-runtime/safety_runtime.py"
        expected = {
            "careful": {"careful": 1}, "freeze": {"freeze": 2},
            "guard": {"careful": 1, "freeze": 2}, "investigate": {"freeze": 2},
        }
        homes = {**self.SAFETY_OWNERS}
        for skill, kinds in expected.items():
            path = self.output / "plugins" / homes[skill] / "skills" / skill / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            for kind, count in kinds.items():
                args = json.dumps(["-B", runtime, "check", kind, "--project",
                                   "${CLAUDE_PROJECT_DIR}"])
                self.assertEqual(text.count('command: "python"\n          args: ' + args), count)
            self.assertNotIn("command: \"bash ${CLAUDE_SKILL_DIR}/", text)

        for skill in ("freeze", "guard", "investigate", "unfreeze"):
            text = (self.output / "plugins" / homes[skill] / "skills" / skill / "SKILL.md").read_text(
                encoding="utf-8")
            self.assertIn("python -B -c", text)
            self.assertIn("SIMONK_SAFETY_INPUT", text)
            self.assertIn("${CLAUDE_PLUGIN_ROOT}", text)
            self.assertIn("${CLAUDE_PROJECT_DIR}", text)
            self.assertIn("${CLAUDE_SESSION_ID}", text)
            self.assertNotIn('STATE_DIR="${CLAUDE_PLUGIN_DATA:-$HOME/.gstack}"', text)
        detail = (self.output / "plugins/SimonKStack/skills/investigate/references/detail.md").read_text(
            encoding="utf-8")
        self.assertIn("Candidate session scope commands", detail)
        self.assertNotIn("CLAUDE_SKILL_DIR", detail)
        self.assertNotIn("CLAUDE_PLUGIN_DATA", detail)

    def test_rederived_projection_rejects_repinned_document_and_runtime_tamper(self):
        self.enable_safety_fixture()
        for kind in ("document", "runtime"):
            with self.subTest(kind=kind):
                output = self.base / ("safety-candidate-" + kind)
                result = self.build_safety(output)
                receipt = self.m.verify_bundle(output, result["bundle_digest"])
                path = ("plugins/SimonKStack/skills/guard/SKILL.md" if kind == "document" else
                        "plugins/SimonKCore/.simonk-runtime/careful/bin/check-careful.sh")
                target = output / path
                data = target.read_bytes() + b"\n# forged after build\n"
                target.write_bytes(data)
                record = next(f for f in receipt["files"] if f["path"] == path)
                record.update(size=len(data), sha256=release.digest(data))
                self.output = output
                digest = self.repin_bundle(receipt)
                with self.assertRaises(ValueError):
                    self.m.verify_bundle(output, digest)

    def test_rederived_projection_rejects_repinned_original_provenance(self):
        self.enable_safety_fixture()
        result = self.build_safety()
        receipt = self.m.verify_bundle(self.output, result["bundle_digest"])
        path = "plugins/SimonKCore/skills/careful/SKILL.md"
        raw = base64.b64decode(receipt["safety_projection"]["originals"][path], validate=True)
        receipt["safety_projection"]["originals"][path] = base64.b64encode(raw + b"\nforged\n").decode("ascii")
        digest = self.repin_bundle(receipt)
        with self.assertRaises(ValueError):
            self.m.verify_bundle(self.output, digest)

    def test_safety_projection_requires_every_reviewed_component(self):
        self.enable_safety_fixture()
        missing = self.repo / "skills-src/investigate/references/detail.md"
        missing.unlink()
        self.rebuild_safety_source("missing")
        with self.assertRaises(ValueError):
            self.build_safety()
        self.assertFalse(self.output.exists())

    def test_safety_projection_rejects_unexpected_transform_count_drift(self):
        self.enable_safety_fixture()
        skill = self.repo / "skills-src/freeze/SKILL.md"
        duplicate = '          command: "bash ${CLAUDE_SKILL_DIR}/bin/check-freeze.sh"\n'
        skill.write_text(skill.read_text(encoding="utf-8") + duplicate, encoding="utf-8", newline="\n")
        self.rebuild_safety_source("drift")
        with self.assertRaises(ValueError):
            self.build_safety()
        self.assertFalse(self.output.exists())

    def test_safety_document_rejects_mixed_line_endings(self):
        raw = (ROOT / "skills-src/careful/SKILL.md").read_bytes()
        lf = raw.replace(b"\r\n", b"\n")
        self.assertNotIn(b"\r", lf)
        crlf = self.m.safety_document("careful", lf.replace(b"\n", b"\r\n"))
        self.assertNotIn(b"\n", crlf.replace(b"\r\n", b""))
        mixed = lf.replace(b"\n", b"\r\n", 1)
        with self.assertRaises(ValueError):
            self.m.safety_document("careful", mixed)

    def test_safety_setup_quoted_data_survives_shell_metacharacters(self):
        bash = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"
        if not bash.is_file():
            self.skipTest("Git Bash is required for the generated setup command")
        sentinels = [self.base / name for name in ("injected-one", "injected-two",
                                                    "injected-three", "injected-four")]
        plugin = self.base / "plugin ' $(touch injected-one) `touch injected-two`"
        project = self.base / "project ' $(touch injected-three) `touch injected-four`"
        boundary = project / "boundary ' $() `literal`"
        runtime = plugin / ".simonk-runtime/safety_runtime.py"
        boundary.mkdir(parents=True)
        runtime.parent.mkdir(parents=True)
        runtime.write_text("import json,sys\nprint(json.dumps(sys.argv))\n", encoding="utf-8")
        session = "session-'$(touch injected-one)-`touch injected-two`"
        env = {k: v for k, v in os.environ.items()
               if k.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP"}}
        env.update(PATH=os.pathsep.join((str(Path(sys.executable).parent),
                                         str(bash.parent.parent / "usr/bin"))),
                   HOME=str(self.base / "home"), USERPROFILE=str(self.base / "home"),
                   BASH_ENV="", ENV="", PYTHONDONTWRITEBYTECODE="1")
        for action in ("set", "clear"):
            markdown = self.m.safety_setup(action)
            shell = markdown.split("```bash\n", 1)[1].split("\n```", 1)[0]
            values = {"${CLAUDE_PLUGIN_ROOT}": str(plugin),
                      "${CLAUDE_PROJECT_DIR}": str(project),
                      "${CLAUDE_SESSION_ID}": session,
                      "<absolute-existing-Windows-directory>": str(boundary)}
            for old, new in values.items():
                shell = shell.replace(old, new)
            result = subprocess.run([str(bash), "--noprofile", "--norc", "-c", shell],
                                    cwd=self.base, env=env, text=True, encoding="utf-8",
                                    capture_output=True, timeout=15)
            with self.subTest(action=action):
                self.assertEqual(result.returncode, 0, result.stderr)
                argv = json.loads(result.stdout)
                expected = [str(runtime), action, "--project", str(project),
                            "--session", session]
                if action == "set":
                    expected += ["--boundary", str(boundary)]
                self.assertEqual(argv, expected)
                self.assertTrue(all(not path.exists() for path in sentinels))

    def test_safety_setup_rejects_unc_root_before_runpy(self):
        import io
        import runpy
        markdown = self.m.safety_setup("set")
        shell = markdown.split("```bash\n", 1)[1].split("\n```", 1)[0]
        prefix, suffix = "python -B -c '", "' <<'SIMONK_SAFETY_INPUT'"
        self.assertTrue(shell.startswith(prefix))
        code = shell[len(prefix):shell.index(suffix)]
        stdin = io.StringIO("\\\\server\\share\nC:\\project\nsession\nC:\\boundary\n")
        with patch.object(sys, "stdin", stdin), patch.object(sys, "argv", ["fixture"]), \
                patch.object(runpy, "run_path", side_effect=AssertionError("runpy reached UNC")) as called:
            with self.assertRaises(SystemExit) as stopped:
                exec(compile(code, "<safety-setup>", "exec"), {})
        self.assertEqual(stopped.exception.code, 2)
        called.assert_not_called()

    def test_safety_setup_rejects_mapped_drive_before_runpy(self):
        import ctypes
        import io
        import runpy
        markdown = self.m.safety_setup("clear")
        shell = markdown.split("```bash\n", 1)[1].split("\n```", 1)[0]
        prefix, suffix = "python -B -c '", "' <<'SIMONK_SAFETY_INPUT'"
        code = shell[len(prefix):shell.index(suffix)]
        stdin = io.StringIO("C:\\candidate\nC:\\project\nsession\n")
        with patch.object(sys, "stdin", stdin), patch.object(sys, "argv", ["fixture"]), \
                patch.object(ctypes.windll.kernel32, "GetDriveTypeW", return_value=4) as drive, \
                patch.object(runpy, "run_path", side_effect=AssertionError("runpy reached mapped drive")) as called:
            with self.assertRaises(SystemExit) as stopped:
                exec(compile(code, "<safety-setup>", "exec"), {})
        self.assertEqual(stopped.exception.code, 2)
        drive.assert_called_once()
        called.assert_not_called()

    def test_actual_candidate_runtime_shares_state_across_core_and_stack(self):
        self.enable_safety_fixture()
        result = self.build_safety()
        self.m.verify_bundle(self.output, result["bundle_digest"])
        bash = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"
        if not bash.is_file():
            self.skipTest("Git Bash is required for candidate runtime E2E")
        project = self.base / "project with spaces"
        boundary = project / "inside"
        outside = project / "outside"
        boundary.mkdir(parents=True)
        outside.mkdir()
        (boundary / "allowed.txt").write_text("fixture", encoding="utf-8")
        (outside / "blocked.txt").write_text("fixture", encoding="utf-8")
        state = self.base / "shared state"
        core_data, stack_data = self.base / "core data", self.base / "stack data"
        core_data.mkdir(); stack_data.mkdir()
        node = shutil.which("node")
        path = [str(Path(sys.executable).parent), str(bash.parent.parent / "usr/bin")]
        if node:
            path.append(str(Path(node).parent))
        common = {k: v for k, v in os.environ.items()
                  if k.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PROGRAMFILES",
                                   "PROGRAMFILES(X86)"}}
        common.update(PATH=os.pathsep.join(path), SIMONK_SAFETY_STATE_ROOT=str(state),
                      SIMONK_SAFETY_BASH=str(bash), PYTHONDONTWRITEBYTECODE="1",
                      GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                      GIT_CONFIG_SYSTEM=os.devnull, GIT_TERMINAL_PROMPT="0")
        core = self.output / "plugins/SimonKCore/.simonk-runtime/safety_runtime.py"
        stack = self.output / "plugins/SimonKStack/.simonk-runtime/safety_runtime.py"

        def invoke(runtime, *args, session=None, file_path=None, command=None, plugin_data=None):
            payload = None
            if session is not None:
                tool_input = ({"command": command} if command is not None else
                              {"file_path": str(file_path)})
                payload = json.dumps({"session_id": session, "cwd": str(project),
                                      "hook_event_name": "PreToolUse", "tool_input": tool_input})
            env = {**common, "CLAUDE_PLUGIN_DATA": str(plugin_data)}
            process = subprocess.run([sys.executable, "-B", str(runtime), *args], input=payload,
                                     text=True, encoding="utf-8", capture_output=True,
                                     cwd=project, env=env, timeout=20)
            return process

        def decision(process):
            self.assertEqual(process.returncode, 0, process.stderr)
            output = json.loads(process.stdout)
            return output.get("hookSpecificOutput", {}).get("permissionDecision", "allow")

        first, second = "session-one", "session-two"
        set_state = invoke(stack, "set", "--project", str(project), "--session", first,
                           "--boundary", str(boundary), plugin_data=stack_data)
        self.assertEqual(set_state.returncode, 0, set_state.stderr)
        self.assertEqual(decision(invoke(stack, "check", "freeze", "--project", str(project),
                                         session=first, file_path=boundary / "allowed.txt",
                                         plugin_data=stack_data)), "allow")
        self.assertEqual(decision(invoke(stack, "check", "freeze", "--project", str(project),
                                         session=first, file_path=outside / "blocked.txt",
                                         plugin_data=stack_data)), "deny")
        self.assertEqual(decision(invoke(stack, "check", "freeze", "--project", str(project),
                                         session=second, file_path=boundary / "allowed.txt",
                                         plugin_data=stack_data)), "deny")
        clear_other = invoke(core, "clear", "--project", str(project), "--session", second,
                             plugin_data=core_data)
        self.assertEqual(clear_other.returncode, 0, clear_other.stderr)
        self.assertEqual(decision(invoke(stack, "check", "freeze", "--project", str(project),
                                         session=first, file_path=outside / "blocked.txt",
                                         plugin_data=stack_data)), "deny")
        clear = invoke(core, "clear", "--project", str(project), "--session", first,
                       plugin_data=core_data)
        self.assertEqual(clear.returncode, 0, clear.stderr)
        self.assertEqual(decision(invoke(stack, "check", "freeze", "--project", str(project),
                                         session=first, file_path=outside / "blocked.txt",
                                         plugin_data=stack_data)), "allow")
        self.assertEqual(decision(invoke(core, "check", "careful", "--project", str(project),
                                         session=first, command="rm -rf /var/data",
                                         plugin_data=core_data)), "ask")

    def test_repeated_builds_equal_but_existing_output_is_preserved(self):
        first = self.build()
        second = self.build(self.base / "candidate2")
        self.assertEqual(first["bundle_digest"], second["bundle_digest"])
        before = (self.output / "bundle.json").read_bytes()
        with self.assertRaises(ValueError):
            self.build()
        self.assertEqual((self.output / "bundle.json").read_bytes(), before)

    def test_dirty_or_wrong_commit_inputs_block_before_output(self):
        self.inputs["plugins"]["SimonKCore"]["commit"] = "0" * 40
        with self.assertRaises(ValueError):
            self.build()
        self.inputs["plugins"]["SimonKCore"]["commit"] = self.git(self.plugins / "SimonKCore", "rev-parse", "HEAD").strip()
        self.put(self.plugins / "SimonKCore", "local-only.txt", "user file")
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse(self.output.exists())

    def test_source_only_replacement_rejects_unexplained_old_helpers(self):
        root = self.plugins / "SimonKCore"
        self.put(root, "skills/alpha/stale-helper.py", "not silently kept or dropped\n")
        self.commit(root)
        self.inputs["plugins"]["SimonKCore"]["commit"] = self.git(root, "rev-parse", "HEAD").strip()
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse(self.output.exists())

    def test_duplicate_extra_or_incorrect_manifest_membership_is_rejected(self):
        root = self.plugins / "SimonKCore"
        self.put(root, "skills/extra-simonk-aihub/SKILL.md", "---\nname: extra-simonk-aihub\n---\nDuplicate\n")
        self.commit(root)
        self.inputs["plugins"]["SimonKCore"]["commit"] = self.git(root, "rev-parse", "HEAD").strip()
        with self.assertRaises(ValueError):
            self.build()

    def test_tampered_missing_or_extra_output_cannot_verify(self):
        for kind in ("tampered", "missing", "extra"):
            with self.subTest(kind=kind):
                output = self.base / kind
                result = self.build(output)
                p = output / "plugins/SimonKCore/commands/inspect.md"
                if kind == "tampered":
                    p.write_bytes(b"changed")
                elif kind == "missing":
                    p.unlink()
                else:
                    (p.parent / "extra.md").write_bytes(b"unlisted")
                with self.assertRaises(ValueError):
                    self.m.verify_bundle(output, result["bundle_digest"])

    def test_source_digest_mismatch_and_protected_target_are_rejected(self):
        with self.assertRaises(ValueError):
            self.m.build_bundle(self.source, "0" * 64, self.plugins, self.inputs, self.output)
        for folder in (".codex", ".claude", ".agents", "SimonK-Plugins"):
            parent = self.base / folder
            parent.mkdir()
            with self.assertRaises(ValueError):
                self.build(parent / "candidate")
        self.assertFalse(self.output.exists())

    def test_commit_input_schema_is_exact(self):
        for kind in ("missing", "unknown", "badsha", "bool", "badname"):
            config = copy.deepcopy(self.inputs)
            if kind == "missing": del config["plugins"]["SimonKAIHub"]
            if kind == "unknown": config["unexpected"] = True
            if kind == "badsha": config["plugins"]["SimonKCore"]["commit"] = "x" * 40
            if kind == "bool": config["schema_version"] = True
            if kind == "badname": config["plugins"]["SimonKCore"]["name"] = "../escape"
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                self.m.build_bundle(self.source, self.source_digest, self.plugins, config, self.output)

    def test_prefix_skill_names_have_exact_membership_independent_of_path_sort(self):
        root = self.plugins / "SimonKCore"
        extra = "extra-simonk-core-more"
        self.put(root, f"skills/{extra}/SKILL.md", f"---\nname: {extra}\n---\nFixture\n")
        path = root / ".claude-plugin/plugin.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["skills"].append(f"./skills/{extra}/")
        self.put(root, ".claude-plugin/plugin.json", json.dumps(manifest))
        self.repin("SimonKCore")
        self.config["plugin_only_out_of_scope"].append(extra)
        self.source = self.base / "source2"
        self.source_digest = release.build_release(self.repo, self.config, self.source)["release_digest"]
        self.assertEqual(self.build()["skills"], 8)

    def test_legacy_and_paired_cache_are_classified_without_reading_excluded_bytes(self):
        root = self.plugins / "SimonKAIHub"
        legacy = "legacy/private-state.log"
        py = "skills/extra-simonk-aihub/scripts/helper.py"
        cache = "skills/extra-simonk-aihub/scripts/__pycache__/helper.cpython-312.pyc"
        self.put(root, legacy, "fixture state never copied")
        self.put(root, py, "print('fixture')\n")
        self.put(root, cache, "fixture cache never copied")
        self.repin("SimonKAIHub")
        original = release.read_file
        def guarded(path, *args, **kwargs):
            self.assertNotIn(Path(path), {root / legacy, root / cache})
            return original(path, *args, **kwargs)
        with patch.object(release, "read_file", side_effect=guarded):
            result = self.build()
        receipt = self.m.verify_bundle(self.output, result["bundle_digest"])
        excluded = [f for f in receipt["bases"]["SimonKAIHub"]["records"] if f["action"] == "excluded"]
        self.assertEqual({f["path"] for f in excluded}, {legacy, cache})
        self.assertTrue(all("git_blob" in f and "sha256" not in f for f in excluded))
        self.assertFalse((self.output / "plugins/SimonKAIHub" / legacy).exists())
        self.assertFalse((self.output / "plugins/SimonKAIHub" / cache).exists())

    def test_orphan_cache_unclassified_and_secret_members_block(self):
        root = self.plugins / "SimonKAIHub"
        for path in ("unexpected.txt", "skills/extra-simonk-aihub/.env",
                     "skills/extra-simonk-aihub/scripts/__pycache__/orphan.cpython-312.pyc"):
            self.put(root, path, "fixture only")
            self.repin("SimonKAIHub")
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.build()
            (root / path).unlink()
            self.repin("SimonKAIHub")
        self.assertFalse(self.output.exists())

    def test_active_components_referencing_excluded_files_block(self):
        root = self.plugins / "SimonKAIHub"
        for text in ("run ${CLAUDE_PLUGIN_ROOT}/legacy/run.ps1", "use scripts/__pycache__/tool.pyc"):
            self.put(root, "commands/inspect.md", text)
            self.repin("SimonKAIHub")
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.build()

    def test_embedded_source_manifest_is_cryptographically_checked(self):
        self.forge(lambda m: m["source_manifest"]["files"][0].update(sha256="0" * 64))

    def test_owned_member_cannot_be_relabeled_official_even_with_repinned_receipt(self):
        def mutate(m):
            f = next(f for f in m["files"] if f["path"].endswith("skills/alpha/SKILL.md"))
            f["origin"] = "official"
        self.forge(mutate)

    def test_forged_completion_flags_and_unknown_fields_block(self):
        self.forge(lambda m: m.update(installation_ready=True))

    def test_base_exclusion_reason_cannot_be_forged(self):
        def mutate(m):
            f = m["bases"]["SimonKCore"]["records"][0]
            f["action"], f["reason"] = "excluded", "not-needed"
        self.forge(mutate)

    def test_boolean_file_size_is_not_an_integer(self):
        # Git's zero-byte agents/.gitkeep makes bool False == int 0 tempting.
        def mutate(m):
            f = next(f for f in m["files"] if f["size"] == 0)
            f["size"] = False
        self.forge(mutate)

    def test_base_hardlink_is_rejected(self):
        path = self.plugins / "SimonKCore/commands/inspect.md"
        link = self.base / "hardlinked.md"
        os.link(path, link)
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse(self.output.exists())

    def test_repinning_receipt_cannot_hide_a_tracked_base_member(self):
        def mutate(m):
            owner = "SimonKCore"
            path = "commands/inspect.md"
            m["bases"][owner]["records"] = [f for f in m["bases"][owner]["records"] if f["path"] != path]
            candidate = f"plugins/{owner}/{path}"
            m["files"] = [f for f in m["files"] if f["path"] != candidate]
            (self.output / candidate).unlink()
        self.forge(mutate)

    def test_untracked_junction_is_rejected_before_git_inspects_worktree(self):
        outside = self.base / "outside-fixture"
        outside.mkdir()
        self.put(outside, "marker.txt", "fixture never read")
        link = self.plugins / "SimonKCore/untracked-junction"
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                       check=True, capture_output=True, timeout=15)
        with patch.object(self.m, "git", side_effect=AssertionError("Git ran before no-follow preflight")):
            with self.assertRaises(ValueError):
                self.build()

    def test_plugin_only_skill_referencing_excluded_cache_is_rejected(self):
        root = self.plugins / "SimonKAIHub"
        self.put(root, "skills/extra-simonk-aihub/scripts/helper.py", "print('fixture')")
        self.put(root, "skills/extra-simonk-aihub/scripts/__pycache__/helper.cpython-312.pyc", "fixture")
        self.put(root, "skills/extra-simonk-aihub/SKILL.md",
                 "---\nname: extra-simonk-aihub\n---\nRun scripts/__pycache__/helper.cpython-312.pyc\n")
        self.repin("SimonKAIHub")
        with self.assertRaises(ValueError):
            self.build()

    def test_git_children_are_offline_and_ignore_inherited_git_overrides(self):
        result = subprocess.CompletedProcess([], 0, stdout=b"fixture", stderr=b"")
        with patch.dict(os.environ, {"GIT_WORK_TREE": "never-used", "GIT_CONFIG_COUNT": "17"}), \
                patch.object(self.m.subprocess, "run", return_value=result) as run:
            self.m.git(self.plugins / "SimonKCore", "rev-parse", "HEAD")
        env = run.call_args.kwargs["env"]
        self.assertEqual(env["GIT_NO_LAZY_FETCH"], "1")
        self.assertEqual(env["GIT_ALLOW_PROTOCOL"], "")
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
        self.assertNotIn("GIT_WORK_TREE", env)
        self.assertNotIn("GIT_CONFIG_COUNT", env)

    def test_local_clean_filter_is_blocked_without_executing_it(self):
        root = self.plugins / "SimonKAIHub"
        self.git(root, "config", "filter.fixture.clean", "DO_NOT_EXECUTE_FIXTURE")
        with patch.object(self.m, "git", side_effect=AssertionError("External-filter repo reached Git")):
            with self.assertRaises(ValueError):
                self.build()

    def test_metadata_preserves_all_except_declared_candidate_fields(self):
        import base64
        root = self.plugins / "SimonKCore"
        originals = {}
        for path in (self.m.PLUGIN, self.m.MARKET):
            m = json.loads((root / path).read_text(encoding="utf-8"))
            m["x-fixture"] = {"policy": ["한국어", False, {"keep": "exact"}]}
            self.put(root, path, json.dumps(m, ensure_ascii=False))
            originals[path] = (root / path).read_bytes()
        self.repin("SimonKCore")
        result = self.build()
        receipt = self.m.verify_bundle(self.output, result["bundle_digest"])
        for path, data in originals.items():
            self.assertEqual(base64.b64decode(receipt["bases"]["SimonKCore"]["original_metadata"][path]), data)
            old = json.loads(data)
            new = json.loads((self.output / "plugins/SimonKCore" / path).read_bytes())
            new["version"] = old["version"]
            if path == self.m.PLUGIN:
                new["skills"] = old["skills"]
            else:
                new["plugins"][0]["version"] = old["plugins"][0]["version"]
            self.assertEqual(new, old)

    def test_every_source_member_and_attribution_is_mapped_exactly(self):
        root = self.plugins / "SimonKCore"
        self.put(root, "skills/alpha/scripts/helper.py", "old official helper")
        self.repin("SimonKCore")
        result = self.build()
        receipt = self.m.verify_bundle(self.output, result["bundle_digest"])
        for member in receipt["source_manifest"]["files"]:
            mapped = [f for f in receipt["files"] if f["origin"] == "source" and f["input_path"] == member["package_path"]]
            self.assertEqual(len(mapped), 1 if member["package_path"].startswith("plugins/") else 5)
            for f in mapped:
                self.assertEqual((f["size"], f["sha256"], f["mode"]),
                                 (member["size"], member["sha256"], member["mode"]))
        self.assertEqual((self.output / "plugins/SimonKCore/skills/alpha/scripts/helper.py").read_bytes(),
                         (self.repo / "skills-src/alpha/scripts/helper.py").read_bytes())

    def test_modified_staged_deleted_and_ignored_files_are_blocked(self):
        root = self.plugins / "SimonKCore"
        path = "commands/inspect.md"
        original = (root / path).read_bytes()
        self.put(root, path, "modified")
        with self.assertRaises(ValueError): self.build()
        self.git(root, "add", path)
        with self.assertRaises(ValueError): self.build()
        (root / path).write_bytes(original)
        self.git(root, "add", path)
        (root / path).unlink()
        with self.assertRaises(ValueError): self.build()
        (root / path).write_bytes(original)
        self.put(root, ".git/info/exclude", "ignored.bin\n")
        self.put(root, "ignored.bin", "not silently shipped")
        with self.assertRaises(ValueError): self.build()

    def test_source_bytes_cannot_change_after_initial_verification(self):
        original = release.verify_release
        def verify_then_change(*args, **kwargs):
            result = original(*args, **kwargs)
            (self.source / "plugins/SimonKCore/skills/alpha/SKILL.md").write_bytes(b"changed after verification")
            return result
        with patch.object(release, "verify_release", side_effect=verify_then_change):
            with self.assertRaises(ValueError): self.build()
        self.assertFalse(self.output.exists())

    def test_commit_object_or_tree_cannot_be_forged_with_repinned_bundle(self):
        self.forge(lambda m: m["bases"]["SimonKCore"].update(tree="0" * 40))

    def test_indented_git_sections_and_options_cannot_hide_in_ini_continuations(self):
        root = self.plugins / "SimonKAIHub"
        config = root / ".git/config"
        original = config.read_bytes()
        attacks = (
            '\n[core]\n probe = x\n   [filter "fixture"]\n   clean = DO_NOT_EXECUTE_FIXTURE\n',
            '\n[core]\n probe = x\n   [include]\n   path = NEVER_READ_FIXTURE\n',
            '\n[core]\n probe = x\n   worktree = NEVER_READ_FIXTURE\n',
        )
        for suffix in attacks:
            # Keep one core section so strict INI duplicate-section rejection cannot mask the gap.
            content = original.decode("utf-8").replace('[core]\n', '[oldcore]\n') + suffix
            config.write_text(content, encoding="utf-8", newline="\n")
            with self.subTest(suffix=suffix), \
                    patch.object(self.m, "git", side_effect=AssertionError("Unsafe local config reached Git")):
                with self.assertRaises(ValueError): self.build()
        config.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
