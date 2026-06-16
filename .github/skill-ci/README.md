# skill-ci — SimonK-stack skills quality gate

`run_ci.py` is the CI entry point that enforces a uniform quality bar across
**every** skill in this repo, in both roots:

- `skills-src/<name>/` — distributable skill sources
- `.claude/skills/<name>/` — dev skills loaded by Claude Code

It is the stack-layout adaptation of the SimonKAIHub plugin gate. Unlike that
copy, it does **not** vendor the validator/test harness — it calls the
canonical in-repo pair under
`.claude/skills/skill-gen-agent/scripts/{validate_skill,test_skill}.py`.

## What it checks (per skill)

| # | Check | Tool | Failure |
|---|-------|------|---------|
| 1 | Structure / lint | `validate_skill.py --format json` | any `error`-level finding (rc ≠ 0) |
| 2 | Test coverage | filesystem | `evals/cases.json` missing |
| 3 | Cases schema | `test_skill.py --dry-run` | cases file fails to parse |
| 4 | Description quality | `validate_skill.py` | `W006` (description score < 0.6) |

It prints a per-skill `PASS` / `FAIL` table (labelled by root-relative path so
same-named skills across roots are distinguishable) and exits non-zero on any
failure, ending with a verbatim `RESULT: PASS` or `RESULT: FAIL` line.

## Run locally

```bash
python3 .github/skill-ci/run_ci.py
```

Stdlib only — no `pip install` needed. CI runs the identical command via
`.github/workflows/skills-ci.yml` (checkout + setup-python 3.11).

## cases.json schema

Each `evals/cases.json` is an object:

```json
{
  "skill": "<skill-name>",
  "version": "<frontmatter version>",
  "cases": [
    {
      "id": "<case-id>",
      "prompt": "<KO or EN user prompt that should trigger the skill>",
      "assertions": [
        { "id": "<assertion-id>", "text": "<observable expectation>" }
      ]
    }
  ]
}
```

Minimum 2 cases, grounded in the skill's real description / triggers /
outputs, with a mix of Korean and English prompts.
