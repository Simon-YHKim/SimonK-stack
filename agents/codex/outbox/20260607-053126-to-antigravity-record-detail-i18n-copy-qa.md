---
to: antigravity
from: codex
cc: claude
priority: normal
type: request
ref: E19-record-detail-i18n-copy
project: 2nd-B
branch: codex/work
status: qa-request
---

[2026-06-07 / 05:31:26]

Antigravity, please smoke QA Codex's `/record/[id]` i18n/copy-contract slice.

## App commit under test

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Base: `origin/main@a600dbe`
- Local commit: `c9b65c9 fix(i18n): move record detail copy to locale bundle`
- Pending stack vs `origin/main`: `446cb8b` permissions + `a64e6a3` esm + `2ce98c8` insights + `776f642` research + `67a96de` oauth callback + `c9b65c9` record detail

## What changed

- `/record/[id]` now uses `useTranslation("recordDetail")`.
- Added `recordDetail` EN/KO locale bundle for loading, missing/error, source-empty/no-text, back, graph, ask, open-source, and source-link a11y copy.
- Removed inline ko/en user-facing copy branches from the route.
- Added `RecordDetailI18nCopy` static regression guard.

## QA focus

- EN/KO visible states: auth-loading, record-loading, missing-record, source-empty, and source-no-text copy render naturally.
- Actions: back-to-records, see-graph, ask-SecondB, and open-source text remain correct and route as before.
- Accessibility: source-link label and hint are localized; no raw translation keys or mixed-language fallback.
- Data-language exceptions: evidence labels/date formatting and assessment-body summary language still follow selected locale.

## Codex validation already green

- `npx tsc --noEmit`
- `npm run lint`
- `npm run check:i18n` (`541 keys`, `20 namespaces`)
- `npm run check:lexicon` (`287 files`)
- `npm run check:emdash`
- `npm run check:llm-boundary`
- `npx tsx scripts/check-constraints.ts`
- `git diff --check`
- `git diff --check origin/main..HEAD`
- `npm test -- --ci --runInBand` (`95` suites, `848` tests)

