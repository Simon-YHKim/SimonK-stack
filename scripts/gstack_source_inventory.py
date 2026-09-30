#!/usr/bin/env python3
"""Read-only Git/worktree inventory for an independently pinned Gstack source clone.

This proves neither Gstack helper closure nor Claude/Codex host compatibility.
It never reads the user's installed Gstack tree, builds binaries, or installs files.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import json
from pathlib import Path
import sys

import plugin_bundle as bundle
import skill_release as release

REGULAR_MODES = {"100644", "100755"}


def _tree_records(root: Path, commit: str) -> list[dict]:
    records = []
    for entry in bundle.git_bytes(root, "ls-tree", "-r", "-l", "-z", commit).split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, kind, raw_oid, raw_size = metadata.decode("ascii").split()
        path = raw_path.decode("utf-8")
        release.relative(path)
        if kind != "blob" or not bundle.OID.fullmatch(raw_oid):
            raise ValueError("Unsupported Git tree object")
        records.append({"path": path, "mode": mode, "git_blob": raw_oid,
                        "git_blob_size": int(raw_size)})
    if not 1 <= len(records) <= release.MAX_FILES:
        raise ValueError("Invalid source inventory size")
    if len({item["path"] for item in records}) != len(records):
        raise ValueError("Duplicate Git tree path")
    return records


def _index_records(root: Path) -> set[tuple[str, str, str]]:
    result = set()
    for entry in bundle.git_bytes(root, "ls-files", "--stage", "-z").split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, raw_oid, stage = metadata.decode("ascii").split()
        path = raw_path.decode("utf-8")
        release.relative(path)
        if stage != "0" or not bundle.OID.fullmatch(raw_oid):
            raise ValueError("Unmerged or invalid source index")
        result.add((path, mode, raw_oid))
    return result


def audit_source(root: Path, expected_commit: str) -> dict:
    """Check a fixed-drive clone and emit an inventory-only, fail-closed verdict.

    Git commit/tree records attest the tracked inventory. The SHA-256 digest pins
    raw working-tree bytes, not an equivalence proof against Git blobs or a signed
    origin. Same-user concurrent child additions remain outside this contract.
    """
    if not isinstance(expected_commit, str) or not bundle.OID.fullmatch(expected_commit):
        raise ValueError("Expected commit must be a full SHA-1 Git OID")
    root = release.no_links(Path(root))
    with ExitStack() as stack:
        actual_files = bundle.pin_snapshot(root, stack)
        bundle.check_base(root, expected_commit)
        records = _tree_records(root, expected_commit)
        expected_index = {(r["path"], r["mode"], r["git_blob"]) for r in records}
        if _index_records(root) != expected_index:
            raise ValueError("Source index differs from pinned tree")
        if actual_files != {r["path"] for r in records}:
            raise ValueError("Source working tree files differ from pinned inventory")
        manifest = []
        unsupported, oversized = [], []
        raw_bytes = 0
        for item in records:
            path, mode = item["path"], item["mode"]
            if mode not in REGULAR_MODES:
                unsupported.append({"path": path, "mode": mode})
                manifest.append({**item, "raw_sha256": None})
                continue
            physical = release.safe_member(root, path)
            size = physical.stat().st_size
            if size > release.MAX_FILE:
                oversized.append({"path": path, "raw_size": size})
                manifest.append({**item, "raw_size": size, "raw_sha256": None})
                raw_bytes += size
                continue
            data = release.read_file(physical)
            raw_bytes += len(data)
            manifest.append({**item, "raw_size": len(data),
                             "raw_sha256": release.digest(data)})
        over_total = raw_bytes > release.MAX_TOTAL
        compatible = not unsupported and not oversized and not over_total
        status = ("unsupported_git_modes" if unsupported else
                  "oversized_source" if oversized or over_total else "regular_tree")
        return {"status": status, "expected_commit": expected_commit,
                "tree_oid": bundle.git(root, "rev-parse", expected_commit + "^{tree}").strip(),
                "files": len(records), "git_blob_bytes": sum(r["git_blob_size"] for r in records),
                "raw_regular_bytes": raw_bytes,
                "raw_manifest_sha256": release.digest(release.encoded(manifest)),
                "unsupported_members": unsupported, "oversized_members": oversized,
                "over_total_limit": over_total, "package_contract_compatible": compatible,
                "runtime_closure_verified": False, "installation_ready": False,
                "scope": "Pinned Git tree/index and raw worktree inventory only; "
                         "no dependency closure, executable build, host or billing proof"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--expected-commit", required=True)
    args = parser.parse_args(argv)
    try:
        result = audit_source(args.source_root, args.expected_commit)
    except (ValueError, OSError, UnicodeError, KeyError, TypeError):
        print('{"status":"blocked","message":"Gstack source inventory failed"}',
              file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["package_contract_compatible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
