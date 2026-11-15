#!/usr/bin/env python3
"""Observe this host's local GUI tools for the /vibe planner (hub D-129, Simon 2026-11-16).

Grok Bot (vibe-bot) stays first for screen work (D-93). When every Bot candidate is blocked,
the planner may use local tools in table order: Playwright headless, Claude in Chrome, then
Computer Use. This script prints `gui_tools` entries for the runtime snapshot.

It reads only three things: the `mcpServers.playwright` entry of ~/.claude.json, the Playwright
MCP config file that entry names, and the Playwright browser folder. Claude in Chrome and
Computer Use exist only inside a live session, so the host attests them from its own tool list
with --chrome / --computer-use, and --interactive when Simon is at this session.

    python collect_gui_tools.py --host-ref <ref> [--host-surface claude] [--interactive]
                                [--chrome] [--computer-use] [--install]

--install fills only what is missing: the pointer-lock guard script and its `browser.initScript`
entry (the config is backed up first), and Chromium through the Playwright CLI
(`npx -y playwright install chromium`). It never registers an MCP server or changes its version.
A changed MCP config applies to new sessions only.

Exit codes: 0 observed, 2 bad arguments, 4 install failed.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

if __name__ == "__main__":
    sys.dont_write_bytecode = True

GUARD_MARKER = "SimonK /vibe D-129 pointer-lock guard"
GUARD_SCRIPT = ("// " + GUARD_MARKER + ": headless Chromium once locked and trapped the real cursor.\n"
                "(() => {\n"
                "  const deny = () => Promise.reject(new DOMException(\"Pointer lock is disabled in automation\","
                " \"NotAllowedError\"));\n"
                "  try { Element.prototype.requestPointerLock = deny; } catch (error) {}\n"
                "  try { Document.prototype.exitPointerLock = () => {}; } catch (error) {}\n"
                "})();\n")
INSTALL_ARGV = ["npx", "-y", "playwright", "install", "chromium"]


class GuiToolError(Exception):
    def __init__(self, code, exit_code=4):
        super().__init__(code)
        self.code, self.exit_code = code, exit_code


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def browser_cache(platform=None, environ=None, home=None):
    """Playwright's default browser cache: Windows %LOCALAPPDATA%, macOS ~/Library/Caches, else ~/.cache."""
    platform, environ, home = platform or sys.platform, os.environ if environ is None else environ, home or Path.home()
    if environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        return Path(environ["PLAYWRIGHT_BROWSERS_PATH"])
    if platform.startswith("win") and environ.get("LOCALAPPDATA"):
        return Path(environ["LOCALAPPDATA"]) / "ms-playwright"
    if platform == "darwin":
        return home / "Library" / "Caches" / "ms-playwright"
    return home / ".cache" / "ms-playwright"


def default_paths():
    home = Path.home()
    return {"claude_json": home / ".claude.json", "browsers": browser_cache(home=home),
            "guard": home / ".claude" / "playwright-pointer-guard.js"}


def playwright_entry(claude_json):
    """Only mcpServers.playwright; nothing else in the file is kept or printed."""
    try:
        data = json.loads(Path(claude_json).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    servers = data.get("mcpServers") if isinstance(data, dict) else None
    entry = servers.get("playwright") if isinstance(servers, dict) else None
    return entry if isinstance(entry, dict) else None


def entry_args(entry):
    args = entry.get("args") if entry else None
    return [a for a in args if isinstance(a, str)] if isinstance(args, list) else []


def config_path(entry):
    args = entry_args(entry)
    for i, arg in enumerate(args):
        if arg == "--config" and i + 1 < len(args):
            return Path(args[i + 1])
        if arg.startswith("--config="):
            return Path(arg.split("=", 1)[1])
    return None


def read_config(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8")) if path else {}
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def init_scripts(entry, config):
    args = entry_args(entry)
    paths = [args[i + 1] for i, a in enumerate(args) if a == "--init-script" and i + 1 < len(args)]
    browser = config.get("browser") if isinstance(config.get("browser"), dict) else {}
    listed = browser.get("initScript")
    if isinstance(listed, list):
        paths.extend(p for p in listed if isinstance(p, str))
    return paths


def guarded(entry, config):
    for item in init_scripts(entry, config):
        try:
            if GUARD_MARKER in Path(item).read_text(encoding="utf-8"):
                return True
        except OSError:
            continue
    return False


# A Playwright browser folder counts only with its completion marker and an executable.
BROWSER_EXECUTABLES = ("chrome.exe", "chrome", "chrome-headless-shell.exe", "chrome-headless-shell", "Chromium.app")


def chromium_installed(browsers):
    try:
        folders = [p for p in Path(browsers).iterdir() if p.is_dir() and p.name.startswith("chromium")]
        for folder in folders:
            if not (folder / "INSTALLATION_COMPLETE").is_file():
                continue
            for build in folder.iterdir():
                if build.is_dir() and build.name.startswith("chrome") and any(
                        (build / name).exists() for name in BROWSER_EXECUTABLES):
                    return True
    except OSError:
        return False
    return False


def read_config_strict(path):
    """Install never rewrites a config it cannot fully read."""
    if not Path(path).exists():
        return {}
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise GuiToolError("PLAYWRIGHT_CONFIG_INVALID") from None
    if not isinstance(data, dict):
        raise GuiToolError("PLAYWRIGHT_CONFIG_INVALID")
    return data


def inspect_playwright(paths):
    entry = playwright_entry(paths["claude_json"])
    args = entry_args(entry)
    config = read_config(config_path(entry))
    browser = config.get("browser") if isinstance(config.get("browser"), dict) else {}
    launch = browser.get("launchOptions") if isinstance(browser.get("launchOptions"), dict) else {}
    package = next((a for a in args if a.startswith("@playwright/mcp")), None)
    return {"registered": entry is not None,
            "headless": "--headless" in args or launch.get("headless") is True,
            "isolated": "--isolated" in args or browser.get("isolated") is True,
            "pointer_lock_guard": guarded(entry, config),
            "chromium": chromium_installed(paths["browsers"]),
            "version_pinned": bool(package) and not package.endswith("@latest") and package.count("@") >= 2,
            "package": package}


def observe(host_ref, host_surface="claude", interactive=False, chrome=False, computer_use=False,
            now=None, paths=None):
    if not isinstance(host_ref, str) or not host_ref.strip():
        raise GuiToolError("HOST_REF_REQUIRED", exit_code=2)
    if host_surface not in ("claude", "codex"):
        raise GuiToolError("HOST_SURFACE_INVALID", exit_code=2)
    now, paths = now or utc_now(), paths or default_paths()
    facts = inspect_playwright(paths)
    notes = []
    if not facts["registered"]:
        notes.append("Playwright MCP is not registered; register it headless and isolated before use.")
    if facts["registered"] and not facts["version_pinned"]:
        notes.append("Playwright MCP runs an unpinned package (" + str(facts["package"]) + "); pin a reviewed version.")
    if not facts["chromium"]:
        notes.append("No Playwright Chromium found; run with --install.")
    if facts["registered"] and not facts["pointer_lock_guard"]:
        notes.append("No pointer-lock guard init script; run with --install.")
    tools = [{"id": "host:playwright", "transport": "playwright",
              "available": facts["registered"] and facts["chromium"], "observed_at": now,
              "evidence": ["collect_gui_tools: mcpServers.playwright, its config file and the browser folder"],
              "host_ref": host_ref, "host_surface": host_surface, "headless": facts["headless"],
              "isolated": facts["isolated"], "pointer_lock_guard": facts["pointer_lock_guard"],
              "version_pinned": facts["version_pinned"]}]
    for flag, transport in ((chrome, "claude-in-chrome"), (computer_use, "computer-use")):
        if flag:
            tools.append({"id": "host:" + transport, "transport": transport, "available": True,
                          "observed_at": now, "evidence": ["host attested from its live tool list"],
                          "host_ref": host_ref, "host_surface": host_surface, "interactive": interactive is True})
    return {"gui_tools": tools, "notes": notes}


def install(paths=None, run=None, stamp=None):
    """Fill only what is missing. Returns the list of changes made."""
    paths, changes = paths or default_paths(), []
    entry = playwright_entry(paths["claude_json"])
    if entry is None:
        raise GuiToolError("PLAYWRIGHT_MCP_NOT_REGISTERED")
    if not guarded(entry, read_config(config_path(entry))):
        target = config_path(entry)
        if target is None:
            raise GuiToolError("PLAYWRIGHT_CONFIG_NOT_USED")  # Flags only; add --config by hand first.
        config = read_config_strict(target)  # Before any write.
        guard = Path(paths["guard"])
        if not guard.exists() or GUARD_MARKER not in guard.read_text(encoding="utf-8"):
            guard.parent.mkdir(parents=True, exist_ok=True)
            guard.write_text(GUARD_SCRIPT, encoding="utf-8", newline="\n")
            changes.append("wrote " + str(guard))
        if target.exists():
            backup = target.with_name(target.name + ".bak-" + (stamp or datetime.now().strftime("%Y%m%d%H%M%S")))
            shutil.copy2(target, backup)
            changes.append("backed up " + str(target) + " to " + str(backup))
        browser = config.setdefault("browser", {})
        if not isinstance(browser, dict):
            raise GuiToolError("PLAYWRIGHT_CONFIG_INVALID")
        scripts = browser.setdefault("initScript", [])
        if not isinstance(scripts, list):
            raise GuiToolError("PLAYWRIGHT_CONFIG_INVALID")
        scripts.append(str(guard))
        target.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        changes.append("added the guard to browser.initScript in " + str(target) + " (new sessions only)")
    if not chromium_installed(paths["browsers"]):
        argv = list(INSTALL_ARGV)
        argv[0] = shutil.which("npx") or "npx"
        code = (run or (lambda a: subprocess.run(a, check=False, timeout=900).returncode))(argv)
        if code != 0 or not chromium_installed(paths["browsers"]):
            raise GuiToolError("CHROMIUM_INSTALL_FAILED")
        changes.append("installed Chromium with " + " ".join(INSTALL_ARGV))
    return changes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host-ref", required=True, help="Non-secret reference of this host session")
    parser.add_argument("--host-surface", default="claude", choices=("claude", "codex"))
    parser.add_argument("--interactive", action="store_true", help="Simon is at this interactive session")
    parser.add_argument("--chrome", action="store_true", help="Claude in Chrome tools are connected here")
    parser.add_argument("--computer-use", action="store_true", help="Computer Use tools are available here")
    parser.add_argument("--install", action="store_true", help="Fill a missing guard or Chromium first")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        changes = install() if args.install else []
        result = observe(args.host_ref, args.host_surface, args.interactive, args.chrome, args.computer_use)
    except GuiToolError as exc:
        print(json.dumps({"error": exc.code}, ensure_ascii=False))
        return exc.exit_code
    result["changes"] = changes
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
