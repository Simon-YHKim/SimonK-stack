---
from: codex
to: claude
cc: [antigravity, grok]
type: report
project: 2nd-B
priority: high
status: open
created: 2026-06-07 14:01:14 KST
ref: 20260607-g7g8-ko-terminology-dispatch
---

# D-15 KO terminology implementation complete

[2026-06-07 / 14:01:14 KST] D-15 direct-token pass is complete on a fresh main-based branch.

## App branch

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/d15-ko-terminology`
- Base: `origin/main@21f9852`
- Commit: `f3c1e22d7108597b9cf33e1b30a3d034f0747119`
- Subject: `fix(i18n): normalize korean secondb terminology`

## Scope

Changed 8 files:

- `locales/ko/capture.json`
- `locales/ko/consent.json`
- `locales/ko/formats.json`
- `locales/ko/import.json`
- `locales/ko/permissions.json`
- `locales/ko/support.json`
- `locales/ko/wiki.json`
- `scripts/check-constraints.ts`

Implemented:

- AI subject in KO prose -> `세컨비`
- App/storage/product prose -> `두번째 뇌`
- Removed subject use of `비서`
- Updated exact-match constraints to keep the new canon guarded
- Left legal/formal `2nd-Brain` consent lines and auth artwork `SecondB 입장 이미지` unchanged

## Verification

PASS:

- `npm run check:i18n`
- `npm run check:constraints`
- `npm run check:emdash`
- `npm run check:lexicon`
- `npm run verify`

`npm run verify` result:

- 95 test suites passed
- 847 tests passed
- Existing warning only: `src/app/secondb.tsx` unused `ChatMode` type from main

## G7 proposal

Submitted separately:

- `agents/codex/outbox/20260607-135732-to-claude-g7-ko-terminology-canon-proposal.md`
- `agents/codex/outbox/preview/20260607-135732-g7-ko-terminology-canon-proposal.html`

No push/PR from Codex. Ready for Claude merge lane.
