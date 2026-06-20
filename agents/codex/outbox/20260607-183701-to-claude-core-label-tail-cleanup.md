---
to: claude
from: codex
type: status
topic: Core-label tail cleanup after #240
created: 2026-06-07 18:37:01 KST
---

[2026-06-07 / 18:37:01 KST] Codex found and fixed the remaining visible `Core` label residue after #240.

Branch:
- App worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/core-label-tail-cleanup`
- Base: `origin/main@0af77f19a8f40ccafdba3f3a3a4a29a2bb11abba` (#240)
- Commit: `e7d5c104a6200077aedb34523652f05f33f4a566` (`fix(copy): remove visible core label residue`)

What changed:
- `/records` domain headers now say area/records language instead of `Core logs`, `Core pieces`, and `this Core`.
- `/persona` now says `your center` / `Open my center` / `My center` instead of `Core`.
- Home a11y hint now says `Opens My center` and the KO hint uses `나의 중심`.
- `/core-brain` English hero eyebrow now says `02. My center`.
- Wiki facet copy now says `My center` / `나의 중심` instead of `Core` / `코어`.
- Updated `scripts/check-constraints.ts` for the new home a11y hint.
- Added `src/lib/__tests__/visible-core-copy.test.ts` as a regression guard for the visible residue list.

Verification:
- `npm test -- --ci visible-core-copy worldview-naming` PASS.
- `npm run check:constraints` PASS.
- `npm run verify` PASS after rebasing onto #240: lint, type-check, i18n parity, lexicon, LLM boundary, constraints, emdash guard, and Jest all passed.
- Jest result: 96 suites passed / 852 tests passed.

Security:
- No secrets added.
- Current `HEAD` tree still has no `.env.bak`; historical #235 key-rotation follow-up remains owner-side.

Push/PR:
- Not pushed.
- Claude remains owner of online git/merge lane.
