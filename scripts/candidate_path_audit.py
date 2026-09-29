#!/usr/bin/env python3
"""Flag unresolved local paths and unportable skill commands in a verified candidate.

This is a conservative static audit, not runtime dependency closure. Unresolved
paths need manual context review; they are not necessarily missing dependencies.
Gstack bin references are reported as external-runtime hints, not proof of
availability. Optional pinned-source evidence checks direct helper files only.
Literal backtick paths and simple Markdown link destinations are inspected in
SKILL.md and reachable Markdown references; dynamic commands, imports and
services remain out of scope.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import posixpath
import re
import sys

import gstack_source_inventory as gstack_inventory
import plugin_bundle
import skill_release as release

INLINE = re.compile(r"`([^`\r\n]+)`")
MARKDOWN_LINK = re.compile(r"\]\(([^)\r\n]+)\)")
SAFE_REFERENCE = re.compile(r"[A-Za-z0-9._/-]{1,240}\Z")
LOCAL_PREFIXES = ("scripts/", "templates/", "references/", "./scripts/",
                  "./templates/", "./references/", "assets/", "./assets/", "../")
COMMAND_START = re.compile(r"(?:^|`)[ \t]*(?:bash|python(?:3)?|node|pwsh|powershell)\b")
SOURCE_ROOT_ARG = re.compile(r"(?<![A-Za-z0-9_./-])(?:\./)?skills-src/[A-Za-z0-9_./-]+")
PROJECT_SKILL_ARG = re.compile(
    r"(?<![A-Za-z0-9_./-])(?:\./)?skills/[A-Za-z0-9_-]+/"
    r"(?:scripts|templates|references)/[A-Za-z0-9_./-]+")
GSTACK_BIN_REF = re.compile(r"(?:~/)?\.claude/skills/gstack/bin/[A-Za-z0-9._-]+")


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


def inspect_external_runtime_hints(skill_path: str, text: str) -> list[dict[str, str]]:
    """Report the affected skill, never executable text or alleged runtime state."""
    if GSTACK_BIN_REF.search(text):
        return [{"skill": skill_path, "reason": "gstack_bin_reference"}]
    return []


def inspect_pinned_gstack_targets(source_root: Path, expected_commit: str,
                                  targets: set[str]) -> dict:
    """Attest direct helper files in a separate pinned clone, never their behavior."""
    if not isinstance(targets, set) or len(targets) > 64 or any(
            not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9._-]+", name)
            or name in {".", ".."} for name in targets):
        raise ValueError("Invalid direct helper target set")
    if not targets:
        return {"status": "no_direct_targets", "present": 0, "missing": 0,
                "nonregular": 0, "source_inventory_verified": False,
                "runtime_closure_verified": False}
    root = release.no_links(Path(source_root))
    source = gstack_inventory.audit_source(root, expected_commit)
    records = {item["path"]: item for item in
               gstack_inventory._tree_records(root, expected_commit)}
    manifest = []
    present = missing = nonregular = 0
    for name in sorted(targets):
        path = f"bin/{name}"
        record = records.get(path)
        if record is None:
            missing += 1
            manifest.append({"path": path, "state": "missing"})
        elif record["mode"] not in gstack_inventory.REGULAR_MODES:
            nonregular += 1
            manifest.append({"path": path, "state": "nonregular"})
        else:
            data = release.read_file(release.safe_member(root, path))
            present += 1
            manifest.append({"path": path, "state": "present",
                             "raw_sha256": release.digest(data)})
    if gstack_inventory.audit_source(root, expected_commit) != source:
        raise ValueError("Gstack source changed during direct helper inspection")
    return {"status": "direct_targets_present" if present == len(targets)
            else "direct_targets_incomplete", "present": present, "missing": missing,
            "nonregular": nonregular, "source_inventory_verified": True,
            "source_commit": expected_commit, "source_tree_oid": source["tree_oid"],
            "source_manifest_sha256": source["raw_manifest_sha256"],
            "source_package_compatible": source["package_contract_compatible"],
            "target_manifest_sha256": release.digest(release.encoded(manifest)),
            "runtime_closure_verified": False}


def inspect_document_references(document_path: str, text: str,
                                available: set[str]) -> list[dict[str, object]]:
    """Resolve explicit local references in a skill or reachable Markdown file."""
    parts = document_path.split("/")
    if (len(parts) < 5 or parts[0] != "plugins" or parts[2] != "skills"
            or not parts[-1].endswith(".md")):
        raise ValueError("Expected a plugin skill Markdown document")
    boundary = f"plugins/{parts[1]}/"
    seen: set[str] = set()
    rows = []
    matches = sorted([*((match, True) for match in INLINE.finditer(text)),
                      *((match, False) for match in MARKDOWN_LINK.finditer(text))],
                     key=lambda item: item[0].start())
    skill_root = "/".join(parts[:4])
    for match, is_inline in matches:
        tokens = match.group(1).split()
        if not tokens:
            continue
        reference = tokens[0].split("#", 1)[0]
        if (not reference.startswith(LOCAL_PREFIXES) or reference in {"../", "./"}
                or not SAFE_REFERENCE.fullmatch(reference)
                or not posixpath.splitext(reference)[1]):
            continue
        # Prose code spans name skill-root resources; Markdown link destinations
        # are relative to the document containing the link.
        base = (skill_root if is_inline and reference.startswith(
            ("scripts/", "templates/", "references/", "assets/"))
            else posixpath.dirname(document_path))
        resolved = posixpath.normpath(posixpath.join(base, reference))
        if resolved in seen:
            continue
        seen.add(resolved)
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


def inspect_skill_references(skill_path: str, text: str,
                             available: set[str]) -> list[dict[str, object]]:
    """Compatibility entrypoint for direct SKILL.md reference inspection."""
    parts = skill_path.split("/")
    if len(parts) != 5 or parts[4] != "SKILL.md":
        raise ValueError("Expected a plugin skill entrypoint")
    return inspect_document_references(skill_path, text, available)


def audit_candidate(root: Path, expected_digest: str, *, gstack_source: Path | None = None,
                    gstack_commit: str | None = None) -> dict:
    """Verify bytes first; report static refs without executing candidate code."""
    if (gstack_source is None) != (gstack_commit is None):
        raise ValueError("Gstack source root and commit must be supplied together")
    root = release.no_links(root)
    receipt = plugin_bundle.verify_bundle(root, expected_digest)
    records = {item["path"]: item for item in receipt["files"]}
    available = set(records)
    rows = []
    unportable_commands = []
    external_runtime_hints = []
    external_runtime_ref_count = 0
    external_runtime_targets: set[str] = set()
    skill_paths = {path for path in available if re.fullmatch(
        r"plugins/[^/]+/skills/[^/]+/SKILL\.md", path)}
    pending = sorted(skill_paths)
    visited: set[str] = set()
    while pending:
        path = pending.pop(0)
        if path in visited:
            continue
        visited.add(path)
        data = release.read_file(release.safe_member(root, path))
        if len(data) != records[path]["size"] or release.digest(data) != records[path]["sha256"]:
            raise ValueError("Skill document changed after candidate verification")
        text = data.decode("utf-8")
        for row in inspect_document_references(path, text, available):
            rows.append({"skill": path, **row})
            target = row["resolved"]
            if (row["status"] == "present" and target not in visited
                    and re.fullmatch(r"plugins/[^/]+/skills/[^/]+/.+\.md", target)):
                pending.append(target)
        if path not in skill_paths:
            continue
        unportable_commands.extend(inspect_unportable_commands(path, text))
        external_runtime_hints.extend(inspect_external_runtime_hints(path, text))
        for match in GSTACK_BIN_REF.finditer(text):
            external_runtime_ref_count += 1
            # Keep names internal: an untrusted filename must not enter JSON.
            external_runtime_targets.add(match.group(0).rsplit("/", 1)[-1])
    unresolved = [row for row in rows if row["status"] != "present"]
    status = ("incomplete" if unresolved or unportable_commands else
              "external_runtime_pending" if external_runtime_hints else "static_paths_present")
    report = {"status": status,
            "bundle_digest": expected_digest, "skills_checked": len(skill_paths),
            "markdown_documents_checked": len(visited),
            "static_refs_checked": len(rows), "unresolved": unresolved,
            "unportable_commands": unportable_commands,
            "external_runtime_hints": external_runtime_hints,
            "external_runtime_counts": {
                "skill_documents": len(external_runtime_hints),
                "literal_references": external_runtime_ref_count,
                "distinct_targets": len(external_runtime_targets)},
            "runtime_closure_verified": False,
            "scope": "literal ASCII backtick paths and simple Markdown link destinations "
                     "in skill entrypoints and reachable Markdown references, "
                     "plus source/project-relative skill command locations; "
                     "literal Gstack bin counts are lexical external-runtime hints, not calls; "
                     "findings need manual review; no execution, imports or services"}
    if gstack_source is not None:
        report["gstack_source_evidence"] = inspect_pinned_gstack_targets(
            gstack_source, gstack_commit, external_runtime_targets)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--expected-digest", required=True)
    parser.add_argument("--gstack-source-root", type=Path)
    parser.add_argument("--gstack-expected-commit")
    args = parser.parse_args(argv)
    try:
        report = audit_candidate(args.package, args.expected_digest,
                                 gstack_source=args.gstack_source_root,
                                 gstack_commit=args.gstack_expected_commit)
    except (ValueError, OSError, UnicodeError, KeyError, TypeError):
        # Avoid echoing untrusted candidate metadata, paths or secret-like text.
        print('{"status":"blocked","message":"Candidate path audit failed"}', file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "static_paths_present" else 1


if __name__ == "__main__":
    raise SystemExit(main())
