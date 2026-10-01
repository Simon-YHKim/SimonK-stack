#!/usr/bin/env python3
"""Read-only snapshot of the flat Core links before any /vibe host change.

With four externally pinned digests it verifies candidate receipts and their
provenance. It does not verify host command precedence, billing, or runtime
quality. It never changes a profile and never grants installation.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import stat
import sys


CLAUDE_NAMES = ("model-router", "multi-terminal-dispatcher", "simonk", "vibe", "vibe-bot")
CODEX_NAMES = ("vibe", "vibe-bot")
PLUGIN_NAMES = ("SimonKCore", "SimonKDesign", "SimonKStack", "SimonKMarket", "SimonKAIHub")
PIN_NAMES = frozenset(("source", "candidate-safety", "codex-overlay-safety",
                       "codex-subset-safety"))


def _verify_candidate_receipts(candidate_root: Path, pins: dict) -> dict:
    """Authenticate all four pinned packages and their provenance, not host loading."""
    if (not isinstance(pins, dict) or set(pins) != PIN_NAMES
            or any(not isinstance(value, str) or len(value) != 64
                   or any(char not in "0123456789abcdef" for char in value)
                   for value in pins.values())):
        return {"status": "invalid", "packages": 0}
    try:
        import skill_release
        import plugin_bundle
        import codex_overlay
        import codex_safe_subset

        skill_release.verify_release(candidate_root / "source", pins["source"])
        claude = plugin_bundle.verify_bundle(candidate_root / "candidate-safety",
                                              pins["candidate-safety"])
        overlay = codex_overlay.verify_overlay(candidate_root / "codex-overlay-safety",
                                                pins["codex-overlay-safety"])
        subset = codex_safe_subset.verify_subset(
            candidate_root / "codex-subset-safety", pins["codex-subset-safety"],
            source=candidate_root / "codex-overlay-safety",
            source_digest=pins["codex-overlay-safety"])
        if (claude["source_digest"] != pins["source"]
                or overlay["candidate_digest"] != pins["candidate-safety"]
                or subset["source_overlay_digest"] != pins["codex-overlay-safety"]):
            raise ValueError("candidate provenance mismatch")
    except (OSError, ValueError, TypeError, KeyError, ImportError):
        return {"status": "invalid", "packages": 0}
    return {"status": "verified", "packages": 4}


def _native_plugin_coverage(candidate_root: Path, snapshot: dict | None) -> dict:
    """Compare supplied CLI list metadata only; never equate it with loaded bytes."""
    if snapshot is None:
        return {"status": "not_observed", "scope_complete": False}
    if not isinstance(snapshot, dict) or set(snapshot) != {"claude", "codex"}:
        raise ValueError("invalid native plugin snapshot")

    coverage = {}
    for host, package in (("claude", "candidate-safety"),
                          ("codex", "codex-subset-safety")):
        expected = {}
        for plugin in PLUGIN_NAMES:
            manifest_path = (candidate_root / package / "plugins" / plugin /
                             (".claude-plugin" if host == "claude" else ".codex-plugin") /
                             "plugin.json")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict):
                raise ValueError("invalid native plugin manifest")
            name, version = manifest.get("name"), manifest.get("version")
            if not isinstance(name, str) or not name or not isinstance(version, str) or not version:
                raise ValueError("invalid native plugin manifest")
            if name in expected:
                raise ValueError("duplicate native plugin name")
            expected[name] = version

        raw = snapshot[host]
        if host == "codex":
            if not isinstance(raw, dict) or not isinstance(raw.get("installed"), list):
                raise ValueError("invalid Codex plugin list")
            entries = raw["installed"]
            key = "pluginId"
        else:
            if not isinstance(raw, list):
                raise ValueError("invalid Claude plugin list")
            entries = raw
            key = "id"
        if any(not isinstance(entry, dict) for entry in entries):
            raise ValueError("invalid native plugin entry")

        counts = Counter()
        for name, version in expected.items():
            matches = [entry for entry in entries if entry.get(key) == f"{name}@{name}"]
            if len(matches) > 1:
                counts["ambiguous"] += 1
            elif not matches:
                counts["missing"] += 1
            elif matches[0].get("version") != version:
                counts["drifted"] += 1
            elif matches[0].get("enabled") is not True or (host == "codex" and
                                                              matches[0].get("installed") is not True):
                counts["disabled"] += 1
            else:
                counts["matched"] += 1
        coverage[host] = {"status": "metadata_matched" if counts["matched"] == len(expected)
                          else "gaps", "scope_complete": True, "expected": len(expected),
                          **{state: counts[state] for state in
                             ("matched", "drifted", "missing", "disabled", "ambiguous")}}
    return {"status": "metadata_matched" if all(row["status"] == "metadata_matched"
              for row in coverage.values()) else "gaps", "scope_complete": True,
            **coverage}


def _flat_coverage(candidate_root: Path, host_roots: tuple[Path, ...],
                   package: str) -> dict:
    """Reuse the repo's bounded metadata scanner; this is not host loading proof."""
    scanner_root = Path(__file__).resolve().parents[1] / "skills-src" / "vibe" / "scripts"
    if str(scanner_root) not in sys.path:
        sys.path.insert(0, str(scanner_root))
    import orchestrate

    source_roots = tuple(candidate_root / package / "plugins" / name / "skills"
                         for name in PLUGIN_NAMES)
    source = orchestrate.skill_inventory(source_roots)
    installed = orchestrate.skill_inventory(host_roots)
    result = orchestrate.skill_coverage(source, installed)
    counts = Counter(row["installation"] for row in result["rows"])
    return {"status": result["status"], "scope_complete": result["scope_complete"],
            "source_skills": len(result["rows"]),
            **{state: counts[state] for state in
               ("matched", "drifted", "missing", "ambiguous_source", "host_only")}}


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


def _is_directory_link(path: Path) -> bool:
    """Recognize symlinks and Windows junctions on Python 3.11 and newer."""
    try:
        info = path.lstat()
    except OSError:
        return False
    mount_point_tag = getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)
    return stat.S_ISLNK(info.st_mode) or getattr(info, "st_reparse_tag", None) == mount_point_tag


def scan(candidate_root: Path, current_root: Path, claude_root: Path, codex_root: Path,
         agents_root: Path, native_snapshot: dict | None = None,
         candidate_pins: dict | None = None) -> dict:
    candidate_verification = ({"status": "not_requested", "packages": 0}
                              if candidate_pins is None else
                              _verify_candidate_receipts(candidate_root, candidate_pins))
    if candidate_verification["status"] == "invalid":
        return {"status": "blocked", "issues": ["CANDIDATE_VERIFICATION_FAILED"],
                "candidate_verification": candidate_verification,
                "candidate_bytes_verified": False, "rollout_gate": "blocked",
                "installation_ready": False, "profile_changed": False}
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
            entry = {"host": host, "name": name}
            entries.append(entry)
            if not candidate.is_file():
                issues.append("CANDIDATE_SKILL_MISSING")
                continue
            entry["candidate_sha256"] = _digest(candidate)
            if not _is_directory_link(link):
                issues.append("NOT_LINK")
                continue
            try:
                target = _direct_target(link)
                expected = current_root / package / "plugins" / "SimonKCore" / "skills" / name
                entry["target_matches_expected"] = (os.path.normcase(str(target)) ==
                                                    os.path.normcase(str(expected.absolute())))
                if not entry["target_matches_expected"]:
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
    alias_entry = {"host": "agents", "name": "vibe"}
    entries.append(alias_entry)
    if not alias.is_symlink():
        issues.append("ALIAS_NOT_SYMLINK")
    else:
        try:
            target = _direct_target(alias)
            expected = claude_root / "skills" / "vibe"
            alias_entry["target_matches_expected"] = (os.path.normcase(str(target)) ==
                                                      os.path.normcase(str(expected.absolute())))
            if not alias_entry["target_matches_expected"]:
                issues.append("ALIAS_TARGET_MISMATCH")
            else:
                checked_links += 1
        except (OSError, RuntimeError):
            issues.append("ALIAS_READ_FAILED")

    flat_coverage = {
        "claude": _flat_coverage(candidate_root, (claude_root / "skills",),
                                 "candidate-safety"),
        "codex": _flat_coverage(candidate_root, (agents_root / "skills", codex_root / "skills"),
                                "codex-subset-safety"),
    }
    try:
        native_coverage = _native_plugin_coverage(candidate_root, native_snapshot)
    except (OSError, ValueError, TypeError):
        native_coverage = {"status": "invalid_snapshot", "scope_complete": False}
        issues.append("NATIVE_SNAPSHOT_INVALID")
    return {"status": "blocked" if issues else "host_snapshot_complete",
            "scope": "seven_flat_core_links_and_one_agents_alias",
            "checked_links": checked_links, "different_skills": different_skills,
            "issues": sorted(set(issues)), "entries": entries,
            "flat_coverage": flat_coverage, "rollout_gate": "blocked",
            "native_plugin_coverage": native_coverage,
            "candidate_verification": candidate_verification,
            "candidate_bytes_verified": candidate_verification["status"] == "verified",
            "host_command_precedence_verified": False,
            "full_skill_set_verified": False, "billing_verified": False,
            "installation_ready": False,
            "profile_changed": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("candidate-root", "expected-current-root", "claude-root", "codex-root", "agents-root"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--native-json-stdin", action="store_true",
                        help="Read combined Claude/Codex plugin-list JSON from stdin (metadata only)")
    for name in ("source", "claude", "overlay", "codex"):
        parser.add_argument("--" + name + "-digest")
    args = parser.parse_args(argv)
    try:
        native_snapshot = None
        if args.native_json_stdin:
            raw = sys.stdin.read(1048577)
            if len(raw) > 1048576:
                raise ValueError("native snapshot too large")
            native_snapshot = json.loads(raw)
            if not isinstance(native_snapshot, dict):
                raise ValueError("native snapshot must be an object")
        digest_values = {"source": args.source_digest,
                         "candidate-safety": args.claude_digest,
                         "codex-overlay-safety": args.overlay_digest,
                         "codex-subset-safety": args.codex_digest}
        candidate_pins = ({name: value for name, value in digest_values.items() if value is not None}
                          if any(value is not None for value in digest_values.values()) else None)
        report = scan(args.candidate_root, args.expected_current_root,
                      args.claude_root, args.codex_root,
                      args.agents_root, native_snapshot=native_snapshot,
                      candidate_pins=candidate_pins)
    except (OSError, ValueError) as exc:
        report = {"status": "blocked", "issues": ["READ_FAILED"],
                  "error_type": type(exc).__name__, "installation_ready": False,
                  "profile_changed": False}
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "host_snapshot_complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
