#!/usr/bin/env python3
"""Compare a verified candidate with existing flat skills without modifying either.

Only candidate-named direct skill directories are read. Junctions/symlinks are
reported and preserved, never traversed. This is byte/path coverage, not a
behavior, ownership, installation or safe-to-replace decision.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import islice
import json
import os
from pathlib import Path
import re
import stat
import sys

import plugin_bundle
import skill_release as release

NAME = re.compile(r"[a-z][a-z0-9-]*\Z")
MAX_SKILL_FILES = 512
MAX_SKILL_ENTRIES = 1024
MAX_SKILL_BYTES = 32 * 1024 * 1024
STATUSES = ("matched", "drifted", "missing", "linked_preserved", "excluded", "unsafe")


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(path))


def _excluded(path: Path, exclusions: tuple[Path, ...]) -> bool:
    path = _absolute(path)
    return any(path == item or path.is_relative_to(item) for item in exclusions)


def _reparse(mode) -> bool:
    return stat.S_ISLNK(mode.st_mode) or bool(getattr(mode, "st_file_attributes", 0) & 0x400)


def _candidate_members(manifest: dict) -> dict[str, tuple[str, dict[str, str]]]:
    owners = manifest["owners"]
    rows = manifest["files"]
    if not isinstance(owners, dict) or not isinstance(rows, list):
        raise ValueError("Invalid verified candidate skill index")
    result = {}
    for name, owner in sorted(owners.items()):
        if not isinstance(name, str) or not NAME.fullmatch(name) or not isinstance(owner, str):
            raise ValueError("Invalid verified candidate owner")
        prefix = f"plugins/{owner}/skills/{name}/"
        members = {entry["path"][len(prefix):]: entry["sha256"] for entry in rows
                   if entry["path"].startswith(prefix)}
        if "SKILL.md" not in members or not members:
            raise ValueError("Verified candidate skill is incomplete")
        result[name] = (owner, members)
    return result


def _direct_members(folder: Path) -> dict[str, str]:
    """Hash regular files without following any nested link or reading siblings."""
    found: dict[str, str] = {}
    stack = [folder]
    total_bytes = 0
    entries = 0
    while stack:
        current = stack.pop()
        remaining = MAX_SKILL_ENTRIES - entries
        children = list(islice(current.iterdir(), remaining + 1))
        if len(children) > remaining:
            raise ValueError("Skill entry limit exceeded")
        entries += len(children)
        for member in sorted(children, key=lambda p: p.name):
            info = member.lstat()
            if _reparse(info):
                raise ValueError("Nested link/reparse point")
            if stat.S_ISDIR(info.st_mode):
                stack.append(member)
                continue
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("Non-regular skill member")
            if len(found) >= MAX_SKILL_FILES or info.st_size > release.MAX_FILE:
                raise ValueError("Skill file-count or per-file size limit exceeded")
            rel = member.relative_to(folder).as_posix()
            if rel in found:
                raise ValueError("Duplicate skill member")
            data = release.read_file(member)
            total_bytes += len(data)
            if total_bytes > MAX_SKILL_BYTES:
                raise ValueError("Skill byte limit exceeded")
            found[rel] = release.digest(data)
    return found


def audit(bundle: Path, expected_digest: str, installed_roots: list[Path],
          excluded_roots=()) -> dict:
    bundle = Path(bundle)
    manifest = plugin_bundle.verify_bundle(bundle, expected_digest)
    candidate = _candidate_members(manifest)
    exclusions = tuple(_absolute(Path(item)) for item in excluded_roots)
    # Resolve only exclusion path metadata; never open any excluded directory.
    exclusions += tuple(item.resolve(strict=False) for item in exclusions)
    if not installed_roots:
        raise ValueError("At least one explicit installed flat root is required")
    roots = []
    seen = set()
    for raw in installed_roots:
        root = _absolute(Path(raw))
        if _excluded(root, exclusions):
            raise ValueError("Installed root is excluded")
        root = release.no_links(root)
        if not root.is_dir():
            raise ValueError("Installed flat root is missing")
        key = os.path.normcase(str(root))
        if key in seen:
            raise ValueError("Duplicate installed root")
        seen.add(key)
        roots.append(root)

    rows = []
    counts = Counter()
    for root in roots:
        for name, (owner, expected) in candidate.items():
            folder = root / name
            row = {"root": str(root), "name": name, "owner": owner}
            if _excluded(folder, exclusions):
                row["status"] = "excluded"
            elif not os.path.lexists(folder):
                row["status"] = "missing"
            else:
                info = folder.lstat()
                if _reparse(info):
                    # Resolution is metadata only. Never inspect the target's files.
                    target = folder.resolve(strict=False)
                    row["status"] = "excluded" if _excluded(target, exclusions) else "linked_preserved"
                    if row["status"] == "linked_preserved":
                        row["target"] = str(target)
                elif not stat.S_ISDIR(info.st_mode):
                    row["status"] = "unsafe"
                    row["reason"] = "not_a_directory"
                else:
                    try:
                        observed = _direct_members(folder)
                    except (OSError, ValueError) as exc:
                        row["status"] = "unsafe"
                        row["reason"] = type(exc).__name__
                    else:
                        changed = sorted(key for key in expected.keys() & observed.keys()
                                         if expected[key] != observed[key])
                        missing = sorted(expected.keys() - observed.keys())
                        extra = sorted(observed.keys() - expected.keys())
                        row.update(files=len(observed), changed=changed,
                                   missing_files=missing, extra_files=extra)
                        row["status"] = "drifted" if changed or missing or extra else "matched"
            counts[row["status"]] += 1
            rows.append(row)
    summary = {status: counts[status] for status in STATUSES}
    scope_complete = not any(counts[key] for key in ("linked_preserved", "excluded", "unsafe"))
    return {"schema_version": 1, "status": "matched" if counts["matched"] == len(rows) else "gaps",
            "candidate_bundle_sha256": expected_digest, "candidate_skills": len(candidate),
            "installed_roots": [str(root) for root in roots],
            "hash_scope": "relative paths and full bytes of regular files in direct skill directories",
            "linked_targets_read": False, "unrelated_skills_read": False,
            "package_evaluated": scope_complete, "behavior_evaluated": False,
            "scope_complete": scope_complete,
            "summary": summary, "rows": rows}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--expected-digest", required=True)
    parser.add_argument("--root", type=Path, action="append", required=True)
    parser.add_argument("--exclude-root", type=Path, action="append", default=[])
    args = parser.parse_args(argv)
    try:
        result = audit(args.bundle, args.expected_digest, args.root, args.exclude_root)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"schema_version": 1, "status": "error",
                          "reason": type(exc).__name__}, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "matched" else 2


if __name__ == "__main__":
    sys.exit(main())
