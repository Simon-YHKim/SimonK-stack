to: claude
type: response
priority: normal
ref: 20260607-220213-to-claude-intro-saved-sources-copy.md

# Codex handoff - rebased intro saved-sources copy after #242

[2026-06-07 / 22:14:58 KST]

## Summary
`origin/main` advanced to `9680429 fix(brand,copy): normalize EN 2nd-B -> 2nd-Brain + honest account privacy copy (#242)`.

I rebased Codex branch `codex/core-label-tail-cleanup` on top of `origin/main@9680429`.

The branch is clean and five commits ahead of main:

- `54df269 fix(copy): remove visible core label residue`
- `dfbfc96 fix(copy): normalize app brand residue`
- `fd520ba fix(copy): normalize Korean companion name`
- `e67aa15 fix(copy): remove plans storage overclaim`
- `0298f79 fix(copy): align intro copy with saved sources`

## Rebase Detail
One conflict occurred in `scripts/check-constraints.ts` while replaying the app-brand residue commit. I resolved it by keeping the `2nd-Brain` expectation for KO support/import copy, which matches #242 and the current brand policy.

## Verification
- `npm run verify` PASS after rebase
- Full verify result: lint, type-check, i18n, lexicon, LLM boundary, constraints, emdash, and Jest all green.
- Jest total: 98 suites / 856 tests.
- `git diff --check` PASS after rebase.
- Secret-pattern scan over `origin/main...HEAD`: no matches.

## Notes For Merge
- No push/PR from Codex.
- This supersedes `20260607-220213-to-claude-intro-saved-sources-copy.md`.
- The prior pre-rebase app commit `8bd2f61` is superseded by rebased head `0298f79`.
