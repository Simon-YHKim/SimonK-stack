#!/usr/bin/env python3
"""Verify candidate skill bytes are preserved across Claude and Codex packages.

This is an offline package invariant, not host loading, routing or quality proof.
Both receipts and the Codex subset's source-overlay provenance must validate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import codex_overlay
import codex_safe_subset
import plugin_bundle
import skill_release as release

ZOOM_PATH = codex_overlay.ZOOM_PATH
MANUAL_FLAG = codex_overlay.MANUAL_FLAG
EXPECTED_EXCLUDED = frozenset(
    f"plugins/{owner}/skills/{skill}/SKILL.md"
    for owner, skill in codex_safe_subset.EXCLUDED_SKILLS
)


def compare(claude: dict[str, str], codex: dict[str, str],
            zoom_original: bytes, zoom_projected: bytes) -> dict:
    """Check exact common bytes, the single host projection and D-29 omissions."""
    if not isinstance(claude, dict) or not isinstance(codex, dict):
        raise ValueError("Skill inventories must be mappings")
    added = set(codex) - set(claude)
    if added:
        raise ValueError("Codex skill set adds unreviewed skills")
    excluded = set(claude) - set(codex)
    if excluded != EXPECTED_EXCLUDED:
        raise ValueError("D-29 excluded skill set differs")
    if ZOOM_PATH not in claude or ZOOM_PATH not in codex:
        raise ValueError("Zoom-out projection is absent")
    if not zoom_original.startswith(b"---\n") or zoom_original.count(MANUAL_FLAG) != 1:
        raise ValueError("Zoom-out marker must be in frontmatter exactly once")
    frontmatter_end = zoom_original.find(b"\n---\n", 4)
    marker_at = zoom_original.find(MANUAL_FLAG)
    if frontmatter_end < 0 or marker_at > frontmatter_end:
        raise ValueError("Zoom-out marker must be in frontmatter")
    if release.digest(zoom_original) != claude[ZOOM_PATH] or \
            release.digest(zoom_projected) != codex[ZOOM_PATH]:
        raise ValueError("Zoom-out receipt differs from package bytes")
    if zoom_projected != zoom_original.replace(MANUAL_FLAG, b"", 1):
        raise ValueError("Zoom-out projection differs from the approved transform")
    shared = set(claude) & set(codex) - {ZOOM_PATH}
    if any(claude[path] != codex[path] for path in shared):
        raise ValueError("Shared skill bytes differ")
    return {"status": "static_content_parity", "claude_skills": len(claude),
            "codex_skills": len(codex), "identical_skills": len(shared),
            "projected_skills": [ZOOM_PATH], "excluded_skills": sorted(excluded),
            "host_behavior_verified": False, "selection_quality_verified": False,
            "installation_ready": False}


def _skills(rows: list[dict]) -> dict[str, str]:
    return {row["path"]: row["sha256"] for row in rows
            if row["path"].startswith("plugins/") and row["path"].endswith("/SKILL.md")}


def audit(claude_root: Path, claude_digest: str, codex_root: Path,
          subset_digest: str, overlay_root: Path, overlay_digest: str) -> dict:
    claude_root = release.no_links(claude_root)
    codex_root = release.no_links(codex_root)
    overlay_root = release.no_links(overlay_root)
    candidate = plugin_bundle.verify_bundle(claude_root, claude_digest)
    subset = codex_safe_subset.verify_subset(codex_root, subset_digest,
                                            overlay_root, overlay_digest)
    overlay = codex_overlay.verify_overlay(overlay_root, overlay_digest)
    if overlay["candidate_digest"] != claude_digest:
        raise ValueError("Codex overlay is not derived from the Claude candidate")
    original = release.read_file(release.safe_member(claude_root, ZOOM_PATH))
    projected = release.read_file(release.safe_member(codex_root, ZOOM_PATH))
    result = compare(_skills(candidate["files"]), _skills(subset["included_members"]),
                     original, projected)
    return {"claude_digest": claude_digest, "subset_digest": subset_digest,
            "overlay_digest": overlay_digest, **result}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("claude", "codex-subset", "codex-overlay"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("claude-digest", "subset-digest", "overlay-digest"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    try:
        result = audit(args.claude, args.claude_digest, args.codex_subset,
                       args.subset_digest, args.codex_overlay, args.overlay_digest)
    except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
