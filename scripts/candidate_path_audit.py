#!/usr/bin/env python3
"""Flag unresolved local paths and unportable skill commands in a verified candidate.

This is a conservative static audit, not runtime dependency closure. Unresolved
paths need manual context review; they are not necessarily missing dependencies.
Dynamic commands, absolute host paths, imports and services are out of scope.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import posixpath
import re
import sys

import plugin_bundle
import skill_release as release

INLINE = re.compile(r"`([^`\r\n]+)`")
SAFE_REFERENCE = re.compile(r"[A-Za-z0-9._/-]{1,240}\Z")
LOCAL_PREFIXES = ("scripts/", "templates/", "references/", "./scripts/",
                  "./templates/", "./references/", "../")
COMMAND_START = re.compile(r"(?:^|`)[ \t]*(?:bash|python(?:3)?|node|pwsh|powershell)\b")
SOURCE_ROOT_ARG = re.compile(r"(?<![A-Za-z0-9_./-])(?:\./)?skills-src/[A-Za-z0-9_./-]+")
PROJECT_SKILL_ARG = re.compile(
    r"(?<![A-Za-z0-9_./-])(?:\./)?skills/[A-Za-z0-9_-]+/"
    r"(?:scripts|templates|references)/[A-Za-z0-9_./-]+")


def inspect_unportable_commands(skill_path: str, text: str) -> list[dict[str, object]]:
    """Report command locations only; never echo candidate command bodies."""
    rows = []
    for line_number, line in enumerate(text.splitlines(), 1):
        for match in COMMAND_START.finditer(line):
            command = line[match.end():].split("`", 1)[0]
            if SOURCE_ROOT_ARG.search(command):
                rows.append({"skill": skill_path, "line": line_number,
                             "reason": "source_checkout_command"})
                break
            if PROJECT_SKILL_ARG.search(command):
                rows.append({"skill": skill_path, "line": line_number,
                             "reason": "project_relative_skill_command"})
                break
    return rows


def inspect_skill_references(skill_path: str, text: str, available: set[str]) -> list[dict[str, object]]:
    """Resolve only explicit local references against the same plugin's file list."""
    parts = skill_path.split("/")
    if len(parts) != 5 or parts[0] != "plugins" or parts[2] != "skills" or parts[4] != "SKILL.md":
        raise ValueError("Expected a plugin skill entrypoint")
    boundary = f"plugins/{parts[1]}/"
    seen: set[str] = set()
    rows = []
    for match in INLINE.finditer(text):
        tokens = match.group(1).split()
        if not tokens:
            continue
        reference = tokens[0].split("#", 1)[0]
        if (not reference.startswith(LOCAL_PREFIXES) or reference in {"../", "./"}
                or not SAFE_REFERENCE.fullmatch(reference)
                or not posixpath.splitext(reference)[1]):
            continue
        if reference in seen:
            continue
        seen.add(reference)
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(skill_path), reference))
        if not resolved.startswith(boundary):
            status = "outside-plugin"
        elif resolved in available:
            status = "present"
        else:
            status = "unresolved"
        row: dict[str, object] = {"reference": reference, "resolved": resolved, "status": status}
        if status == "unresolved":
            # A basename match is a review hint, never proof that a relative path works.
            basename = posixpath.basename(resolved)
            alternatives = sorted(path for path in available
                                  if path.startswith(boundary) and posixpath.basename(path) == basename)
            if alternatives:
                row["possible_targets"] = alternatives[:5]
        rows.append(row)
    return rows


def audit_candidate(root: Path, expected_digest: str) -> dict:
    """Verify bytes first; report static refs without executing candidate code."""
    root = release.no_links(root)
    receipt = plugin_bundle.verify_bundle(root, expected_digest)
    records = {item["path"]: item for item in receipt["files"]}
    available = set(records)
    rows = []
    unportable_commands = []
    checked = 0
    for path in sorted(available):
        if not re.fullmatch(r"plugins/[^/]+/skills/[^/]+/SKILL\.md", path):
            continue
        checked += 1
        data = release.read_file(release.safe_member(root, path))
        if len(data) != records[path]["size"] or release.digest(data) != records[path]["sha256"]:
            raise ValueError("Skill changed after candidate verification")
        text = data.decode("utf-8")
        for row in inspect_skill_references(path, text, available):
            rows.append({"skill": path, **row})
        unportable_commands.extend(inspect_unportable_commands(path, text))
    unresolved = [row for row in rows if row["status"] != "present"]
    return {"status": "incomplete" if unresolved or unportable_commands else "static_paths_present",
            "bundle_digest": expected_digest, "skills_checked": checked,
            "static_refs_checked": len(rows), "unresolved": unresolved,
            "unportable_commands": unportable_commands,
            "runtime_closure_verified": False,
            "scope": "literal ASCII backtick paths and source/project-relative skill command locations; "
                     "findings need manual review; no execution, imports, host paths or services"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--expected-digest", required=True)
    args = parser.parse_args(argv)
    try:
        report = audit_candidate(args.package, args.expected_digest)
    except (ValueError, OSError, UnicodeError, KeyError, TypeError):
        # Avoid echoing untrusted candidate metadata, paths or secret-like text.
        print('{"status":"blocked","message":"Candidate path audit failed"}', file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["unresolved"] or report["unportable_commands"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
