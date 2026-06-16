---
name: skill-gen-agent
description: Use when the user wants to create, refactor, validate, or test a Claude Code Skill. Triggers on requests like "create a skill", "make a skill for X", "improve this skill", "refactor skill", "validate my skill", "test this skill", "스킬 만들어줘", "스킬 개선". Produces a complete skill package (SKILL.md + scripts + references) following Anthropic's progressive-disclosure guidelines, with automatic best-practices validation, optional self-testing, bilingual (Korean/English) interaction, and version tracking.
version: 0.5.0
compatibility:
  - python>=3.9
  - claude-code
---

# Skill-Gen Agent

Skill-Gen Agent is an enhanced successor to `skill-creator`. It turns an idea
into a production-grade Claude Code Skill through a structured, validated,
and optionally self-tested workflow.

It operates in **five modes**. Detect the user's intent and pick one:

| Mode | Trigger phrases | Entry section |
|------|-----------------|---------------|
| `create`   | "make a skill", "new skill", "스킬 만들어" | [Mode: Create](#mode-create) |
| `refactor` | "improve this skill", "refactor skill", "스킬 개선" | [Mode: Refactor](#mode-refactor) |
| `validate` | "check this skill", "validate", "lint" | [Mode: Validate](#mode-validate) |
| `test`     | "test this skill", "does this skill work" | [Mode: Test](#mode-test) |
| `version`  | "bump version", "changelog", "release" | [Mode: Version](#mode-version) |

If the mode is ambiguous, ask the user which mode they want with a single
short question — **do not** proceed on assumption.

---

## Communicating with the user

- Detect the user's language from their first message. If they write in
  Korean, **interact in Korean** but still write the final `SKILL.md` in
  English (skills are loaded by Claude whose internal language is English —
  English descriptions trigger more reliably). See
  `references/i18n.md` for rules.
- Be concise. Ask **at most 4 questions at a time**, grouped by topic.
- Never fabricate library behaviour. If you need current docs, use the
  `mcp__*query-docs` tool or `WebFetch`.
- Show the user the SKILL.md diff before writing, unless they have said
  "just do it" / "알아서 해줘".

---

## Mode: Create

A 7-step pipeline. Each step has a gate — do not advance until the
gate passes. Evaluation is built in **early**, not at the end.

### Step 1 — Capture intent (interview)

Read `references/interview.md` for the full 7-round question bank.
At minimum, run Rounds 1–4 and Round 5 (freedom level). Collect:

1. **What** does the skill do? (one sentence, verb-led)
2. **When** should Claude trigger it? (verbatim phrases + file/tool hooks)
3. **Output** format? (file, edits, report, side effect)
4. **Dependencies?** (libs, CLIs, MCP servers, network)
5. **Freedom level?** (high / medium / low — see `best-practices.md` §5)
6. **Target models?** (Haiku / Sonnet / Opus) — Haiku's floor sets
   the design budget if included.

**Gate:** you can restate the purpose in one sentence with no
compound "and...and...", name 3 trigger phrases, the output, the
top dependency, and the freedom level.

### Step 2 — Baseline & eval design

**Evaluation-driven development** (from the official guide). Before
writing SKILL.md, design how you will know it works:

1. Run the target task on Claude **without** a skill and note the
   failures or missing context.
2. Write 3 eval cases (`evals/cases.json`) targeting those gaps.
3. Read `references/testing.md` for the schema and the rule
   "grade the outcome, not the path".

**Gate:** `cases.json` exists and `test_skill.py --dry-run` passes.

### Step 3 — Research & design

- If the skill wraps a library/SDK/CLI, fetch current docs
  (`mcp__*query-docs` or `WebFetch`). **Do not** rely on memory.
- Read `references/anatomy.md` to decide what goes in SKILL.md vs
  `references/` vs `scripts/`, and to pick a disclosure pattern
  (high-level / domain-specific / conditional).
- Read `references/design-principles.md` for judgment calls the
  rules don't cover.

**Gate:** you have a written file plan (list of files + one-line
purpose each). Show it to the user for approval.

### Step 4 — Scaffold from template

Copy `templates/SKILL.md.tmpl` to the new skill directory and fill
in:

- YAML frontmatter (`name` kebab-case ≤64 chars, no `anthropic`/
  `claude`; `description` third-person ≤1024 chars; `version`;
  optional `compatibility`)
- `## Overview` — one paragraph
- `## Workflow` — numbered imperative steps (consider the checklist
  pattern from `best-practices.md` §9.1)
- `## References` — one level deep, all links direct from SKILL.md
- `## Scripts` — table of scripts with purpose

Prefer **gerund form** for the name (`processing-pdfs`,
`analyzing-spreadsheets`). Write the `description` in third person,
lead with "Use when...", include verbatim trigger phrases, state
the output, be pushy.

### Step 5 — Validate

```bash
python scripts/validate_skill.py <path-to-skill>
```

Checks: frontmatter validity, name/description constraints, third-
person description, semver, 500-line ceiling, no placeholder
markers, no Windows paths, no nested references, TOC on long
reference files, broken links, description score. **Gate:**
validator exits 0.

### Step 6 — Test

```bash
python scripts/test_skill.py <path-to-skill> \
    --cases <path-to-skill>/evals/cases.json \
    --out <path-to-skill>/evals/grading.json
```

Spawn a subagent with the skill loaded. Run each eval case. Grade
each assertion. For multi-model skills, run the harness against
each target model and record the model in `grading.json`.

**Gate:** all cases pass, or the user explicitly accepts known
failures.

### Step 7 — Version & package

```bash
python scripts/version_log.py <path-to-skill> init --version 0.1.0 \
    --message "Initial release"
```

Report to the user:
- Path to the new skill
- One-line description
- How to load (`~/.claude/skills/<name>/` user-wide or
  `.claude/skills/<name>/` project-local)
- Baseline grading result
- Next steps (observe Claude B in real use — see the Claude A /
  Claude B loop in `testing.md`)

---

## Mode: Refactor

For improving an existing skill.

1. Read the target `SKILL.md` in full.
2. Run `python scripts/validate_skill.py <path>` and capture findings.
3. Run `python scripts/refactor_skill.py <path> --analyze` which
   additionally reports:
   - Body length and section lengths (heuristic for "bloat")
   - Sections that look like reference material and should move to
     `references/`
   - Imperative vs. descriptive voice ratio
   - Whether the `description` looks "pushy" enough
4. Run `python scripts/refactor_skill.py <path> --fix` to preview
   **safe mechanical fixes** (Windows paths, missing TOCs on long
   reference files, trailing whitespace, missing final newline, CRLF).
   If they look correct, run again with `--apply`.
5. Present the remaining **semantic refactor plan** (things fix mode
   cannot touch — first-person descriptions, reserved names,
   placeholder markers, nested references, >500-line bodies) to the
   user as a checklist. Wait for approval.
6. Apply semantic changes one section at a time. After each, re-run
   `validate_skill.py`.
7. `version_log.py bump --minor --message "<summary>"`.

See `references/refactor-playbook.md` for common smells, the auto-fix
coverage table, and the manual fixes for semantic smells.

---

## Mode: Validate

Fast path. Just run the validator and report.

```bash
python scripts/validate_skill.py <path> --format human
```

If the user wants JSON for CI, add `--format json`.

---

## Mode: Test

For evaluating whether a skill actually works when invoked.

1. If `<skill>/evals/cases.json` exists, use it. Else generate cases
   interactively — ask the user for 2–3 real-world prompts.
2. Run `python scripts/test_skill.py <path> --cases <path>/evals/cases.json`.
3. Report pass/fail per case with grader evidence.
4. If failures exist and the user wants to fix them, switch to **Mode:
   Refactor** with the failing case as context.

See `references/testing.md` for the case file schema.

---

## Mode: Version

For bumping / logging. Thin wrapper around `version_log.py`.

```bash
python scripts/version_log.py <path> bump --patch --message "fix typo"
python scripts/version_log.py <path> bump --minor --message "add X"
python scripts/version_log.py <path> show
```

---

## References

- `references/anatomy.md` — Skill anatomy, the 3 disclosure patterns, one-level-deep rule
- `references/best-practices.md` — All validator-enforced rules (frontmatter, naming, description, progressive disclosure, freedom, scripts, workflows)
- `references/design-principles.md` — The *why* behind the rules (distilled from Anthropic engineering + Unix philosophy)
- `references/interview.md` — 7-round question bank for requirement gathering
- `references/quickstart.md` — End-to-end worked example (Mode: Create, start to finish)
- `references/refactor-playbook.md` — Common skill smells and fixes
- `references/testing.md` — Eval schema, evaluation-driven dev, Claude A / Claude B loop
- `references/i18n.md` — Bilingual interaction rules (Korean UI / English artifacts)

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/validate_skill.py` | Best-practices linter for SKILL.md packages |
| `scripts/test_skill.py` | Spawns a subagent and runs eval cases |
| `scripts/refactor_skill.py` | Analyzes existing skills and suggests fixes |
| `scripts/version_log.py` | Version bump + CHANGELOG management |
| `scripts/install_skill.py` | Copies a skill to `~/.claude/skills/` or a project-local dir (validates first, detects conflicts) |
| `scripts/tests/run_all.py` | Integration tests for all helper scripts (17 checks) |

## Templates

| Template | Purpose |
|----------|---------|
| `templates/SKILL.md.tmpl` | Starting SKILL.md with placeholders |
| `templates/script.py.tmpl` | Python script with argparse boilerplate |
| `templates/reference.md.tmpl` | Reference doc starter |
| `templates/cases.json.tmpl` | Eval cases starter |

## Principles

1. **Progressive disclosure.** SKILL.md is a menu; push depth into `references/`.
2. **Evals first.** Design tests before documentation. A skill without evals is a hypothesis.
3. **Validate everything.** Never hand a skill back without a passing `validate_skill.py` run.
4. **Outcome over path.** Grade the final state, not the sequence of tool calls.
5. **Third person in descriptions; imperative in workflows.**
6. **Fail loud, succeed quiet.** Validator and scripts exit non-zero with a concrete message on failure; silent on success.
7. **Claude is already smart.** Don't explain what the model already knows; add only the context that's specific to your domain.
8. **Iterate with Claude in the loop.** Watch Claude B use the skill; feed observations back to Claude A. See `testing.md`.

For deeper rationale, read `references/design-principles.md`.

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
