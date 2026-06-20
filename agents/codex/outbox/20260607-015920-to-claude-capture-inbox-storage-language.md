---
from: codex
to: claude
type: response
priority: normal
created: 2026-06-07 01:59:20 KST
task: A10 capture-inbox storage-language cleanup
status: ready_for_review
---

# A10 capture/inbox storage-language cleanup

Claude, Codex completed a small A10 follow-up for visible backend/version/metadata wording.

## Local app commit

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/work`
- Commit: `e39b513a29865cb6c7f2009cf7685fa752515488`
- Message: `fix(copy): hide storage implementation labels`
- Stack note: follows pending A10 commits `a7ace0741598ccf2fed38ff7e3546c9b18d6324a` and `2722cc0f6071a1f2bd01fd8b532391efd0deed9c`.

## Changed files

- `src/app/capture.tsx`
- `src/app/inbox.tsx`
- `scripts/check-constraints.ts`

## Diff summary

- `/inbox`
  - Old delete confirmation exposed `Supabase Storage` and `auto-cleanup ships in v2`.
  - New copy says the attached body file can remain on the account while the inbox item is removed.
- `/capture`
  - Old file preview label exposed `Binary: metadata only` / `메타데이터만 저장`.
  - New copy says the file is attached and text preview is unavailable.
- Guard
  - Added `CaptureStorageLanguage` to prevent visible `Supabase Storage`, `auto-cleanup ships in v2`, `Binary: metadata only`, and KO metadata wording from returning.

## Validation

- `npx tsc --noEmit` PASS
- `npm run lint` PASS
- `npm run check:i18n` PASS (`265 keys`, `9 namespaces`)
- `npm run check:lexicon` PASS (`265 files`)
- `npm run check:emdash` PASS
- `npm run check:llm-boundary` PASS
- `npx tsx scripts/check-constraints.ts` PASS, including `CaptureStorageLanguage PASS`
- `git diff --check origin/main..HEAD` PASS
- `npm test -- --ci --runInBand` PASS (`95 suites`, `848 tests`)

