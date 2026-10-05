# Contributing to SimonKAIHub

This plugin is part of the SimonK plugin suite. Every skill ships with an
evaluation set and is enforced by a CI quality gate — contributions that skip
either will fail CI and cannot be merged.

## Repository layout

```
.claude-plugin/
  plugin.json          # plugin manifest (lists every skill path)
  marketplace.json     # marketplace entry
commands/              # slash-command entry points (e.g. /skaihub)
agents/                # plugin-local subagents (optional)
skills/
  <skill-name>/
    SKILL.md           # the skill (YAML frontmatter + body)
    evals/cases.json   # REQUIRED — evaluation cases for the skill
    references/        # optional supporting docs
    scripts/           # optional helper scripts
.github/
  skill-ci/            # vendored, stdlib-only quality gate (run_ci.py + validators)
  workflows/skills-ci.yml
```

## The quality gate (CI)

Every PR runs `.github/skill-ci/run_ci.py`, which checks **each skill**:

1. **Lint** — `validate_skill.py` reports 0 errors (frontmatter, naming, body limits).
2. **Test coverage** — `evals/cases.json` exists.
3. **Cases schema** — the cases file passes `test_skill.py --dry-run`.
4. **Description quality** — description scores ≥ 0.6 (leads with "Use when…", states the output).

Run it locally before pushing:

```bash
python3 .github/skill-ci/run_ci.py
```

A skill that is missing evals, has a malformed `cases.json`, or has a weak
description will fail the gate.

## Adding or changing a skill

1. **Create the skill** under `skills/<skill-name>/SKILL.md` with valid frontmatter:
   - `name` (kebab-case, matches the directory), `description`, `version` (semver).
   - The `description` must lead with **"Use when …"**, keep concrete trigger
     phrases (Korean + English), and **state the output** (Produces/Returns…).
2. **Write `evals/cases.json`** (≥ 2 cases). Schema:
   ```json
   {
     "skill": "<skill-name>",
     "version": "<semver>",
     "cases": [
       {
         "id": "short-id",
         "prompt": "a realistic user prompt (KO or EN)",
         "assertions": [
           { "id": "assertion-id", "text": "what a correct response must do" }
         ]
       }
     ]
   }
   ```
3. **Register the skill** in `.claude-plugin/plugin.json` under `"skills"`.
4. **Run the gate**: `python3 .github/skill-ci/run_ci.py` → `RESULT: PASS`.
5. **Add an entry point** in `commands/` only if the skill is a user-facing
   slash command (most sub-skills are routed by the orchestrator and don't need one).

## Domain rules for this plugin

- Skills help the **user's** AI product/feature — not this plugin's own behavior.
- Never skip the eval and safety gates in any build flow.
- Do not hardcode a supposed current model lineup in skill recommendations or templates. Verify exact API IDs, availability, and pricing against provider documentation when making a product decision; keep unknown fields unset. Interactive subscription usage does not imply that a product API call is included.
- Secrets via env, never hardcoded; state cost/latency caps; log model calls.

## Commits & PRs

- Conventional Commits: `feat(skills):`, `fix(skills):`, `test(skills):`, `docs:`, `chore:`.
- Keep PRs scoped to one skill or one concern where possible.
- CI (`skills-ci` + `validate-plugin`) must be green before merge.

## License / provenance

MIT. Some infrastructure skills originate from Simon's SimonK stack and may
include gstack (garrytan, MIT) lineage; keep provenance in each `SKILL.md` and
in `NOTICE`.
