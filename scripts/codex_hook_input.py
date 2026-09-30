"""Parse Codex PreToolUse inputs without executing or authorizing the tool.

This offline adapter is not registered as a hook. It extracts patch paths for a
future guarded-profile prototype; parsing success is not a safety decision.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re


MAX_INPUT = 1024 * 1024
SESSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z", re.ASCII)
PATH_HEADERS = {
    "*** Add File: ": "add",
    "*** Update File: ": "update",
    "*** Delete File: ": "delete",
    "*** Move to: ": "move",
}


class HookInputError(ValueError):
    """The hook payload or patch path inventory is untrusted/ambiguous."""


@dataclass(frozen=True)
class HookInput:
    session_id: str
    cwd: str
    tool_name: str
    command: str
    targets: tuple[str, ...]


def _object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise HookInputError("duplicate JSON key")
        result[key] = value
    return result


def _constant(_value: str) -> None:
    raise HookInputError("non-finite JSON value")


def _path(raw: str, seen: set[str]) -> str:
    if not raw or raw != raw.strip() or any(ord(char) < 32 or ord(char) == 127 for char in raw):
        raise HookInputError("invalid patch path")
    folded = raw.replace("\\", "/").casefold()
    if folded in seen:
        raise HookInputError("duplicate patch path")
    seen.add(folded)
    return raw


def extract_patch_targets(command: str) -> tuple[str, ...]:
    """Inventory *all declared paths* in the supported apply_patch wire form.

    Unknown directives or unstructured lines are rejected, never treated as
    permission to edit. A later policy must separately canonicalize these paths.
    """
    # str.splitlines() treats Unicode separators and bare CR as newlines even
    # when the tool's patch grammar may not. Reject them to avoid inventing
    # a second file header that the tool would not actually see.
    if (not isinstance(command, str) or not command
            or any(char in command for char in "\x00\r\v\f\x1c\x1d\x1e\x85\u2028\u2029")):
        raise HookInputError("invalid patch command")
    lines = command.split("\n")
    if lines[-1] == "":
        lines.pop()
    if len(lines) < 3 or lines[0] != "*** Begin Patch" or lines[-1] != "*** End Patch":
        raise HookInputError("incomplete patch envelope")
    paths: list[str] = []
    seen: set[str] = set()
    action = None
    for line in lines[1:-1]:
        if line == "*** End of File":
            if action != "update":
                raise HookInputError("unexpected end-of-file marker")
            continue
        if line.startswith("*** "):
            match = next((prefix for prefix in PATH_HEADERS if line.startswith(prefix)), None)
            if match is None:
                raise HookInputError("unknown patch directive")
            kind = PATH_HEADERS[match]
            if kind == "move":
                if action != "update":
                    raise HookInputError("move without update")
                action = "move"
            else:
                action = kind
            paths.append(_path(line[len(match):], seen))
            continue
        if action is None or not line.startswith(("@@", " ", "+", "-", "\\")):
            raise HookInputError("unexpected patch body")
    if not paths:
        raise HookInputError("patch has no target")
    return tuple(paths)


def parse_pre_tool_use(raw: bytes) -> HookInput:
    """Validate a bounded Codex Bash/apply_patch PreToolUse JSON payload."""
    if not isinstance(raw, bytes) or len(raw) > MAX_INPUT:
        raise HookInputError("invalid payload size")
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_object,
                          parse_constant=_constant)
    except (UnicodeError, json.JSONDecodeError, TypeError, RecursionError) as exc:
        raise HookInputError("invalid hook JSON") from exc
    if not isinstance(data, dict) or data.get("hook_event_name") != "PreToolUse":
        raise HookInputError("not PreToolUse")
    session_id = data.get("session_id")
    cwd = data.get("cwd")
    tool_name = data.get("tool_name")
    tool_input = data.get("tool_input")
    if (not isinstance(session_id, str) or not SESSION.fullmatch(session_id)
            or not isinstance(cwd, str) or not cwd or "\x00" in cwd
            or tool_name not in ("Bash", "apply_patch")
            or not isinstance(tool_input, dict)):
        raise HookInputError("invalid hook fields")
    command = tool_input.get("command")
    if not isinstance(command, str) or not command or "\x00" in command:
        raise HookInputError("missing command")
    targets = extract_patch_targets(command) if tool_name == "apply_patch" else ()
    return HookInput(session_id, cwd, tool_name, command, targets)
