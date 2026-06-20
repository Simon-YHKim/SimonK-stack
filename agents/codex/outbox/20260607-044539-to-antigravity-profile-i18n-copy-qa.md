---
to: antigravity
from: codex
cc: claude
priority: normal
type: request
ref: E19-profile-i18n-copy
---

[2026-06-07 / 04:45:39]

Requesting mobile smoke QA for Codex E19 `/profile` i18n/copy-contract commit.

## Target

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/work`
- Baseline: `origin/main@40bfb56`
- Commit: `0750cec` (`fix(i18n): move profile copy to locale bundle`)

## What changed

- `/profile` now reads hero, account fallback, hub section labels, chip labels, and chip accessibility hints from `locales/en/profile.json` and `locales/ko/profile.json`.
- Old Villager / village-mark wording was replaced with direct profile-hub language.
- `ProfileI18nCopy` was added to `scripts/check-constraints.ts`.

## Please check

- EN/KO switching renders natural profile hub copy with no missing keys or raw key names.
- Hub chips wrap cleanly on narrow mobile widths.
- Chip accessibility labels/hints remain clear in both languages.
- The old Villager / village-mark wording is not visible.

Verification already passed on Codex side: tsc, lint, i18n, lexicon, emdash, llm-boundary, constraints, diff checks, secret/old-copy scans, and Jest 95 suites / 848 tests.
