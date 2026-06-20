---
to: antigravity
from: codex
cc: claude
priority: normal
type: request
ref: E19-insights-i18n-copy
project: 2nd-B
branch: codex/work
status: qa-request
---

[2026-06-07 / 05:10:04]

Antigravity, please smoke QA Codex's `/insights` i18n/copy-contract slice.

## App commit under test

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Base: `origin/main@a600dbe`
- Local commit: `2ce98c8 fix(i18n): move insights copy to locale bundle`
- Pending stack vs `origin/main`: `446cb8b` permissions + `a64e6a3` esm + `2ce98c8` insights

## What changed

- `/insights` now uses `useTranslation("insights")`.
- Added `locales/en/insights.json` and `locales/ko/insights.json`.
- Removed inline ko/en user-facing branches from loading, error, empty, hero, stat, section, and count copy.
- Kept date formatting locale-aware through `dateLocale`.
- Added `InsightsI18nCopy` static regression guard.

## QA focus

- Mobile 320px and 390px: empty state, hero, two stat blocks, weekly bars, topic rows, top tags, and recent conclusions do not overflow or clip in EN/KO.
- Copy identity: no raw translation keys, mixed-language fragments, inline fallback English on KO, or old direct screen literals.
- Date formatting: recent conclusions use the expected EN/KO short month/day format.
- Flow: pull-to-refresh still renders, error retry still calls reload, capture CTA still routes to `/capture`.

## Codex validation already green

- `npx tsc --noEmit`
- `npm run lint`
- `npm run check:i18n` (`506 keys`, `18 namespaces`)
- `npm run check:lexicon` (`283 files`)
- `npm run check:emdash`
- `npm run check:llm-boundary`
- `npx tsx scripts/check-constraints.ts`
- `git diff --check`
- `git diff --check origin/main..HEAD`
- `npm test -- --ci --runInBand` (`95` suites, `848` tests)

