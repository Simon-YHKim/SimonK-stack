#!/usr/bin/env python3
"""Validate a Claude Code Skill package against Skill-Gen Agent best practices.

Usage:
    python validate_skill.py <path-to-skill-dir> [--format human|json]

Exit code is 0 iff there are no errors. Warnings do not fail the run.

Checks performed:
    - SKILL.md exists and has YAML frontmatter
    - Frontmatter has required fields: name, description, version
    - `name` is kebab-case and matches the directory name
    - `description` scores >= 0.6 on the trigger heuristic
    - SKILL.md body is under 500 lines (warn at 400)
    - No TODO/FIXME/<placeholder> markers
    - All `references/*.md` and `scripts/*` files linked from SKILL.md exist
    - No broken relative markdown links
    - `version` is valid semver
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[\w.]+)?(?:\+[\w.]+)?$")
KEBAB_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
TODO_RE = re.compile(r"\b(TODO|FIXME|XXX|<placeholder>)\b", re.IGNORECASE)
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
BODY_SOFT_LIMIT = 400
BODY_HARD_LIMIT = 500
NAME_MAX = 64
DESC_MAX = 1024
DESC_WARN = 900
RESERVED_NAME_WORDS = ("anthropic", "claude")
FIRST_PERSON_RE = re.compile(
    r"(?<![A-Za-z])(I\s+(?:can|will|help|am|have)|I'(?:ll|ve|m)|"
    r"you\s+can\s+use\s+(?:this|me)|you'(?:ll|re|ve))",
    re.IGNORECASE,
)
WINDOWS_PATH_RE = re.compile(
    r"[`\"']([a-zA-Z0-9_.-]+(?:\\[a-zA-Z0-9_.-]+)+)[`\"']"
)
LONG_REF_LINES = 100


@dataclass
class Finding:
    level: str  # "error" | "warning" | "info"
    code: str
    message: str
    file: str | None = None
    line: int | None = None


@dataclass
class Report:
    skill_path: str
    findings: list[Finding] = field(default_factory=list)

    def add(self, level: str, code: str, message: str,
            file: str | None = None, line: int | None = None) -> None:
        self.findings.append(Finding(level, code, message, file, line))

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_json(self) -> str:
        return json.dumps(
            {"skill_path": self.skill_path,
             "ok": self.ok,
             "findings": [asdict(f) for f in self.findings]},
            indent=2,
        )

    def to_human(self) -> str:
        lines = [f"Validating: {self.skill_path}", ""]
        if not self.findings:
            lines.append("  OK - no issues found.")
            return "\n".join(lines)
        for f in self.findings:
            loc = ""
            if f.file:
                loc = f" ({f.file}" + (f":{f.line}" if f.line else "") + ")"
            lines.append(f"  [{f.level.upper():7}] {f.code}: {f.message}{loc}")
        lines.append("")
        lines.append(f"  {len(self.errors)} error(s), "
                     f"{len(self.warnings)} warning(s)")
        lines.append(f"  Result: {'OK' if self.ok else 'FAIL'}")
        return "\n".join(lines)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str, int]:
    """Return (frontmatter_dict, body_text, body_start_line).

    Uses a minimal YAML parser so the script has zero dependencies.
    Supports scalar key: value and simple list (`- item`) entries at top
    level, which is all the skill frontmatter needs.
    """
    if not text.startswith("---"):
        raise ValueError("Missing opening --- for YAML frontmatter")
    # Split on lines to find the closing fence.
    lines = text.splitlines(keepends=False)
    if lines[0].strip() != "---":
        raise ValueError("Missing opening --- for YAML frontmatter")
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        raise ValueError("Missing closing --- for YAML frontmatter")

    fm_lines = lines[1:end_idx]
    body_lines = lines[end_idx + 1:]
    body_text = "\n".join(body_lines)

    data: dict[str, Any] = {}
    current_list_key: str | None = None
    buf_key: str | None = None
    buf_lines: list[str] = []

    def flush_folded() -> None:
        nonlocal buf_key, buf_lines
        if buf_key is not None:
            data[buf_key] = " ".join(
                l.strip() for l in buf_lines if l.strip()
            )
            buf_key = None
            buf_lines = []

    for raw in fm_lines:
        if not raw.strip():
            continue
        if raw.startswith("  ") and buf_key is not None:
            buf_lines.append(raw)
            continue
        if raw.lstrip().startswith("- ") and current_list_key is not None:
            data[current_list_key].append(raw.lstrip()[2:].strip())
            continue
        flush_folded()
        current_list_key = None
        if ":" not in raw:
            continue
        key, _, val = raw.partition(":")
        key = key.strip()
        val = val.strip()
        if val == "":
            # Could be list or folded scalar; peek next non-empty line.
            data[key] = []
            current_list_key = key
        elif val in (">", "|", ">-", "|-"):
            buf_key = key
            buf_lines = []
        else:
            # Strip simple quotes.
            if (val.startswith('"') and val.endswith('"')) or \
               (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            data[key] = val
    flush_folded()

    # If any "list" ended up empty, convert back to empty string for safety.
    for k, v in list(data.items()):
        if isinstance(v, list) and not v:
            data[k] = ""

    return data, body_text, end_idx + 2


def score_description(desc: str) -> tuple[float, list[str]]:
    """Heuristic quality score for a skill description, 0.0-1.0.

    Higher is better. Returns (score, reasons).
    """
    reasons: list[str] = []
    score = 0.0
    if not desc:
        return 0.0, ["description is empty"]

    d = desc.strip()
    dl = d.lower()

    # Length
    if len(d) >= 80:
        score += 0.15
    else:
        reasons.append("description is short (<80 chars)")
    if len(d) > 400:
        reasons.append("description is very long (>400 chars); may be clipped")

    # Leads with "Use when" or similar imperative trigger pattern
    if dl.startswith("use when") or dl.startswith("use this") \
            or dl.startswith("use for"):
        score += 0.2
    else:
        reasons.append("does not lead with 'Use when...'")

    # Mentions concrete trigger phrases
    if re.search(r'"[^"]{3,}"|"[^"]{3,}"', d) or "triggers on" in dl:
        score += 0.2
    else:
        reasons.append("no verbatim trigger phrases detected")

    # Mentions output / produces / returns
    if any(w in dl for w in ("produces", "returns", "outputs", "creates", "writes")):
        score += 0.15
    else:
        reasons.append("does not state the output")

    # Has concrete hooks (file extensions, tool names)
    if re.search(r"\.\w{2,5}\b", d) or re.search(r"\b[A-Z][A-Za-z0-9_]+\.\w+", d):
        score += 0.15

    # Pushy
    if any(w in dl for w in ("whenever", "always", "proactively")):
        score += 0.15

    score = min(score, 1.0)
    return score, reasons


def validate(skill_path: Path) -> Report:
    report = Report(skill_path=str(skill_path))
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        report.add("error", "E001", "SKILL.md not found")
        return report

    text = skill_md.read_text(encoding="utf-8")

    # Frontmatter
    try:
        fm, body, body_start = parse_frontmatter(text)
    except ValueError as e:
        report.add("error", "E002", f"Frontmatter: {e}", file="SKILL.md")
        return report

    # Strict YAML validation — catches escape bugs that the minimal parser
    # silently tolerates. Claude Code uses PyYAML-grade strict parsing when
    # loading skill frontmatter; anything that fails here will be loaded
    # only partially (truncated at the first stray unescaped quote).
    try:
        import yaml  # type: ignore
        try:
            raw_fm = text.split("---", 2)[1] if text.startswith("---") else ""
            yaml.safe_load(raw_fm)
        except yaml.YAMLError as e:  # type: ignore[attr-defined]
            report.add(
                "error",
                "E013",
                f"Strict YAML parse failed (Claude Code load risk — quotes likely unescaped in description): {e}",
                file="SKILL.md",
            )
    except ImportError:
        # PyYAML not installed — skip. Minimal parser already ran.
        pass

    # Required fields
    for required in ("name", "description", "version"):
        if required not in fm or not str(fm[required]).strip():
            report.add("error", "E003",
                       f"Frontmatter missing required field '{required}'",
                       file="SKILL.md")

    # name
    name = str(fm.get("name", ""))
    if name:
        if len(name) > NAME_MAX:
            report.add("error", "E004a",
                       f"name is {len(name)} chars (> {NAME_MAX} max)",
                       file="SKILL.md")
        if not KEBAB_RE.match(name):
            report.add("error", "E004",
                       f"name '{name}' is not kebab-case", file="SKILL.md")
        lower_name = name.lower()
        for reserved in RESERVED_NAME_WORDS:
            if reserved in lower_name:
                report.add("error", "E004b",
                           f"name '{name}' contains reserved word "
                           f"'{reserved}'", file="SKILL.md")
        if name != skill_path.name:
            report.add("warning", "W004",
                       f"name '{name}' does not match directory "
                       f"'{skill_path.name}'", file="SKILL.md")

    # version
    version = str(fm.get("version", ""))
    if version and not SEMVER_RE.match(version):
        report.add("error", "E005",
                   f"version '{version}' is not valid semver",
                   file="SKILL.md")

    # description
    desc = str(fm.get("description", ""))
    if desc:
        if len(desc) > DESC_MAX:
            report.add("error", "E006a",
                       f"description is {len(desc)} chars (> {DESC_MAX} max)",
                       file="SKILL.md")
        elif len(desc) > DESC_WARN:
            report.add("warning", "W006a",
                       f"description is {len(desc)} chars (near "
                       f"{DESC_MAX} cap)", file="SKILL.md")

        fp = FIRST_PERSON_RE.search(desc)
        if fp:
            report.add("error", "E006b",
                       f"description uses first/second person "
                       f"('{fp.group(0)}'); rewrite in third person",
                       file="SKILL.md")

        score, reasons = score_description(desc)
        if score < 0.6:
            report.add("warning", "W006",
                       f"description score {score:.2f} < 0.6: "
                       + "; ".join(reasons),
                       file="SKILL.md")
        else:
            report.add("info", "I006",
                       f"description score {score:.2f}",
                       file="SKILL.md")

    # Body length
    body_lines = body.count("\n") + 1 if body else 0
    if body_lines > BODY_HARD_LIMIT:
        report.add("error", "E007",
                   f"SKILL.md body has {body_lines} lines "
                   f"(> {BODY_HARD_LIMIT}); move content to references/",
                   file="SKILL.md")
    elif body_lines > BODY_SOFT_LIMIT:
        report.add("warning", "W007",
                   f"SKILL.md body has {body_lines} lines "
                   f"(> {BODY_SOFT_LIMIT} soft limit)",
                   file="SKILL.md")

    # Placeholder / TODO
    for i, line in enumerate(text.splitlines(), start=1):
        if TODO_RE.search(line):
            report.add("error", "E008",
                       f"placeholder/TODO marker: {line.strip()}",
                       file="SKILL.md", line=i)

    # Linked files exist
    for m in MD_LINK_RE.finditer(text):
        target = m.group(1).split("#", 1)[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (skill_path / target).resolve()
        try:
            resolved.relative_to(skill_path.resolve())
        except ValueError:
            continue  # out-of-skill link, skip
        if not resolved.exists():
            report.add("error", "E009",
                       f"broken relative link: {target}",
                       file="SKILL.md")

    # Backtick-quoted references/scripts paths
    for quoted in re.finditer(r"`(references/[^`]+|scripts/[^`]+|templates/[^`]+)`", text):
        rel = quoted.group(1)
        # Strip argparse-style suffixes after a space and markdown anchors
        rel_path = rel.split()[0].split("#", 1)[0]
        # Ignore wildcards and angle-bracket placeholders
        if "*" in rel_path or "<" in rel_path:
            continue
        resolved = (skill_path / rel_path).resolve()
        if not resolved.exists():
            report.add("warning", "W009",
                       f"referenced path not found: {rel_path}",
                       file="SKILL.md")

    # Windows-style backslash paths
    for i, line in enumerate(text.splitlines(), start=1):
        m = WINDOWS_PATH_RE.search(line)
        if m:
            report.add("error", "E011",
                       f"Windows-style backslash path '{m.group(1)}'; "
                       f"use forward slashes",
                       file="SKILL.md", line=i)

    # H2 structure
    if "## " not in body:
        report.add("warning", "W010",
                   "SKILL.md body has no H2 sections", file="SKILL.md")

    # Reference-file checks: nesting depth and TOC for long files
    refs_dir = skill_path / "references"
    if refs_dir.is_dir():
        for ref in sorted(refs_dir.glob("*.md")):
            ref_text = ref.read_text(encoding="utf-8")
            rel = ref.relative_to(skill_path).as_posix()

            # Nested reference: links to another references/*.md
            for m in MD_LINK_RE.finditer(ref_text):
                target = m.group(1).split("#", 1)[0].strip()
                if not target or target.startswith(
                        ("http://", "https://", "mailto:")):
                    continue
                # Resolve relative to ref file
                target_resolved = (ref.parent / target).resolve()
                try:
                    rel_from_skill = target_resolved.relative_to(
                        skill_path.resolve())
                except ValueError:
                    continue
                if rel_from_skill.parts and rel_from_skill.parts[0] \
                        == "references" and target_resolved != ref:
                    report.add("error", "E012",
                               f"reference file links to another "
                               f"reference file: {target}; flatten to "
                               f"one level deep",
                               file=rel)

            # Long reference without TOC
            ref_lines = ref_text.count("\n") + 1
            if ref_lines > LONG_REF_LINES:
                lowered = ref_text.lower()
                if "## contents" not in lowered \
                        and "## table of contents" not in lowered:
                    report.add("warning", "W013",
                               f"reference file is {ref_lines} lines "
                               f"(> {LONG_REF_LINES}) but has no "
                               f"'## Contents' table of contents",
                               file=rel)

    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("skill_path", type=Path, help="path to skill directory")
    p.add_argument("--format", choices=("human", "json"), default="human")
    args = p.parse_args(argv)

    if not args.skill_path.is_dir():
        print(f"error: {args.skill_path} is not a directory", file=sys.stderr)
        return 2

    report = validate(args.skill_path)
    if args.format == "json":
        print(report.to_json())
    else:
        print(report.to_human())
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
