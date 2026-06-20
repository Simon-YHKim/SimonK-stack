to: claude
type: fyi
priority: normal
ref: 20260608-010958-to-claude-readme-copy-absorbed-244.md

# Codex handoff - README Advisor residue cleanup

[2026-06-08 / 01:21:03 KST]

## Summary
After #244, Codex scanned public README copy for stale visible guidance terminology. README still listed feature 4 as `Advisor`, even though current product surfaces present the user-facing chat as SecondB.

## App Commit
- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/core-label-tail-cleanup`
- Commit: `16d3e8c fix(copy): replace README Advisor residue with SecondB`
- Divergence after commit: `0 1` from `origin/main`
- Push/PR: not pushed by Codex

## Changes
- `README.md`: feature 4 now reads `SecondB chat` and describes analytic/new-angle reflections grounded in saved records and validated frameworks.
- `scripts/check-constraints.ts`: `OldGuidanceCopyResidue` now also guards README against the old `Advisor`/`Toggle-mode guidance` phrasing.

## Verification
- `npm run check:constraints` PASS.
- `npm run verify` PASS.
- Full verify covered lint, type-check, i18n, lexicon, LLM boundary, constraints, emdash, and Jest.
- Jest total: 98 suites / 856 tests.
- `git diff --check` PASS.
- Sensitive-pattern scan: clean.

## Notes
- Scope is public README copy plus its regression guard only.
- Runtime internal `advisor` function/type names were not changed.
- This is a local app commit ready for Claude review/merge handling.
