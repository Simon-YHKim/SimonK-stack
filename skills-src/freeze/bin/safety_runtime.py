#!/usr/bin/env python3
"""Windows-only bridge for SimonK's unchanged Bash safety leaves.

The bridge owns only a local project/session state namespace and a bounded
direct-child process boundary.  It does not authenticate the caller, activate
host hooks, execute tool commands, or make a candidate install-ready.  Timeout
kills Git Bash itself, not an independently escaped descendant tree.  Atomic
replacement assumes one same-user writer for a project/session key; concurrent
writers are outside this deliberately small v1 contract.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess
import sys
import tempfile
from typing import Any


SCHEMA_VERSION = 1
MAX_INPUT = 1024 * 1024
MAX_OUTPUT = 64 * 1024
PROCESS_TIMEOUT = 5
SESSION_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z", re.ASCII)
REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


class SafetyRuntimeError(Exception):
    """Expected validation/runtime failure whose details must not escape."""


def _decision(policy: str) -> dict[str, Any]:
    decision = "ask" if policy == "careful" else "deny"
    reason = ("[careful] Safety runtime unavailable; review before approving."
              if policy == "careful"
              else "[freeze] Safety runtime unavailable; blocked, fail closed.")
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }


def _emit(data: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(data, ensure_ascii=True, separators=(",", ":")) + "\n")


def _local_path(raw: str | os.PathLike[str]) -> Path:
    value = os.fspath(raw)
    if (not isinstance(value, str) or not value
            or any(ord(char) < 32 or ord(char) == 127 for char in value)
            or "${" in value or value.startswith(("\\\\", "//"))):
        raise SafetyRuntimeError
    path = Path(value)
    if (not path.is_absolute() or not re.fullmatch(r"[A-Za-z]:", path.drive)):
        raise SafetyRuntimeError
    try:
        drive_type = ctypes.windll.kernel32.GetDriveTypeW(path.drive + "\\")
    except (AttributeError, OSError) as exc:
        raise SafetyRuntimeError from exc
    if drive_type != 3:  # DRIVE_FIXED; mapped/network/removable roots are out of contract.
        raise SafetyRuntimeError
    return path


def _directory_info(path: Path) -> os.stat_result:
    try:
        info = path.lstat()
    except (OSError, ValueError) as exc:
        raise SafetyRuntimeError from exc
    if (path.is_symlink()
            or bool(getattr(info, "st_file_attributes", 0) & REPARSE_POINT)
            or not stat.S_ISDIR(info.st_mode)):
        raise SafetyRuntimeError
    return info


def _is_reparse(path: Path) -> bool:
    try:
        info = path.lstat()
    except (OSError, ValueError) as exc:
        raise SafetyRuntimeError from exc
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & REPARSE_POINT)


def _safe_regular_file(path: Path) -> os.stat_result:
    path = Path(os.path.abspath(str(_local_path(path))))
    _safe_directory(path.parent)
    try:
        info = path.lstat()
    except (OSError, ValueError) as exc:
        raise SafetyRuntimeError from exc
    if (_is_reparse(path) or not stat.S_ISREG(info.st_mode)
            or getattr(info, "st_nlink", 1) != 1):
        raise SafetyRuntimeError
    return info


def _safe_directory(path: Path, *, create: bool = False) -> Path:
    path = Path(os.path.abspath(str(_local_path(path))))
    parts = path.parts
    current = Path(parts[0])
    _directory_info(current)
    for component in parts[1:]:
        current /= component
        try:
            info = current.lstat()
        except FileNotFoundError:
            if not create:
                raise SafetyRuntimeError
            try:
                current.mkdir()
            except (OSError, ValueError) as exc:
                raise SafetyRuntimeError from exc
            info = _directory_info(current)
        except (OSError, ValueError) as exc:
            raise SafetyRuntimeError from exc
        if (current.is_symlink()
                or bool(getattr(info, "st_file_attributes", 0) & REPARSE_POINT)
                or not stat.S_ISDIR(info.st_mode)):
            raise SafetyRuntimeError
    return path


def _canonical_directory(raw: str | os.PathLike[str]) -> str:
    path = _safe_directory(Path(raw))
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise SafetyRuntimeError from exc
    _safe_directory(resolved)
    return str(resolved)


def _valid_session(raw: Any) -> str:
    if not isinstance(raw, str) or not SESSION_RE.fullmatch(raw):
        raise SafetyRuntimeError
    return raw


def _state_root(*, create: bool) -> Path:
    explicit = os.environ.get("SIMONK_SAFETY_STATE_ROOT")
    if explicit:
        root = Path(explicit)
    else:
        local = os.environ.get("LOCALAPPDATA")
        if not local:
            raise SafetyRuntimeError
        root = Path(local) / "SimonK" / "safety-v1"
    if not root.is_absolute():
        raise SafetyRuntimeError
    if create:
        root = _safe_directory(root, create=True)
    else:
        root = _safe_directory(root)
    return root


def _state_path(project: str, session: str, *, create: bool) -> Path:
    root = _state_root(create=create)
    states = root / "states"
    if create:
        states = _safe_directory(states, create=True)
    else:
        states = _safe_directory(states)
    namespace = hashlib.sha256(
        (os.path.normcase(project) + "\0" + session).encode("utf-8")
    ).hexdigest()
    return states / (namespace + ".json")


def _atomic_write(path: Path, state: dict[str, Any]) -> None:
    path = _safe_directory(path.parent) / path.name
    if path.exists() or path.is_symlink():
        _safe_regular_file(path)
    payload = (json.dumps(state, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":")) + "\n").encode("utf-8")
    temporary = path.parent / ("." + path.name + "." + secrets.token_hex(8) + ".tmp")
    descriptor = None
    created = False
    identity: tuple[int, int] | None = None
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        created = True
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or getattr(info, "st_nlink", 1) != 1:
            raise SafetyRuntimeError
        identity = (info.st_dev, info.st_ino)
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = None
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        _safe_regular_file(temporary)
        if path.exists() or path.is_symlink():
            _safe_regular_file(path)
        os.replace(temporary, path)
        created = False
        _safe_regular_file(path)
    except (OSError, SafetyRuntimeError) as exc:
        raise SafetyRuntimeError from exc
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if created:
            try:
                info = _safe_regular_file(temporary)
                if identity == (info.st_dev, info.st_ino):
                    temporary.unlink()
            except (OSError, ValueError, SafetyRuntimeError):
                pass


def _write_state(project_raw: str, session_raw: str, boundary_raw: str | None) -> None:
    project = _canonical_directory(project_raw)
    session = _valid_session(session_raw)
    state: dict[str, Any] = {
        "project": project,
        "schema_version": SCHEMA_VERSION,
        "session": session,
        "status": "inactive" if boundary_raw is None else "active",
    }
    if boundary_raw is not None:
        state["boundary"] = _canonical_directory(boundary_raw)
    path = _state_path(project, session, create=True)
    _atomic_write(path, state)


def _load_state(project: str, session: str) -> dict[str, Any]:
    path = _state_path(project, session, create=False)
    _safe_regular_file(path)
    try:
        if path.stat().st_size > MAX_INPUT:
            raise SafetyRuntimeError
        raw = path.read_bytes()
        state = _strict_json(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError,
            RecursionError, SafetyRuntimeError) as exc:
        raise SafetyRuntimeError from exc
    if not isinstance(state, dict):
        raise SafetyRuntimeError
    common = {"project", "schema_version", "session", "status"}
    if state.get("status") == "active":
        if set(state) != common | {"boundary"}:
            raise SafetyRuntimeError
    elif state.get("status") == "inactive":
        if set(state) != common:
            raise SafetyRuntimeError
    else:
        raise SafetyRuntimeError
    if (type(state.get("schema_version")) is not int
            or state["schema_version"] != SCHEMA_VERSION
            or state.get("project") != project
            or state.get("session") != session):
        raise SafetyRuntimeError
    if state["status"] == "active":
        boundary = state.get("boundary")
        if not isinstance(boundary, str) or _canonical_directory(boundary) != boundary:
            raise SafetyRuntimeError
    return state


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SafetyRuntimeError
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    raise SafetyRuntimeError


def _strict_json(raw: str) -> Any:
    return json.loads(raw, object_pairs_hook=_unique_object,
                      parse_constant=_reject_constant)


def _read_hook_input() -> dict[str, Any]:
    raw = sys.stdin.buffer.read(MAX_INPUT + 1)
    if len(raw) > MAX_INPUT:
        raise SafetyRuntimeError
    try:
        data = _strict_json(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError, ValueError, TypeError,
            RecursionError, SafetyRuntimeError) as exc:
        raise SafetyRuntimeError from exc
    if not isinstance(data, dict) or not isinstance(data.get("tool_input"), dict):
        raise SafetyRuntimeError
    data["session_id"] = _valid_session(data.get("session_id"))
    cwd = data.get("cwd")
    if not isinstance(cwd, str):
        raise SafetyRuntimeError
    data["cwd"] = _canonical_directory(cwd)
    return data


def _known_bash_candidates() -> list[Path]:
    candidates = []
    for variable, suffix in (
        ("ProgramFiles", "Git/bin/bash.exe"),
        ("ProgramFiles(x86)", "Git/bin/bash.exe"),
        ("LOCALAPPDATA", "Programs/Git/bin/bash.exe"),
    ):
        value = os.environ.get(variable)
        if value:
            candidates.append(Path(value) / suffix)
    return candidates


def _locate_bash() -> tuple[Path, Path]:
    explicit = os.environ.get("SIMONK_SAFETY_BASH")
    candidates = [Path(explicit)] if explicit else _known_bash_candidates()
    for candidate in candidates:
        try:
            if not candidate.is_absolute() or candidate.name.lower() != "bash.exe":
                continue
            _safe_regular_file(candidate)
            cygpath = candidate.parent.parent / "usr/bin/cygpath.exe"
            _safe_regular_file(cygpath)
            return candidate.resolve(strict=True), cygpath.resolve(strict=True)
        except (OSError, SafetyRuntimeError):
            continue
    raise SafetyRuntimeError


def _find_node() -> Path | None:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if not directory:
            continue
        candidate = Path(directory) / "node.exe"
        try:
            _safe_regular_file(candidate)
            return candidate.resolve(strict=True)
        except (OSError, SafetyRuntimeError):
            continue
    return None


def _cygpath(cygpath: Path, native: str) -> str:
    try:
        result = subprocess.run(
            [str(cygpath), "-u", native],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=PROCESS_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise SafetyRuntimeError from exc
    if result.returncode or len(result.stdout) > 4096:
        raise SafetyRuntimeError
    try:
        value = result.stdout.decode("utf-8").strip()
    except UnicodeError as exc:
        raise SafetyRuntimeError from exc
    if not value.startswith("/") or any(ord(char) < 32 for char in value):
        raise SafetyRuntimeError
    return value


def _safe_resource(path: Path) -> Path:
    _safe_regular_file(path)
    try:
        return path.resolve(strict=True)
    except OSError as exc:
        raise SafetyRuntimeError from exc


def _hook_environment(bash: Path, cygpath: Path, private_root: Path,
                      plugin_data: Path | None) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items()
           if key.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP"}}
    paths = [bash.parent.parent / "usr/bin", bash.parent.parent / "mingw64/bin"]
    node = _find_node()
    if node is not None:
        paths.append(node.parent)
    posix_private = _cygpath(cygpath, str(private_root))
    env.update(
        PATH=os.pathsep.join(map(str, paths)),
        HOME=posix_private,
        USERPROFILE=str(private_root),
        GSTACK_HOME=posix_private + "/analytics-only",
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_SYSTEM=os.devnull,
        GIT_TERMINAL_PROMPT="0",
        BASH_ENV="",
        ENV="",
        LC_ALL="C",
    )
    if plugin_data is not None:
        env["CLAUDE_PLUGIN_DATA"] = _cygpath(cygpath, str(plugin_data))
    return env


def _tool_path(cwd: str, raw: Any) -> Path:
    if (not isinstance(raw, str) or not raw
            or any(ord(char) < 32 or ord(char) == 127 for char in raw)
            or "${" in raw):
        raise SafetyRuntimeError
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = Path(cwd) / candidate
    candidate = _local_path(candidate)  # Validate the fixed drive without normalizing '..'.
    parts = candidate.parts
    current = Path(parts[0])
    _directory_info(current)
    # The unchanged leaf requires every parent of a new target to exist.  Check
    # each lexical component in order so "missing/../allowed" cannot be
    # normalized into an apparently valid path before the leaf sees it.
    for component in parts[1:-1]:
        if component == ".":
            continue
        if component == "..":
            current = current.parent
            continue
        current /= component
        try:
            if not current.is_dir():
                raise SafetyRuntimeError
        except (OSError, ValueError) as exc:
            raise SafetyRuntimeError from exc
    return candidate


def _run_leaf(policy: str, payload: dict[str, Any], boundary: str | None) -> dict[str, Any]:
    runtime = Path(__file__).resolve(strict=True).parent
    bash, cygpath = _locate_bash()
    helper = (runtime / "careful/bin/check-careful.sh" if policy == "careful"
              else runtime / "freeze/bin/check-freeze.sh")
    helper = _safe_resource(helper)
    _safe_resource(runtime / "careful/bin/hook-extract.sh")

    translated = dict(payload)
    translated["tool_input"] = dict(payload["tool_input"])
    if policy == "freeze":
        native = _tool_path(translated["cwd"], translated["tool_input"].get("file_path"))
        translated["tool_input"]["file_path"] = _cygpath(cygpath, str(native))

    try:
        encoded = json.dumps(translated, ensure_ascii=False, allow_nan=False,
                             separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise SafetyRuntimeError from exc
    if len(encoded) > MAX_INPUT:
        raise SafetyRuntimeError

    with tempfile.TemporaryDirectory(prefix="simonk-safety-") as temporary:
        private = Path(temporary)
        plugin_data = None
        if policy == "freeze":
            if boundary is None:
                raise SafetyRuntimeError
            plugin_data = private / "plugin-data"
            plugin_data.mkdir()
            posix_boundary = _cygpath(cygpath, boundary).rstrip("/") + "/"
            (plugin_data / "freeze-dir.txt").write_text(posix_boundary + "\n", encoding="utf-8")
        env = _hook_environment(bash, cygpath, private, plugin_data)
        posix_helper = _cygpath(cygpath, str(helper))
        try:
            with tempfile.TemporaryFile() as output:
                process = subprocess.Popen(
                    [str(bash), "--noprofile", "--norc", posix_helper],
                    stdin=subprocess.PIPE,
                    stdout=output,
                    stderr=subprocess.DEVNULL,
                    cwd=translated["cwd"],
                    env=env,
                )
                try:
                    process.communicate(encoded, timeout=PROCESS_TIMEOUT)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
                    raise SafetyRuntimeError
                if process.returncode != 0 or output.tell() > MAX_OUTPUT:
                    raise SafetyRuntimeError
                output.seek(0)
                raw_output = output.read(MAX_OUTPUT + 1)
        except (OSError, subprocess.SubprocessError) as exc:
            raise SafetyRuntimeError from exc
    try:
        result = _strict_json(raw_output.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError, ValueError, TypeError,
            RecursionError, SafetyRuntimeError) as exc:
        raise SafetyRuntimeError from exc
    if result == {}:
        return result
    if not isinstance(result, dict) or set(result) != {"hookSpecificOutput"}:
        raise SafetyRuntimeError
    hook = result["hookSpecificOutput"]
    allowed = "ask" if policy == "careful" else "deny"
    if (not isinstance(hook, dict)
            or set(hook) != {"hookEventName", "permissionDecision",
                             "permissionDecisionReason"}
            or hook.get("hookEventName") != "PreToolUse"
            or hook.get("permissionDecision") != allowed
            or not isinstance(hook.get("permissionDecisionReason"), str)
            or not hook["permissionDecisionReason"]):
        raise SafetyRuntimeError
    return result


def _check(policy: str, project_raw: str) -> dict[str, Any]:
    project = _canonical_directory(project_raw)
    payload = _read_hook_input()
    session = payload["session_id"]
    if policy == "careful":
        return _run_leaf(policy, payload, None)
    state = _load_state(project, session)
    if state["status"] == "inactive":
        return {}
    return _run_leaf(policy, payload, state["boundary"])


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SimonK candidate safety runtime")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("set", "clear"):
        command = commands.add_parser(name)
        command.add_argument("--project", required=True)
        command.add_argument("--session", required=True)
        command.add_argument("--boundary")
    check = commands.add_parser("check")
    check.add_argument("policy", choices=("careful", "freeze"))
    check.add_argument("--project", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if os.name != "nt":
        if args.command == "check":
            _emit(_decision(args.policy))
            return 0
        sys.stderr.write("safety runtime state update failed\n")
        return 2
    if args.command in {"set", "clear"}:
        if ((args.command == "set" and args.boundary is None)
                or (args.command == "clear" and args.boundary is not None)):
            sys.stderr.write("safety runtime state update failed\n")
            return 2
        try:
            _write_state(args.project, args.session,
                         args.boundary if args.command == "set" else None)
        except (OSError, ValueError, TypeError, UnicodeError, RecursionError,
                SafetyRuntimeError):
            sys.stderr.write("safety runtime state update failed\n")
            return 2
        return 0
    try:
        result = _check(args.policy, args.project)
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError,
            SafetyRuntimeError):
        result = _decision(args.policy)
    _emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
