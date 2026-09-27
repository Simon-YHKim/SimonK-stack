#!/usr/bin/env python3
"""Report migration gaps between a verified bundle and isolated Gstack documents.

This never installs, runs or rewrites a skill. Headings are review hints, not
proof that instructions or safety policy are semantically equivalent.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

import candidate_path_audit as paths
import plugin_bundle
import skill_release as release

ENTRYPOINT = re.compile(r"plugins/[^/]+/skills/[^/]+/SKILL\.md\Z")
VALID_NAME = re.compile(r"[a-z][a-z0-9-]*\Z")
POLICY_HEADINGS = (
    ("skill_routing", "## Skill routing"),
    ("session_scope", "## Candidate session scope commands"),
    ("completion_report", "## 완료 보고 (HTML) — 표준"),
)


def _frontmatter_end(lines: list[str]) -> int:
    if not lines or lines[0].strip() != "---":
        raise ValueError("Skill frontmatter missing")
    try:
        return next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as exc:
        raise ValueError("Skill frontmatter is unterminated") from exc


def declared_name(text: str) -> str:
    lines = text.splitlines()
    end = _frontmatter_end(lines)
    names = [line.split(":", 1)[1].strip().strip("\"'")
             for line in lines[1:end] if re.match(r"^name\s*:", line)]
    if len(names) != 1 or not VALID_NAME.fullmatch(names[0]):
        raise ValueError("Skill name is missing, duplicate or invalid")
    return names[0]


def compare_pair(name: str, legacy_text: str, generated_text: str | None) -> dict:
    if generated_text is None:
        return {"name": name, "status": "missing_generated", "policy_gaps": [],
                "body_over_500_lines": False, "generated_body_lines": None}
    if declared_name(generated_text) != name:
        raise ValueError("Generated skill name does not match its mapping")
    lines = generated_text.splitlines()
    body_lines = len(lines) - _frontmatter_end(lines) - 1
    legacy_headers = set(re.findall(r"^## .+$", legacy_text, re.MULTILINE))
    generated_headers = set(re.findall(r"^## .+$", generated_text, re.MULTILINE))
    gaps = [key for key, heading in POLICY_HEADINGS
            if heading in legacy_headers and heading not in generated_headers]
    too_long = body_lines > 500
    return {"name": name, "status": "review_required" if gaps or too_long else "static_match",
            "policy_gaps": gaps, "body_over_500_lines": too_long,
            "generated_body_lines": body_lines}


def generated_index(root: Path, host: str) -> dict[str, str]:
    root = release.no_links(Path(root))
    if host not in {"claude", "codex"}:
        raise ValueError("Unsupported generated host")
    parent = root if host == "claude" else release.safe_member(root, ".agents/skills")
    if not parent.is_dir():
        return {}
    result = {}
    for folder in sorted(parent.iterdir()):
        if not folder.is_dir():
            continue
        member = (folder.relative_to(root) / "SKILL.md").as_posix()
        path = release.safe_member(root, member)
        if not path.is_file():
            continue
        body = release.read_file(path).decode("utf-8")
        name = declared_name(body)
        if name in result:
            raise ValueError("Duplicate generated skill name")
        result[name] = body
    return result


def audit_candidate(package: Path, expected_digest: str, generated_root: Path) -> dict:
    package = release.no_links(Path(package))
    receipt = plugin_bundle.verify_bundle(package, expected_digest)
    generated_root = release.no_links(Path(generated_root))
    host_docs = {host: generated_index(generated_root, host)
                 for host in ("claude", "codex")}
    entries = []
    seen = set()
    for item in receipt["files"]:
        path = item["path"]
        if not ENTRYPOINT.fullmatch(path):
            continue
        data = release.read_file(release.safe_member(package, path))
        if len(data) != item["size"] or release.digest(data) != item["sha256"]:
            raise ValueError("Candidate skill changed after verification")
        body = data.decode("utf-8")
        if not paths.GSTACK_BIN_REF.search(body):
            continue
        name = declared_name(body)
        if name in seen:
            raise ValueError("Duplicate legacy skill name")
        seen.add(name)
        entries.append((name, body))
    missing = {host: [] for host in host_docs}
    matched = {host: 0 for host in host_docs}
    over_500 = {host: 0 for host in host_docs}
    gap_counts = {key: 0 for key, _ in POLICY_HEADINGS}
    issues = []
    for name, legacy_body in sorted(entries):
        for host, docs in host_docs.items():
            row = compare_pair(name, legacy_body, docs.get(name))
            if row["status"] == "missing_generated":
                missing[host].append(name)
            else:
                matched[host] += 1
            if row["body_over_500_lines"]:
                over_500[host] += 1
            for gap in row["policy_gaps"]:
                gap_counts[gap] += 1
            if row["status"] != "static_match":
                issues.append({"host": host, **row})
    status = ("no_legacy_gstack_refs" if not entries else
              "migration_review_required" if issues else "static_mapping_present")
    return {"status": status,
            "bundle_digest": expected_digest, "skills_checked": len(entries),
            "matched": matched, "missing": missing, "over_500_body_lines": over_500,
            "policy_gap_counts": gap_counts, "issues": issues,
            "runtime_closure_verified": False, "host_compatibility_verified": False,
            "scope": "Literal generated name, body length and selected legacy headings only; "
                     "no semantic equivalence, generated provenance, runtime or host proof"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--expected-digest", required=True)
    parser.add_argument("--generated-root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = audit_candidate(args.package, args.expected_digest, args.generated_root)
    except (ValueError, OSError, UnicodeError, KeyError, TypeError):
        print('{"status":"blocked","message":"Gstack migration audit failed"}', file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "static_mapping_present" else 1


if __name__ == "__main__":
    raise SystemExit(main())
