"""Package a skill folder as a ZIP that the claude.ai app accepts (Customize > Skills > Upload).

The app rejects a SKILL.md whose frontmatter has keys other than name, description,
license, compatibility, metadata and allowed-tools. Our skills carry version/author, so
this script moves every other key into `metadata` as a string. `allowed-tools` is moved
too: it names Claude Code tools, which do not exist in the app.

The ZIP root is a folder named after the skill. Output is deterministic (sorted entries,
fixed timestamps), so the same input gives the same bytes.

Usage:
  python scripts/claude_app_skill_zip.py skills-src/karpathy-guidelines --out dist/claude-app
  python scripts/claude_app_skill_zip.py <installed skill dir> --skill-md <app SKILL.md> \
      --include references/quick-rules.md --out <dir> --strict

--skill-md   use this SKILL.md instead of the one in the skill folder (an app edition)
--include    only package these files (relative paths or globs); SKILL.md is always included
--exclude    extra globs to leave out (evals/, caches and backups are always left out)
--strict     fail when packaged Markdown still has Claude Code-only references
"""
import argparse
import fnmatch
import json
import os
import re
import sys
import zipfile
from pathlib import Path

KEEP_KEYS = ("name", "description", "license", "compatibility", "metadata")
DEFAULT_EXCLUDE = (
    "evals/*", "__pycache__/*", "*/__pycache__/*", "*.pyc", "*.bak", "*.bak*",
    "*.tmpl", ".DS_Store", ".git/*",
)
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):(.*)$")
XML_TAG_RE = re.compile(r"</?[A-Za-z][^>]*>")
CLAUDE_CODE_ONLY = {
    "${CLAUDE_SKILL_DIR}": re.compile(r"\$\{CLAUDE_SKILL_DIR\}"),
    "~/.claude": re.compile(r"~/\.claude"),
    "_workspace/": re.compile(r"_workspace/"),
    "subagent_type": re.compile(r"subagent_type"),
}
ZIP_TIME = (1980, 1, 1, 0, 0, 0)


class BuildError(Exception):
    pass


def split_frontmatter(text):
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise BuildError("SKILL.md must start with a '---' frontmatter block")
    end = text.find("\n---\n", 3)
    if end < 0:
        raise BuildError("SKILL.md frontmatter is not closed with '---'")
    return text[4:end + 1], text[end + 5:]


def parse_entries(fm):
    """Top-level keys in order: [key, text after the colon, continuation lines]."""
    entries = []
    for line in fm.split("\n"):
        m = KEY_RE.match(line)
        if m and not line[:1].isspace():
            entries.append([m.group(1), m.group(2).strip(), []])
        elif entries:
            entries[-1][2].append(line)
        elif line.strip():
            raise BuildError(f"unexpected frontmatter line: {line!r}")
    for e in entries:
        while e[2] and not e[2][-1].strip():
            e[2].pop()
    keys = [e[0] for e in entries]
    dup = sorted({k for k in keys if keys.count(k) > 1})
    if dup:
        raise BuildError(f"duplicate frontmatter keys: {dup}")
    return entries


def unquote(v):
    if len(v) >= 2 and v[0] == v[-1] == '"':
        try:
            return json.loads(v)
        except ValueError as exc:
            raise BuildError(f"cannot read quoted value {v[:40]!r}: {exc}") from exc
    if len(v) >= 2 and v[0] == v[-1] == "'":
        return v[1:-1].replace("''", "'")
    return v


def scalar(first, cont):
    """The string value of one entry (plain, quoted, folded, literal or a list)."""
    lines = [c.strip() for c in cont if c.strip()]
    if first[:1] in (">", "|") and len(first) <= 2:
        return (" " if first[0] == ">" else "\n").join(lines)
    if not cont:
        return unquote(first)
    if not first and lines and all(x.startswith("- ") for x in lines):
        return ", ".join(unquote(x[2:].strip()) for x in lines)
    return " ".join(([first] if first else []) + lines)


def entry_text(e):
    head = f"{e[0]}:" + (f" {e[1]}" if e[1] else "")
    return "\n".join([head] + e[2])


def app_frontmatter(fm, expected_name):
    entries = parse_entries(fm)
    by_key = {e[0]: e for e in entries}
    for required in ("name", "description"):
        if required not in by_key:
            raise BuildError(f"frontmatter has no '{required}'")

    name = scalar(by_key["name"][1], by_key["name"][2])
    if name != expected_name:
        raise BuildError(f"name '{name}' must match the folder name '{expected_name}'")
    if len(name) > 64 or not NAME_RE.match(name):
        raise BuildError(f"name '{name}' must be lowercase words joined by '-', at most 64 chars")
    if "claude" in name or "anthropic" in name:
        raise BuildError(f"name '{name}' uses a reserved word")
    desc = scalar(by_key["description"][1], by_key["description"][2])
    if not desc.strip():
        raise BuildError("description is empty")
    if len(desc) > 1024:
        raise BuildError(f"description is {len(desc)} chars; the app allows 1024")
    if XML_TAG_RE.search(desc):
        raise BuildError("description contains an XML tag")

    moved = [(e[0], scalar(e[1], e[2])) for e in entries if e[0] not in KEEP_KEYS]
    meta = by_key.get("metadata")
    meta_lines = []
    indent = "  "
    if meta:
        if meta[1]:
            raise BuildError("inline 'metadata:' values are not supported; use an indented block")
        meta_lines = list(meta[2])
        first_child = next((c for c in meta_lines if c.strip()), "")
        indent = first_child[: len(first_child) - len(first_child.lstrip())] or "  "
        existing = {KEY_RE.match(c.strip()).group(1) for c in meta_lines
                    if c[:1].isspace() and KEY_RE.match(c.strip())}
        clash = sorted(k for k, _ in moved if k in existing)
        if clash:
            raise BuildError(f"metadata already has {clash}")
    meta_lines += [f"{indent}{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in moved]

    out = [entry_text(by_key[k]) for k in KEEP_KEYS[:4] if k in by_key]
    if meta_lines:
        out.append("\n".join(["metadata:"] + meta_lines))
    return "\n".join(out) + "\n", [k for k, _ in moved], desc


def select_files(src, include, exclude):
    files, skipped_links = [], []
    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src).as_posix()
        if p.is_symlink():
            skipped_links.append(rel)
            continue
        if not p.is_file() or rel == "SKILL.md":
            continue
        if any(fnmatch.fnmatch(rel, g) for g in DEFAULT_EXCLUDE + tuple(exclude)):
            continue
        if include and not any(fnmatch.fnmatch(rel, g) for g in include):
            continue
        files.append(rel)
    if include:
        missing = [g for g in include if not any(fnmatch.fnmatch(f, g) for f in files)]
        if missing:
            raise BuildError(f"--include matched nothing: {missing}")
    return files, skipped_links


def scan_claude_code_only(texts):
    found = {}
    for rel, text in texts.items():
        for label, rx in CLAUDE_CODE_ONLY.items():
            n = len(rx.findall(text))
            if n:
                found.setdefault(rel, {})[label] = n
    return found


def build(src, out_dir, skill_md=None, include=(), exclude=(), strict=False):
    src = Path(src).resolve()
    if not src.is_dir():
        raise BuildError(f"not a folder: {src}")
    md_path = Path(skill_md).resolve() if skill_md else src / "SKILL.md"
    if not md_path.is_file():
        raise BuildError(f"SKILL.md not found: {md_path}")
    fm, body = split_frontmatter(md_path.read_text(encoding="utf-8"))
    new_fm, moved, desc = app_frontmatter(fm, src.name)
    skill_text = f"---\n{new_fm}---\n{body}"

    files, skipped_links = select_files(src, include, exclude)
    texts = {"SKILL.md": skill_text}
    for rel in files:
        if rel.endswith(".md"):
            texts[rel] = (src / rel).read_text(encoding="utf-8", errors="replace")
    warnings = scan_claude_code_only(texts)
    if strict and warnings:
        raise BuildError(f"Claude Code-only references remain: {warnings}")

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{src.name}.zip"
    tmp = target.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in ["SKILL.md"] + files:
            info = zipfile.ZipInfo(f"{src.name}/{rel}", date_time=ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            data = skill_text.encode("utf-8") if rel == "SKILL.md" else (src / rel).read_bytes()
            z.writestr(info, data)
    os.replace(tmp, target)
    return {
        "name": src.name,
        "zip": str(target),
        "bytes": target.stat().st_size,
        "files": ["SKILL.md"] + files,
        "moved_to_metadata": moved,
        "description_chars": len(desc),
        "skill_md_lines": skill_text.count("\n"),
        "claude_code_only": warnings,
        "skipped_symlinks": skipped_links,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("skill_dir")
    ap.add_argument("--out", required=True)
    ap.add_argument("--skill-md")
    ap.add_argument("--include", action="append", default=[])
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args(argv)
    try:
        report = build(a.skill_dir, a.out, a.skill_md, a.include, a.exclude, a.strict)
    except BuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
