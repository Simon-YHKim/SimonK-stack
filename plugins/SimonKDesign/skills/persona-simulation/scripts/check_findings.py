#!/usr/bin/env python3
"""Fail closed when a persona HTML report omits visible file:line evidence."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
from typing import Optional


KIND = re.compile(r"\b(?:BLOCKER|DROPOUT|DISTRUST|CONFUSION)\b")
EVIDENCE = re.compile(r"[A-Za-z0-9_./\\()\-]+\.(?:tsx|ts|jsx|js|py|kt|swift):[1-9][0-9]*")
SCOPE = re.compile(r"PERSONA-SCOPE:\s*\S+")


class VisibleText(HTMLParser):
    """Read displayed text, not tag attributes, comments, scripts or styles."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag in {"head", "script", "style"}:
            self.hidden += 1
        elif not self.hidden:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"head", "script", "style"} and self.hidden:
            self.hidden -= 1
        elif not self.hidden:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


def check_report(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, f"missing or non-file report: {path}"
    try:
        raw = path.read_text(encoding="utf-8")
        parser = VisibleText()
        parser.feed(raw)
        parser.close()
    except (OSError, UnicodeError, ValueError) as error:
        return False, f"unreadable report: {path} ({type(error).__name__})"

    text = " ".join(parser.parts)
    findings = list(KIND.finditer(text))
    if not findings:
        if SCOPE.search(text):
            return True, "0 findings with explicit scope"
        return False, "0 findings without PERSONA-SCOPE"
    for index, finding in enumerate(findings):
        end = findings[index + 1].start() if index + 1 < len(findings) else len(text)
        if not EVIDENCE.search(text, finding.end(), end):
            return False, f"{finding.group()} without visible file:line evidence (finding {index + 1})"
    return True, f"{len(findings)} findings with visible file:line evidence"


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="*", type=Path)
    parser.add_argument("--expect", type=Path, help="exact report expected from this run")
    args = parser.parse_args(argv)

    if args.expect and args.reports and args.expect not in args.reports:
        print("FAIL: --expect is not among explicit reports")
        return 1
    if args.expect:
        reports = args.reports or [args.expect]
    else:
        reports = args.reports or sorted(Path.cwd().glob("persona-sim-*.html"))
    if not reports:
        print("FAIL: no persona-sim-*.html report found")
        return 1

    for path in reports:
        okay, result = check_report(path)
        if not okay:
            print(f"FAIL: {path}: {result}")
            return 1
    print(f"PASS: {len(reports)} report(s) checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
