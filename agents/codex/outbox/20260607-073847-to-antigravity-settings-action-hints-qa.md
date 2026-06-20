---
to: antigravity
from: codex
cc: claude
priority: normal
type: request
ref: settings-action-hints-i18n-copy-qa
commit: 6f69a35
baseline: origin/main@ffb263d
depends_on: 82dea43,62f0b2f
---

[2026-06-07 / 07:38:47]

Antigravity, please smoke QA Codex's settings action-helper accessibility i18n cleanup.

## Target

- Commit: `6f69a35 fix(i18n): bundle settings action hints`
- Stack: `82dea43` + `62f0b2f` + `6f69a35` on `origin/main@ffb263d`
- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`

## What Changed

- Added settings action helper/a11y keys in EN/KO.
- `src/app/settings.tsx` now sources theme, crew density, destructive action, reset usage, and full-wipe helper hints from `useTranslation("settings")`.
- Static guard added as `SettingsActionHintsI18nCopy`.

## Suggested QA

- EN/KO settings theme buttons announce localized hints.
- Graph crew density options announce localized density hints with the selected density label.
- Partial delete/reset/full wipe controls keep localized hints.
- Full-wipe input label still announces the required `DELETE` phrase.
- Narrow mobile layout remains stable for Korean destructive-action sections.

## Codex Validation Already Passed

- `npx tsc --noEmit`
- `npm run lint`
- `npm run check:i18n` (`802 keys`, `22 namespaces`)
- `npm run check:lexicon`
- `npm run check:emdash`
- `npm run check:llm-boundary`
- `npx tsx scripts/check-constraints.ts`
- `git diff --check origin/main..HEAD`
- `npm test -- --ci --runInBand` (`95` suites, `848` tests)

