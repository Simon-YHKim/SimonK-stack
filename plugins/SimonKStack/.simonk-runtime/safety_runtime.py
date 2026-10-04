#!/usr/bin/env python3
"""Windows-only bridge for SimonK's unchanged Bash safety leaves.

The bridge owns only a local project/session state namespace and a bounded
leaf process tree.  It does not authenticate the caller, activate host hooks,
execute tool commands, or make a candidate install-ready.  The leaf starts
suspended inside its own Windows Job Object, so a timeout, any other exit path
or the bridge's own death kills the whole tree: Git for Windows' bin/bash.exe
launcher, the real usr/bin/bash.exe it starts, and every descendant (freeze
0.2.5).  Atomic replacement assumes one same-user writer for a project/session
key; concurrent writers are outside this deliberately small v1 contract.

Decisions (hub decision D-62 follow-up 5): a leaf's own decision passes
through unchanged with its reason -- `{}` allow, careful `ask`, careful or
freeze `deny` (careful 0.2.2 denies HIGH commands and its own failures; freeze
denies outside the boundary and whatever it cannot judge). Anything the bridge
itself cannot do or read (no Git Bash, bad state, bad or oversized leaf output,
timeout) is a fail-closed `deny`; it is never downgraded to `ask`. A timeout
deny says so and that retrying is safe: it is not a verdict on the command.
On any OS other than Windows every check is a deliberate `deny` whose reason
says the runtime is Windows-only and how to get out (D-76 step 4).
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
import time
from typing import Any


SCHEMA_VERSION = 1
MAX_INPUT = 1024 * 1024
MAX_OUTPUT = 64 * 1024
# One wall-clock budget, in seconds, for a whole check: every cygpath call and
# the leaf share it, so a check never waits longer than this before it denies.
# Measured 2026-10-04 on the reference Windows PC (12 threads): the slowest
# whole check took 2.8 s with three test suites running and 14.7 s with six,
# where 14 of 90 leaf runs exceeded the old 5 s per-process limit. 20 s covers
# that with margin and stays far below the host's 600 s hook limit, past which
# a timed-out PreToolUse hook would not block the tool call at all.
CHECK_TIMEOUT = 20
# After the leaf tree is killed, wait at most this long (seconds, outside the
# check budget) for its processes to be gone before the check returns.
REAP_TIMEOUT = 5
CREATE_SUSPENDED = 0x00000004  # Windows process creation flag.
SESSION_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z", re.ASCII)
REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
# careful-powershell runs the careful leaf in its deny-only PowerShell-tool
# mode (leaf argument "powershell", careful 0.2.2).
POLICIES = ("careful", "careful-powershell", "freeze")
# Decisions a leaf may emit besides `{}`. Anything else is invalid output.
LEAF_DECISIONS = {
    "careful": ("ask", "deny"),
    "careful-powershell": ("ask", "deny"),
    "freeze": ("deny",),
}


# Non-Windows hosts (D-76 step 4): the runtime supports Windows only, so every
# check is denied on purpose. The reason says so and names the way out; Python,
# Git Bash or Node repairs would not help there. The plugin's shell-form guard
# hook (scripts/plugin_bundle.py NON_WINDOWS_REASONS) gives the same reasons
# byte for byte when no Python is on PATH at all.
NON_WINDOWS_REASONS = {
    "careful": (
        "[careful][WINDOWS ONLY] The SimonK safety runtime supports Windows only, "
        "so on this OS every Bash and PowerShell command is blocked on purpose "
        "(fail closed). This is not a verdict on the command. Way out: start a "
        "new session without /careful and /guard, or run /plugin disable "
        "simonk-core@simonk-stack (for /careful) or /plugin disable "
        "simonk-stack@simonk-stack (for /guard) and then start a new session."),
    "freeze": (
        "[freeze][WINDOWS ONLY] The SimonK safety runtime supports Windows only, "
        "so on this OS every Edit and Write is blocked on purpose (fail closed). "
        "This is not a verdict on the edit. /unfreeze cannot lift it here: the "
        "boundary state it clears exists only on Windows. Way out: start a new "
        "session without /freeze, /guard and /investigate, or run /plugin disable "
        "simonk-stack@simonk-stack and then start a new session."),
}


class SafetyRuntimeError(Exception):
    """Expected validation/runtime failure whose details must not escape."""


class SafetyRuntimeTimeout(SafetyRuntimeError):
    """The check ran out of its CHECK_TIMEOUT budget before the leaf decided."""


def _decision(policy: str, *, timed_out: bool = False) -> dict[str, Any]:
    """Fail-closed decision for a check the runtime itself could not complete."""
    if timed_out:
        reason = (f"[freeze] Safety check timed out after {CHECK_TIMEOUT} s; edit "
                  "blocked, fail closed. Nothing was written and this is not a "
                  "verdict on the edit, so retrying is safe."
                  if policy == "freeze"
                  else f"[careful][RUNTIME TIMEOUT] Safety check did not finish within "
                       f"{CHECK_TIMEOUT} s, so the command was blocked (fail closed) "
                       "and not run. This is not a verdict on the command; retrying "
                       "is safe. If it keeps timing out, the machine is overloaded "
                       "or the plugin safety runtime is stuck.")
    else:
        reason = ("[freeze] Safety runtime unavailable; blocked, fail closed."
                  if policy == "freeze"
                  else "[careful][RUNTIME FAILURE] Safety runtime failed, command not "
                       "checked, so it is blocked (fail closed). Way out: repair the "
                       "plugin safety runtime (Python, Git Bash and Node on PATH), or "
                       "start a new session without /careful.")
    return _deny(reason)


def _non_windows_decision(policy: str) -> dict[str, Any]:
    """Deliberate deny on a host the runtime does not support."""
    return _deny(NON_WINDOWS_REASONS["freeze" if policy == "freeze" else "careful"])


def _deny(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
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


def _remaining(deadline: float) -> float:
    """Seconds left in this check's budget; a spent budget is a timeout."""
    left = deadline - time.monotonic()
    if left <= 0:
        raise SafetyRuntimeTimeout
    return left


def _cygpath(cygpath: Path, native: str, deadline: float) -> str:
    try:
        result = subprocess.run(
            [str(cygpath), "-u", native],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=_remaining(deadline),
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise SafetyRuntimeTimeout from None
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
                      plugin_data: Path | None, deadline: float) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items()
           if key.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP"}}
    paths = [bash.parent.parent / "usr/bin", bash.parent.parent / "mingw64/bin"]
    node = _find_node()
    if node is not None:
        paths.append(node.parent)
    posix_private = _cygpath(cygpath, str(private_root), deadline)
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
        env["CLAUDE_PLUGIN_DATA"] = _cygpath(cygpath, str(plugin_data), deadline)
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


class _LeafJob:
    """Unnamed Windows Job Object that owns one leaf's whole process tree.

    Git for Windows' bin/bash.exe is a launcher that runs usr/bin/bash.exe as
    its child, so killing only the started process left the real shell running
    (2026-10-05: six leaf shells were still busy-looping 8 hours after timeout
    tests).  The leaf starts suspended and joins this job before its first
    instruction, so every descendant is born inside it; no breakaway is
    allowed.  KILL_ON_JOB_CLOSE also kills the tree if the bridge itself dies.
    Documented APIs only:
    https://learn.microsoft.com/windows/win32/procthread/job-objects
    """

    def __init__(self) -> None:
        self._handle = None
        try:
            from ctypes import wintypes
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        except (AttributeError, ImportError, OSError, ValueError) as exc:
            raise SafetyRuntimeError from exc
        handle, dword, bool_ = wintypes.HANDLE, wintypes.DWORD, wintypes.BOOL
        for name, argtypes, restype in (
            ("CreateJobObjectW", (ctypes.c_void_p, wintypes.LPCWSTR), handle),
            ("SetInformationJobObject",
             (handle, ctypes.c_int, ctypes.c_void_p, dword), bool_),
            ("QueryInformationJobObject",
             (handle, ctypes.c_int, ctypes.c_void_p, dword, ctypes.c_void_p), bool_),
            ("AssignProcessToJobObject", (handle, handle), bool_),
            ("TerminateJobObject", (handle, wintypes.UINT), bool_),
            ("OpenProcess", (dword, bool_, dword), handle),
            ("CreateToolhelp32Snapshot", (dword, dword), handle),
            ("Thread32First", (handle, ctypes.c_void_p), bool_),
            ("Thread32Next", (handle, ctypes.c_void_p), bool_),
            ("OpenThread", (dword, bool_, dword), handle),
            ("ResumeThread", (handle,), dword),
            ("CloseHandle", (handle,), bool_),
        ):
            function = getattr(kernel32, name)
            function.argtypes, function.restype = argtypes, restype
        self._kernel32 = kernel32

        class BasicLimits(ctypes.Structure):  # JOBOBJECT_BASIC_LIMIT_INFORMATION
            _fields_ = [("per_process_user_time", ctypes.c_int64),
                        ("per_job_user_time", ctypes.c_int64),
                        ("limit_flags", dword),
                        ("minimum_working_set", ctypes.c_size_t),
                        ("maximum_working_set", ctypes.c_size_t),
                        ("active_process_limit", dword),
                        ("affinity", ctypes.c_size_t),
                        ("priority_class", dword),
                        ("scheduling_class", dword)]

        class ExtendedLimits(ctypes.Structure):  # JOBOBJECT_EXTENDED_LIMIT_INFORMATION
            _fields_ = [("basic", BasicLimits), ("io", ctypes.c_uint64 * 6),
                        ("memory", ctypes.c_size_t * 4)]

        class Accounting(ctypes.Structure):  # JOBOBJECT_BASIC_ACCOUNTING_INFORMATION
            _fields_ = [("times", ctypes.c_int64 * 4), ("page_faults", dword),
                        ("total_processes", dword), ("active_processes", dword),
                        ("terminated_processes", dword)]

        class ThreadEntry(ctypes.Structure):  # THREADENTRY32
            _fields_ = [("size", dword), ("usage", dword), ("thread_id", dword),
                        ("owner_pid", dword), ("base_priority", wintypes.LONG),
                        ("delta_priority", wintypes.LONG), ("flags", dword)]

        self._accounting, self._thread_entry = Accounting, ThreadEntry
        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            raise SafetyRuntimeError
        self._handle = job
        limits = ExtendedLimits()
        limits.basic.limit_flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel32.SetInformationJobObject(  # JobObjectExtendedLimitInformation
                job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            self.close()
            raise SafetyRuntimeError

    def adopt(self, process: subprocess.Popen) -> None:
        """Put a CREATE_SUSPENDED leaf into the job, then let it run."""
        kernel32 = self._kernel32
        # PROCESS_SET_QUOTA | PROCESS_TERMINATE, as AssignProcessToJobObject needs.
        target = kernel32.OpenProcess(0x0100 | 0x0001, False, process.pid)
        if not target:
            raise SafetyRuntimeError
        try:
            if not kernel32.AssignProcessToJobObject(self._handle, target):
                raise SafetyRuntimeError
        finally:
            kernel32.CloseHandle(target)
        snapshot = kernel32.CreateToolhelp32Snapshot(0x4, 0)  # TH32CS_SNAPTHREAD
        if not snapshot or snapshot == ctypes.c_void_p(-1).value:
            raise SafetyRuntimeError
        resumed = False
        try:
            entry = self._thread_entry()
            entry.size = ctypes.sizeof(entry)
            found = kernel32.Thread32First(snapshot, ctypes.byref(entry))
            while found:
                if entry.owner_pid == process.pid:
                    thread = kernel32.OpenThread(0x0002, False, entry.thread_id)  # THREAD_SUSPEND_RESUME
                    if thread:
                        try:
                            # CREATE_SUSPENDED left the initial thread at count 1.
                            resumed = kernel32.ResumeThread(thread) == 1 or resumed
                        finally:
                            kernel32.CloseHandle(thread)
                entry.size = ctypes.sizeof(entry)
                found = kernel32.Thread32Next(snapshot, ctypes.byref(entry))
        finally:
            kernel32.CloseHandle(snapshot)
        if not resumed:
            raise SafetyRuntimeError

    def kill(self) -> None:
        """Kill every process in the tree; wait, bounded, until none is left."""
        if not self._handle:
            return
        kernel32 = self._kernel32
        kernel32.TerminateJobObject(self._handle, 1)
        deadline = time.monotonic() + REAP_TIMEOUT
        info = self._accounting()
        while (kernel32.QueryInformationJobObject(  # JobObjectBasicAccountingInformation
                   self._handle, 1, ctypes.byref(info), ctypes.sizeof(info), None)
               and info.active_processes and time.monotonic() < deadline):
            time.sleep(0.01)

    def close(self) -> None:
        """Kill whatever is still in the tree, then release the job."""
        if self._handle:
            try:
                self.kill()
            finally:
                self._kernel32.CloseHandle(self._handle)
                self._handle = None


def _run_leaf(policy: str, payload: dict[str, Any], boundary: str | None,
              deadline: float) -> dict[str, Any]:
    runtime = Path(__file__).resolve(strict=True).parent
    bash, cygpath = _locate_bash()
    helper = (runtime / "freeze/bin/check-freeze.sh" if policy == "freeze"
              else runtime / "careful/bin/check-careful.sh")
    leaf_args = ["powershell"] if policy == "careful-powershell" else []
    helper = _safe_resource(helper)
    _safe_resource(runtime / "careful/bin/hook-extract.sh")

    translated = dict(payload)
    translated["tool_input"] = dict(payload["tool_input"])
    if policy == "freeze":
        native = _tool_path(translated["cwd"], translated["tool_input"].get("file_path"))
        translated["tool_input"]["file_path"] = _cygpath(cygpath, str(native), deadline)

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
            posix_boundary = _cygpath(cygpath, boundary, deadline).rstrip("/") + "/"
            (plugin_data / "freeze-dir.txt").write_text(posix_boundary + "\n", encoding="utf-8")
        env = _hook_environment(bash, cygpath, private, plugin_data, deadline)
        posix_helper = _cygpath(cygpath, str(helper), deadline)
        # No job, no leaf: an uncontained leaf could outlive its timeout.
        job = _LeafJob()
        try:
            with tempfile.TemporaryFile() as output:
                # Take the budget before starting the leaf, so a spent budget
                # never leaves a started process behind.
                timeout = _remaining(deadline)
                process = subprocess.Popen(
                    [str(bash), "--noprofile", "--norc", posix_helper, *leaf_args],
                    stdin=subprocess.PIPE,
                    stdout=output,
                    stderr=subprocess.DEVNULL,
                    cwd=translated["cwd"],
                    env=env,
                    creationflags=CREATE_SUSPENDED,
                )
                try:
                    job.adopt(process)
                except SafetyRuntimeError:
                    process.kill()  # Still suspended, so it has started nothing.
                    process.communicate()
                    raise
                try:
                    process.communicate(encoded, timeout=timeout)
                except subprocess.TimeoutExpired:
                    job.kill()  # The launcher, the real bash and all descendants.
                    process.communicate()
                    raise SafetyRuntimeTimeout from None
                if process.returncode != 0 or output.tell() > MAX_OUTPUT:
                    raise SafetyRuntimeError
                output.seek(0)
                raw_output = output.read(MAX_OUTPUT + 1)
        except (OSError, subprocess.SubprocessError) as exc:
            raise SafetyRuntimeError from exc
        finally:
            job.close()  # Also kills anything the leaf left running on exit.
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
    # Pass the leaf's decision and reason through unchanged; never downgrade a
    # deny. Tuple membership compares with ==, so a non-string value is just
    # invalid output (fail-closed deny), not a TypeError.
    if (not isinstance(hook, dict)
            or set(hook) != {"hookEventName", "permissionDecision",
                             "permissionDecisionReason"}
            or hook.get("hookEventName") != "PreToolUse"
            or hook.get("permissionDecision") not in LEAF_DECISIONS[policy]
            or not isinstance(hook.get("permissionDecisionReason"), str)
            or not hook["permissionDecisionReason"]):
        raise SafetyRuntimeError
    return result


def _check(policy: str, project_raw: str) -> dict[str, Any]:
    deadline = time.monotonic() + CHECK_TIMEOUT
    project = _canonical_directory(project_raw)
    payload = _read_hook_input()
    session = payload["session_id"]
    if policy != "freeze":
        return _run_leaf(policy, payload, None, deadline)
    state = _load_state(project, session)
    if state["status"] == "inactive":
        return {}
    return _run_leaf(policy, payload, state["boundary"], deadline)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SimonK candidate safety runtime")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("set", "clear"):
        command = commands.add_parser(name)
        command.add_argument("--project", required=True)
        command.add_argument("--session", required=True)
        command.add_argument("--boundary")
    check = commands.add_parser("check")
    check.add_argument("policy", choices=POLICIES)
    check.add_argument("--project", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if os.name != "nt":
        if args.command == "check":
            _emit(_non_windows_decision(args.policy))
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
        if args.command == "clear":
            # Same line as the flat writer (freeze-state.sh clear), which /unfreeze documents.
            print("FREEZE_CLEARED: user-requested edit boundary removal completed.")
        return 0
    try:
        result = _check(args.policy, args.project)
    except SafetyRuntimeTimeout:
        result = _decision(args.policy, timed_out=True)
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError,
            SafetyRuntimeError):
        result = _decision(args.policy)
    _emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
