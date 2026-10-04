"""Offline tests for the SimonK careful hook (hub decision D-56, step 1).

Each test installs a copy of this skill under a temporary HOME
(HOME/.claude/skills/careful) and runs the exact frontmatter hook command
through Git Bash, feeding a PreToolUse JSON payload on stdin. Commands are only
DATA: the hook inspects them and never executes them. No network, no model
calls, no writes outside the temporary directory.

Run:  python -B <skill-dir>/bin/test_check_careful.py  (skills-src/careful in a checkout)
Windows needs Git for Windows at C:/Program Files/Git (the `bash` that
PowerShell finds first is usually WSL, which breaks Windows paths).
"""
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

SKILL = Path(__file__).resolve().parents[1]
if os.name == "nt":
    BASH = Path("C:/Program Files/Git/bin/bash.exe")
else:
    BASH = Path(shutil.which("bash") or "/missing/bash")
GIT_ROOT = BASH.parent.parent
EXPECTED_HOOK = 'bash "$HOME/.claude/skills/careful/bin/check-careful.sh"'
EXPECTED_PS_HOOK = 'bash "$HOME/.claude/skills/careful/bin/check-careful.sh" powershell'
BANNER_A = "<!-- AUTO-GENERATED from "
BANNER_B = "<!-- Regenerate: bun run gen:skill-docs -->"

# Hub decision D-62 A1: Windows/MSYS-shaped catastrophic deletes in a SIMPLE
# command are HIGH (deny). Before 0.2.1 the rm forms were MEDIUM ask and the
# cmd.exe/PowerShell forms were allowed with no warning at all.
WINDOWS_HIGH_DENY = (
    # MSYS / WSL / Cygwin drive roots and one-level globs
    "rm -rf /c", "rm -rf /c/", "rm -rf /c/*", "rm -rf /e/", "rm -rf /C/",
    "rm -rf /mnt/c", "rm -rf /mnt/c/", "rm -rf /mnt/c/*", "rm -rf /cygdrive/d",
    # Windows drive spellings (quoted or not)
    "rm -rf C:", "rm -rf C:/", "rm -rf C:\\", "rm -rf C:\\*", "rm -rf C:/*",
    "rm -rf 'C:\\'", 'rm -rf "C:/"', "rm -rf c:\\\\",
    # home and its direct contents
    "rm -rf ~/*", "rm -rf ~/.*", 'rm -rf "$HOME"/*', "rm -rf $HOME/*",
    "rm -rf ${HOME}", "rm -rf ${HOME}/*", 'rm -rf "${HOME}"',
    # root variants and flag spellings
    "rm -rf /.*", "rm -rf //", "rm -rf -- /", "rm -rf -- /c/", "rm -fr /c/",
    "rm -r -f C:/", "rm -Rf /mnt/d", "rm --recursive --force ~/*",
    "sudo rm -rf /c/", "sudo rm -rf --no-preserve-root /", "rm -rf /c/ /d/",
    "rm -rf /c/ 2>/dev/null",
    # cmd.exe launched from the Bash tool
    "cmd /c rd /s /q C:\\", "cmd //c rd /s /q C:\\", "cmd.exe /c rmdir /s /q C:\\",
    'cmd.exe /c "rmdir /s /q C:\\"', "cmd /C RD /S /Q D:\\", "cmd //c rd //s //q C:/",
    "cmd /c rd /s /q C:", "cmd /c del /s /q C:\\*", "cmd /c del /f /s /q C:\\*.*",
    "cmd /c rd /s /q ~", "C:/Windows/System32/cmd.exe /c rd /s /q C:\\",
    # PowerShell launched from the Bash tool
    'powershell -c "Remove-Item -Recurse -Force C:\\"',
    'powershell -Command "Remove-Item -Recurse -Force C:\\"',
    'powershell.exe -NoProfile -Command "Remove-Item -Path C:\\* -Recurse -Force"',
    "pwsh -c 'Remove-Item -Recurse -Force ~'", 'pwsh -Command "rm -r -fo C:/"',
    "pwsh -NoProfile -ExecutionPolicy Bypass -Command \"Remove-Item -LiteralPath 'C:\\' -Recurse -Force\"",
    'powershell -c "ri -rec -force $HOME"', "pwsh -c 'Remove-Item -Recurse -Force $HOME\\*'",
    "powershell -c 'Remove-Item -Recurse -Force \\'",
    'powershell -c "Remove-Item -Recurse -Force C:\\ -ErrorAction SilentlyContinue"',
    # 0.2.2: cmd/PowerShell spell home as %USERPROFILE% / $env:USERPROFILE too
    "cmd /c rd /s /q %USERPROFILE%", "powershell -c 'Remove-Item -Recurse $env:USERPROFILE'",
)

# Near misses keep exactly the tier they had on 0.2.0 (measured 2026-10-03):
# project subfolders, the build-artifact allowlist, ambiguous variables (any
# but HOME), literal profile paths, globs deeper than one level, relative
# targets, compound commands and deleters outside rm/rd/del/Remove-Item.
NEAR_MISS = (
    ("rm -rf /c/Users/me/project/build", "allow"),  # build-artifact allowlist
    ("rm -rf C:/project/dist", "allow"), ("rm -rf ~/*/build", "allow"),
    ("rm -rf node_modules", "allow"), ("rm -rf build dist", "allow"),
    ("rm -rf ./C", "ask"), ('rm -rf "$HOME/project/tmp"', "ask"),
    ('rm -rf "$HOME"/project', "ask"), ("rm -rf /c/Users/someone", "ask"),
    ("rm -rf /c/Windows", "ask"), ('rm -rf "E:/Work Space"', "ask"),
    ("rm -rf ~/.claude", "ask"), ("rm -rf $USERPROFILE", "ask"),
    ("rm -rf ${USERPROFILE}", "ask"), ("rm -rf $TMPDIR", "ask"),
    ("rm -rf .", "ask"), ("rm -rf ..", "ask"), ("rm -rf *", "ask"),
    ("rm -rf \\*", "ask"), ("rm -rf /c/*/*", "ask"), ("rm -rf ~/*/", "ask"),
    ("rm -rf $HOME/*.log", "ask"), ("rm -rf /mnt", "ask"), ("rm -rf /mnt/*", "ask"),
    ("rm -rf /mnt/c/Users/me/proj", "ask"), ("rm -rf /cache", "ask"),
    ("rm -rf C:*", "ask"), ("rm -rf /c/ ./build", "ask"),
    ("rm -rf /c/ && echo done", "ask"), ("rm -f /c", "allow"),
    ("cmd /c rd /s /q C:\\Users\\me\\project\\build", "allow"),
    ('cmd.exe /c "rmdir /s /q C:\\Users"', "allow"), ("cmd /c rd /q C:\\", "allow"),
    ("cmd /c del /q C:\\*", "allow"), ("cmd /c dir C:\\", "allow"),
    ('cmd /c "rd /s /q C:\\ & echo done"', "allow"),
    ('powershell -c "Remove-Item -Recurse -Force .\\build"', "allow"),
    ('powershell -c "Remove-Item -Force C:\\"', "allow"),
    ('powershell -c "Get-ChildItem C:\\"', "allow"),
    ('powershell -c "Remove-Item -Recurse -Force C:\\; echo"', "allow"),
    ('powershell -c "Remove-Item -Recurse $env:SystemDrive\\"', "allow"),
    ("powershell -File wipe.ps1 C:\\", "allow"),
    ("powershell -EncodedCommand UgBlAG0A", "allow"),
    ('pwsh -c "Get-ChildItem C:\\ | Remove-Item -Recurse"', "allow"),
    ('pwsh -c "Remove-Item -Recurse -Force C:\\ -WhatIf"', "allow"),
    ("find / -delete", "allow"), ("git clean -fdx", "allow"),
    ("chmod -R 000 ~", "allow"), ("mv ~ /tmp/x", "allow"),
)

# Hub decision D-62 minimal B: the PowerShell tool is checked DENY-ONLY.
# Literal catastrophic shapes in any simple command (; | && { } ( ) split).
PS_HIGH_DENY = (
    "Remove-Item -Recurse -Force C:\\", "Remove-Item -Recurse -Force C:\\*",
    "Remove-Item C:/ -Recurse", "Remove-Item -Path C: -Recurse -Force",
    "ri -r -fo $HOME", "Remove-Item -Recurse -Force $HOME\\*", "Remove-Item -Recurse -Force ~",
    "rm -r -fo ~\\*", "Remove-Item -Recurse -Force $env:USERPROFILE",
    'Remove-Item -Recurse -Force "$env:USERPROFILE\\*"',
    "Remove-Item -Recurse -Force ${env:USERPROFILE}", "rmdir -Recurse D:\\",
    "del -Recurse -Force E:\\*", "erase -r C:\\", "rd /s /q C:\\", "rmdir /s C:\\",
    "Remove-Item -LiteralPath 'C:\\' -Recurse -Force -ErrorAction SilentlyContinue",
    "Remove-Item -Path:C:\\ -Recurse", "Remove-Item -Recurse -Force C:\\,D:\\",
    "Microsoft.PowerShell.Management\\Remove-Item -Recurse C:\\",
    "& Remove-Item -Recurse C:\\", "cd E:\\x; Remove-Item -Recurse -Force C:\\",
    "Get-Date\nRemove-Item -Recurse -Force C:\\",
    "Get-ChildItem x | ForEach-Object { Remove-Item -Recurse -Force $HOME }",
    "cmd /c rd /s /q C:\\", 'cmd /c "rmdir /s /q C:\\"', "cmd.exe /c rd /s /q %USERPROFILE%",
    "cmd /c del /s /q C:\\*", 'pwsh -c "Remove-Item -Recurse -Force C:\\"',
    'powershell -NoProfile -Command "Remove-Item -Recurse $HOME"',
    "Format-Volume -DriveLetter D", "Clear-Disk -Number 1 -RemoveData -Confirm:$false",
    "Initialize-Disk -Number 2", "Remove-Partition -DriveLetter E",
    "Storage\\Format-Volume -DriveLetter D",
)

# Everything else is ALLOWED on the PowerShell tool (never ask): ordinary
# deletes, dry runs, other destroyers and the documented string-matching gaps.
PS_ALLOW = (
    "Remove-Item -Recurse .\\build", "Remove-Item -Recurse -Force .\\build",
    "Remove-Item C:\\Users\\me\\project\\tmp -Recurse",
    'Remove-Item -Recurse -Force "E:\\Work Space\\x\\node_modules"',
    "Remove-Item C:\\", "Remove-Item -Force C:\\", "Remove-Item -Recurse -Force C:\\ -WhatIf",
    "Format-Volume -DriveLetter D -WhatIf", "Get-Help Format-Volume", "Get-ChildItem C:\\",
    "Remove-Item -Recurse /c", "Remove-Item -Recurse C:\\Users",
    "Remove-Item -Recurse -Include *.log C:\\", "cmd /c rd /q C:\\",
    "cmd /c rd /s /q C:\\Users\\me\\build", "rm -rf C:\\",
    'Write-Output "Remove-Item -Recurse -Force C:\\"', "# Remove-Item -Recurse -Force C:\\",
    "git reset --hard", "git status", "robocopy a b /MIR", 'Set-Content -Path x.txt -Value "a; b"',
    # gaps: other variables, splatting, pipeline input, encoded / indirect commands
    "Remove-Item -Recurse -Force $env:TEMP\\x", "Remove-Item -Recurse -Force $env:SystemDrive\\",
    "Remove-Item -Recurse -Force $sp", "Remove-Item @params",
    "Get-ChildItem C:\\ | Remove-Item -Recurse -Force", "powershell -EncodedCommand UgBlAG0A",
    'Invoke-Expression "Remove-Item -Recurse C:\\"',
)


def posix(path):
    path = Path(path).absolute()
    if os.name == "nt":
        return "/" + path.drive[0].lower() + path.as_posix()[2:]
    return str(path)


def frontmatter_hooks():
    """(matcher, command) pairs of the PreToolUse entries, in order."""
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    front = text.split("---", 2)[1]
    found = re.findall(r'^\s*- matcher:\s*"([^"]+)"\s*\n\s*hooks:\s*\n\s*- type: command\s*\n'
                       r"\s*command:\s*'([^']*)'\s*$", front, re.M)
    if len(found) != len(re.findall(r"^\s*command:", front, re.M)):
        raise AssertionError("unparsed hook command in frontmatter: %r" % found)
    return found


@unittest.skipUnless(BASH.is_file(), "Git Bash / POSIX bash is required")
class CarefulHookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="careful hook ")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.home = self.base / "home"
        self.install = self.home / ".claude/skills/careful"
        shutil.copytree(SKILL / "bin", self.install / "bin",
                        ignore=shutil.ignore_patterns("*.py", "__pycache__"))
        shutil.copyfile(SKILL / "SKILL.md", self.install / "SKILL.md")
        self.state = self.home / ".gstack"
        self.work = self.base / "work dir"
        self.work.mkdir()
        # python3 shim: a deterministic parser regardless of the host PATH.
        self.shims = self.base / "shims"
        self.shims.mkdir()
        shim = self.shims / "python3"
        shim.write_bytes(("#!/bin/sh\nexec " + shlex.quote(posix(sys.executable)) +
                          ' "$@"\n').encode("utf-8"))
        shim.chmod(0o755)
        if os.name == "nt":
            self.git_paths = [str(GIT_ROOT / "usr/bin"), str(GIT_ROOT / "mingw64/bin")]
        else:
            self.git_paths = ["/usr/bin", "/bin"]
        self.env = self.make_env([str(self.shims)] + self.git_paths)
        hooks = dict(frontmatter_hooks())
        self.hook_command, self.ps_hook_command = hooks.get("Bash"), hooks.get("PowerShell")

    def make_env(self, path_entries, **extra):
        env = {k: v for k, v in os.environ.items()
               if k.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "COMSPEC"}}
        env.update(HOME=posix(self.home), USERPROFILE=str(self.home),
                   PATH=os.pathsep.join(path_entries),
                   GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                   GIT_TERMINAL_PROMPT="0", BASH_ENV="", ENV="")
        env.update(extra)
        return env

    def startup(self, name, body):
        path = self.base / name
        path.write_text(body, encoding="utf-8", newline="\n")
        return posix(path)

    def run_hook(self, payload, *, env=None, cwd=None, hook=None):
        data = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        p = subprocess.run([str(BASH), "--noprofile", "--norc", "-c", hook or self.hook_command],
                           input=data.encode("utf-8"), capture_output=True,
                           cwd=str(cwd or self.work), env=env or self.env, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr.decode("utf-8", "replace"))
        out = p.stdout.decode("utf-8")
        result = json.loads(out)  # exactly one JSON object, nothing else
        if not result:
            return "allow", ""
        self.assertEqual(set(result), {"hookSpecificOutput"})
        spec = result["hookSpecificOutput"]
        self.assertEqual(spec["hookEventName"], "PreToolUse")
        self.assertIn(spec["permissionDecision"], {"ask", "deny"})
        self.assertTrue(spec["permissionDecisionReason"])
        return spec["permissionDecision"], spec["permissionDecisionReason"]

    def bash_cmd(self, command, **kw):
        return self.run_hook({"tool_name": "Bash", "tool_input": {"command": command}}, **kw)

    def ps_cmd(self, command, **kw):
        # Payload shape measured live 2026-10-03: tool_input {command, description}.
        return self.run_hook({"tool_name": "PowerShell",
                              "tool_input": {"command": command, "description": "d"}},
                             hook=self.ps_hook_command, **kw)

    def assert_failure_deny(self, outcome, detail=None):
        decision, reason = outcome
        self.assertEqual(decision, "deny", reason)
        self.assertIn("[careful][HOOK FAILURE]", reason)
        self.assertIn("careful hook itself failed", reason)
        self.assertIn("NOT safety-checked", reason)
        self.assertIn("fix the hook", reason)
        self.assertIn("without /careful", reason)
        if detail:
            self.assertIn(detail, reason)

    def git(self, repo, *args):
        exe = GIT_ROOT / "mingw64/bin/git.exe" if os.name == "nt" else Path(shutil.which("git"))
        subprocess.run([str(exe), "-C", str(repo), "-c", "user.name=t",
                        "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false",
                        *args], check=True, capture_output=True, env=self.env, timeout=30)

    def make_repo(self, name, default="main", symbolic=True):
        repo = self.base / name
        repo.mkdir()
        self.git(repo, "init", "-q", "-b", default)
        self.git(repo, "commit", "-q", "--allow-empty", "-m", "init")
        self.git(repo, "update-ref", "refs/remotes/origin/" + default, "HEAD")
        if symbolic:
            self.git(repo, "symbolic-ref", "refs/remotes/origin/HEAD",
                     "refs/remotes/origin/" + default)
        return repo

    # --- hook wiring -----------------------------------------------------
    def test_frontmatter_hook_is_home_anchored_and_banner_free(self):
        self.assertEqual(frontmatter_hooks(), [("Bash", EXPECTED_HOOK),
                                               ("PowerShell", EXPECTED_PS_HOOK)])
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("CLAUDE_SKILL_DIR}/bin", text.split("---", 2)[1])
        self.assertNotIn("/gstack/careful", self.hook_command)
        self.assertRegex(text.split("---", 2)[1], r"(?m)^version: 0\.2\.5$")
        head = text.encode("utf-8")[:8192].decode("utf-8", "ignore")
        self.assertFalse(BANNER_A in head and BANNER_B in head,
                         "gstack banner would make setup treat this folder as gstack-owned")

    # --- allow -----------------------------------------------------------
    def test_safe_commands_allow(self):
        for command in ("git status --short", "ls -la", "rm -rf node_modules",
                        "rm -rf build", "rm -Rf web/dist", "git push origin topic",
                        "git commit -m '한글 커밋 메시지 ✓'"):
            with self.subTest(command=command):
                self.assertEqual(self.bash_cmd(command)[0], "allow")

    def test_non_bash_payload_is_allowed(self):
        for payload in ({"tool_name": "Edit", "tool_input": {"file_path": "a.py"}},
                        {"tool_name": "Read", "tool_input": {"file_path": "a.py"}},
                        {"tool_name": "Write", "tool_input": {"file_path": "x", "content": "rm -rf /"}}):
            with self.subTest(tool=payload["tool_name"]):
                self.assertEqual(self.run_hook(payload)[0], "allow")

    # --- HIGH = deny -----------------------------------------------------
    def test_high_rm_root_or_home_denies(self):
        for command in ("rm -rf /", "rm -rf ~", "rm -rf $HOME", 'rm -rf "/"',
                        "sudo rm -rf --no-preserve-root /", "rm -r /*"):
            with self.subTest(command=command):
                decision, reason = self.bash_cmd(command)
                self.assertEqual(decision, "deny", reason)
                self.assertIn("[careful][HIGH]", reason)

    def test_windows_shaped_high_denies(self):
        for command in WINDOWS_HIGH_DENY:
            with self.subTest(command=command):
                decision, reason = self.bash_cmd(command)
                self.assertEqual(decision, "deny", reason)
                self.assertIn("[careful][HIGH]", reason)
                if re.match(r"(?i)^(\S*[/\\])?(cmd|powershell|pwsh)", command):
                    self.assertIn("cmd.exe/PowerShell", reason)
                else:
                    self.assertIn("drive root", reason)

    def test_windows_shaped_near_misses_keep_previous_tier(self):
        for command, expected in NEAR_MISS:
            with self.subTest(command=command):
                decision, reason = self.bash_cmd(command)
                self.assertEqual(decision, expected, reason)
                self.assertNotIn("[HIGH]", reason)

    # --- PowerShell tool: deny-only -------------------------------------------
    def test_powershell_high_denies(self):
        for command in PS_HIGH_DENY:
            with self.subTest(command=command):
                decision, reason = self.ps_cmd(command)
                self.assertEqual(decision, "deny", reason)
                self.assertIn("[careful][HIGH]", reason)

    def test_powershell_everything_else_allows_never_asks(self):
        for command in PS_ALLOW:
            with self.subTest(command=command):
                decision, reason = self.ps_cmd(command)
                self.assertEqual(decision, "allow", reason)

    def test_powershell_force_push_to_default_branch(self):
        repo = self.make_repo("ps repo main")
        for command in ("git push --force origin main", "git push -f origin HEAD:main",
                        "git push origin +main", "git push --force"):
            with self.subTest(command=command):
                decision, reason = self.ps_cmd(command, cwd=repo)
                self.assertEqual(decision, "deny", reason)
                self.assertIn("default branch (main)", reason)
        # --force-with-lease, feature branches and compound commands (a
        # Set-Location could change the repo) are allowed, not asked.
        for command in ("git push --force-with-lease origin main", "git push --force origin feature-x",
                        "git push -f origin topic", "cd ..\\other; git push -f origin main"):
            with self.subTest(command=command):
                self.assertEqual(self.ps_cmd(command, cwd=repo)[0], "allow")

    def test_powershell_internal_failure_denies(self):
        for tool_input in ({}, {"command": ""}, {"command": 7}, {"command": "ls\u0000x"},
                           {"description": "only"}):
            with self.subTest(tool_input=tool_input):
                outcome = self.run_hook({"tool_name": "PowerShell", "tool_input": tool_input},
                                        hook=self.ps_hook_command)
                self.assert_failure_deny(outcome, "PowerShell payload has no usable tool_input.command")
        for payload in ("", '{"tool_input":', "not json", "[]"):
            with self.subTest(payload=payload):
                self.assert_failure_deny(self.run_hook(payload, hook=self.ps_hook_command))
        for name, body in (("ps tr fails.sh", "tr() { return 3; }\n"),
                           ("ps sed fails.sh", "sed() { return 4; }\n")):
            with self.subTest(failure=name):
                env = self.make_env([str(self.shims)] + self.git_paths,
                                    BASH_ENV=self.startup(name, body))
                self.assert_failure_deny(self.ps_cmd("Get-Date", env=env), "unexpected script error")
        (self.install / "bin/hook-extract.sh").unlink()
        self.assert_failure_deny(self.ps_cmd("Get-Date"), "hook-extract.sh is missing or broken")

    def test_hook_mode_argument_and_absent_tool_name(self):
        # No tool_name: the entry that ran the script decides the tool.
        rd = {"tool_input": {"command": "Remove-Item -Recurse C:\\"}}
        reset = {"tool_input": {"command": "git reset --hard"}}
        self.assertEqual(self.run_hook(rd, hook=self.ps_hook_command)[0], "deny")
        self.assertEqual(self.run_hook(reset, hook=self.ps_hook_command)[0], "allow")
        self.assertEqual(self.run_hook(rd)[0], "allow")
        self.assertEqual(self.run_hook(reset)[0], "ask")
        # tool_name wins over the entry; an unknown mode argument fails closed.
        self.assertEqual(self.run_hook({"tool_name": "PowerShell", **rd})[0], "deny")
        self.assertEqual(self.run_hook({"tool_name": "Bash", **reset}, hook=self.ps_hook_command)[0], "ask")
        self.assert_failure_deny(self.run_hook({"tool_name": "Bash", **reset},
                                               hook=self.hook_command + " powrshell"),
                                 "unknown hook mode argument")

    def test_high_force_push_to_default_branch_denies(self):
        repo = self.make_repo("repo main")
        for command in ("git push --force origin main", "git push -f origin HEAD:main",
                        "git push origin +main", 'git push -f origin "main"', "git push --force"):
            with self.subTest(command=command):
                decision, reason = self.bash_cmd(command, cwd=repo)
                self.assertEqual(decision, "deny", reason)
                self.assertIn("default branch (main)", reason)

    def test_default_branch_fallback_and_custom_default(self):
        fallback = self.make_repo("no origin head", symbolic=False)
        self.assertEqual(self.bash_cmd("git push -f origin main", cwd=fallback)[0], "deny")
        trunk = self.make_repo("trunk repo", default="trunk")
        self.assertEqual(self.bash_cmd("git push -f origin trunk", cwd=trunk)[0], "deny")
        decision, reason = self.bash_cmd("git push -f origin main", cwd=trunk)
        self.assertEqual(decision, "ask")
        self.assertNotIn("[HIGH]", reason)

    def test_force_push_feature_branch_is_medium_ask(self):
        repo = self.make_repo("repo topic")
        decision, reason = self.bash_cmd("git push -f origin topic", cwd=repo)
        self.assertEqual(decision, "ask")
        self.assertNotIn("[HIGH]", reason)

    def test_force_with_lease_is_never_high(self):
        repo = self.make_repo("repo lease")
        for command in ("git push --force-with-lease origin main", "git push --force-with-lease",
                        "git push --force-with-lease=main:abc123 origin main"):
            with self.subTest(command=command):
                decision, reason = self.bash_cmd(command, cwd=repo)
                self.assertNotEqual(decision, "deny", reason)
                self.assertNotIn("[HIGH]", reason)
                self.assertEqual(decision, "ask")  # MEDIUM: --force substring

    # --- MEDIUM = ask ----------------------------------------------------
    def test_medium_families_ask(self):
        for command in ("rm -rf ./src", "rm -r /var/data", "rm -rf build/output",
                        "DROP TABLE users;", "truncate orders;", "git reset --hard",
                        "git reset --hard HEAD~3", "git checkout .", "git restore .",
                        "kubectl delete pod x", "docker rm -f x", "docker system prune -a",
                        "rm -rf / && echo done", "rm -rf ~; ls", "rm -rf /\nrm -rf node_modules"):
            with self.subTest(command=command):
                decision, reason = self.bash_cmd(command)
                self.assertEqual(decision, "ask", reason)
                self.assertNotIn("[HIGH]", reason)

    def test_obfuscation_asks(self):
        for command in ("rm${IFS}-rf${IFS}/", "echo cm0gLXJmIC8= | base64 -d | sh"):
            with self.subTest(command=command):
                decision, reason = self.bash_cmd(command)
                self.assertEqual(decision, "ask")
                self.assertIn("obfuscation", reason)

    def test_hook_never_executes_input_command(self):
        self.assertEqual(self.bash_cmd("touch must-not-exist; rm -rf /var/data")[0], "ask")
        self.assertFalse((self.work / "must-not-exist").exists())

    # --- internal failure = deny -----------------------------------------
    def test_invalid_or_empty_payload_denies(self):
        for payload in ("", "   ", '{"tool_input":', "not json", "[]", "null", '"Bash"',
                        '{"tool_name":7,"tool_input":{"command":"ls"}}'):
            with self.subTest(payload=payload):
                self.assert_failure_deny(self.run_hook(payload))

    def test_bash_payload_without_usable_command_denies(self):
        for payload in ({"tool_name": "Bash", "tool_input": {}},
                        {"tool_name": "Bash"},
                        {"tool_name": "Bash", "tool_input": None},
                        {"tool_name": "Bash", "tool_input": {"command": ""}},
                        {"tool_name": "Bash", "tool_input": {"command": 7}},
                        {"tool_name": "Bash", "tool_input": {"command": "ls\u0000rm -rf /"}},
                        {"tool_input": {}}, {}):
            with self.subTest(payload=payload):
                self.assert_failure_deny(self.run_hook(payload), "tool_input.command")

    def test_tool_name_match_is_case_insensitive(self):
        self.assertEqual(self.run_hook({"tool_name": "bash", "tool_input": {"command": "rm -rf /"}})[0], "deny")
        self.assertEqual(self.run_hook({"tool_input": {"command": "rm -rf /"}})[0], "deny")

    def test_missing_extractor_denies(self):
        (self.install / "bin/hook-extract.sh").unlink()
        self.assert_failure_deny(self.bash_cmd("git status"), "hook-extract.sh is missing or broken")

    def test_broken_extractor_denies(self):
        (self.install / "bin/hook-extract.sh").write_text("if then fi (\n", encoding="utf-8")
        self.assert_failure_deny(self.bash_cmd("git status"), "hook-extract.sh is missing or broken")

    def test_outdated_extractor_denies(self):
        # An older helper that sources fine but lacks the tool_name extractor.
        old = (self.install / "bin/hook-extract.sh").read_text(encoding="utf-8")
        old = old.replace("gstack_hook_extract_tool_name()", "_removed_tool_name()")
        (self.install / "bin/hook-extract.sh").write_text(old, encoding="utf-8", newline="\n")
        self.assert_failure_deny(self.bash_cmd("git status"), "out of date")

    def test_no_json_parser_denies(self):
        env = self.make_env(self.git_paths)  # no python3 shim, no node
        probe = subprocess.run([str(BASH), "--noprofile", "--norc", "-c",
                                "command -v python3 || command -v node || true"],
                               capture_output=True, text=True, env=env, timeout=30)
        if probe.stdout.strip():
            self.skipTest("a python3/node parser is reachable from the Git paths: " + probe.stdout.strip())
        self.assert_failure_deny(self.bash_cmd("git status", env=env), "could not parse")

    def test_failing_parser_denies(self):
        env = self.make_env([str(self.shims)] + self.git_paths,
                            BASH_ENV=self.startup("parser fails.sh", "python3() { return 1; }\nnode() { return 127; }\n"))
        self.assert_failure_deny(self.bash_cmd("git status", env=env), "could not parse")

    def test_matcher_error_denies_instead_of_non_match(self):
        # grep exits 2 only for the kubectl family: `git status` would be a
        # clean non-match there, so an allow here would mean rc 2 was swallowed.
        env = self.make_env([str(self.shims)] + self.git_paths, BASH_ENV=self.startup(
            "grep error.sh", 'grep() { case "$*" in *kubectl*) return 2 ;; esac; command grep "$@"; }\n'))
        self.assert_failure_deny(self.bash_cmd("git status", env=env), "pattern matcher (grep) errored with exit 2")
        always = self.make_env([str(self.shims)] + self.git_paths,
                               BASH_ENV=self.startup("grep always.sh", "grep() { return 2; }\n"))
        self.assert_failure_deny(self.bash_cmd("rm -rf /", env=always), "pattern matcher")

    def test_unexpected_failure_hits_exit_trap(self):
        for name, body, command in (("cat fails.sh", "cat() { return 13; }\n", "git status"),
                                    ("tr fails.sh", "tr() { return 3; }\n", "rm -rf /var/data")):
            with self.subTest(failure=name):
                env = self.make_env([str(self.shims)] + self.git_paths,
                                    BASH_ENV=self.startup(name, body))
                self.assert_failure_deny(self.bash_cmd(command, env=env), "unexpected script error")

    # --- project patterns (additive only) --------------------------------
    def write_patterns(self, relative, lines):
        path = self.state / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    def test_project_pattern_adds_warning(self):
        self.write_patterns("careful-patterns.txt",
                            ["# team rules", "", "(", r"^terraform[[:space:]]+destroy"])
        decision, reason = self.bash_cmd("terraform destroy -auto-approve")
        self.assertEqual(decision, "ask")
        self.assertIn("Project rule matched", reason)
        self.assertEqual(self.bash_cmd("git status")[0], "allow")  # invalid "(" skipped

    def test_project_pattern_cannot_suppress_baseline(self):
        self.write_patterns("careful-patterns.txt", [".*"])
        decision, reason = self.bash_cmd("rm -rf /var/data")
        self.assertEqual(decision, "ask")
        self.assertIn("recursive delete", reason)
        self.assertNotIn("Project rule", reason)
        decision, reason = self.bash_cmd("rm -rf /")
        self.assertEqual(decision, "deny")
        self.assertIn("[HIGH]", reason)
        self.assertEqual(self.bash_cmd("git status")[0], "ask")  # additive only

    def test_per_project_pattern_with_env_slug(self):
        self.write_patterns("projects/demo-proj/careful-patterns.txt", [r"^make[[:space:]]+deploy"])
        env = self.make_env([str(self.shims)] + self.git_paths, GSTACK_PROJECT_SLUG="demo-proj")
        self.assertEqual(self.bash_cmd("make deploy", env=env)[0], "ask")
        self.assertEqual(self.bash_cmd("make test", env=env)[0], "allow")

    def test_per_project_pattern_with_resolved_slug(self):
        repo = self.make_repo("slug repo")
        out = subprocess.run([str(BASH), "--noprofile", "--norc",
                              posix(self.install / "bin/gstack-slug.sh")],
                             capture_output=True, text=True, cwd=str(repo), env=self.env, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        slug = re.search(r"^SLUG=([A-Za-z0-9._-]+)$", out.stdout, re.M).group(1)
        self.write_patterns("projects/%s/careful-patterns.txt" % slug, [r"^make[[:space:]]+deploy"])
        decision, reason = self.bash_cmd("make deploy", cwd=repo)
        self.assertEqual(decision, "ask")
        self.assertIn("Project rule matched", reason)

    def test_missing_slug_helper_denies_only_when_project_patterns_exist(self):
        (self.install / "bin/gstack-slug.sh").unlink()
        self.assertEqual(self.bash_cmd("make test")[0], "allow")  # no per-project file: unused
        self.write_patterns("projects/other/careful-patterns.txt", ["^never"])
        self.assert_failure_deny(self.bash_cmd("make test"), "gstack-slug.sh is missing")

    # --- parser parity / shared-helper contract ---------------------------
    def test_node_only_parser_parity(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node not installed")
        env = self.make_env(self.git_paths + [str(Path(node).parent)])
        self.assertEqual(self.bash_cmd("git status", env=env)[0], "allow")
        self.assertEqual(self.bash_cmd("rm -rf /", env=env)[0], "deny")
        self.assertEqual(self.bash_cmd("git reset --hard", env=env)[0], "ask")
        self.assertEqual(self.run_hook({"tool_name": "Edit", "tool_input": {"file_path": "a"}}, env=env)[0], "allow")
        self.assert_failure_deny(self.run_hook('{"tool_input":', env=env))
        self.assert_failure_deny(self.run_hook({"tool_name": "Bash", "tool_input": {}}, env=env))

    def test_shared_helper_contract_for_freeze(self):
        # freeze sources this file: strict field extraction and the SimonK state root.
        helper = posix(self.install / "bin/hook-extract.sh")
        script = ('. "$1"; gstack_hook_extract_field \'{"tool_input":{}}\' file_path; echo "rc=$?"; '
                  'gstack_hook_extract_field \'{"tool_input":{"file_path":"a\\nb"}}\' file_path; echo "rc=$?"; '
                  'printf "root=%s\\n" "$(gstack_hook_state_root)"')
        run = lambda env: subprocess.run([str(BASH), "--noprofile", "--norc", "-c", script, "t", helper],
                                         capture_output=True, text=True, env=env, timeout=30).stdout
        out = run(self.env)
        self.assertEqual(out.count("rc=1"), 2, out)
        self.assertIn("root=" + posix(self.home) + "/.gstack", out)
        out = run(self.make_env([str(self.shims)] + self.git_paths, CLAUDE_PLUGIN_DATA="/plugin/state",
                                GSTACK_HOME="/analytics/only"))
        self.assertIn("root=/plugin/state", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
