"""Package a skill folder as a ZIP that the claude.ai app accepts (Customize > Skills > Upload).

The app rejects a SKILL.md whose frontmatter has keys other than name, description,
license, compatibility, metadata and allowed-tools. Our skills carry version/author, so
this script moves every other key into `metadata` as a string. `allowed-tools` is moved
too: it names Claude Code tools, which do not exist in the app. `compatibility` is written
as one string of at most 500 chars, as the Agent Skills spec requires: a list such as
[claude-code, codex] becomes "claude-code, codex". YAML comments are dropped.

The ZIP root is a folder named after the skill. Output is deterministic (sorted entries,
fixed timestamps, Unix modes), so the same input gives the same bytes. A file that starts
with '#!' or has an exec bit (POSIX) is stored as 0755, every other file as 0644.

Never packaged: this build's own output (an --out folder inside the skill, *.zip.tmp),
secret-bearing files at any depth (.env, .env.*, *.pem, *.key, *.p12, *.pfx, id_rsa*,
id_ed25519*, .npmrc, .netrc, .pypirc; left out even when --include matches them and
listed by name in the report's excluded_secrets), evals/, caches and backups.

Usage:
  python scripts/claude_app_skill_zip.py skills-src/karpathy-guidelines --out dist/claude-app
  python scripts/claude_app_skill_zip.py <installed skill dir> --skill-md <app SKILL.md> \
      --include references/quick-rules.md --out <dir> --strict

--skill-md   use this SKILL.md instead of the one in the skill folder (an app edition)
--include    only package these files (relative paths or globs); SKILL.md is always included
--exclude    extra globs to leave out (on top of the defaults above)
--strict     fail when packaged Markdown still has Claude Code-only references
"""
import argparse
import fnmatch
import json
import os
import posixpath
import re
import stat
import sys
import zipfile
from pathlib import Path

KEEP_KEYS = ("name", "description", "license", "compatibility", "metadata")
DEFAULT_EXCLUDE = (
    "evals/*", "__pycache__/*", "*/__pycache__/*", "*.pyc", "*.bak", "*.bak*",
    "*.tmpl", ".DS_Store", ".git/*", "*.zip.tmp",
)
# Matched against the file name alone, so they apply at the root and at any depth.
SECRET_NAMES = (
    ".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx", "id_rsa*", "id_ed25519*",
    ".npmrc", ".netrc", ".pypirc",
)
COMPATIBILITY_MAX = 500
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):(.*)$")
BLOCK_RE = re.compile(r"^[|>][-+0-9]*$")
XML_TAG_RE = re.compile(r"</?[A-Za-z][^>]*>")
CLAUDE_CODE_ONLY = {
    "${CLAUDE_SKILL_DIR}": re.compile(r"\$\{CLAUDE_SKILL_DIR\}"),
    "~/.claude": re.compile(r"~/\.claude"),
    "_workspace/": re.compile(r"_workspace/"),
    "subagent_type": re.compile(r"subagent_type"),
}
ZIP_TIME = (1980, 1, 1, 0, 0, 0)
ZIP_UNIX = 3  # "made by Unix": extractors read the mode bits on every build platform


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


def scan_quotes(v):
    """([(index, char) outside quotes], True when a quote is still open at the end).

    A quote opens a quoted scalar only at the start of the value or, in a flow
    collection, at the start of an item; an apostrophe inside plain text is text."""
    flow = v[:1] in ("[", "{")
    chars, quote, i = [], None, 0
    while i < len(v):
        c = v[i]
        if quote == '"' and c == "\\":
            i += 2
            continue
        if quote and c == quote:
            if quote == "'" and v[i + 1:i + 2] == "'":
                i += 2
                continue
            quote = None
        elif not quote and c in "\"'" and (i == 0 or flow and v[:i].rstrip()[-1:] in ("[", "{", ",")):
            quote = c
        elif not quote:
            chars.append((i, c))
        i += 1
    return chars, quote is not None


def strip_comment(v):
    """A one-line YAML value without its comment ('#' at the start or after a space)."""
    v = v.strip()
    for i, c in scan_quotes(v)[0]:
        if c == "#" and (i == 0 or v[i - 1] in " \t"):
            return v[:i].rstrip()
    return v


def is_block_scalar(first):
    return bool(BLOCK_RE.match(first))


def lines_are_content(first):
    """True when indented lines after this value belong to it even if they start with '#':
    a '|' or '>' block scalar, or a quoted value that continues on the next line."""
    return is_block_scalar(first) or scan_quotes(first)[1]


def parse_entries(fm):
    """Top-level keys in order: [key, text after the colon, continuation lines].

    Comment lines are dropped, except indented lines of a '|' or '>' block scalar or of
    a multi-line quoted value (those are content). A trailing comment is cut from the
    text after the colon."""
    entries = []
    for line in fm.split("\n"):
        m = KEY_RE.match(line)
        if m and not line[:1].isspace():
            entries.append([m.group(1), strip_comment(m.group(2)), []])
        elif line.lstrip().startswith("#") and not (
                line[:1].isspace() and entries and lines_are_content(entries[-1][1])):
            continue
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


def flow_items(v):
    """Items of a flow sequence such as '[a, "b"]', or None when v is not a flat one."""
    if not (v.startswith("[") and v.endswith("]")):
        return None
    depth, cuts, end = 0, [], None
    for i, c in scan_quotes(v)[0]:
        if end is not None:
            return None
        if c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
        elif c == "," and depth == 1:
            cuts.append(i)
        if depth > 1:
            return None
        if depth == 0:
            end = i
    if end != len(v) - 1:
        return None
    parts = [v[a + 1:b].strip() for a, b in zip([0] + cuts, cuts + [end])]
    return [unquote(p) for p in parts if p]


def scalar(first, cont):
    """The string value of one entry (plain, quoted, folded, literal, block or flow list)."""
    if is_block_scalar(first):
        lines = [c.strip() for c in cont if c.strip()]
        return (" " if first[0] == ">" else "\n").join(lines)
    quoted = first[:1] in ('"', "'")
    lines = [x for x in (c.strip() if quoted else strip_comment(c) for c in cont) if x]
    if not first and lines and all(x.startswith("- ") for x in lines):
        return ", ".join(unquote(x[2:].strip()) for x in lines)
    text = " ".join(([first] if first else []) + lines)
    items = flow_items(text)
    if items is not None:
        return ", ".join(items)
    return text if lines else unquote(first)


def entry_text(e):
    head = f"{e[0]}:" + (f" {e[1]}" if e[1] else "")
    return "\n".join([head] + e[2])


def compatibility_text(e):
    """`compatibility` as the single string (at most 500 chars) the Agent Skills spec requires."""
    text = scalar(e[1], e[2]).strip()
    if not text:
        raise BuildError("compatibility is empty; name the environment or remove the key")
    if len(text) > COMPATIBILITY_MAX:
        raise BuildError(f"compatibility is {len(text)} chars; the spec allows {COMPATIBILITY_MAX}")
    return text


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

    out = [entry_text(by_key[k]) for k in ("name", "description", "license") if k in by_key]
    if "compatibility" in by_key:
        compat = compatibility_text(by_key["compatibility"])
        out.append(f"compatibility: {json.dumps(compat, ensure_ascii=False)}")
    if meta_lines:
        out.append("\n".join(["metadata:"] + meta_lines))
    return "\n".join(out) + "\n", [k for k, _ in moved], desc


def inside(path, root):
    """True when path is root or below it (case-insensitive where the OS is)."""
    p, r = os.path.normcase(str(path)), os.path.normcase(str(root))
    return p == r or p.startswith(r.rstrip(os.sep) + os.sep)


def is_secret(rel):
    return any(fnmatch.fnmatch(posixpath.basename(rel), g) for g in SECRET_NAMES)


def select_files(src, include, exclude, skip=()):
    """Packaged files, skipped symlinks and excluded secret files (all relative to src).

    `skip` holds absolute paths (files or folders) that are never packaged."""
    files, skipped_links, secrets = [], [], []
    for p in sorted(src.rglob("*")):
        if any(inside(p, s) for s in skip):
            continue
        rel = p.relative_to(src).as_posix()
        if p.is_symlink():
            skipped_links.append(rel)
            continue
        if not p.is_file() or rel == "SKILL.md":
            continue
        if is_secret(rel):
            secrets.append(rel)
            continue
        if any(fnmatch.fnmatch(rel, g) for g in DEFAULT_EXCLUDE + tuple(exclude)):
            continue
        if include and not any(fnmatch.fnmatch(rel, g) for g in include):
            continue
        files.append(rel)
    if include:
        missing = [g for g in include if not any(fnmatch.fnmatch(f, g) for f in files)]
        if missing:
            note = f"; secret files are never packaged: {secrets}" if secrets else ""
            raise BuildError(f"--include matched nothing: {missing}{note}")
    return files, skipped_links, secrets


def output_paths(src, out_dir, target):
    """Paths under src that a build writes and must not package on the next run."""
    out_real = out_dir.resolve()
    skip = [target.resolve(), target.with_suffix(".zip.tmp").resolve()]
    if inside(out_real, src) and os.path.normcase(str(out_real)) != os.path.normcase(str(src)):
        skip.append(out_real)
    return skip


def scan_claude_code_only(texts):
    found = {}
    for rel, text in texts.items():
        for label, rx in CLAUDE_CODE_ONLY.items():
            n = len(rx.findall(text))
            if n:
                found.setdefault(rel, {})[label] = n
    return found


def file_mode(path, data):
    """0o755 for a helper meant to run (an exec bit on POSIX, or a '#!' first line), else 0o644."""
    if os.name != "nt" and path.stat().st_mode & 0o111:
        return 0o755
    return 0o755 if data.startswith(b"#!") else 0o644


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

    out_dir = Path(out_dir)
    target = out_dir / f"{src.name}.zip"
    tmp = target.with_suffix(".zip.tmp")
    files, skipped_links, secrets = select_files(
        src, include, exclude, skip=output_paths(src, out_dir, target))
    texts = {"SKILL.md": skill_text}
    for rel in files:
        if rel.endswith(".md"):
            texts[rel] = (src / rel).read_text(encoding="utf-8", errors="replace")
    warnings = scan_claude_code_only(texts)
    if strict and warnings:
        raise BuildError(f"Claude Code-only references remain: {warnings}")

    out_dir.mkdir(parents=True, exist_ok=True)
    executables = []
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in ["SKILL.md"] + files:
            if rel == "SKILL.md":
                data, mode = skill_text.encode("utf-8"), 0o644
            else:
                data = (src / rel).read_bytes()
                mode = file_mode(src / rel, data)
            if mode == 0o755:
                executables.append(rel)
            info = zipfile.ZipInfo(f"{src.name}/{rel}", date_time=ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = ZIP_UNIX
            info.external_attr = (stat.S_IFREG | mode) << 16
            z.writestr(info, data)
    os.replace(tmp, target)
    return {
        "name": src.name,
        "zip": str(target),
        "bytes": target.stat().st_size,
        "files": ["SKILL.md"] + files,
        "executables": executables,
        "moved_to_metadata": moved,
        "description_chars": len(desc),
        "skill_md_lines": skill_text.count("\n"),
        "claude_code_only": warnings,
        "skipped_symlinks": skipped_links,
        "excluded_secrets": secrets,
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
