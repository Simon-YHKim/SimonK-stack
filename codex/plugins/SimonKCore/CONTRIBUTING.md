# Contributing to SimonKCore

This plugin is the **shared-infrastructure** layer of the SimonK plugin suite —
delegation, model-routing, memory/knowledge tools, persona-validation, and
completion reporting that the other SimonK plugins (AIHub, Stack) consume. Every
skill ships with an evaluation set and is enforced by a CI quality gate —
contributions that skip either will fail CI and cannot be merged.

## Repository layout

```
.claude-plugin/
  plugin.json          # plugin manifest (lists every skill path)
  marketplace.json     # marketplace entry
commands/              # slash-command entry points (e.g. /find-skill, /simonk)
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
5. **Add an entry point** in `commands/` only if the skill is a genuine
   user-facing slash command (e.g. `/find-skill`, `/simonk`). Most Core skills
   are **infrastructure invoked by other plugins or auto-routed** (model-router,
   html-default-output, session hooks, the various `*-upgrade` skills) and do
   **not** get a command — the skill stays the single source of truth.

## Domain rules for this plugin

- Core is **shared infrastructure**, not a single-orchestrator domain plugin.
  Skills here are **consumed by the other SimonK plugins** (AIHub routes its AI
  pipelines through `model-router`; both AIHub and Stack call `persona-validate`
  before completion and `completion-report` to wrap up). Design each skill to be
  callable as a dependency, not just interactively.
- **Degrade gracefully when a sibling is absent.** A consumer may have Core
  installed without AIHub/Stack (or vice-versa). Detect missing dependencies and
  fall back rather than hard-failing.
- **`find-skill` is the router/dispatcher** over the rest of the suite. When you
  add or rename a skill, keep its routing references (backtick-quoted skill
  names, `[[wikilinks]]`) pointing at skills that actually exist — a dangling
  intra-plugin route breaks discovery. Never invent skill names.
- **Keep the two real user entry points thin.** `/find-skill` and `/simonk` just
  invoke their skill with `$ARGUMENTS`; all logic lives in the `SKILL.md`.
- **Secrets via env, never hardcoded.** State cost/latency caps and log model
  calls in any skill that touches an LLM or external API (e.g. `model-router`,
  `gcloud-helper`). Reference only current models (Claude Opus 4.8 / Sonnet 4.6 /
  Haiku 4.5 / Fable 5, Gemini 2.x).

## Commits & PRs

- Conventional Commits: `feat(skills):`, `fix(skills):`, `test(skills):`, `docs:`, `chore:`.
- Keep PRs scoped to one skill or one concern where possible.
- CI (`skills-ci` + `validate-plugin`) must be green before merge.

## License / provenance

MIT. Some infrastructure skills originate from Simon's SimonK stack and may
include gstack (garrytan, MIT) lineage; keep provenance in each `SKILL.md` and
in `NOTICE`.
