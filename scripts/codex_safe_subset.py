#!/usr/bin/env python3
"""Build a pinned Codex general-skill subset without Claude-only safety controls.

This is an offline candidate projection of a verified Codex v2 overlay. It
neither installs plugins nor claims that Codex enforces safety policies.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import tempfile

import codex_overlay
import skill_release as r

SCOPE = "five-plugin-codex-general-skills-only-v2"
DECISION_REF = "D-29"
EXCLUDED_SKILLS = (
    ("SimonKCore", "careful"),
    ("SimonKStack", "freeze"),
    ("SimonKStack", "guard"),
    ("SimonKStack", "investigate"),
    ("SimonKCore", "unfreeze"),
)
EXCLUDED_PREFIXES = (tuple(f"plugins/{owner}/skills/{skill}/"
                           for owner, skill in EXCLUDED_SKILLS)
                     + tuple(f"plugins/{owner}/.simonk-runtime/"
                             for owner in ("SimonKCore", "SimonKStack")))
REQUIRED_EXCLUDED_FILES = (tuple(f"plugins/{owner}/skills/{skill}/SKILL.md"
                                 for owner, skill in EXCLUDED_SKILLS)
                           + tuple(f"plugins/{owner}/.simonk-runtime/safety_runtime.py"
                                   for owner in ("SimonKCore", "SimonKStack")))
EXCLUDED_NAMES = tuple(f"simonk-{owner.removeprefix('SimonK').lower()}:{skill}"
                       for owner, skill in EXCLUDED_SKILLS)
LIMITATIONS = [
    "D-29: careful, guard, freeze and investigate are excluded because their Codex policy hooks are not verified.",
    "The dependent Claude-only unfreeze skill and Core/Stack safety runtimes are also excluded; source files remain unchanged.",
    "The subset contains general skills only; it is not a user installation or host behavior test.",
    "The original overlay and all excluded source directories are preserved.",
    "Host skill selection, dependency closure, costs, plugin rollback and safety parity remain unverified.",
]
RECEIPT_NAME = "subset.json"


def _member(source, path):
    payload = r.read_file(r.safe_member(source, path))
    return {"path": path, "sha256": r.digest(payload), "size": len(payload)}


def _inventory(source):
    files = r.files_under(source)
    if RECEIPT_NAME in files:
        raise ValueError("Source already contains a subset receipt")
    for path in REQUIRED_EXCLUDED_FILES:
        if path not in files:
            raise ValueError("Required Claude-only safety control is absent")
    included = sorted(path for path in files
                      if not any(path.startswith(prefix) for prefix in EXCLUDED_PREFIXES))
    excluded = sorted(files - set(included))
    if "overlay.json" not in included or "bundle.json" not in included:
        raise ValueError("Source provenance receipts are missing")
    return ([_member(source, path) for path in included],
            [_member(source, path) for path in excluded])


def _receipt(source_digest, included, excluded):
    return {
        "schema_version": 1,
        "scope": SCOPE,
        "decision_ref": DECISION_REF,
        "source_overlay_digest": source_digest,
        "excluded_skills": list(EXCLUDED_NAMES),
        "included_members": included,
        "excluded_members": excluded,
        "host_compatibility_verified": False,
        "installation_ready": False,
        "limitations": LIMITATIONS,
    }


def _checked_members(value, *, excluded):
    if not isinstance(value, list) or not value:
        raise ValueError("Invalid subset member list")
    paths = []
    for item in value:
        if (not isinstance(item, dict) or set(item) != {"path", "sha256", "size"}
                or not isinstance(item["path"], str)
                or str(r.relative(item["path"])) != item["path"]
                or not isinstance(item["sha256"], str)
                or not r.HEX.fullmatch(item["sha256"])
                or type(item["size"]) is not int
                or not 0 <= item["size"] <= r.MAX_FILE):
            raise ValueError("Invalid subset member")
        is_excluded = any(item["path"].startswith(prefix) for prefix in EXCLUDED_PREFIXES)
        if is_excluded != excluded:
            raise ValueError("Safety-control membership differs")
        paths.append(item["path"])
    if paths != sorted(set(paths)):
        raise ValueError("Subset member order or uniqueness differs")
    return set(paths)


def verify_subset(package, expected_digest, source=None, source_digest=None):
    """Verify pinned bytes alone, or additionally prove source-overlay provenance."""
    package = r.no_links(package)
    if not isinstance(expected_digest, str) or not r.HEX.fullmatch(expected_digest):
        raise ValueError("A pinned subset SHA-256 is required")
    data = r.read_file(package / RECEIPT_NAME)
    if r.digest(data) != expected_digest:
        raise ValueError("Subset receipt digest mismatch")
    receipt = r.decoded(data)
    expected_keys = {"schema_version", "scope", "decision_ref", "source_overlay_digest",
                     "excluded_skills", "included_members", "excluded_members",
                     "host_compatibility_verified", "installation_ready", "limitations"}
    if (not isinstance(receipt, dict) or set(receipt) != expected_keys
            or type(receipt["schema_version"]) is not int or receipt["schema_version"] != 1
            or receipt["scope"] != SCOPE or receipt["decision_ref"] != DECISION_REF
            or not isinstance(receipt["source_overlay_digest"], str)
            or not r.HEX.fullmatch(receipt["source_overlay_digest"])
            or receipt["excluded_skills"] != list(EXCLUDED_NAMES)
            or receipt["host_compatibility_verified"] is not False
            or receipt["installation_ready"] is not False
            or receipt["limitations"] != LIMITATIONS or data != r.encoded(receipt)):
        raise ValueError("Invalid subset-only receipt")
    included = _checked_members(receipt["included_members"], excluded=False)
    excluded = _checked_members(receipt["excluded_members"], excluded=True)
    for path in REQUIRED_EXCLUDED_FILES:
        if path not in excluded:
            raise ValueError("Missing safety-control omission proof")
    if ("overlay.json" not in included or "bundle.json" not in included
            or r.files_under(package) != included | {RECEIPT_NAME}):
        raise ValueError("Missing or extra subset member")
    for item in receipt["included_members"]:
        payload = r.read_file(r.safe_member(package, item["path"]))
        if len(payload) != item["size"] or r.digest(payload) != item["sha256"]:
            raise ValueError("Subset member differs from receipt")
    if r.digest(r.read_file(package / "overlay.json")) != receipt["source_overlay_digest"]:
        raise ValueError("Copied source-overlay receipt differs")
    if source is None:
        if source_digest is not None:
            raise ValueError("Source pin needs a source directory")
    else:
        source = r.no_links(source)
        if source_digest != receipt["source_overlay_digest"]:
            raise ValueError("Source-overlay pin differs")
        with r.pinned(source, directory=True):
            codex_overlay.verify_overlay(source, source_digest)
            source_included, source_excluded = _inventory(source)
        if (source_included != receipt["included_members"]
                or source_excluded != receipt["excluded_members"]):
            raise ValueError("Subset provenance differs from source overlay")
    return receipt


def build_subset(source, source_digest, output):
    source = r.no_links(source)
    if not isinstance(source_digest, str) or not r.HEX.fullmatch(source_digest):
        raise ValueError("A pinned source-overlay SHA-256 is required")
    target = r.destination(output, source)
    if os.path.lexists(target):
        raise ValueError("Build never overwrites existing output")
    with r.pinned(source, directory=True):
        if r.digest(r.read_file(source / "overlay.json")) != source_digest:
            raise ValueError("Source-overlay receipt digest mismatch")
        codex_overlay.verify_overlay(source, source_digest)
        included, excluded = _inventory(source)
        receipt_data = r.encoded(_receipt(source_digest, included, excluded))
        if len(receipt_data) > r.MAX_FILE:
            raise ValueError("Subset receipt exceeds byte limit")
        subset_digest = r.digest(receipt_data)
        with r.pinned(target.parent, directory=True):
            stage = Path(tempfile.mkdtemp(prefix=".simonk-codex-subset-", dir=target.parent))
            with r.pinned(stage, directory=True, delete=True):
                for item in included:
                    payload = r.read_file(r.safe_member(source, item["path"]))
                    if len(payload) != item["size"] or r.digest(payload) != item["sha256"]:
                        raise ValueError("Source member changed during subset build")
                    r.write_member(stage, item["path"], payload, "100644")
                r.write_member(stage, RECEIPT_NAME, receipt_data, "100644")
                verify_subset(stage, subset_digest)
                codex_overlay.verify_overlay(source, source_digest)
                r.publish_new(stage, target)
    verify_subset(target, subset_digest, source, source_digest)
    return {"status": "codex_general_subset_bytes_verified",
            "source_overlay_digest": source_digest, "subset_digest": subset_digest,
            "plugins": 5,
            "skills": sum(item["path"].endswith("/SKILL.md") for item in included),
            "excluded_skills": list(EXCLUDED_NAMES), "installation_ready": False,
            "host_compatibility_verified": False, "path": str(target)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--source-overlay", type=Path, required=True)
    build.add_argument("--overlay-digest", required=True)
    build.add_argument("--output", type=Path, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--package", type=Path, required=True)
    verify.add_argument("--subset-digest", required=True)
    verify.add_argument("--source-overlay", type=Path)
    verify.add_argument("--overlay-digest")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            result = build_subset(args.source_overlay, args.overlay_digest, args.output)
        else:
            checked = verify_subset(args.package, args.subset_digest,
                                    args.source_overlay, args.overlay_digest)
            result = {"status": "codex_general_subset_bytes_verified",
                      "subset_digest": args.subset_digest,
                      "source_provenance_verified": args.source_overlay is not None,
                      "installation_ready": checked["installation_ready"]}
        print(r.encoded(result).decode("utf-8"), end="")
        return 0
    except (ValueError, OSError, TypeError, KeyError, IndexError):
        print('{"status":"blocked","reason":"codex_subset_invalid"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
