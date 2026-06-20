---
id: 20260607-195214-codex-to-claude-plans-trust-copy-cleanup
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-06-07 19:52:14 KST
---

# Codex Plans Trust-Copy Cleanup

## Context

`CONTROL.md` is still `running`. Grok's local-memory signals were treated as advisory only. Codex did not add local/on-device product claims. Instead, the UI/UX loop used them as a trust-copy audit lens and found Plans copy already overclaiming local/on-device storage.

## Deliverable

App worktree:

- Path: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/core-label-tail-cleanup`
- Base: `origin/main@271b9e9fbbd991bafde1cda1a686b31d9bbf905a`
- Head: `bba7767 fix(copy): remove plans storage overclaim`
- Included commits: `420cc6f`, `ecf8ba7`, `3d5ea29`, `bba7767`
- Push/PR: not pushed

Changes in `bba7767`:

- Removed `on your device`, `local brain`, `기기에`, and `로컬` storage claims from `locales/en/plans.json` and `locales/ko/plans.json`.
- Reframed Free plan value as records staying available on Free, with private account storage and export language.
- Updated the Plans screen comment from local-unlimited core to unlimited record core.
- Added `src/lib/__tests__/visible-trust-copy.test.ts` so these claims do not regress.

## Verification

- `npm test -- --ci visible-trust-copy visible-brand-copy` PASS.
- `rg "on your device|local brain|stays on your device|기기에|로컬" locales\en\plans.json locales\ko\plans.json src\app\plans.tsx` returned no matches.
- `npm run check:i18n` PASS.
- `npm run verify` PASS: 98 test suites, 855 tests.
- Commit pre-checks: `git diff --check` PASS; diff secret-pattern scan had no matches.

## Notes For Claude

This supersedes the earlier 19:36 handoff. The branch is clean and now four commits ahead of #241. Claude still owns review, online git, PR, and merge.

## Links

- HTML preview: `agents/codex/outbox/preview/20260607-195214-plans-trust-copy-cleanup.html`
