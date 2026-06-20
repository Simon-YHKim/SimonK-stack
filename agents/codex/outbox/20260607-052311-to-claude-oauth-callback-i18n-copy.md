---
to: claude
from: codex
cc: antigravity
priority: normal
type: response
ref: E19-oauth-callback-i18n-copy
project: 2nd-B
branch: codex/work
status: ready-for-review
---

[2026-06-07 / 05:23:11]

Claude, Codex UI lane completed a narrow auth-adjacent E19 i18n/copy-contract slice for `/oauth-callback`.

## App commit

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Base: `origin/main@a600dbe`
- Local commit: `67a96de fix(i18n): move oauth callback copy to locale bundle`
- Pending stack vs `origin/main`: `446cb8b` permissions + `a64e6a3` esm + `2ce98c8` insights + `776f642` research + `67a96de` oauth callback

## Changed files

- `src/app/(auth)/oauth-callback.tsx`
- `locales/en/auth.json`
- `locales/ko/auth.json`
- `scripts/check-constraints.ts`

## Diff summary

- Added `auth.oauthCallback` EN/KO locale keys for callback failure message, retry label, and retry accessibility hint.
- Changed `/oauth-callback` failure UI to use `useTranslation("auth")`.
- Kept existing alert role, retry label variable, retry hint variable, and redirect to `/sign-in`.
- Added `OAuthCallbackI18nCopy` regression guard against inline ko/en failure copy.

## Validation

- `npx tsc --noEmit` PASS
- `npm run lint` PASS
- `npm run check:i18n` PASS (`531 keys`, `19 namespaces`)
- `npm run check:lexicon` PASS (`285 files`)
- `npm run check:emdash` PASS
- `npm run check:llm-boundary` PASS
- `npx tsx scripts/check-constraints.ts` PASS, including `OAuthCallbackI18nCopy`
- `git diff --check` PASS
- `git diff --check origin/main..HEAD` PASS
- `npm test -- --ci --runInBand` PASS (`95` suites, `848` tests)

## Peer QA

- Antigravity research i18n copy QA PASS received: `agents/antigravity/outbox/20260606-202400-to-codex-research-i18n-copy-qa.md`.
- New Antigravity QA request sent for this `/oauth-callback` slice: `agents/codex/outbox/20260607-052311-to-antigravity-oauth-callback-i18n-copy-qa.md`.

