"""Offline Codex guarded-profile policy candidate; not installed as a hook.

This uses Codex's supported PreToolUse deny result, not Claude's unsupported
ask result. It is an accident-prevention aid, not a complete security boundary:
the host can skip untrusted hooks and some tool paths do not emit this event.

Careful leaf decisions (hub decision D-62 follow-up 5): `{}` allows; a leaf
`deny` (careful 0.2.2 HIGH commands and its own hook failures) passes through
with the leaf's reason; a leaf `ask` becomes a deny with a fixed Codex reason
because Codex has no ask. Anything else, and every failure of this policy
itself, is a deny with the policy's own reason.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from codex_hook_input import HookInput, MAX_INPUT, parse_pre_tool_use


def _deny(reason: str) -> dict:
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}


def _contained_patch(event: HookInput, boundary: Path) -> bool:
    cwd = Path(event.cwd)
    allowed = Path(boundary)
    if not cwd.is_absolute() or not cwd.is_dir() or not allowed.is_absolute():
        return False
    allowed = allowed.resolve(strict=True)
    if not allowed.is_dir():
        return False
    for raw in event.targets:
        target = Path(raw)
        if not target.is_absolute():
            target = cwd / target
        # An existing physical parent is required. That catches missing/../..
        # paths and lets resolve follow an existing junction or symlink.
        target.parent.resolve(strict=True)
        resolved = target.resolve(strict=False)
        if not resolved.is_relative_to(allowed):
            return False
    return True


def _posix(path: Path) -> str:
    absolute = path.absolute()
    if os.name == "nt":
        if len(absolute.drive) != 2 or absolute.drive[1] != ":":
            raise ValueError("a local drive path is required")
        return "/" + absolute.drive[0].lower() + absolute.as_posix()[2:]
    return str(absolute)


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate leaf key")
        result[key] = value
    return result


def _careful_leaf(raw: bytes, event: HookInput, bash: Path, script: Path) -> dict | None:
    """Run the careful leaf; None for allow, else its validated hook output."""
    bash = Path(bash).resolve(strict=True)
    script = Path(script).resolve(strict=True)
    if not bash.is_file() or not script.is_file() or not Path(event.cwd).is_dir():
        raise ValueError("missing safety runtime")
    with tempfile.TemporaryDirectory(prefix="simonk-codex-careful-") as private_name:
        private = Path(private_name)
        env = {key: value for key, value in os.environ.items()
               if key.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP"}}
        path_parts = [str(bash.parent.parent / "usr/bin")]
        node = shutil.which("node")
        if node:
            path_parts.append(str(Path(node).parent))
        env.update(PATH=os.pathsep.join(path_parts), HOME=_posix(private),
                   USERPROFILE=str(private), GSTACK_HOME=_posix(private),
                   GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                   GIT_CONFIG_SYSTEM=os.devnull, GIT_TERMINAL_PROMPT="0",
                   BASH_ENV="", ENV="", LC_ALL="C")
        with tempfile.TemporaryFile() as output:
            process = subprocess.Popen(
                [str(bash), "--noprofile", "--norc", _posix(script)],
                stdin=subprocess.PIPE, stdout=output, stderr=subprocess.DEVNULL,
                cwd=event.cwd, env=env,
            )
            try:
                process.communicate(raw, timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                raise ValueError("safety leaf timed out") from None
            if process.returncode != 0 or output.tell() > 64 * 1024:
                raise ValueError("safety leaf failed")
            output.seek(0)
            encoded = output.read(64 * 1024 + 1)
    result = json.loads(encoded.decode("utf-8"), object_pairs_hook=_strict_object)
    if result == {}:
        return None
    if not isinstance(result, dict) or set(result) != {"hookSpecificOutput"}:
        raise ValueError("invalid safety leaf output")
    hook = result["hookSpecificOutput"]
    # The careful leaf emits only ask or deny besides `{}`. Tuple membership
    # compares with ==, so a non-string value is invalid output, not a TypeError.
    if (not isinstance(hook, dict)
            or set(hook) != {"hookEventName", "permissionDecision", "permissionDecisionReason"}
            or hook.get("hookEventName") != "PreToolUse"
            or hook.get("permissionDecision") not in ("ask", "deny")
            or not isinstance(hook.get("permissionDecisionReason"), str)
            or not hook["permissionDecisionReason"]):
        raise ValueError("invalid safety leaf decision")
    return hook


def judge_pre_tool_use(raw: bytes, *, boundary: Path | None = None,
                       bash: Path | None = None,
                       careful_script: Path | None = None) -> dict:
    """Return only `{}` or a supported Codex deny object; never run input."""
    try:
        event = parse_pre_tool_use(raw)
        if event.tool_name == "apply_patch":
            if boundary is None or _contained_patch(event, boundary):
                return {}
            return _deny("[SimonK] Patch is outside the guarded edit boundary.")
        if bash is None or careful_script is None:
            return _deny("[SimonK] Command safety runtime is unavailable.")
        leaf = _careful_leaf(raw, event, bash, careful_script)
        if leaf is None:
            return {}
        if leaf["permissionDecision"] == "deny":
            # The leaf already blocked it; keep its reason (HIGH tier or its
            # own hook failure) instead of reporting a failed safety check.
            return _deny(leaf["permissionDecisionReason"])
        return _deny("[SimonK] Destructive command blocked. Review and run outside "
                     "this guarded session only if authorized.")
    except Exception:
        # A hook exception would otherwise be reported by Codex and the tool
        # could continue. A live host timeout/termination remains unproven.
        return _deny("[SimonK] Safety check could not finish; tool blocked.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline Codex guarded-profile hook candidate")
    parser.add_argument("--boundary", type=Path)
    parser.add_argument("--bash", type=Path)
    parser.add_argument("--careful-script", type=Path)
    args = parser.parse_args(argv)
    raw = sys.stdin.buffer.read(MAX_INPUT + 1)
    result = judge_pre_tool_use(raw, boundary=args.boundary, bash=args.bash,
                                careful_script=args.careful_script)
    sys.stdout.write(json.dumps(result, ensure_ascii=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
