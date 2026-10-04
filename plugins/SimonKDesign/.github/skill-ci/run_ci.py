#!/usr/bin/env python3
"""SimonK plugin skills quality gate (CI entry point).

Runs four checks against every skill under ``skills/<name>/``:

1. **Structure / lint** — ``validate_skill.py`` must report 0 errors.
2. **Test coverage** — every skill MUST ship ``evals/cases.json``.
3. **Cases schema**  — ``test_skill.py --dry-run`` must parse the cases.
4. **Description quality gate** — no W006 (description score < 0.6).

Stdlib only; safe to run in CI without ``pip install``. Child Python processes
and captured output use UTF-8 independently of the parent console locale.
Exits non-zero if any skill fails any check, printing a per-skill summary table.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent  # repo root (.github/skill-ci -> repo)
SKILLS = ROOT / "skills"
VALIDATE = HERE / "validate_skill.py"
TEST = HERE / "test_skill.py"


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, capture_output=True)
    try:
        output = ((p.stdout or b"") + (p.stderr or b"")).decode("utf-8")
    except UnicodeDecodeError:
        return 2, "invalid UTF-8 child output"
    return p.returncode, output


def check_skill(d: Path) -> tuple[bool, list[str]]:
    fails: list[str] = []

    # 1. validate_skill.py — 0 errors (rc==0 means report.ok)
    rc, out = run([sys.executable, "-X", "utf8", str(VALIDATE), str(d), "--format", "json"])
    if rc != 0:
        # surface the error codes for the log
        codes = ""
        try:
            data = json.loads(out)
            findings = data.get("findings") or data.get("issues") or []
            codes = " ".join(
                f.get("code", "?") for f in findings if f.get("level") == "error"
            )
        except Exception:
            codes = "(see log)"
        fails.append(f"validator errors [{codes}]")

    # 4. description quality gate — W006 = description score < 0.6
    if "W006" in out:
        fails.append("description score < 0.6 (W006)")

    # 2. evals/cases.json must exist
    cases = d / "evals" / "cases.json"
    if not cases.exists():
        fails.append("missing evals/cases.json")
    else:
        # 3. cases must parse (dry-run)
        rc2, _ = run(
            [sys.executable, "-X", "utf8", str(TEST), str(d), "--cases", str(cases), "--dry-run"]
        )
        if rc2 != 0:
            fails.append("cases.json failed dry-run")

    return (not fails), fails


def main() -> int:
    if not SKILLS.is_dir():
        print(f"error: {SKILLS} not found", file=sys.stderr)
        return 2
    skills = sorted(p for p in SKILLS.iterdir() if (p / "SKILL.md").exists())
    if not skills:
        print("error: no skills found", file=sys.stderr)
        return 2

    print(f"skills quality gate - {len(skills)} skills under {SKILLS.name}/\n")
    any_fail = False
    for d in skills:
        ok, fails = check_skill(d)
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {d.name}" + ("" if ok else "  - " + "; ".join(fails)))
        any_fail = any_fail or not ok

    print()
    if any_fail:
        print("RESULT: FAIL - fix the items above before merging.")
        return 1
    print(f"RESULT: PASS - all {len(skills)} skills clean (lint + evals + quality).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
