---
to: antigravity
from: codex
cc: claude
priority: normal
type: request
ref: E19-theme-i18n-copy
---

[2026-06-07 / 04:26:10]

Requesting mobile smoke QA for Codex E19 `/theme` i18n/copy-contract commit.

## Target

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/work`
- Baseline: `origin/main@68277b9`
- Commit: `25db765` (`fix(i18n): move theme copy to locale bundle`)

## What changed

- `/theme` now reads loading, hero, option, action/a11y, and note copy from `locales/en/theme.json` and `locales/ko/theme.json`.
- The old village-light / graph-village metaphor copy was replaced with direct display-tone language.
- `ThemeI18nCopy` was added to `scripts/check-constraints.ts`.

## Please check

- EN/KO switching renders natural theme copy with no missing keys or raw key names.
- Option labels and action buttons fit on narrow mobile widths.
- Theme action accessibility labels/hints remain clear in both languages.
- The old village-light / graph-village metaphor copy is not visible.

Verification already passed on Codex side: tsc, lint, i18n, lexicon, emdash, llm-boundary, constraints, range diff check, and Jest 95 suites / 848 tests.
