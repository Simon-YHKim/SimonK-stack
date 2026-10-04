# skill-ci — vendored skills quality gate

Self-contained CI tooling that enforces a professional quality bar on every
skill in this plugin. Runs in `.github/workflows/skills-ci.yml` on every PR.

## What it checks (per skill under `skills/<name>/`)

| # | Check | Tool | Fails when |
|---|-------|------|------------|
| 1 | Structure / lint | `validate_skill.py` | frontmatter missing required fields, bad naming, body over limit, etc. (any **error**) |
| 2 | Test coverage | `run_ci.py` | `evals/cases.json` is missing |
| 3 | Cases schema | `test_skill.py --dry-run` | `cases.json` is malformed |
| 4 | Description quality | `validate_skill.py` (W006) | description scores < 0.6 (doesn't lead with "Use when…" / doesn't state output) |

`run_ci.py` is the entry point; it shells out to the two vendored scripts and
prints a per-skill PASS/FAIL table, exiting non-zero on any failure.

## Run locally

```bash
python3 .github/skill-ci/run_ci.py
```

## Provenance

`validate_skill.py` and `test_skill.py` are vendored (pinned copies) from
`skill-gen-agent` in [SimonK-stack](https://github.com/Simon-YHKim/SimonK-stack)
(MIT). Vendored so CI is reproducible and has no external dependency — both
scripts are stdlib-only. Re-sync when the upstream validator changes.

## Adding a new skill

A new `skills/<name>/` will fail CI until it has:
- a valid `SKILL.md` (name, description, version), and
- `evals/cases.json` with at least one case (≥2 recommended).
