#!/usr/bin/env python3
"""Run evaluation cases against a skill.

Usage:
    test_skill.py <skill-path> --cases <cases.json> [--out grading.json]
                              [--dry-run]

This script is a thin harness. It does two things:

1. **Structure check** — parses cases.json, verifies schema.
2. **Invocation helper** — for each case, prints the prompt the agent
   should run against a subagent loaded with the skill. The actual
   subagent invocation is handled by the Skill-Gen Agent orchestrator
   because spawning Claude subagents is outside this script's scope
   (stdlib-only, no anthropic SDK).

If `--dry-run` is set, the script only validates the cases file and
exits. Otherwise it writes a scaffold `grading.json` with all
assertions marked `pending`, which the agent fills in after running
each case.

See `references/testing.md` for the schema.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


def load_cases(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("cases.json must be a JSON object")
    for required in ("skill", "cases"):
        if required not in data:
            raise ValueError(f"cases.json missing '{required}'")
    if not isinstance(data["cases"], list) or not data["cases"]:
        raise ValueError("cases.json 'cases' must be a non-empty list")
    for i, c in enumerate(data["cases"]):
        if "id" not in c or "prompt" not in c or "assertions" not in c:
            raise ValueError(
                f"case[{i}] missing required fields (id, prompt, assertions)")
        if not isinstance(c["assertions"], list) or not c["assertions"]:
            raise ValueError(
                f"case[{i}] must have at least one assertion")
        for j, a in enumerate(c["assertions"]):
            if "id" not in a or "text" not in a:
                raise ValueError(
                    f"case[{i}].assertion[{j}] missing id or text")
    return data


def scaffold_grading(cases: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill": cases["skill"],
        "run_at": dt.datetime.utcnow().isoformat() + "Z",
        "results": [
            {
                "case_id": c["id"],
                "passed": 0,
                "failed": 0,
                "assertions": [
                    {
                        "id": a["id"],
                        "text": a["text"],
                        "passed": None,
                        "evidence": "pending",
                    }
                    for a in c["assertions"]
                ],
            }
            for c in cases["cases"]
        ],
    }


def print_agent_instructions(skill_path: Path, cases: dict[str, Any]) -> None:
    print("# Skill-Gen Agent test harness")
    print(f"# Skill:  {skill_path}")
    print(f"# Cases:  {len(cases['cases'])}")
    print()
    print("For each case below, the orchestrator should:")
    print("  1. Spawn a subagent with the skill loaded")
    print("  2. Run the prompt")
    print("  3. For each assertion, grade passed=true|false + evidence")
    print("  4. Update grading.json")
    print()
    for c in cases["cases"]:
        print(f"## case: {c['id']}")
        print(f"   prompt: {c['prompt']!r}")
        print("   assertions:")
        for a in c["assertions"]:
            print(f"     - [{a['id']}] {a['text']}")
        print()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("skill_path", type=Path)
    p.add_argument("--cases", type=Path, required=True)
    p.add_argument("--out", type=Path, default=None,
                   help="write scaffold grading.json here")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    if not args.skill_path.is_dir():
        print(f"error: {args.skill_path} is not a directory", file=sys.stderr)
        return 2
    if not args.cases.exists():
        print(f"error: {args.cases} not found", file=sys.stderr)
        return 2

    try:
        cases = load_cases(args.cases)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"error: invalid cases file: {e}", file=sys.stderr)
        return 2

    print_agent_instructions(args.skill_path, cases)

    if args.dry_run:
        print("dry-run ok")
        return 0

    out = args.out or (args.skill_path / "evals" / "grading.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(scaffold_grading(cases), f, indent=2)
    print(f"scaffold written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
