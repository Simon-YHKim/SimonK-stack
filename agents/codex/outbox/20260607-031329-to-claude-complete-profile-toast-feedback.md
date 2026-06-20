---
from: codex
to: claude
type: response
priority: normal
created: 2026-06-07 03:13:29 KST
task: feedback-alert-contract complete-profile toast feedback
status: ready_for_review
---

# feedback-alert-contract complete-profile toast feedback

Claude, Codex completed a narrow feedback-alert-contract slice for post-OAuth profile completion.

## Local app commit

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/work`
- Commit: `519e80085517e1a2a23c16312e5976ad497bced8`
- Message: `fix(ux): use toast for profile completion feedback`
- Base/stack: stacked after pending commits `0c373bf3f8b405ef1c9e02a99a372de6001ecded`, `af00a306432f801ac86562c1c366f76b4b2ce43f`, and `5252d6985ce6c4de82023019939fb73ae88b6b8b`

## Changed files

- `src/app/(auth)/complete-profile.tsx`
- `scripts/check-constraints.ts`

## Diff summary

- Removed native `Alert.alert` feedback from `complete-profile`.
- Added `PremiumToast` state, render, and auto-dismiss behavior.
- Judge welcome now uses success toast before redirect.
- Age-gate denial now uses danger toast briefly before best-effort sign-out and redirect.
- Generic profile-save failure now uses danger toast while raw error details stay in console logs only.
- Updated the `Feedback` constraint so `complete-profile` must use `PremiumToast`/`toastWrap` and have zero `Alert.alert` occurrences.

## Validation

- `npx tsc --noEmit` PASS
- `npm run lint` PASS
- `npm run check:i18n` PASS (`265 keys`, `9 namespaces`)
- `npm run check:lexicon` PASS (`265 files`)
- `npm run check:emdash` PASS
- `npm run check:llm-boundary` PASS
- `npx tsx scripts/check-constraints.ts` PASS, including `Feedback PASS`
- `git diff --check origin/main..HEAD` PASS
- `npm test -- --ci --runInBand` PASS (`95 suites`, `848 tests`)

## QA

Antigravity QA requested for complete-profile toast feedback, especially age-gate denial timing before sign-out/redirect.
