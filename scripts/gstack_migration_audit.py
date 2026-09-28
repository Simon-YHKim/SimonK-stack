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


def generated_index(root: Path, host: str) -> dict[str, tuple[str, str]]:
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
        result[name] = (member, body)
    return result


def generated_digest(documents: dict[str, tuple[str, str]]) -> str:
    """Pin the selected generated SKILL.md bytes, not their claimed origin."""
    members = {name: {"path": member, "sha256": release.digest(body.encode("utf-8"))}
               for name, (member, body) in sorted(documents.items())}
    return release.digest(release.encoded(members))


def generated_markdown_documents(root: Path,
                                 skills: dict[str, tuple[str, str]]) -> dict[str, tuple[str, str]]:
    """Read Markdown under declared skill folders, including support sections."""
    root = release.no_links(Path(root))
    documents = {}
    for skill_path, _ in skills.values():
        folder = release.safe_member(root, Path(skill_path).parent.as_posix())
        for path in sorted(folder.rglob("*")):
            if path.suffix.casefold() not in {".md", ".markdown"}:
                continue
            member = path.relative_to(root).as_posix()
            body = release.read_file(release.safe_member(root, member)).decode("utf-8")
            documents[member] = (member, body)
    if any(documents.get(member, (None, None))[1] != body
           for member, body in skills.values()):
        raise ValueError("Generated SKILL.md changed during Markdown scan")
    return documents


def generated_markdown_digest(documents: dict[str, tuple[str, str]]) -> str:
    """Pin all selected Markdown paths and bytes; this is not an origin proof."""
    members = {member: release.digest(body.encode("utf-8"))
               for member, body in sorted(documents.values())}
    return release.digest(release.encoded(members))


def _literal_link_counts(documents: dict[str, tuple[str, str]], prefix: str) -> dict:
    counts = [body.replace("\\", "/").casefold().count(prefix)
              for _, body in documents.values()]
    return {"files": sum(count > 0 for count in counts),
            "occurrences": sum(counts)}


def generated_root_links(documents: dict[str, tuple[str, str]], root: Path) -> dict:
    """Count literal links to the render folder; these need relocation review."""
    prefix = root.as_posix().replace("\\", "/").rstrip("/").casefold() + "/"
    return _literal_link_counts(documents, prefix)


def generated_user_home_gstack_links(documents: dict[str, tuple[str, str]]) -> dict:
    """Count literal links to a separately installed user-home Gstack tree."""
    return _literal_link_counts(documents, "~/.claude/skills/gstack/")


def generated_shell_home_gstack_links(documents: dict[str, tuple[str, str]]) -> dict:
    """Count either shell HOME spelling without exposing file bodies."""
    prefixes = ("$home/.claude/skills/gstack/", "${home}/.claude/skills/gstack/")
    counts = [sum(body.replace("\\", "/").casefold().count(prefix)
                  for prefix in prefixes) for _, body in documents.values()]
    return {"files": sum(count > 0 for count in counts), "occurrences": sum(counts)}


def generated_user_home_gstack_link_kinds(documents: dict[str, tuple[str, str]]) -> dict:
    """Group literal home links by first component; never emit path bodies."""
    prefix = "~/.claude/skills/gstack/"
    counts = {key: 0 for key in
              ("bin", "scripts", "docs", "other_asset_or_skill", "dynamic_or_root")}
    for _, body in documents.values():
        normalized = body.replace("\\", "/").casefold()
        for match in re.finditer(re.escape(prefix), normalized):
            component = re.match(r"[a-z0-9][a-z0-9._-]*", normalized[match.end():])
            head = component.group() if component else None
            kind = (head if head in {"bin", "scripts", "docs"} else
                    "other_asset_or_skill" if head else "dynamic_or_root")
            counts[kind] += 1
    return counts


def audit_candidate(package: Path, expected_digest: str, generated_root: Path,
                    expected_generated_digests: dict[str, str] | None = None,
                    expected_generated_markdown_digests: dict[str, str] | None = None) -> dict:
    package = release.no_links(Path(package))
    receipt = plugin_bundle.verify_bundle(package, expected_digest)
    generated_root = release.no_links(Path(generated_root))
    host_docs = {host: generated_index(generated_root, host)
                 for host in ("claude", "codex")}
    generated_digests = {host: generated_digest(docs) for host, docs in host_docs.items()}
    markdown_docs = {host: generated_markdown_documents(generated_root, docs)
                     for host, docs in host_docs.items()}
    markdown_digests = {host: generated_markdown_digest(docs)
                        for host, docs in markdown_docs.items()}
    root_links = {host: generated_root_links(docs, generated_root)
                  for host, docs in markdown_docs.items()}
    home_links = {host: generated_user_home_gstack_links(docs)
                  for host, docs in markdown_docs.items()}
    shell_home_links = {host: generated_shell_home_gstack_links(docs)
                        for host, docs in markdown_docs.items()}
    home_link_kinds = {host: generated_user_home_gstack_link_kinds(docs)
                       for host, docs in markdown_docs.items()}
    if expected_generated_digests is not None:
        if (set(expected_generated_digests) != set(generated_digests)
                or any(not re.fullmatch(r"[0-9a-f]{64}", value)
                       for value in expected_generated_digests.values())
                or expected_generated_digests != generated_digests):
            raise ValueError("Generated document digest mismatch")
    if expected_generated_markdown_digests is not None:
        if (set(expected_generated_markdown_digests) != set(markdown_digests)
                or any(not re.fullmatch(r"[0-9a-f]{64}", value)
                       for value in expected_generated_markdown_digests.values())
                or expected_generated_markdown_digests != markdown_digests):
            raise ValueError("Generated Markdown digest mismatch")
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
            generated = docs.get(name)
            row = compare_pair(name, legacy_body, generated[1] if generated else None)
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
              "migration_review_required" if issues or any(
                  row["occurrences"] for row in (*root_links.values(), *home_links.values(),
                                                  *shell_home_links.values()))
              else "static_mapping_present")
    return {"status": status,
            "bundle_digest": expected_digest, "skills_checked": len(entries),
            "generated_doc_digests": generated_digests,
            "generated_bytes_verified": expected_generated_digests is not None,
            "generated_markdown_digests": markdown_digests,
            "generated_markdown_files": {host: len(docs) for host, docs in markdown_docs.items()},
            "generated_markdown_bytes_verified": expected_generated_markdown_digests is not None,
            "generated_root_links": root_links,
            "generated_user_home_gstack_links": home_links,
            "generated_shell_home_gstack_links": shell_home_links,
            "generated_user_home_gstack_link_kinds": home_link_kinds,
            "matched": matched, "missing": missing, "over_500_body_lines": over_500,
            "policy_gap_counts": gap_counts, "issues": issues,
            "runtime_closure_verified": False, "host_compatibility_verified": False,
            "scope": "Literal generated name, body length, all generated Markdown "
                     "render-root/user-home/shell-HOME links and selected legacy headings only; "
                     "home link kinds are first-component hints, not executable-path proof; "
                     "digest pins are byte equality, not generated provenance; "
                     "no semantic equivalence, runtime or host proof"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--expected-digest", required=True)
    parser.add_argument("--generated-root", type=Path, required=True)
    parser.add_argument("--expected-claude-digest")
    parser.add_argument("--expected-codex-digest")
    parser.add_argument("--expected-claude-markdown-digest")
    parser.add_argument("--expected-codex-markdown-digest")
    args = parser.parse_args(argv)
    try:
        if bool(args.expected_claude_digest) != bool(args.expected_codex_digest):
            raise ValueError("Both generated digests are required together")
        generated_pins = ({"claude": args.expected_claude_digest,
                           "codex": args.expected_codex_digest}
                          if args.expected_claude_digest else None)
        if bool(args.expected_claude_markdown_digest) != bool(args.expected_codex_markdown_digest):
            raise ValueError("Both generated Markdown digests are required together")
        markdown_pins = ({"claude": args.expected_claude_markdown_digest,
                          "codex": args.expected_codex_markdown_digest}
                         if args.expected_claude_markdown_digest else None)
        result = audit_candidate(args.package, args.expected_digest, args.generated_root,
                                 generated_pins, markdown_pins)
    except (ValueError, OSError, UnicodeError, KeyError, TypeError):
        print('{"status":"blocked","message":"Gstack migration audit failed"}', file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "static_mapping_present" else 1


if __name__ == "__main__":
    raise SystemExit(main())
