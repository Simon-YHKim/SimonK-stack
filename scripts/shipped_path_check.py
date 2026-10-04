#!/usr/bin/env python3
"""Fail on machine-specific absolute paths in shipped skill files (D-76 step 1).

Every tracked file under skills-src/ ships in the five-plugin candidate
(skill_release.collect copies `git ls-files skills-src/`), so this check scans
exactly that list. candidate_path_audit.py runs the same detector over every
receipt-verified member of a built candidate.

A finding is an absolute path that only works on one machine:
- user_home: a home folder with a concrete account name, in Windows
  (C:\\Users\\<name>), Git Bash (/c/Users/<name>), WSL (/mnt/c/Users/<name>),
  macOS (/Users/<name>) or Linux (/home/<name>) spelling;
- machine_root: one of this workstation's workspace roots (MACHINE_ROOTS) on
  any drive spelling, e.g. E:\\Coding Infra or /e/2ndB;
- claude_project_slug: a Claude project folder name derived from such a path,
  e.g. E--Coding-Infra or C--Users-<name>.

Placeholders (<name>, me, ...), $HOME/~/%USERPROFILE% forms and system
folders are not findings. MACHINE_ROOTS only knows this workstation's roots;
the user-home rule is general. A documented exception names a plugin-relative
file, the exact matched literal and its exact count in shipped_path_exceptions
.json, so one more occurrence still fails and a fixed file makes the entry stale.
Findings report file, line and kind only; matched text is never printed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parent
EXCEPTIONS = SCRIPTS / "shipped_path_exceptions.json"
SOURCE_PREFIX = "skills-src/"
MAX_BYTES = 8 * 1024 * 1024

SEP = r"(?:\\\\|\\|/)"
NAME = r"[^\\/\s\"'`<>|*?:;,()\[\]{}=]+"
# Drive spellings: C:\ C:/ C:\\ (escaped), Git Bash /c/, WSL /mnt/c/.
WIN_DRIVE = r"(?<![A-Za-z0-9])[A-Za-z]:" + SEP + "+"
POSIX_DRIVE = r"(?<![\w.~$/-])/(?:mnt/)?[A-Za-z]/"
# This workstation's workspace roots. Extend when a new local root appears.
MACHINE_ROOTS = r"(?:coding[ _-]?infra(?:-backup)?|coding|2ndb|simonk-plugins)"
ROOT_END = r"(?=" + SEP + r"|[\"'`\s)\],;]|$)"

USER_HOME = re.compile(
    r"(?:" + WIN_DRIVE + "|" + POSIX_DRIVE + r"|(?<![\w.~$/:-])/)"
    r"(?i:users|home)" + SEP + "+(?P<name>" + NAME + ")")
MACHINE_ROOT = re.compile(
    r"(?:" + WIN_DRIVE + "|" + POSIX_DRIVE + ")(?i:" + MACHINE_ROOTS + ")" + ROOT_END)
PROJECT_SLUG = re.compile(
    r"(?<![A-Za-z0-9-])[A-Za-z]--(?:(?i:users)-(?P<name>[A-Za-z0-9._]+)"
    r"|(?i:coding-infra|coding|2ndb)(?![A-Za-z0-9]))")

# Generic account names used in examples, fixtures and CI images.
PLACEHOLDER_USERS = frozenset({
    "me", "you", "user", "username", "yourname", "your-name", "your_name", "name",
    "someone", "example", "fixture", "test", "tester", "foo", "x", "alice", "bob",
    "runner", "runneradmin", "public", "default", "all users", "node", "ubuntu",
    "vscode", "codespace", "...", "\u2026"})
PLACEHOLDER_START = ("<", "{", "[", "$", "%", "*", ".", "\u2026")


def _concrete(name: str) -> bool:
    """A real account name; one-letter names (/Users/j/foo) are examples."""
    name = name.strip()
    return len(name) > 1 and not name.startswith(PLACEHOLDER_START) and (
        name.casefold() not in PLACEHOLDER_USERS)


def find_machine_paths(text: str) -> list[dict[str, object]]:
    """Return {line, kind, literal} rows; callers must not print literal."""
    rows = []
    for line_number, line in enumerate(text.splitlines(), 1):
        taken: list[tuple[int, int]] = []
        for kind, pattern in (("user_home", USER_HOME), ("machine_root", MACHINE_ROOT),
                              ("claude_project_slug", PROJECT_SLUG)):
            for match in pattern.finditer(line):
                name = match.groupdict().get("name")
                if name is not None and not _concrete(name):
                    continue
                if any(start < match.end() and match.start() < end for start, end in taken):
                    continue
                taken.append(match.span())
                rows.append({"line": line_number, "kind": kind, "literal": match.group(0)})
    return rows


def load_exceptions(path: Path = EXCEPTIONS) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"schema_version", "exceptions"} \
            or data["schema_version"] != 1 or not isinstance(data["exceptions"], list):
        raise ValueError("Invalid shipped path exception file")
    seen = set()
    for item in data["exceptions"]:
        if (not isinstance(item, dict)
                or set(item) != {"path", "literal", "count", "origin", "reason"}
                or not isinstance(item["path"], str) or item["path"].startswith(("/", "plugins/"))
                or not isinstance(item["literal"], str) or not item["literal"]
                or type(item["count"]) is not int or item["count"] < 1
                or item["origin"] not in {"source", "official"}
                or not isinstance(item["reason"], str) or len(item["reason"].strip()) < 20):
            raise ValueError("Invalid shipped path exception entry")
        key = (item["path"], item["literal"])
        if key in seen:
            raise ValueError("Duplicate shipped path exception entry")
        seen.add(key)
    return data["exceptions"]


def check_files(files, exceptions, *, require_exact: bool, key_of=lambda path: path) -> dict:
    """files: iterable of (path, text); key_of(path) is the plugin-relative key.

    An exception covers a literal only while it occurs at most COUNT times in
    that file; one more occurrence reports all of them. require_exact (source
    mode) also reports an exception that no longer matches exactly, so a fixed
    file cannot keep a stale allowance. A candidate subset may omit files.
    """
    allowed = {(e["path"], e["literal"]): e["count"] for e in exceptions}
    findings, stale, excepted, seen_keys, checked = [], [], 0, set(), 0
    for path, text in files:
        key = key_of(path)
        seen_keys.add(key)
        checked += 1
        rows = find_machine_paths(text)
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["literal"]] = counts.get(row["literal"], 0) + 1
        for row in rows:
            limit = allowed.get((key, row["literal"]))
            if limit is not None and counts[row["literal"]] <= limit:
                excepted += 1
                continue
            findings.append({"path": path, "line": row["line"], "kind": row["kind"]})
        if require_exact:
            stale.extend({"path": path, "reason": "exception_count_mismatch"}
                         for (exc_key, literal), count in allowed.items()
                         if exc_key == key and counts.get(literal, 0) < count)
    if require_exact:
        stale.extend({"path": e["path"], "reason": "exception_file_not_shipped"}
                     for e in exceptions
                     if e["origin"] == "source" and e["path"] not in seen_keys)
    status = "machine_paths_found" if findings or stale else "no_machine_paths"
    return {"status": status, "files_checked": checked, "findings": findings,
            "stale_exceptions": stale, "excepted_occurrences": excepted}


def plugin_relative(source_path: str) -> str:
    """skills-src/<skill>/<rest> -> skills/<skill>/<rest> (its path in a plugin)."""
    if not source_path.startswith(SOURCE_PREFIX):
        raise ValueError("Not a shipped source path")
    return "skills/" + source_path[len(SOURCE_PREFIX):]


def decode_text(data: bytes) -> str | None:
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def shipped_source_files(repo: Path = REPO):
    """Yield (plugin-relative path, text) for every tracked skills-src file."""
    listed = subprocess.run(["git", "-C", str(repo), "ls-files", "-z", "--", SOURCE_PREFIX],
                            capture_output=True, timeout=60, check=True).stdout
    for name in sorted(filter(None, listed.decode("utf-8").split("\0"))):
        path = repo / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
            continue
        text = decode_text(path.read_bytes())
        if text is not None:
            yield plugin_relative(name), text


def check_source(repo: Path = REPO, exceptions_path: Path = EXCEPTIONS) -> dict:
    return check_files(shipped_source_files(repo), load_exceptions(exceptions_path),
                       require_exact=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", type=Path, default=REPO,
                        help="SimonK-stack checkout to scan (default: this script's repo)")
    parser.add_argument("--exceptions", type=Path, default=EXCEPTIONS)
    args = parser.parse_args(argv)
    try:
        report = check_source(args.repo, args.exceptions)
    except (ValueError, OSError, subprocess.SubprocessError, json.JSONDecodeError):
        print('{"status":"blocked","message":"Shipped path check failed"}', file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "no_machine_paths" else 1


if __name__ == "__main__":
    raise SystemExit(main())
