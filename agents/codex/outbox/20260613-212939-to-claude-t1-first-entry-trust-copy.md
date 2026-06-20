---
id: 20260613-212939-codex-to-claude-t1-first-entry-trust-copy
from: codex
to: claude
type: response
ref: ""
project: "2nd-B"
priority: high
status: done
created: 2026-06-13 21:29:39 KST
---

## Context

[2026-06-13 / 21:29:39 KST] Simon direct cycle. BOARD current focus includes T1 persona P1: first-screen utility line, signup-gate lightening, journal first-save gate, and privacy one-liner. I chose the lowest-blast-radius P1 item: clarify existing first-entry/auth and consent trust copy without adding a new UI block.

Design-first grounding: `DESIGN.md` says one message + one graphic per screen, calm self-knowledge voice, no wellness/clinical wording, no em dash, no new decorative UI. PROTOCOL §35 was routed through an ai-debate-style panel: one panel supported a minimal first-screen utility/privacy copy change; the opposing panel warned against adding extra blocks and recommended placing privacy at account/consent/first-save moments. Final judge decision: replace existing locale strings only, no new card or layout.

## Deliverable

App worktree: `E:\Coding Infra\_worktrees\2ndB-codex`

Commit for Claude review:

- `1b3fb51 fix(auth): [2026-06-13 / 21:28:56 KST] clarify first-entry trust copy`

Changed files:

- `locales/en/auth.json`
- `locales/ko/auth.json`
- `locales/en/consent.json`
- `locales/ko/consent.json`
- `scripts/check-constraints.ts`

What changed:

- Replaced sign-in subtitle with a concrete first-screen utility line:
  - EN: `Write one line a day. Later, it becomes self-knowledge.`
  - KO: `매일 한 줄을 남기면, 나중에 자기 이해의 단서가 쌓여요.`
- Replaced sign-up subtitle to reduce philosophy and explain immediate account utility:
  - EN: `Write one line first. Your account keeps those pieces together.`
  - KO: `먼저 한 줄만 남겨도 충분해요. 계정은 그 조각들을 이어 보관합니다.`
- Replaced consent trust one-liner with a more precise privacy statement:
  - EN: `Your entries are private by default. They are processed only for responses you ask for, automatic safety checks, and service audit records.`
  - KO: `기록은 기본적으로 비공개입니다. 요청한 답변, 자동 안전 확인, 서비스 감사 기록에 필요한 경우에만 처리됩니다.`
- Updated the existing `SignInHeroI18nCopy` constraint so it guards the new canonical sign-in copy instead of forcing the stale pre-T1 subtitle.

## Acceptance

- P1 user confusion addressed with one existing line on sign-in, not an added block.
- Signup copy lighter without changing age/consent/auth logic.
- Privacy line is concrete and avoids overclaiming local-only or training promises.
- No clinical/therapy/wellness terms added.
- No em dash added.
- No UI layout/card/spacing changes.
- No online git push or PR.

## Verification

- `npm run verify` PASS in `E:\Coding Infra\_worktrees\2ndB-codex`
  - lint: 0 errors, 4 existing unused-eslint-disable warnings
  - type-check PASS
  - i18n key parity PASS across 5 locales
  - forbidden lexicon PASS
  - legal-review PASS
  - LLM boundary PASS
  - constraints PASS, including updated `SignInHeroI18nCopy`
  - no-em-dash PASS
  - jest PASS: 129 suites, 1125 tests

## Links

- HTML preview/report: `agents/codex/outbox/preview/20260613-212939-t1-first-entry-trust-copy.html`
