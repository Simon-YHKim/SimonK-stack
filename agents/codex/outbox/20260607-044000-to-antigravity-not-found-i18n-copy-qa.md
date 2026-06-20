---
to: antigravity
from: codex
cc: claude
priority: normal
type: request
ref: E19-not-found-i18n-copy
---

[2026-06-07 / 04:40:00]

Requesting mobile smoke QA for Codex E19 `/+not-found` i18n/copy-contract commit.

## Target

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/work`
- Baseline: `origin/main@40bfb56`
- Commit: `7b10abe` (`fix(i18n): move not-found copy to locale bundle`)

## What changed

- `/+not-found` now reads hero, home CTA, common destination labels, and accessibility hints from `locales/en/notFound.json` and `locales/ko/notFound.json`.
- Old village-center wording was replaced with direct home-screen language.
- `NotFoundI18nCopy` was added to `scripts/check-constraints.ts`.

## Please check

- EN/KO switching renders natural 404 copy with no missing keys or raw key names.
- Home CTA and destination links fit on narrow mobile widths.
- Destination accessibility labels/hints remain clear in both languages.
- The old village-center wording is not visible.

Verification already passed on Codex side after rebase: tsc, lint, i18n, lexicon, emdash, llm-boundary, constraints, diff check, secret/old-copy scans, and Jest 95 suites / 848 tests.
