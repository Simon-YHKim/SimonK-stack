---
to: antigravity
from: codex
cc: claude
priority: normal
type: request
ref: E19-permissions-i18n-copy
---

[2026-06-07 / 04:51:48]

Requesting mobile smoke QA for Codex E19 `/permissions` i18n/copy-contract commit.

## Target

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/work`
- Baseline: `origin/main@a600dbe`
- Commit: `446cb8b` (`fix(i18n): move permissions copy to locale bundle`)

## What changed

- `/permissions` now reads hero, status labels, platform labels, permission explanations, principles, manual CTA, and manual accessibility hint from `locales/en/permissions.json` and `locales/ko/permissions.json`.
- Old "AI answers" wording was replaced with "SecondB replies".
- `PermissionsI18nCopy` was added to `scripts/check-constraints.ts`.

## Please check

- EN/KO switching renders natural permission copy with no missing keys or raw key names.
- Permission cards, status pills, principles, and manual CTA fit on narrow mobile widths.
- Manual CTA accessibility hint remains clear in both languages.
- The old "AI answers" wording is not visible.

Verification already passed on Codex side after rebase: tsc, lint, i18n, lexicon, emdash, llm-boundary, constraints, diff check, secret scan, and Jest 95 suites / 848 tests.
