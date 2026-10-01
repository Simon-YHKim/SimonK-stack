"""Recoverable flat-link switch for isolated Windows rehearsal profiles only.

No CLI, native plugin installer, or user-profile apply path is supplied. A
separate release decision is required before adapting this for real profiles.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile

import vibe_host_preflight as preflight


class TransitionError(ValueError):
    pass


HEX = re.compile(r"[0-9a-f]{64}\Z")
JOURNAL_NAME = "vibe-flat-transition.json"
MAX_JOURNAL_BYTES = 32 * 1024
NAMES = (("claude", preflight.CLAUDE_NAMES, "candidate-safety"),
         ("codex", preflight.CODEX_NAMES, "codex-subset-safety"))


def _digest(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise TransitionError("SKILL_BYTES_UNREADABLE") from exc


def _same(left: Path | None, right: Path) -> bool:
    return left is not None and os.path.normcase(str(left.absolute())) == os.path.normcase(
        str(right.absolute()))


def _fingerprint(plan: dict) -> str:
    data = {key: value for key, value in plan.items() if key != "plan_digest"}
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _preflight(plan: dict, native_snapshot: dict) -> None:
    result = preflight.scan(Path(plan["candidate_root"]), Path(plan["current_root"]),
                            Path(plan["claude_root"]), Path(plan["codex_root"]),
                            Path(plan["agents_root"]), native_snapshot=native_snapshot,
                            candidate_pins=plan["pins"])
    if (result.get("status") != "host_snapshot_complete" or result.get("issues")
            or result.get("checked_links") != 8
            or result.get("candidate_bytes_verified") is not True
            or result.get("native_plugin_coverage", {}).get("status") != "metadata_matched"):
        raise TransitionError("HOST_OR_NATIVE_PLUGINS_NOT_READY")


def _alias(plan: dict) -> None:
    alias = Path(plan["agents_root"]) / "skills/vibe"
    expected = Path(plan["claude_root"]) / "skills/vibe"
    if not alias.is_symlink() or not _same(preflight._direct_target(alias), expected):
        raise TransitionError("AGENTS_ALIAS_CHANGED")


def _expected(plan: dict) -> list[dict]:
    run_id = "vibe-" + plan["pins"]["candidate-safety"][:12]
    entries = []
    for host, names, package in NAMES:
        root = Path(plan[host + "_root"])
        for name in names:
            entries.append({
                "host": host, "name": name,
                "link": str(root / "skills" / name),
                "archive": str(root / "flat-link-archive" / run_id / name),
                "quarantine": str(root / "flat-link-quarantine" / run_id / name),
                "old_target": str(Path(plan["current_root"]) / package /
                                  "plugins/SimonKCore/skills" / name),
                "new_target": str(Path(plan["candidate_root"]) / package /
                                  "plugins/SimonKCore/skills" / name),
            })
    return entries


def _validate(plan: dict) -> None:
    keys = {"schema_version", "scope", "candidate_root", "current_root", "claude_root",
            "codex_root", "agents_root", "pins", "entries", "plan_digest"}
    if not isinstance(plan, dict) or set(plan) != keys:
        raise TransitionError("PLAN_SHAPE_INVALID")
    if (type(plan["schema_version"]) is not int or plan["schema_version"] != 1
            or plan["scope"] != "isolated-flat-rehearsal"
            or not isinstance(plan["pins"], dict) or set(plan["pins"]) != preflight.PIN_NAMES
            or any(not isinstance(value, str) or not HEX.fullmatch(value)
                   for value in plan["pins"].values())
            or not isinstance(plan["entries"], list) or len(plan["entries"]) != 7
            or not isinstance(plan["plan_digest"], str)
            or plan["plan_digest"] != _fingerprint(plan)):
        raise TransitionError("PLAN_CHANGED")
    for key in ("candidate_root", "current_root", "claude_root", "codex_root", "agents_root"):
        path = plan[key]
        if not isinstance(path, str) or not Path(path).is_absolute():
            raise TransitionError("PLAN_ROOT_INVALID")
    for entry, expected in zip(plan["entries"], _expected(plan)):
        if (not isinstance(entry, dict) or set(entry) != set(expected) | {"old_sha256", "new_sha256"}
                or any(entry.get(key) != value for key, value in expected.items())
                or any(not isinstance(entry.get(key), str) or not HEX.fullmatch(entry[key])
                       for key in ("old_sha256", "new_sha256"))):
            raise TransitionError("PLAN_LINK_CHANGED")


def _isolated(plan: dict, isolated_root: Path) -> None:
    root = _journal_path(isolated_root).parent
    for key in ("candidate_root", "current_root", "claude_root", "codex_root", "agents_root"):
        child = Path(plan[key]).absolute()
        if child.parent != root or preflight._is_directory_link(child):
            raise TransitionError("OUTSIDE_ISOLATED_ROOT")
    for host in ("claude", "codex", "agents"):
        _plain_ancestors(Path(plan[host + "_root"]) / "skills", root)
    for entry in plan["entries"]:
        for key in ("old_target", "new_target"):
            _plain_ancestors(Path(entry[key]), root)
        for key in ("archive", "quarantine"):
            _plain_ancestors(Path(entry[key]).parent, root)


def _journal_path(isolated_root: Path) -> Path:
    if os.name != "nt":
        raise TransitionError("WINDOWS_REHEARSAL_ONLY")
    root = Path(isolated_root).absolute()
    temp = Path(tempfile.gettempdir()).absolute()
    if (root.parent != temp or not root.name.startswith("vibe-flat-test-")
            or not root.is_dir() or preflight._is_directory_link(root)):
        raise TransitionError("ISOLATED_ROOT_REQUIRED")
    return root / JOURNAL_NAME


def _plain_ancestors(path: Path, root: Path) -> None:
    try:
        parts = path.absolute().relative_to(root).parts
    except ValueError as exc:
        raise TransitionError("OUTSIDE_ISOLATED_ROOT") from exc
    current = root
    for part in parts:
        current = current / part
        if os.path.lexists(current) and preflight._is_directory_link(current):
            raise TransitionError("REPARSE_PARENT_UNSAFE")


def _link_target(path: Path) -> Path | None:
    if not os.path.lexists(path):
        return None
    if not preflight._is_directory_link(path):
        raise TransitionError("NON_LINK_COLLISION")
    return preflight._direct_target(path)


def _old_ready(entry: dict) -> None:
    link = Path(entry["link"])
    old = Path(entry["old_target"])
    new = Path(entry["new_target"])
    if (not _same(_link_target(link), old)
            or _digest(link / "SKILL.md") != entry["old_sha256"]
            or _digest(new / "SKILL.md") != entry["new_sha256"]
            or os.path.lexists(entry["archive"]) or os.path.lexists(entry["quarantine"])):
        raise TransitionError("LINK_STATE_CHANGED")


def prepare_plan(candidate: Path, current: Path, claude: Path, codex: Path,
                 agents: Path, pins: dict, native_snapshot: dict) -> dict:
    plan = {"schema_version": 1, "scope": "isolated-flat-rehearsal",
            "candidate_root": str(Path(candidate).absolute()),
            "current_root": str(Path(current).absolute()),
            "claude_root": str(Path(claude).absolute()),
            "codex_root": str(Path(codex).absolute()),
            "agents_root": str(Path(agents).absolute()),
            "pins": dict(pins), "entries": []}
    if set(plan["pins"]) != preflight.PIN_NAMES:
        raise TransitionError("CANDIDATE_PINS_REQUIRED")
    _preflight(plan, native_snapshot)
    _alias(plan)
    for entry in _expected(plan):
        old = Path(entry["old_target"])
        link = Path(entry["link"])
        if not _same(_link_target(link), old):
            raise TransitionError("LINK_STATE_CHANGED")
        entry["old_sha256"] = _digest(link / "SKILL.md")
        entry["new_sha256"] = _digest(Path(entry["new_target"]) / "SKILL.md")
        if os.path.lexists(entry["archive"]) or os.path.lexists(entry["quarantine"]):
            raise TransitionError("ARCHIVE_COLLISION")
        plan["entries"].append(entry)
    plan["plan_digest"] = _fingerprint(plan)
    _validate(plan)
    return plan


def _private_parent(path: Path, root: Path) -> None:
    parent = path.parent
    if parent.parent.parent != root:
        raise TransitionError("ARCHIVE_OUTSIDE_HOST")
    for part in (parent.parent, parent):
        if os.path.lexists(part) and (not part.is_dir() or preflight._is_directory_link(part)):
            raise TransitionError("ARCHIVE_PARENT_UNSAFE")
        part.mkdir(exist_ok=True)


def _write_journal(plan: dict, isolated_root: Path) -> None:
    path = _journal_path(isolated_root)
    payload = json.dumps(plan, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    if len(payload) > MAX_JOURNAL_BYTES:
        raise TransitionError("JOURNAL_TOO_LARGE")
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as exc:
        raise TransitionError("JOURNAL_EXISTS_OR_UNWRITABLE") from exc
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())
    except OSError as exc:
        # A partial journal is retained for inspection; no link has moved yet.
        raise TransitionError("JOURNAL_NOT_DURABLE") from exc


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate journal key")
        result[key] = value
    return result


def recover_isolated(isolated_root: Path) -> None:
    """Restore an interrupted isolated switch using its pre-move disk journal."""
    path = _journal_path(isolated_root)
    try:
        info = path.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or info.st_size == 0 or info.st_size > MAX_JOURNAL_BYTES):
            raise TransitionError("JOURNAL_UNSAFE")
        plan = json.loads(path.read_bytes().decode("utf-8"), object_pairs_hook=_unique_pairs)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        raise TransitionError("JOURNAL_UNREADABLE") from exc
    _validate(plan)
    _isolated(plan, isolated_root)
    rollback_isolated(plan, isolated_root)


def apply_isolated(plan: dict, isolated_root: Path, native_snapshot: dict) -> None:
    _validate(plan)
    _isolated(plan, isolated_root)
    _preflight(plan, native_snapshot)
    _alias(plan)
    for entry in plan["entries"]:
        _old_ready(entry)
    _write_journal(plan, isolated_root)
    try:
        for entry in plan["entries"]:
            root = Path(plan[entry["host"] + "_root"])
            archive = Path(entry["archive"])
            quarantine = Path(entry["quarantine"])
            _private_parent(archive, root)
            _private_parent(quarantine, root)
            _old_ready(entry)
            os.rename(entry["link"], archive)
            os.symlink(entry["new_target"], entry["link"], target_is_directory=True)
        for entry in plan["entries"]:
            link = Path(entry["link"])
            if (not _same(_link_target(link), Path(entry["new_target"]))
                    or _digest(link / "SKILL.md") != entry["new_sha256"]):
                raise TransitionError("NEW_LINK_VERIFICATION_FAILED")
        _alias(plan)
    except (OSError, TransitionError) as exc:
        try:
            rollback_isolated(plan, isolated_root)
        except (OSError, TransitionError) as recovery:
            raise TransitionError("LINK_SWITCH_AND_RECOVERY_FAILED") from recovery
        raise TransitionError("LINK_SWITCH_FAILED_RESTORED") from exc


def rollback_isolated(plan: dict, isolated_root: Path) -> None:
    _validate(plan)
    _isolated(plan, isolated_root)
    _alias(plan)
    # Validate every state before the first move, then recheck each at use.
    modes = [_rollback_mode(entry) for entry in plan["entries"]]
    for entry, mode in reversed(list(zip(plan["entries"], modes))):
        if _rollback_mode(entry) != mode:
            raise TransitionError("ROLLBACK_STATE_CHANGED")
        if mode == "already":
            continue
        link, archive, quarantine = map(Path, (entry["link"], entry["archive"],
                                               entry["quarantine"]))
        if mode == "new":
            os.rename(link, quarantine)
        os.rename(archive, link)
    for entry in plan["entries"]:
        link = Path(entry["link"])
        if (not _same(_link_target(link), Path(entry["old_target"]))
                or _digest(link / "SKILL.md") != entry["old_sha256"]):
            raise TransitionError("ROLLBACK_VERIFICATION_FAILED")
    _alias(plan)


def _rollback_mode(entry: dict) -> str:
    link, archive, quarantine = map(Path, (entry["link"], entry["archive"],
                                           entry["quarantine"]))
    current = _link_target(link)
    saved = _link_target(archive)
    old, new = Path(entry["old_target"]), Path(entry["new_target"])
    if saved is None and _same(current, old):
        if _digest(link / "SKILL.md") != entry["old_sha256"]:
            raise TransitionError("OLD_LINK_BYTES_CHANGED")
        return "already"
    if not _same(saved, old) or _digest(archive / "SKILL.md") != entry["old_sha256"]:
        raise TransitionError("OLD_LINK_NOT_RECOVERABLE")
    if current is None:
        if os.path.lexists(quarantine):
            if (not _same(_link_target(quarantine), new)
                    or _digest(quarantine / "SKILL.md") != entry["new_sha256"]):
                raise TransitionError("QUARANTINE_STATE_CHANGED")
        return "missing"
    if (not _same(current, new) or os.path.lexists(quarantine)
            or _digest(link / "SKILL.md") != entry["new_sha256"]):
        raise TransitionError("NEW_LINK_STATE_CHANGED")
    return "new"
