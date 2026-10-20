"""Install the SimonK runtime into ~/.simonk/runtime (Windows, macOS, Linux).

The runtime is the shared tool set the gstack-derived SimonK-stack skills call:
bin scripts, browse/design/pdf binaries, the Chrome extension, hosts and the
skills' support files (sections, templates, ...). runtime/RUNTIME.json pins the
upstream commit (garrytan/gstack, MIT).

Preview by default. With --apply it:
  1. takes the runtime files from the pinned commit's git objects (never from a
     working tree), from --source (a clean checkout at the pinned commit) or
     from a fresh clone (--clone);
  2. leaves out tests, git metadata, other hosts' folders and every SKILL.md;
  3. rewrites home-anchored paths (~/, $HOME/, homedir()) from the upstream
     install ".claude/skills/gstack" to ".simonk/runtime" and from the state
     folder ".gstack" to ".simonk/state", so scripts and compiled tools default
     to the new folders even without the environment variables; a
     project-relative ".claude/skills/gstack" (a legacy vendored copy in a
     repository) is left as is. Text files are stored with LF line endings;
  3b. copies SimonK-stack's own version of each skill listed in
     skills-src/VENDORED.md over the upstream skill folder, so every
     "~/.simonk/runtime/<skill>/..." reference (sections, templates, another
     skill's SKILL.md) reads the SimonK text, not the upstream one;
  4. installs dependencies from the pinned bun.lock (--frozen-lockfile) and
     rebuilds the compiled tools so they carry the new paths;
  5. builds everything in a staging folder and swaps it in, so --force leaves
     no files from an earlier runtime behind;
  6. turns off update checks, telemetry and auto-upgrade and reads them back;
  7. points the state folder at ~/.simonk/state (user environment on Windows,
     ~/.simonk/env.sh to source elsewhere).

It never edits the source checkout and never reads the state folder's
credential files.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import uuid
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[1]
UPSTREAM = "https://github.com/garrytan/gstack.git"
EXCLUDE_TOP = {".git", ".github", ".agents", ".cursor", ".factory", ".gbrain", ".hermes", ".kiro", ".openclaw",
               ".opencode", ".slate", ".gstack", "test", "agents", "agents-digest", "contrib", "openclaw", "supabase",
               "claude-code", "gstack", "gstack-upgrade"}  # upstream router and upgrade skill: not carried over
EXCLUDE_TOP_FILES = {"CHANGELOG.md", "CONTRIBUTING.md", "TODOS.md", "README.md", "AGENTS.md", "CLAUDE.md",
                     "conductor.json", ".gitlab-ci.yml", ".gitattributes", ".gitignore", ".osv-scanner.toml",
                     ".env.example", "slop-scan.config.json", "test-setup.ts", "USING_GBRAIN_WITH_GSTACK.md",
                     "setup", "connect-chrome"}
EXCLUDE_NAMES = {"SKILL.md", "SKILL.md.tmpl"}
TEXT_EXT = {"", ".sh", ".ts", ".js", ".mjs", ".cjs", ".json", ".md", ".py", ".yaml", ".yml", ".txt", ".html",
            ".css", ".tmpl", ".toml"}
# Only home-anchored forms move. A project-relative ".claude/skills/gstack" is a
# legacy vendored copy inside a repository and must still be recognized as one.
SHELL_HOME = rb"((?:~|\$HOME|\$\{HOME\}|\$\{homeDir\})/)"
# First argument of a path.join that is the user's home: homedir(), HOME,
# process.env.HOME || '...', env.HOME || homedir(), home, userHome(), ...
# Project roots (cwd, projectDir, root, base) are not matched.
JS_HOME = (rb"((?:[\w.]*homedir\(\)|\b(?:ENV\.|env\.|process\.env\.)?HOME"
           rb"(?:\s*\|\|\s*(?:['\"][^'\"\n]*['\"]|[\w.]*homedir\(\)))?"
           rb"|\bhome|\buserHome\(\)|\buserHome\s*\|\|\s*['\"][^'\"\n]*['\"])\s*,\s*['\"])")
REWRITES = [
    (re.compile(SHELL_HOME + rb"\.claude/skills/gstack(?![\w-])"), rb"\1.simonk/runtime"),
    (re.compile(JS_HOME + rb"\.claude/skills/gstack(?![\w-])"), rb"\1.simonk/runtime"),
    (re.compile(SHELL_HOME + rb"\.gstack(?![\w-])"), rb"\1.simonk/state"),
    (re.compile(JS_HOME + rb"\.gstack(?=['\"/])"), rb"\1.simonk/state"),
]
VENDORED_LINE = re.compile(r"^- `([a-z0-9-]+)`")


def rewrite_text(text: bytes) -> bytes:
    """Point home-anchored install and state paths at ~/.simonk/runtime and ~/.simonk/state."""
    for rx, rep in REWRITES:
        text = rx.sub(rep, text)
    return text
COMPILE = [("browse/src/cli.ts", "browse/dist/browse"), ("browse/src/find-browse.ts", "browse/dist/find-browse"),
           ("design/src/cli.ts", "design/dist/design"), ("make-pdf/src/cli.ts", "make-pdf/dist/pdf"),
           ("bin/gstack-global-discover.ts", "bin/gstack-global-discover")]


class InstallError(Exception):
    pass


def run(cmd, cwd=None, env=None, check=True):
    p = subprocess.run([str(c) for c in cmd], cwd=cwd, env=env, capture_output=True)
    if check and p.returncode != 0:
        raise InstallError(f"{Path(str(cmd[0])).name} failed (exit {p.returncode})")
    return p


def load_pin(path: Path) -> dict:
    pin = json.loads(path.read_text(encoding="utf-8"))
    for key in ("upstream_commit", "upstream_version", "state_env", "config"):
        if key not in pin:
            raise InstallError(f"pin file lacks {key}")
    return pin


def find_bash() -> str | None:
    if os.name == "nt":
        git = shutil.which("git")
        if git:
            root = Path(git).resolve().parent.parent
            for c in (root / "bin" / "bash.exe", root / "usr" / "bin" / "bash.exe"):
                if c.exists():
                    return str(c)
        c = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe"
        return str(c) if c.exists() else None  # never the WSL bash.exe in System32
    return shutil.which("bash")


def resolve_source(source: Path, pin: dict) -> str:
    """Return the full pinned commit after checking the checkout is clean and at the pin."""
    if not (source / ".git").exists():
        raise InstallError(f"source is not a git checkout: {source}")
    head = run(["git", "-C", source, "rev-parse", "HEAD"]).stdout.decode().strip()
    if not head.startswith(pin["upstream_commit"]):
        raise InstallError(f"source HEAD {head[:12]} is not the pinned commit {pin['upstream_commit']}")
    dirty = run(["git", "-C", source, "status", "--porcelain", "--untracked-files=no"]).stdout.decode().strip()
    if dirty:
        raise InstallError("source checkout has local modifications")
    version = run(["git", "-C", source, "show", f"{head}:VERSION"]).stdout.decode().strip()
    if version != pin["upstream_version"]:
        raise InstallError(f"pinned commit VERSION {version} does not match {pin['upstream_version']}")
    return head


def clone_source(pin: dict, into: Path) -> Path:
    run(["git", "clone", "--quiet", "--no-checkout", UPSTREAM, into])
    full = run(["git", "-C", into, "rev-parse", pin["upstream_commit"]]).stdout.decode().strip()
    run(["git", "-C", into, "checkout", "--quiet", "--detach", full])
    return into


def wanted(rel: PurePosixPath) -> bool:
    parts = rel.parts
    if not parts or parts[0] in EXCLUDE_TOP:
        return False
    if len(parts) == 1 and parts[0] in EXCLUDE_TOP_FILES:
        return False
    if rel.name in EXCLUDE_NAMES:
        return False
    if len(parts) >= 2 and parts[1] == "test" and parts[0] in {"browse", "design", "make-pdf"}:
        return False  # tool test suites
    return True


def export_tree(source: Path, commit: str, staging: Path) -> tuple[int, int]:
    """Write the pinned commit's files (git objects, not the working tree) into staging."""
    data = run(["git", "-C", source, "archive", "--format=tar", commit]).stdout
    files = patched = 0
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        for m in tar.getmembers():
            if not m.isfile():
                continue
            rel = PurePosixPath(m.name)
            if not wanted(rel):
                continue
            raw = tar.extractfile(m).read()
            out = staging.joinpath(*rel.parts)
            out.parent.mkdir(parents=True, exist_ok=True)
            if rel.suffix.lower() in TEXT_EXT and b"\0" not in raw[:4096]:
                lf = raw.replace(b"\r\n", b"\n")
                raw = rewrite_text(lf)
                patched += raw != lf
            out.write_bytes(raw)
            if m.mode & 0o111:
                out.chmod(0o755)
            files += 1
    return files, patched


def overlay_skills(staging: Path, skills_src: Path, pin: dict) -> int:
    """Copy SimonK's vendored skills over the upstream skill folders of the same name."""
    listing = skills_src / "VENDORED.md"
    if not listing.is_file():
        raise InstallError(f"skill list not found: {listing}")
    upstream_names = pin.get("skill_overlay", {}).get("upstream_names", {})
    copied = 0
    for line in listing.read_text(encoding="utf-8").splitlines():
        m = VENDORED_LINE.match(line)
        if not m:
            continue
        name = m.group(1)
        src, dst = skills_src / name, staging / upstream_names.get(name, name)
        if not (src / "SKILL.md").is_file() or not dst.is_dir():
            continue  # no upstream folder to replace (a SimonK-only skill)
        for f in sorted(src.rglob("*")):
            rel = f.relative_to(src)
            if not f.is_file() or rel.parts[0] == "evals" or "__pycache__" in rel.parts:
                continue
            out = dst / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, out)
            copied += 1
    return copied


def build(staging: Path, bash: str) -> None:
    bun = shutil.which("bun")
    if not bun:
        raise InstallError("bun is required to rebuild the runtime tools (or pass --skip-build)")
    # Always resolve dependencies from the pinned lockfile in staging; an existing
    # node_modules in the source checkout is untracked and unverified.
    env = dict(os.environ, PATH=str(Path(bun).parent) + os.pathsep + os.environ.get("PATH", ""))
    run([bun, "install", "--frozen-lockfile"], cwd=staging, env=env)
    for src, out in COMPILE:
        run([bun, "build", "--compile", src, "--outfile", out], cwd=staging, env=env)
    run([bash, "browse/scripts/build-node-server.sh"], cwd=staging, env=env)
    for f in staging.glob(".*.bun-build"):
        f.unlink()
    (staging / "browse" / "dist" / ".build-complete").write_text("complete\n", encoding="utf-8")


def configure(target: Path, state: Path, pin: dict, bash: str) -> dict:
    env = dict(os.environ, **{name: str(state) for name in pin["state_env"]})
    tool = target / "bin" / "gstack-config"
    got = {}
    for key, value in pin["config"].items():
        run([bash, tool, "set", key, value], env=env)
        got[key] = run([bash, tool, "get", key], env=env).stdout.decode().strip()
        if got[key] != value:
            raise InstallError(f"config {key} reads back {got[key]!r}, expected {value!r}")
    return got


def persist_env(state: Path, pin: dict) -> str:
    if os.name == "nt":
        import winreg  # noqa: PLC0415 - Windows only
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as key:
            for name in pin["state_env"]:
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, str(state))
        return "user environment (open a new terminal)"
    env_file = state.parent / "env.sh"
    env_file.write_text("".join(f'export {n}="{state}"\n' for n in pin["state_env"]), encoding="utf-8")
    return f"{env_file} (source it from your shell profile)"


def main(argv=None) -> int:
    home = Path.home()
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--source", type=Path, default=home / ".claude" / "skills" / "gstack",
                    help="clean checkout at the pinned commit (default: ~/.claude/skills/gstack)")
    ap.add_argument("--clone", action="store_true", help="clone the pinned upstream commit instead of --source")
    ap.add_argument("--target", type=Path, default=home / ".simonk" / "runtime")
    ap.add_argument("--state", type=Path, default=home / ".simonk" / "state")
    ap.add_argument("--pin", type=Path, default=REPO / "runtime" / "RUNTIME.json")
    ap.add_argument("--skills-src", type=Path, default=REPO / "skills-src",
                    help="SimonK-stack skills to lay over the upstream skill folders")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--force", action="store_true", help="replace an existing runtime")
    ap.add_argument("--skip-build", action="store_true")
    ap.add_argument("--skip-config", action="store_true")
    ap.add_argument("--skip-env", action="store_true")
    a = ap.parse_args(argv)
    try:
        pin = load_pin(a.pin)
        work = Path(tempfile.mkdtemp(prefix="simonk-runtime-"))
        try:
            source = clone_source(pin, work / "src") if a.clone else a.source
            commit = resolve_source(source, pin)
            print(f"runtime source : {source} @ {commit[:12]} (VERSION {pin['upstream_version']})")
            print(f"runtime target : {a.target}")
            print(f"state folder   : {a.state}")
            if not a.apply:
                print("Preview only. Re-run with --apply to install.")
                return 0
            if a.target.exists() and not a.force:
                raise InstallError(f"target already exists: {a.target} (use --force to replace it)")
            bash = find_bash()
            if not bash and not (a.skip_build and a.skip_config):
                raise InstallError("bash (Git Bash on Windows) is required")
            staging = a.target.parent / f".{a.target.name}.staging-{uuid.uuid4().hex[:8]}"
            staging.mkdir(parents=True)
            old = None  # the previous runtime, kept until setup succeeds
            try:
                files, patched = export_tree(source, commit, staging)
                print(f"exported {files} files, rewrote the install path in {patched}")
                if "skill_overlay" in pin:
                    print(f"laid {overlay_skills(staging, a.skills_src, pin)} SimonK skill files over upstream")
                if not a.skip_build:
                    build(staging, bash)
                    print("rebuilt the compiled tools")
                if a.target.exists():
                    old = a.target.parent / f".{a.target.name}.old-{uuid.uuid4().hex[:8]}"
                    a.target.rename(old)
                staging.rename(a.target)
            except BaseException:
                shutil.rmtree(staging, ignore_errors=True)
                if old is not None and not a.target.exists():
                    old.rename(a.target)
                raise
            try:
                a.state.mkdir(parents=True, exist_ok=True)
                if not a.skip_config:
                    got = configure(a.target, a.state, pin, bash)
                    print("config: " + ", ".join(f"{k}={v}" for k, v in got.items()))
                if not a.skip_env:
                    print("state folder set in " + persist_env(a.state, pin))
            except BaseException:
                # A runtime whose isolation settings were not verified is not kept:
                # put the previous one back (or remove a first install).
                failed = a.target.parent / f".{a.target.name}.failed-{uuid.uuid4().hex[:8]}"
                a.target.rename(failed)
                if old is not None:
                    old.rename(a.target)
                    print("install-runtime: setup failed; restored the previous runtime", file=sys.stderr)
                shutil.rmtree(failed, ignore_errors=True)
                raise
            if old is not None:
                shutil.rmtree(old, ignore_errors=True)
            print("Done.")
            return 0
        finally:
            shutil.rmtree(work, ignore_errors=True)
    except (InstallError, OSError, subprocess.SubprocessError) as exc:
        print(f"install-runtime: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
