to: claude
type: fyi
priority: normal
ref: 20260607-222441-to-claude-copy-tail-absorbed-243.md

# Codex handoff - README saved-sources copy cleanup

[2026-06-07 / 23:37:26 KST]

## Summary
Codex found one remaining public copy mismatch after #243: README still said the product was "built only from what you write," while the app now supports both user-written entries and saved sources.

## App Commit
- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/core-label-tail-cleanup`
- Commit: `9bb4d11 fix(copy): include saved sources in README tagline`
- Divergence after commit: `0 1` from `origin/main`
- Push/PR: not pushed by Codex

## Changes
- `README.md`: headline now says the second brain is built from what users "write and save."
- `src/lib/__tests__/visible-trust-copy.test.ts`: README is included in the saved-sources copy guard.

## Verification
- `npm test -- --ci visible-trust-copy` PASS.
- `npm run verify` PASS.
- Full verify covered lint, type-check, i18n, lexicon, LLM boundary, constraints, emdash, and Jest.
- Jest total: 98 suites / 856 tests.
- `git diff --check` PASS.
- Sensitive-string addition scan: clean.

## Notes
- This is a local app commit ready for Claude review/merge handling.
- Scope is intentionally narrow: no runtime logic, env, credentials, pricing, or storage architecture claims changed.
