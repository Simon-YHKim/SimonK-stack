"""Offline tests for the SimonK freeze / unfreeze / guard hooks (hub decision D-62, step A2).

Each test installs copies of skills-src/careful/bin and skills-src/freeze/bin under a
temporary HOME (HOME/.claude/skills/<skill>/bin) and runs the exact frontmatter hook
commands through Git Bash, feeding PreToolUse JSON payloads on stdin. The setup and
clear commands are taken from the SKILL.md files themselves. Payload paths are only
DATA: the hook judges them and never edits anything. No network, no model calls, no
writes outside the temporary directory.

Run:  python -B skills-src/freeze/bin/test_check_freeze.py
Windows needs Git for Windows at C:/Program Files/Git. Optional: set
FREEZE_HOOK_UNDER_TEST to another check-freeze.sh to run the same cases against it
(used to count the cases the gstack 1.91.9 original fails).
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

FREEZE = Path(__file__).resolve().parents[1]
SKILLS_SRC = FREEZE.parent
if os.name == "nt":
    BASH = Path("C:/Program Files/Git/bin/bash.exe")
else:
    BASH = Path(shutil.which("bash") or "/missing/bash")
GIT_ROOT = BASH.parent.parent
WINDOWS = os.name == "nt"
FREEZE_HOOK = 'bash "$HOME/.claude/skills/freeze/bin/check-freeze.sh"'
CAREFUL_HOOK = 'bash "$HOME/.claude/skills/careful/bin/check-careful.sh"'
STATE_WRITER_UPSTREAM_SHA256 = "ee14660e8dd6fedb1e6673fccffa9ff1740047955ef5b59d58d246ad1dccebf5"
BANNER_A = "<!-- AUTO-GENERATED from "
BANNER_B = "<!-- Regenerate: bun run gen:skill-docs -->"
# D-68 fixed warning: investigate stays the gstack copy, whose Windows scope lock is broken.
INVESTIGATE_WARNING = "Windows에서 investigate 잠금 금지. 편집이 전부 막히면 /unfreeze."
SKILL_VERSIONS = {"freeze": "0.2.7", "unfreeze": "0.2.1", "guard": "0.2.3"}
HIDE_CYGPATH = ('command() { if [ "${1-}" = -v ] && [ "${2-}" = cygpath ]; then return 1; fi; '
                'builtin command "$@"; }\n')


def posix(path):
    path = Path(path).absolute()
    if WINDOWS:
        return "/" + path.drive[0].lower() + path.as_posix()[2:]
    return str(path)


def front(skill):
    return (SKILLS_SRC / skill / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1]


def hooks_of(skill):
    """[(matcher, command)] in frontmatter order."""
    pairs = re.findall(r'-\s*matcher:\s*"([^"]+)"\s*\n\s*hooks:\s*\n\s*-\s*type:\s*command\s*\n'
                       r"\s*command:\s*'([^']*)'", front(skill))
    return pairs


def bash_block(skill, marker):
    text = (SKILLS_SRC / skill / "SKILL.md").read_text(encoding="utf-8")
    blocks = [b for b in re.findall(r"```bash\n(.*?)```", text, re.S) if marker in b]
    if len(blocks) != 1:
        raise AssertionError("expected one bash block with %r in %s, got %d" % (marker, skill, len(blocks)))
    return blocks[0]


@unittest.skipUnless(BASH.is_file(), "Git Bash / POSIX bash is required")
class FreezeHookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="freeze hook ")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.home = self.base / "home"
        self.skills = self.home / ".claude/skills"
        for skill in ("careful", "freeze"):
            shutil.copytree(SKILLS_SRC / skill / "bin", self.skills / skill / "bin",
                            ignore=shutil.ignore_patterns("*.py", "__pycache__"))
        for skill in ("careful", "freeze"):
            shutil.copyfile(SKILLS_SRC / skill / "SKILL.md", self.skills / skill / "SKILL.md")
        override = os.environ.get("FREEZE_HOOK_UNDER_TEST")
        if override:
            shutil.copyfile(override, self.skills / "freeze/bin/check-freeze.sh")
        self.state = self.home / ".gstack"
        self.work = self.base / "work dir"
        self.inside = self.work / "src"
        self.inside.mkdir(parents=True)
        (self.work / "src-other").mkdir()
        (self.inside / "existing.txt").write_text("fixture", encoding="utf-8")
        self.outside = self.base / "outside dir"
        self.outside.mkdir()
        self.shims = self.base / "shims"
        self.shims.mkdir()
        shim = self.shims / "python3"
        shim.write_bytes(("#!/bin/sh\nexec " + shlex.quote(posix(sys.executable)) +
                          ' "$@"\n').encode("utf-8"))
        shim.chmod(0o755)
        if WINDOWS:
            self.git_paths = [str(GIT_ROOT / "usr/bin"), str(GIT_ROOT / "mingw64/bin")]
        else:
            self.git_paths = ["/usr/bin", "/bin"]
        self.env = self.make_env()

    # --- helpers -----------------------------------------------------------
    def make_env(self, **extra):
        env = {k: v for k, v in os.environ.items()
               if k.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "COMSPEC"}}
        env.update(HOME=posix(self.home), USERPROFILE=str(self.home),
                   PATH=os.pathsep.join([str(self.shims)] + self.git_paths),
                   GSTACK_HOME=posix(self.base / "analytics"),
                   GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                   GIT_TERMINAL_PROMPT="0", BASH_ENV="", ENV="")
        env.update(extra)
        return env

    def startup(self, name, body):
        path = self.base / name
        path.write_text(body, encoding="utf-8", newline="\n")
        return self.make_env(BASH_ENV=posix(path))

    def bash(self, command, *, cwd=None, env=None, stdin=b""):
        return subprocess.run([str(BASH), "--noprofile", "--norc", "-c", command],
                              input=stdin, capture_output=True, cwd=str(cwd or self.work),
                              env=env or self.env, timeout=60)

    def script(self, name, body, *, env=None):
        path = self.base / name
        path.write_text(body, encoding="utf-8", newline="\n")
        return subprocess.run([str(BASH), "--noprofile", "--norc", posix(path)],
                              capture_output=True, text=True, cwd=str(self.work),
                              env=env or self.env, timeout=60)

    def decide(self, payload, *, command=FREEZE_HOOK, cwd=None, env=None):
        data = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        p = self.bash(command, cwd=cwd, env=env, stdin=data.encode("utf-8"))
        self.assertEqual(p.returncode, 0, p.stderr.decode("utf-8", "replace"))
        result = json.loads(p.stdout.decode("utf-8"))  # exactly one JSON object
        if not result:
            return "allow", ""
        self.assertEqual(set(result), {"hookSpecificOutput"})
        spec = result["hookSpecificOutput"]
        self.assertEqual(spec["hookEventName"], "PreToolUse")
        self.assertIn(spec["permissionDecision"], {"ask", "deny"})
        self.assertTrue(spec["permissionDecisionReason"])
        return spec["permissionDecision"], spec["permissionDecisionReason"]

    def edit(self, file_path, **kw):
        return self.decide({"tool_name": "Write", "tool_input": {"file_path": file_path}}, **kw)

    def forms(self, path):
        """The path as Claude Code (C:\\), mixed (C:/) and MSYS (/c/) strings."""
        if WINDOWS:
            return [str(path), Path(path).as_posix(), posix(path)]
        return [str(path)]

    def set_boundary(self, raw, *, env=None):
        body = bash_block("freeze", 'freeze-state.sh" set').replace("<user-provided-path>", raw)
        return self.script("set-boundary.sh", body, env=env)

    def freeze(self, raw=None):
        p = self.set_boundary(raw if raw is not None else str(self.inside))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertRegex(p.stdout, r"(?m)^FREEZE_OWNER=[0-9a-f]{32}$")
        self.assertRegex(p.stdout, r"(?m)^FREEZE_DIR=/")
        return p

    def state_lines(self):
        return (self.state / "freeze-dir.txt").read_text(encoding="utf-8").splitlines()

    def assert_deny(self, outcome, *needles):
        decision, reason = outcome
        self.assertEqual(decision, "deny", reason)
        self.assertTrue(reason.startswith("[freeze]"), reason)
        for needle in needles:
            self.assertIn(needle, reason)

    # --- wiring, provenance and setup ownership ---------------------------
    def test_frontmatter_hooks_are_home_anchored_and_banner_free(self):
        self.assertEqual(hooks_of("freeze"), [("Edit", FREEZE_HOOK), ("Write", FREEZE_HOOK)])
        self.assertEqual(hooks_of("guard"), [("Bash", CAREFUL_HOOK), ("Edit", FREEZE_HOOK),
                                             ("Write", FREEZE_HOOK)])
        self.assertEqual(hooks_of("unfreeze"), [])
        for skill in ("freeze", "unfreeze", "guard"):
            with self.subTest(skill=skill):
                self.assertRegex(front(skill), r"(?m)^version: %s$" % re.escape(SKILL_VERSIONS[skill]))
                self.assertNotIn("CLAUDE_SKILL_DIR", front(skill))
                self.assertNotIn("/gstack/", front(skill))
                head = (SKILLS_SRC / skill / "SKILL.md").read_bytes()[:8192].decode("utf-8", "ignore")
                self.assertFalse(BANNER_A in head and BANNER_B in head,
                                 "gstack banner would make setup treat this folder as gstack-owned")
                self.assertFalse((SKILLS_SRC / skill / ".gstack-owned").exists())

    def test_deny_reasons_name_no_install_path(self):
        # The plugin runtime ships these same leaves, so a flat ~/.claude/skills
        # path in a deny reason would send plugin users to a folder they lack.
        for script in (FREEZE / "bin" / "check-freeze.sh",
                       SKILLS_SRC / "careful" / "bin" / "hook-extract.sh"):
            with self.subTest(script=script.name):
                reasons = re.findall(r'permissionDecisionReason":"([^"]*)"',
                                     script.read_text(encoding="utf-8"))
                if script.name == "check-freeze.sh":
                    self.assertTrue(reasons)
                for reason in reasons:
                    self.assertNotIn(".claude/skills", reason)

    def test_investigate_warning_is_the_first_setup_line(self):
        for skill in ("freeze", "guard"):
            with self.subTest(skill=skill):
                text = (SKILLS_SRC / skill / "SKILL.md").read_text(encoding="utf-8")
                setup = text.split("\n## Setup\n", 1)[1]
                first = next(line for line in setup.splitlines() if line.strip())
                self.assertEqual(first, INVESTIGATE_WARNING)

    def test_vendored_state_writer_is_upstream_plus_attribution(self):
        lines = (FREEZE / "bin/freeze-state.sh").read_bytes().split(b"\n")
        self.assertEqual(lines[0], b"#!/usr/bin/env bash")
        i = 1
        while lines[i].startswith(b"#"):
            i += 1
        self.assertGreater(i, 2, "attribution block missing")
        self.assertIn(b"garrytan/gstack", b"\n".join(lines[1:i]))
        upstream = b"\n".join([lines[0]] + lines[i:])
        self.assertEqual(hashlib.sha256(upstream).hexdigest(), STATE_WRITER_UPSTREAM_SHA256)
        for name in ("check-freeze.sh", "freeze-state.sh"):
            self.assertNotIn(b"\r", (FREEZE / "bin" / name).read_bytes(), name)

    def test_setup_preflight_reports_missing_hook_scripts(self):
        preflight = bash_block("freeze", "FREEZE_MISSING")
        self.assertEqual(preflight, bash_block("guard", "FREEZE_MISSING"))
        self.assertEqual(self.script("pre.sh", preflight).stdout, "")
        (self.skills / "careful/bin/hook-extract.sh").unlink()
        out = self.script("pre.sh", preflight).stdout
        self.assertIn("FREEZE_MISSING: ~/.claude/skills/careful/bin/hook-extract.sh", out)

    # --- no boundary ------------------------------------------------------
    def test_no_state_allows_everything(self):
        self.assertFalse(self.state.exists())
        self.assertEqual(self.edit(str(self.outside / "x.txt"))[0], "allow")
        self.assertEqual(self.edit("relative.txt")[0], "allow")
        self.assertEqual(self.decide('{"tool_input":')[0], "allow")

    # --- inside / outside in every path form -------------------------------
    def test_inside_outside_and_prefix_collision_for_all_path_forms(self):
        self.freeze()
        for path, expected in ((self.inside / "new.txt", "allow"),
                               (self.inside / "existing.txt", "allow"),
                               (self.inside, "allow"),
                               (self.outside / "new.txt", "deny"),
                               (self.work / "src-other" / "new.txt", "deny"),
                               (self.work / "top.txt", "deny")):
            for form in self.forms(path):
                with self.subTest(path=form):
                    self.assertEqual(self.edit(form)[0], expected)

    def test_boundary_written_in_any_form_gives_same_decisions(self):
        for raw in self.forms(self.inside):
            with self.subTest(boundary=raw):
                self.freeze(raw)
                for form in self.forms(self.inside / "new.txt"):
                    self.assertEqual(self.edit(form)[0], "allow")
                for form in self.forms(self.outside / "new.txt"):
                    self.assertEqual(self.edit(form)[0], "deny")

    @unittest.skipUnless(WINDOWS, "drive letters and case-insensitive paths are Windows-only")
    def test_case_differences_are_ignored_on_windows(self):
        self.freeze(str(self.inside).lower())
        inside = str(self.inside / "New.TXT")
        for form in (inside.upper(), inside.lower(), inside[0].lower() + inside[1:],
                     Path(inside.upper()).as_posix()):
            with self.subTest(path=form):
                self.assertEqual(self.edit(form)[0], "allow")
        other = str(self.work / "SRC-OTHER" / "x.txt")
        self.assertEqual(self.edit(other.upper())[0], "deny")
        self.assertEqual(self.edit(str(self.outside / "x.txt").upper())[0], "deny")

    def test_cwd_inside_but_path_outside_denies(self):
        # The gstack 1.91.9 bug: a C:\ path was joined to the cwd and allowed.
        self.freeze()
        for form in self.forms(self.outside / "escape.txt"):
            with self.subTest(path=form):
                self.assert_deny(self.edit(form, cwd=self.inside), "outside the freeze boundary")

    def test_relative_and_ambiguous_paths_deny_without_cwd_fallback(self):
        self.freeze()
        cases = ["new.txt", "src/new.txt", "./new.txt", "~/new.txt"]
        if WINDOWS:
            cases += ["src\\new.txt", ".\\new.txt", "C:new.txt", "\\Users\\x.txt"]
        for path in cases:
            with self.subTest(path=path):
                decision, reason = self.edit(path, cwd=self.inside)
                self.assertEqual(decision, "deny", reason)
                self.assertRegex(reason, r"relative path")

    def test_new_file_judged_by_existing_parent(self):
        self.freeze()
        new = self.inside / "brand-new.txt"
        self.assertFalse(new.exists())
        for form in self.forms(new):
            self.assertEqual(self.edit(form)[0], "allow")
        for form in self.forms(self.inside / "missing" / "deep" / "new.txt"):
            self.assert_deny(self.edit(form), "parent directory does not exist")
        self.assertFalse(new.exists(), "the hook must never create the file")

    def test_dotdot_unc_and_device_paths_deny(self):
        self.freeze()
        cases = [posix(self.inside) + "/../src-other/x.txt", posix(self.inside) + "/sub/../x.txt"]
        if WINDOWS:
            cases += [str(self.inside) + "\\..\\..\\outside dir\\x.txt",
                      "\\\\server\\share\\x.txt", "//server/share/x.txt",
                      "\\\\?\\" + str(self.inside / "x.txt"), "\\\\.\\C:\\x.txt"]
        for path in cases:
            with self.subTest(path=path):
                self.assertEqual(self.edit(path)[0], "deny")

    @unittest.skipUnless(WINDOWS, "cygpath is Git for Windows")
    def test_cygpath_conversion_failure_denies(self):
        self.freeze()
        env = self.startup("broken cygpath.sh", "cygpath() { return 1; }\n")
        for form in self.forms(self.inside / "new.txt"):
            with self.subTest(path=form):
                self.assert_deny(self.edit(form, env=env), "cygpath")

    @unittest.skipUnless(WINDOWS, "cygpath is Git for Windows")
    def test_pure_bash_fallback_without_cygpath(self):
        env = self.startup("no cygpath.sh", HIDE_CYGPATH)
        self.freeze(posix(self.inside))  # /c/ form: physical path, no mount alias
        for form in self.forms(self.inside / "new.txt") + [str(self.inside / "n.txt").upper()]:
            with self.subTest(path=form):
                self.assertEqual(self.edit(form, env=env)[0], "allow")
        for form in self.forms(self.outside / "new.txt"):
            self.assertEqual(self.edit(form, env=env)[0], "deny")
        alias = subprocess.run([str(GIT_ROOT / "usr/bin/cygpath.exe"), "-u", str(self.inside)],
                               capture_output=True, text=True).stdout.strip()
        if alias != posix(self.inside):
            # The state names a mount alias (/tmp/...) that cannot be folded without
            # cygpath: the mismatch must fail closed, never allow.
            (self.state / "freeze-dir.txt").write_text(alias + "\n", encoding="utf-8")
            self.assertEqual(self.edit(str(self.inside / "new.txt"), env=env)[0], "deny")

    # --- state writer: busy lock, concurrency, unfreeze ------------------------
    def test_busy_lock_changes_nothing(self):
        self.freeze()
        before = self.state_lines()
        lock = self.state / ".freeze-mutation.lock"
        lock.mkdir()
        p = self.set_boundary(str(self.outside))
        self.assertEqual(p.returncode, 1)
        self.assertIn("FREEZE_BUSY", p.stderr)
        self.assertNotIn("FREEZE_DIR=", p.stdout)
        clear = self.script("clear.sh", bash_block("unfreeze", 'freeze-state.sh" clear'))
        self.assertEqual(clear.returncode, 1)
        self.assertIn("FREEZE_BUSY", clear.stderr)
        self.assertEqual(self.state_lines(), before)
        self.assertTrue(lock.is_dir(), "a busy writer must not remove someone else's lock")
        self.assertEqual(self.edit(str(self.outside / "x.txt"))[0], "deny")
        lock.rmdir()
        self.freeze(str(self.outside))  # retry after the holder finished
        self.assertEqual(self.edit(str(self.outside / "x.txt"))[0], "allow")

    def test_concurrent_writers_leave_one_consistent_state(self):
        dirs = [self.inside, self.outside]
        writer = posix(self.skills / "freeze/bin/freeze-state.sh")
        procs = []
        for n in range(8):
            target = posix(dirs[n % 2])
            cmd = "for i in 1 2 3; do bash %s set %s; echo rc=$?; done" % (shlex.quote(writer),
                                                                         shlex.quote(target))
            procs.append(subprocess.Popen([str(BASH), "--noprofile", "--norc", "-c", cmd],
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                          cwd=str(self.work), env=self.env))
        owners, busy = {}, 0
        for proc in procs:
            out, err = proc.communicate(timeout=120)
            out, err = out.decode("utf-8"), err.decode("utf-8")
            codes = re.findall(r"rc=(\d+)", out)
            self.assertEqual(len(codes), 3, out + err)
            self.assertTrue(set(codes) <= {"0", "1"}, out + err)
            busy += codes.count("1")
            self.assertEqual(err.count("FREEZE_BUSY"), codes.count("1"), err)
            for owner, boundary in re.findall(r"FREEZE_OWNER=([0-9a-f]{32})\nFREEZE_DIR=(.*)\n", out):
                owners[owner] = boundary
        self.assertTrue(owners, "at least one writer must succeed")
        lines = self.state_lines()
        self.assertEqual(len(lines), 2)
        owner = lines[1].removeprefix("gstack-freeze-v1:")
        self.assertIn(owner, owners)
        self.assertEqual(lines[0], owners[owner])
        leftovers = [p.name for p in self.state.iterdir() if p.name != "freeze-dir.txt"]
        self.assertEqual(leftovers, [], "lock dir or temp files left behind")
        expected = "allow" if lines[0].endswith("/src") else "deny"
        self.assertEqual(self.edit(str(self.inside / "x.txt"))[0], expected)
        print("concurrent writers: %d busy of 24 runs" % busy, file=sys.stderr)

    def test_unfreeze_clears_state(self):
        self.freeze()
        self.assertEqual(self.edit(str(self.outside / "x.txt"))[0], "deny")
        clear = bash_block("unfreeze", 'freeze-state.sh" clear')
        p = self.script("clear.sh", clear)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("FREEZE_CLEARED", p.stdout)
        self.assertFalse((self.state / "freeze-dir.txt").exists())
        self.assertEqual(self.edit(str(self.outside / "x.txt"))[0], "allow")
        self.assertIn("FREEZE_CLEARED", self.script("clear.sh", clear).stdout)  # idempotent

    def test_unfreeze_preserves_unexpected_state_type(self):
        self.state.mkdir(parents=True)
        (self.state / "freeze-dir.txt").mkdir()
        p = self.script("clear.sh", bash_block("unfreeze", 'freeze-state.sh" clear'))
        self.assertEqual(p.returncode, 1)
        self.assertIn("FREEZE_PRESERVED", p.stderr)
        self.assertTrue((self.state / "freeze-dir.txt").is_dir())
        self.assertEqual(self.edit(str(self.inside / "x.txt"))[0], "deny")

    def test_setup_block_keeps_special_characters_literal(self):
        odd = self.base / "it's $HOME `x` dir"
        odd.mkdir()
        raw = str(odd) + ("\\" if WINDOWS else "/")
        p = self.freeze(raw)
        self.assertTrue(p.stdout.rstrip().endswith("it's $HOME `x` dir"), p.stdout)
        self.assertEqual(self.edit(str(odd / "a.txt"))[0], "allow")
        self.assertEqual(self.edit(str(self.inside / "a.txt"))[0], "deny")

    # --- invalid state, payload and installation --------------------------
    def test_invalid_state_denies(self):
        self.state.mkdir(parents=True)
        target = self.state / "freeze-dir.txt"
        for content in ("", "   \n", "relative/dir\n", "C:relative\n", posix(self.base / "gone") + "\n",
                        posix(self.inside) + "/../src\n", posix(self.inside) + "\x01\n",
                        "\n" + "gstack-freeze-v1:" + "0" * 32 + "\n"):
            with self.subTest(content=content):
                target.write_text(content, encoding="utf-8", newline="")
                self.assertEqual(self.edit(str(self.inside / "x.txt"))[0], "deny")
        target.unlink()
        target.mkdir()
        self.assertEqual(self.edit(str(self.inside / "x.txt"))[0], "deny")

    def test_legacy_one_line_state_still_works(self):
        self.state.mkdir(parents=True)
        for line in (posix(self.inside) + "/", "  " + posix(self.inside) + "  "):
            with self.subTest(state=line):
                (self.state / "freeze-dir.txt").write_text(line + "\n", encoding="utf-8")
                self.assertEqual(self.edit(str(self.inside / "x.txt"))[0], "allow")
                self.assertEqual(self.edit(str(self.outside / "x.txt"))[0], "deny")

    def test_invalid_payload_denies(self):
        self.freeze()
        for payload in ("", "{}", '{"tool_input":', '{"tool_input":{}}', '{"tool_input":null}',
                        '{"tool_input":{"file_path":7}}', '{"tool_input":{"file_path":""}}',
                        json.dumps({"tool_input": {"file_path": str(self.inside / "x.txt") + "\n"}})):
            with self.subTest(payload=payload):
                self.assertEqual(self.decide(payload)[0], "deny")

    def test_missing_broken_or_outdated_helper_denies(self):
        self.freeze()
        helper = self.skills / "careful/bin/hook-extract.sh"
        original = helper.read_text(encoding="utf-8")
        helper.write_text(original.replace("gstack_hook_state_root()", "renamed_state_root()"),
                          encoding="utf-8", newline="\n")
        self.assert_deny(self.edit(str(self.inside / "x.txt")), "out of date")
        helper.write_text("this is not bash (\n", encoding="utf-8", newline="\n")
        self.assert_deny(self.edit(str(self.inside / "x.txt")), "unavailable")
        helper.unlink()
        self.assert_deny(self.edit(str(self.inside / "x.txt")), "unavailable")

    def test_unexpected_failure_hits_backstop(self):
        self.freeze()
        env = self.startup("stdin failure.sh", "cat() { return 13; }\n")
        self.assert_deny(self.edit(str(self.inside / "x.txt"), env=env), "failed unexpectedly")

    def test_final_symlink_to_outside_is_denied(self):
        self.freeze()
        target = self.outside / "real.txt"
        target.write_text("fixture", encoding="utf-8")
        link = self.inside / "link.txt"
        try:
            link.symlink_to(target)
        except OSError as exc:
            self.skipTest("cannot create a symlink fixture here: " + type(exc).__name__)
        self.assertEqual(self.edit(str(link))[0], "deny")

    def test_deny_reason_names_path_and_native_boundary(self):
        self.freeze()
        outside = str(self.outside / 'q"uote.txt')
        decision, reason = self.edit(outside)
        self.assertEqual(decision, "deny")
        self.assertIn(outside, reason)
        self.assertIn(str(self.inside), reason)

    # --- guard wiring --------------------------------------------------------
    def test_guard_runs_careful_and_freeze_from_home(self):
        self.freeze()
        bash_payload = lambda c: {"tool_name": "Bash", "tool_input": {"command": c}}
        self.assertEqual(self.decide(bash_payload("git status"), command=CAREFUL_HOOK)[0], "allow")
        self.assertEqual(self.decide(bash_payload("git reset --hard"), command=CAREFUL_HOOK)[0], "ask")
        self.assertEqual(self.decide(bash_payload("rm -rf /"), command=CAREFUL_HOOK)[0], "deny")
        self.assertEqual(self.edit(str(self.inside / "x.txt"))[0], "allow")
        self.assertEqual(self.edit(str(self.outside / "x.txt"), cwd=self.inside)[0], "deny")
        shutil.rmtree(self.skills / "freeze")
        p = self.bash(FREEZE_HOOK, stdin=b"{}")
        self.assertNotEqual(p.returncode, 0, "a missing hook script cannot start (fail-open)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
