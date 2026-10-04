# Contributing to SimonKMarket

This plugin is part of the SimonK plugin suite. Every skill ships with an
evaluation set and is enforced by a CI quality gate — contributions that skip
either will fail CI and cannot be merged.

## Repository layout

```
.claude-plugin/
  plugin.json          # plugin manifest (lists every skill path)
  marketplace.json     # marketplace entry
commands/              # slash-command entry points (e.g. /skmarket)
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
   slash command. Most sub-skills (e.g. `pmf-analyzer`, `paid-ads-campaign`,
   `payment-integrator`) are routed by the `skmarket` orchestrator and don't need one.

## Domain rules for this plugin

- Skills serve the **user's** marketing / market-research / growth work — not this
  plugin's own behavior. The `skmarket` orchestrator stays the single source of
  truth for routing; sub-skills do one job each (don't duplicate the router's logic).
- **No claims without data.** Keep the 근거 → 가설 → 실험 → 결론 chain; mark estimates
  as estimates and cite sources (WebSearch/WebFetch). Quantify with scenarios
  (보수/기본/공격), prioritize hypotheses with ICE/RICE.
- **Honest, compliant marketing only.** No 과장·기만 카피 (route copy through
  `human-voice-guard`); no fake reviews or 여론 조작 — community work requires
  disclosure and human approval. Flag 개인정보·광고심의 regulation where relevant.
- **Never skip the gates**: the `persona-validate` (SimonKCore) 출시-전 게이트 —
  marketing-expert + target-user panel, 치명 리스크(과장·규제) 0 — before completion.
  Degrade gracefully (inline self-check) when SimonKCore is absent.
- **Respect budget/asset level.** Low-asset / low-tech users → 무료·저비용·노코드 first;
  never push paid PG/ads on a thin budget without warning. Gloss expert jargon
  (ICE/RICE·AARRR·ROAS/CAC·MoR·Incoterms·HS코드) on first use.
- Secrets via env, never hardcoded; state cost/latency caps where a skill calls
  an external API or paid channel.

## Commits & PRs

- Conventional Commits: `feat(skills):`, `fix(skills):`, `test(skills):`, `docs:`, `chore:`.
- Keep PRs scoped to one skill or one concern where possible.
- CI (`skills-ci` + `validate-plugin`) must be green before merge.

## License / provenance

MIT. Some infrastructure skills (수익화·분석 통합군) are shared with the SimonK stack
and may include gstack (garrytan, MIT) lineage; keep provenance in each `SKILL.md`
and in `NOTICE`.
