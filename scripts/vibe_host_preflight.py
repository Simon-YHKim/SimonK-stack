#!/usr/bin/env python3
"""Read-only snapshot of the flat Core links before any /vibe host change.

This does not verify candidate receipts, host command precedence, billing, or
runtime quality. It never changes a profile and never grants installation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


CLAUDE_NAMES = ("model-router", "multi-terminal-dispatcher", "simonk", "vibe", "vibe-bot")
CODEX_NAMES = ("vibe", "vibe-bot")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _direct_target(link: Path) -> Path:
    """Normalize the link text without following another link in its target."""
    raw = link.readlink()
    if os.name == "nt":
        value = str(raw)
        if value.startswith("\\\\?\\UNC\\"):
            raw = Path("\\\\" + value[8:])
        elif value.startswith("\\\\?\\"):
            raw = Path(value[4:])
    return Path(os.path.abspath(raw if raw.is_absolute() else link.parent / raw))


def scan(candidate_root: Path, current_root: Path, claude_root: Path, codex_root: Path,
         agents_root: Path) -> dict:
    issues: list[str] = []
    entries: list[dict] = []
    checked_links = 0
    different_skills = 0
    for host, root, package, names in (
        ("claude", claude_root, "candidate-safety", CLAUDE_NAMES),
        ("codex", codex_root, "codex-subset-safety", CODEX_NAMES),
    ):
        for name in names:
            link = root / "skills" / name
            candidate = candidate_root / package / "plugins" / "SimonKCore" / "skills" / name / "SKILL.md"
            entry = {"host": host, "name": name, "link": str(link),
                     "candidate_skill": str(candidate)}
            entries.append(entry)
            if not candidate.is_file():
                issues.append("CANDIDATE_SKILL_MISSING")
                continue
            entry["candidate_sha256"] = _digest(candidate)
            if not (link.is_symlink() or link.is_junction()):
                issues.append("NOT_LINK")
                continue
            try:
                entry["target"] = str(_direct_target(link))
                expected = current_root / package / "plugins" / "SimonKCore" / "skills" / name
                entry["expected_target"] = str(expected.absolute())
                if os.path.normcase(entry["target"]) != os.path.normcase(entry["expected_target"]):
                    issues.append("LINK_TARGET_MISMATCH")
                installed = link / "SKILL.md"
                if not installed.is_file():
                    issues.append("INSTALLED_SKILL_MISSING")
                    continue
                entry["installed_sha256"] = _digest(installed)
            except (OSError, RuntimeError):
                issues.append("LINK_READ_FAILED")
                continue
            checked_links += 1
            entry["same_bytes"] = entry["installed_sha256"] == entry["candidate_sha256"]
            different_skills += not entry["same_bytes"]

    alias = agents_root / "skills" / "vibe"
    alias_entry = {"host": "agents", "name": "vibe", "link": str(alias)}
    entries.append(alias_entry)
    if not alias.is_symlink():
        issues.append("ALIAS_NOT_SYMLINK")
    else:
        try:
            alias_entry["target"] = str(_direct_target(alias))
            expected = claude_root / "skills" / "vibe"
            if os.path.normcase(alias_entry["target"]) != os.path.normcase(str(expected.absolute())):
                issues.append("ALIAS_TARGET_MISMATCH")
            else:
                checked_links += 1
        except (OSError, RuntimeError):
            issues.append("ALIAS_READ_FAILED")

    return {"status": "blocked" if issues else "host_snapshot_complete",
            "scope": "seven_flat_core_links_and_one_agents_alias",
            "checked_links": checked_links, "different_skills": different_skills,
            "issues": sorted(set(issues)), "entries": entries,
            "candidate_bytes_verified": False, "host_command_precedence_verified": False,
            "full_skill_set_verified": False, "billing_verified": False,
            "installation_ready": False,
            "profile_changed": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate-root", "expected-current-root", "claude-root", "codex-root", "agents-root"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = scan(args.candidate_root, args.expected_current_root,
                      args.claude_root, args.codex_root,
                      args.agents_root)
    except OSError as exc:
        report = {"status": "blocked", "issues": ["READ_FAILED"],
                  "error_type": type(exc).__name__, "installation_ready": False,
                  "profile_changed": False}
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "host_snapshot_complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
