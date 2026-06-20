---
id: 20260607-193616-codex-to-claude-korean-companion-name-cleanup
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-06-07 19:36:16 KST
---

# Codex Korean Companion Name Cleanup

## Context

`CONTROL.md` is still `running`. During the 5-minute autonomous UI/UX loop, Codex followed the #241-based copy branch and found Korean user-facing AI companion naming split across `세컨비`, `세컨드비`, and `SecondB`.

## Deliverable

App worktree:

- Path: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/core-label-tail-cleanup`
- Base: `origin/main@271b9e9fbbd991bafde1cda1a686b31d9bbf905a`
- Head: `3d5ea29 fix(copy): normalize Korean companion name`
- Prior included commits: `420cc6f fix(copy): remove visible core label residue`, `ecf8ba7 fix(copy): normalize app brand residue`
- Push/PR: not pushed

Changes in `3d5ea29`:

- Normalized Korean locale AI companion copy to `세컨비`.
- Kept app/storage/product brand copy as `2nd-Brain`.
- Updated home, wiki, and SecondB accessibility labels using the longer `세컨드비` form.
- Updated `scripts/check-constraints.ts` exact expectations.
- Extended `src/lib/__tests__/visible-brand-copy.test.ts` so Korean locale files reject `SecondB`, and selected app/component surfaces reject `세컨드비`.

## Verification

- `npm test -- --ci visible-brand-copy` PASS.
- `rg "\bSecondB\b" locales\ko --glob "*.json"` returned no matches.
- `rg "세컨드비" src\app src\components locales --glob "*.json" --glob "*.tsx" --glob "*.ts"` returned no matches.
- `npm run check:constraints` PASS.
- `npm run verify` PASS: 97 test suites, 854 tests.
- Commit pre-checks: `git diff --check` PASS; diff secret-pattern scan had no matches.

## Notes For Claude

This is a local handoff only. Claude still owns online git, review, PR, and merge. The branch is clean and now three commits ahead of #241.

## Links

- HTML preview: `agents/codex/outbox/preview/20260607-193616-korean-companion-name-cleanup.html`
