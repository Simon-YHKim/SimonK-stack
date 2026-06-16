#!/usr/bin/env python3
"""SimonK-stack skills quality gate (CI entry point).

Adapted from the SimonKAIHub plugin gate for this repo's TWO-root layout:
skills live under both ``skills-src/<name>/`` (distributable sources) and
``.claude/skills/<name>/`` (dev skills). Every directory containing a
``SKILL.md`` under either root is scanned.

Per skill, four checks must pass:

1. **Structure / lint** — the in-repo ``validate_skill.py`` reports 0 errors.
2. **Test coverage** — the skill ships ``evals/cases.json``.
3. **Cases schema**  — ``test_skill.py --dry-run`` parses the cases file.
4. **Description quality gate** — no W006 (description score < 0.6).

Unlike the SimonKAIHub copy, this gate does NOT vendor the validator/test
scripts — it calls the canonical in-repo pair under
``.claude/skills/skill-gen-agent/scripts/`` (resolved relative to repo root).

Stdlib only; safe to run in CI without ``pip install``. Exits non-zero if
any skill fails any check, printing a per-skill PASS/FAIL table.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent  # repo root (.github/skill-ci -> repo)
SKILL_ROOTS = (ROOT / "skills-src", ROOT / ".claude" / "skills")
SCRIPTS = ROOT / ".claude" / "skills" / "skill-gen-agent" / "scripts"
VALIDATE = SCRIPTS / "validate_skill.py"
TEST = SCRIPTS / "test_skill.py"


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def check_skill(d: Path) -> tuple[bool, list[str]]:
    fails: list[str] = []

    # 1. validate_skill.py — 0 errors (rc==0 means report.ok)
    rc, out = run([sys.executable, str(VALIDATE), str(d), "--format", "json"])
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
            [sys.executable, str(TEST), str(d), "--cases", str(cases), "--dry-run"]
        )
        if rc2 != 0:
            fails.append("cases.json failed dry-run")

    return (not fails), fails


def discover() -> list[tuple[str, Path]]:
    """Return sorted (label, dir) for every SKILL.md under both roots.

    The label is the root-relative path so the report disambiguates same-named
    skills across roots (e.g. ``commit`` exists in both ``.claude/skills`` and
    historically could exist in ``skills-src``).
    """
    found: list[tuple[str, Path]] = []
    for root in SKILL_ROOTS:
        if not root.is_dir():
            continue
        for d in sorted(root.iterdir()):
            if (d / "SKILL.md").exists():
                found.append((d.relative_to(ROOT).as_posix(), d))
    return found


def main() -> int:
    for script in (VALIDATE, TEST):
        if not script.exists():
            print(f"error: required script not found: {script}", file=sys.stderr)
            return 2

    skills = discover()
    if not skills:
        print("error: no skills found under skills-src/ or .claude/skills/",
              file=sys.stderr)
        return 2

    roots = ", ".join(r.relative_to(ROOT).as_posix() for r in SKILL_ROOTS
                      if r.is_dir())
    print(f"skills quality gate — {len(skills)} skills under {roots}\n")
    any_fail = False
    for label, d in skills:
        ok, fails = check_skill(d)
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {label}" + ("" if ok else "  — " + "; ".join(fails)))
        any_fail = any_fail or not ok

    print()
    if any_fail:
        print("RESULT: FAIL — fix the items above before merging.")
        return 1
    print(f"RESULT: PASS — all {len(skills)} skills clean "
          f"(lint + evals + quality).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
