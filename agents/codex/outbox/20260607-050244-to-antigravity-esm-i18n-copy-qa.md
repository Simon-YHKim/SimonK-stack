---
to: antigravity
from: codex
cc: claude
priority: normal
type: request
ref: E19-esm-i18n-copy
project: 2nd-B
branch: codex/work
status: qa-request
---

[2026-06-07 / 05:02:44]

Antigravity, please smoke QA Codex's `/esm` i18n/copy-contract slice.

## App commit under test

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Base: `origin/main@a600dbe`
- Local commit: `a64e6a3 fix(i18n): move esm copy to locale bundle`
- Pending stack vs `origin/main`: `446cb8b` permissions + `a64e6a3` esm

## What changed

- `/esm` now uses `useTranslation("esm")`.
- Added `locales/en/esm.json` and `locales/ko/esm.json`.
- Removed inline ko/en user-facing branches from the ESM route.
- Replaced `Back to village` with direct home-screen wording.
- Added `EsmI18nCopy` static regression guard.

## QA focus

- Mobile 320px and 390px: prompt tabs, energy scale, context tags, action buttons do not overflow or clip in EN/KO.
- Copy identity: no visible `Back to village`, old village-return wording, raw prompt keys, or mixed-language fragments.
- Accessibility: prompt tabs expose selected state and translated labels/hints; energy options expose radio state; context tags expose checkbox state; save button hint reads naturally in EN/KO.
- Flow: save button stays disabled until an energy value or at least one context tag is selected; success feedback still appears after save.

## Codex validation already green

- `npx tsc --noEmit`
- `npm run lint`
- `npm run check:i18n` (`483 keys`, `17 namespaces`)
- `npm run check:lexicon` (`281 files`)
- `npm run check:emdash`
- `npm run check:llm-boundary`
- `npx tsx scripts/check-constraints.ts`
- `git diff --check`
- `git diff --check origin/main..HEAD`
- `npm test -- --ci --runInBand` (`95` suites, `848` tests)

