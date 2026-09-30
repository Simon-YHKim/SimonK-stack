#!/usr/bin/env python3
"""Audit version identity across two verified, immutable-in-use candidates.

Only package bytes and declared plugin versions are compared. This does not
select a versioning scheme, prove a host update, or approve installation.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

import plugin_bundle
import skill_release as release


def _content(manifest: dict, owner: str) -> dict[str, tuple[str, str]]:
    prefix = f"plugins/{owner}/"
    metadata = {prefix + plugin_bundle.PLUGIN, prefix + plugin_bundle.MARKET}
    return {row["path"][len(prefix):]: (row["sha256"], row["mode"])
            for row in manifest["files"]
            if row["path"].startswith(prefix) and row["path"] not in metadata}


def compare(before: dict, after: dict, before_versions: dict[str, str],
            after_versions: dict[str, str], before_metadata: dict, after_metadata: dict) -> dict:
    """A changed payload needs a new version; version-only churn is advisory."""
    owners = set(before["inputs"]["plugins"])
    if (owners != set(after["inputs"]["plugins"]) or owners != set(before_versions)
            or owners != set(after_versions) or owners != set(before_metadata)
            or owners != set(after_metadata) or owners != release.OWNERS):
        raise ValueError("Candidate owner sets differ")
    rows = []
    for owner in sorted(owners):
        old = {**_content(before, owner), **before_metadata[owner]}
        new = {**_content(after, owner), **after_metadata[owner]}
        changed = sorted(path for path in old.keys() | new.keys() if old.get(path) != new.get(path))
        old_version, new_version = before_versions[owner], after_versions[owner]
        if not isinstance(old_version, str) or not isinstance(new_version, str):
            raise ValueError("Invalid plugin version")
        state = ("collision" if changed and old_version == new_version else
                 "churn" if not changed and old_version != new_version else
                 "updated" if changed else "stable")
        rows.append({"owner": owner, "state": state, "version_before": old_version,
                     "version_after": new_version, "changed_files": len(changed),
                     "changed_paths": changed[:20], "changed_paths_truncated": len(changed) > 20})
    return {"status": "collision" if any(row["state"] == "collision" for row in rows)
            else "churn" if any(row["state"] == "churn" for row in rows)
            else "consistent", "plugins": rows,
            "scope": "verified candidate package bytes with version-normalized manifests; no host behavior"}


def _metadata(root: Path, manifest: dict) -> tuple[dict[str, str], dict]:
    """Hash manifest semantics with only the generated version fields blanked."""
    files = {row["path"]: row for row in manifest["files"]}
    versions = {}
    payload = {}
    with release.pinned(root, directory=True):
        for owner in sorted(release.OWNERS):
            payload[owner] = {}
            for relative in (plugin_bundle.PLUGIN, plugin_bundle.MARKET):
                path = f"plugins/{owner}/{relative}"
                row = files[path]
                data = release.read_file(release.safe_member(root, path))
                if len(data) != row["size"] or release.digest(data) != row["sha256"]:
                    raise ValueError("Plugin manifest changed after candidate verification")
                document = release.decoded(data)
                if not isinstance(document, dict) or not isinstance(document.get("version"), str):
                    raise ValueError("Invalid plugin manifest version")
                if relative == plugin_bundle.PLUGIN:
                    versions[owner] = document["version"]
                normalized = copy.deepcopy(document)
                normalized["version"] = ""
                if relative == plugin_bundle.MARKET:
                    if (not isinstance(normalized.get("plugins"), list)
                            or len(normalized["plugins"]) != 1
                            or not isinstance(normalized["plugins"][0], dict)):
                        raise ValueError("Invalid marketplace manifest")
                    normalized["plugins"][0]["version"] = ""
                payload[owner][relative] = (release.digest(release.encoded(normalized)), row["mode"])
    return versions, payload


def audit(before_root: Path, before_digest: str, after_root: Path, after_digest: str) -> dict:
    before_root, after_root = release.no_links(before_root), release.no_links(after_root)
    if before_root == after_root:
        raise ValueError("Transition requires distinct candidates")
    before = plugin_bundle.verify_bundle(before_root, before_digest)
    after = plugin_bundle.verify_bundle(after_root, after_digest)
    before_versions, before_metadata = _metadata(before_root, before)
    after_versions, after_metadata = _metadata(after_root, after)
    result = compare(before, after, before_versions, after_versions,
                     before_metadata, after_metadata)
    return {"before_digest": before_digest, "after_digest": after_digest, **result}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--before-digest", required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--after-digest", required=True)
    args = parser.parse_args(argv)
    try:
        result = audit(args.before, args.before_digest, args.after, args.after_digest)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "invalid", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 2 if result["status"] == "collision" else 0


if __name__ == "__main__":
    sys.exit(main())
