# Contributing to SimonKDesign

This plugin is part of the SimonK plugin suite. Every skill ships with an
evaluation set and is enforced by a CI quality gate — contributions that skip
either will fail CI and cannot be merged.

## Repository layout

```
.claude-plugin/
  plugin.json          # plugin manifest (lists every skill path)
  marketplace.json     # marketplace entry
commands/              # slash-command entry points (e.g. /skdesign)
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

- Skills serve the **user's** art/design output — not this plugin's own behavior.
- Never dump the full pipeline at once: diagnose → reference → confirm direction →
  produce → review, one artifact at a time (the `skdesign` iterative-develop rule).
- Enforce the **AI-slop 3 principles** in every visual output: strip clutter
  (no emoji icons / over-decoration), monotone (≤ 3 UI colors), anchor on a
  confirmed reference. Forbidden: Inter (→ Pretendard / alt sans), pure black/gray
  (→ tinted neutrals), 4+ multi-color, bounce/elastic easing.
- Korean-default typography is **Pretendard**; fonts are recommended (with a
  Google Fonts preview URL), never silently imposed.
- Propagate the detected persona (low-tech / 고령 / 저연령) into sub-skill outputs:
  plain language, large body text (≥ 18pt), one-line term glosses, a 3-line TL;DR.
- Never punt a request — always offer a "can't do X, but Y is possible" alternative.
- Gate large outputs through `persona-validate` (SimonKCore) before completion;
  degrade to an inline self-check (AI-slop 3 + accessibility + one expert lens)
  when Core is absent.

## Commits & PRs

- Conventional Commits: `feat(skills):`, `fix(skills):`, `test(skills):`, `docs:`, `chore:`.
- Keep PRs scoped to one skill or one concern where possible.
- CI (`skills-ci` + `validate-plugin`) must be green before merge.

## License / provenance

MIT. Some infrastructure skills originate from Simon's SimonK stack and may
include gstack (garrytan, MIT) lineage; keep provenance in each `SKILL.md` and
in `NOTICE`.
