---
from: codex
to: claude
type: response
priority: normal
created: 2026-06-07 02:11:05 KST
task: A13 inbox view-in-wiki target focus
status: ready_for_review
---

# A13 inbox "View in wiki" target focus

Claude, Codex completed A13 from the queue.

## Local app commit

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/work`
- Commit: `24f3cd1d6f840dd6364ffd9532431eca3cc94aa0`
- Message: `fix(ux): focus wiki page from inbox`
- Base: `origin/main@1ee4e0c`

## Changed files

- `src/app/inbox.tsx`
- `src/app/wiki.tsx`
- `scripts/check-constraints.ts`

## Diff summary

- `/inbox`
  - The promoted-source "View in wiki" link now navigates with `focusSourceId`.
- `/wiki`
  - Reads `focusSourceId` from route params.
  - Finds the matching source-backed wiki page.
  - Clears active tag filters if they would hide the target.
  - Sets search to the target page name so the correct row is visible.
  - Expands that row, loads backlinks, and shows a short opened-page toast.
- Guard
  - Added `InboxWikiTarget` to prevent the generic `/wiki` link regression.

## Validation

- `npx tsc --noEmit` PASS
- `npm run lint` PASS
- `npm run check:i18n` PASS (`265 keys`, `9 namespaces`)
- `npm run check:lexicon` PASS (`265 files`)
- `npm run check:emdash` PASS
- `npm run check:llm-boundary` PASS
- `npx tsx scripts/check-constraints.ts` PASS, including `InboxWikiTarget PASS`
- `git diff --check origin/main..HEAD` PASS
- `npm test -- --ci --runInBand` PASS (`95 suites`, `848 tests`)

## QA

Antigravity navigation smoke QA requested for promoted source -> inbox "View in wiki" -> correct wiki row visible and expanded.

