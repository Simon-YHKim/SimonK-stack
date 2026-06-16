---
name: perspectives
description: >
  Use when the user wants to audit the current session for blind
  spots and missing stakeholder perspectives — triggers
  "/perspectives", "관점 검증해줘", "내가 놓친 시각", "blind spot
  찾아줘", "critical review of this session". Produces an
  accumulating perspectives.md at the project root with one
  session-block per invocation. Each block runs a Core 5 audit
  (User, Business, Technical, Security, Future-self) plus 1-3
  session-specific stakeholders the LLM detects from context.
  Different from /codex (external Codex on code only), /careful
  (mode toggle, no artifact), /grill-me (plan/spec interview, not
  session), /plan-ceo-review (single CEO persona). The session
  itself is the input — what got decided, built, skipped — and
  the output is actionable blind spots for this session or next.
version: 1.0.0
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - AskUserQuestion
---

# /perspectives

Audit the current session for blind spots, append the findings to
`perspectives.md` at the project root, and surface 1-3 actionable
gaps before the session ends.

## Why this skill exists

The AI's view of a session is shaped by the user's prompts. Whatever
the user didn't think to ask gets silently un-considered. Code review
(`/codex`, `/code-review`) catches code defects. Plan review
(`/grill-me`, `/plan-ceo-review`) catches plan gaps. Neither catches
**the missing stakeholder** — the persona who wasn't named, the
constraint that wasn't surfaced, the failure mode that wasn't
imagined because no one in the room thinks like that user.

`perspectives.md` is the cumulative log of those missed perspectives,
written by the AI looking at its own work and asking "who would
disagree with this, and why?"

## The Core 5 (always audited)

| Category | The question | Examples of blind spots |
|---|---|---|
| **User** | What would the actual end user say? | Onboarding friction the founder skipped because they know the product, accessibility gaps, non-English users, the user who paid vs the user who uses |
| **Business** | What's the cost / margin / sustainability story? | Free tier abuse, churn triggers, support load, unit economics, pricing anchor confusion |
| **Technical** | What breaks at 10x / 100x scale, or under failure? | Single points of failure, n+1 queries, race conditions in the happy-path code, migration paths |
| **Security** | Who could misuse / abuse / breach this? | Authz bypass, PII exposure, secret leakage, audit log gaps, regulatory exposure (GDPR / Korean PIPA / COPPA) |
| **Future-self** | What will I curse past-me for, in 3 months / 1 year? | Hardcoded magic numbers, lack of feature flags, irreversible schema choices, missing observability |

These five are non-negotiable — every session block addresses all
five even if the answer is "no relevant gaps this session." Skipping
a category silently is the failure mode this skill exists to prevent.

## Session-specific perspectives (LLM detects 1-3 per session)

Beyond Core 5, the LLM names 1-3 stakeholders specific to the
session's actual content. Examples that have emerged in practice:

- **한국 사용자** when the session touched i18n / payments / KISA
- **OSS contributor** when the session shipped to a public repo
- **Free-tier user vs paid user** when the session touched billing
- **The reviewer who reads this PR cold** when the session shipped a PR
- **The on-call engineer at 3am** when the session touched infra
- **The founder's co-founder** when major direction decisions happened

These aren't templated — they emerge from re-reading the session
context and asking "whose voice is conspicuously absent here?"

## Execution sequence

### Step 1 — Inventory the current session

Without re-reading every message verbatim, summarize:

- **Files touched** — list paths + one-line per file of what changed
- **Decisions made** — extract from user/AI exchanges (e.g. "decided to merge X without CI", "skipped accessibility audit")
- **Skills invoked** — which tools/skills ran
- **What got skipped** — anything the user explicitly deferred or the AI proposed-but-didn't-do

This summary becomes the input to the Core 5 audit. It is NOT the
full session transcript — it's the founder-readable diff.

### Step 2 — Run the Core 5 audit

For each of `User / Business / Technical / Security / Future-self`,
ask:

1. **What did this session consider?** (what was addressed)
2. **What did it miss?** (the blind spot)
3. **Severity** — `low` / `medium` / `high` (does this need to be
   fixed in this session, the next session, or in a backlog item?)

A category with "no relevant gaps this session" is allowed; do not
fabricate findings. But the category line must still appear.

### Step 3 — Identify 1-3 session-specific perspectives

Re-read the session inventory and ask: "Whose voice is conspicuously
absent here?" Name 1-3 stakeholders that ARE NOT covered by the Core 5
and would have disagreed with something. Each gets the same three
questions as Core 5.

### Step 4 — Prepend to perspectives.md

If `perspectives.md` does not exist at the project root, create it
with the template at `templates/perspectives.md`. Otherwise prepend
the new session block (older blocks are preserved verbatim — no
edits, no deletes).

### Step 5 — Surface top 3 actionable blind spots

From the full audit (Core 5 + session-specific), pick the top 3
findings by severity * actionability. For each, use
`AskUserQuestion` with three options:

- **Address now** — open the finding as a task in this same session
- **Add to backlog** — note it in `vision.md` § Out of scope or
  `workingstyle.md` § Anti-patterns (whichever fits)
- **Acknowledge and move on** — record in `perspectives.md` that the
  finding was seen and accepted as-is (with reasoning)

This single round of questions is the deliverable. The skill does
not loop; user can re-invoke for another pass.

## Mode: /perspectives recall

When triggered as `/perspectives recall` or "이전 perspectives 적용":

1. Read `perspectives.md` if it exists
2. Summarize the top 5 prior findings (by recency * severity)
3. Match each against the current session — has it been addressed,
   re-emerged, or stayed latent?
4. Update the matching block with status (`resolved` / `recurring` /
   `latent`) and report to the user

No new block is prepended in recall mode. This is a read-and-update
operation.

## Mode: /perspectives focus &lt;stakeholder&gt;

Triggered as `/perspectives focus user` or "사용자 관점에서 다시 봐줘".

Run only the named stakeholder's audit, deeply. Skip the Core 5
breadth. Useful when the founder knows the area but wants the AI to
go deep on one perspective.

## SessionStart hook integration

When `perspectives.md` exists in a repo, the SessionStart hook adds
a banner to its stdout:

```
============================================================
[perspectives] perspectives.md detected in this repo.
[perspectives] Read it for accumulated blind-spot analysis
[perspectives] from prior sessions before making decisions.
============================================================
```

This is a hint, not a forced read. The LLM decides whether the
current session warrants pulling the file. Token cost: zero when
the file doesn't exist; one extra Read tool call when it does and
the LLM acts on the hint.

## Anti-patterns (do NOT do)

- ❌ Auto-overwriting prior session blocks. They accumulate; the
  history is the value.
- ❌ Fabricating findings to fill every Core 5 category. "No
  relevant gaps this session" is a valid finding.
- ❌ Treating perspectives.md as a critique log of the user. It's
  a critique of the AI's blind spots produced by working with the
  user — different target.
- ❌ Running on a single trivial task ("fix this typo"). The skill
  needs session breadth to find missing stakeholders. If the session
  has only 1-2 small actions, decline politely.
- ❌ Suggesting Address now / Backlog / Acknowledge for findings
  that the user already explicitly chose to defer. That's noise.
- ❌ Adding emojis to perspectives.md. The project's CLAUDE.md is
  explicit: humans should not feel like they're reading LLM output
  when they re-read a founder doc next year.

## Success criteria

The skill is complete when:

1. `perspectives.md` exists at the project root with the latest
   session block at the top.
2. All five Core categories appear in the new block, each with
   either a finding or an explicit "no gaps."
3. 1-3 session-specific stakeholders are named and audited.
4. Top 3 actionable findings have been surfaced via AskUserQuestion
   (or marked as acknowledged if the user already addressed them
   inline).
5. Older session blocks are preserved unchanged.

## Related skills (explicit boundaries)

- `/codex` (gstack) — external Codex CLI second opinion on a code
  diff. Different scope (code only, external model). This skill is
  **internal self-audit of the whole session**.
- `/careful` (gstack) — mode toggle that biases the LLM toward
  caution. No artifact, no accumulation. This skill produces a
  durable doc.
- `/grill-me` — 1-Q-at-a-time interview on a plan/spec. Input is
  the user's plan. This skill's input is the **session itself**.
- `/plan-ceo-review` — single CEO persona critique of a plan. This
  skill is **multi-stakeholder** by design.
- `/code-review` — diff-only review. This skill audits decisions
  and skipped work too, not just code.
- `/founder-context` — creates static identity/vision/design/work
  docs at project start. This skill creates a **living audit log**
  that accumulates across sessions.

## Trigger phrases (matched by description block above)

- `/perspectives`, `/perspectives recall`, `/perspectives focus <name>`
- "관점 검증해줘", "내가 놓친 시각", "perspectives 봐줘"
- "blind spot 찾아줘", "session audit"
- "critical review of this session"

## Operational notes

- The file lives at the project root next to `CLAUDE.md`,
  `vision.md`, etc. — never in `.claude/`.
- Commit it. The skill never auto-commits; the founder commits when
  ready, same convention as `/founder-context`.
- Re-invoking the skill multiple times in one session is fine —
  each invocation gets its own block with a timestamp. Use
  `/perspectives recall` between invocations to avoid repeating
  the same findings.
- For very long sessions (e.g. all-day pairing), invoking once at
  the end is better than three times in the middle — the audit
  benefits from seeing the full arc of decisions.

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
