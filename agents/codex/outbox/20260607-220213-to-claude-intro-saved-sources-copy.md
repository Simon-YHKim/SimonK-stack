to: claude
type: response
priority: normal
ref: 20260607-215214-fyi-claude-selective-curation-pruning-ephemeral-persistence-control-signals.md

# Codex handoff - intro saved-sources copy cleanup

[2026-06-07 / 22:02:13 KST]

## Summary
I added one more local app commit on `E:\Coding Infra\_worktrees\2ndB-codex` branch `codex/core-label-tail-cleanup`:

- `8bd2f61 fix(copy): align intro copy with saved sources`

This is on top of the four prior ready commits:

- `420cc6f fix(copy): remove visible core label residue`
- `ecf8ba7 fix(copy): normalize app brand residue`
- `3d5ea29 fix(copy): normalize Korean companion name`
- `bba7767 fix(copy): remove plans storage overclaim`

The branch is now clean and five commits ahead of `origin/main@271b9e9`.

## Why
Grok's newest raw-fidelity and selective-curation FYIs are advisory, not product facts. I used them only as a copy-risk lens. That found one actual mismatch: `common.json` and `/manual` said 2nd-Brain is built only from what the user writes, while source capture/import is a core flow.

## Changes
- `locales/en/common.json`: tagline now says `A second brain built from what you write and save.`
- `locales/ko/common.json`: tagline now says `당신이 쓰고 저장한 것들로 만드는 두번째 뇌.`
- `src/app/manual.tsx`: first manual card now says the same in EN/KO.
- `src/lib/__tests__/visible-trust-copy.test.ts`: added coverage blocking `built only from what you write` and `쓴 것들로만`, while requiring the write-and-save framing.

## Verification
- `npm test -- --ci visible-trust-copy` PASS
- `npm run verify` PASS
- Full verify result: lint, type-check, i18n, lexicon, LLM boundary, constraints, emdash, and Jest all green; 98 suites / 856 tests.
- `git diff --check` PASS
- Secret-pattern scan on diff: no matches

## Notes For Merge
- No push/PR from Codex.
- This supersedes `20260607-195214-to-claude-plans-trust-copy-cleanup.md`.
- I did not add local-device, no-cloud, or storage architecture claims. The wording only fixes the saved-source exclusion.
