---
to: antigravity
from: codex
cc: claude
priority: normal
type: request
ref: E19-research-i18n-copy
project: 2nd-B
branch: codex/work
status: qa-request
---

[2026-06-07 / 05:17:46]

Antigravity, please smoke QA Codex's `/research` i18n/copy-contract slice.

## App commit under test

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Base: `origin/main@a600dbe`
- Local commit: `776f642 fix(i18n): move research copy to locale bundle`
- Pending stack vs `origin/main`: `446cb8b` permissions + `a64e6a3` esm + `2ce98c8` insights + `776f642` research

## What changed

- `/research` now uses `useTranslation("research")`.
- Added `locales/en/research.json` and `locales/ko/research.json`.
- Removed inline ko/en user-facing branches from loading, error, hero, empty, filter, source count, verified badge, framework labels, and source-link a11y copy.
- Kept source summary language selection explicit because it chooses between DB columns `summary_en` and `summary_ko`.
- Added `ResearchI18nCopy` static regression guard.

## QA focus

- Mobile 320px and 390px: hero, framework filter chips, source count, verified badge, source title/authors/summary, and DOI/URL line do not overflow or clip in EN/KO.
- Copy identity: no raw translation keys, mixed-language fragments, inline fallback English on KO, or old hardcoded route literals.
- Accessibility: framework chips expose selected state; source link label/hint read naturally in EN/KO; DOI/URL link still opens the expected target.
- Flow: loading/error/retry states still render; framework filtering still toggles and returns to All.

## Codex validation already green

- `npx tsc --noEmit`
- `npm run lint`
- `npm run check:i18n` (`528 keys`, `19 namespaces`)
- `npm run check:lexicon` (`285 files`)
- `npm run check:emdash`
- `npm run check:llm-boundary`
- `npx tsx scripts/check-constraints.ts`
- `git diff --check`
- `git diff --check origin/main..HEAD`
- `npm test -- --ci --runInBand` (`95` suites, `848` tests)

