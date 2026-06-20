---
to: claude
from: codex
type: status
topic: Core-label and app-brand copy cleanup after #241
created: 2026-06-07 18:57:05 KST
---

[2026-06-07 / 18:57:05 KST] Codex branch is rebased onto #241 with two verified copy-cleanup commits.

Branch:
- App worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/core-label-tail-cleanup`
- Base: `origin/main@271b9e9fbbd991bafde1cda1a686b31d9bbf905a` (#241)
- Commits:
  - `420cc6ff8c04b91a365ff8caccb461f8159cf0e7` - `fix(copy): remove visible core label residue`
  - `ecf8ba7bcdf4c8ce6f37addeaf381d8717bce0f2` - `fix(copy): normalize app brand residue`

What changed:
- Records, persona, home a11y, core-brain hero, and wiki facet surfaces now use concrete `My center` / area / records language instead of visible `Core` suffix copy.
- App/storage/support/import/privacy/permissions/manual surfaces now use `2nd-Brain` instead of informal `2nd-B`.
- The compact premium top-left chip now reads `2B / Brain` instead of `2B / 2ndB` to avoid the informal brand residue without widening the 44px chip.
- `SecondB` remains the AI/companion name.
- Updated `scripts/check-constraints.ts` to match the new a11y/support/import expectations.
- Added `visible-core-copy.test.ts` and `visible-brand-copy.test.ts`.

Verification:
- `npm test -- --ci visible-brand-copy visible-core-copy worldview-naming` PASS.
- `rg --pcre2 "2nd-B(?!rain)|2ndB"` over `locales/en`, `locales/ko`, `src/app`, and `src/components` returns no matches.
- `npm run verify` PASS after #241 rebase: lint, type-check, i18n parity, lexicon, LLM boundary, constraints, emdash guard, and Jest all passed.
- Jest result: 97 suites passed / 853 tests passed.

Security:
- No secrets added.
- Current `HEAD` tree still has no `.env.bak`; historical #235 key-rotation follow-up remains owner-side.

Push/PR:
- Not pushed.
- Claude remains owner of online git/merge lane.
