---
id: 20260613-224706-codex-to-claude-t4-v10-pattern-data-asset-weight
from: codex
to: claude
type: response
ref: user-direct-20260613-t4-asset-weight
project: 2nd-B
priority: high
status: done
created: 2026-06-13 22:47:06 KST
---

## Context
[2026-06-13 / 22:47:06 KST] Simon direct one-cycle order. Highest-value next item selected: T4 asset weight, because Android runtime smoke found `public/assets/tesseract-v10/pattern_data_*.png` color variants adding about 15.07 MiB.

## Deliverable
- App worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- App commit for Claude review: `62505c1 fix(assets): [2026-06-13 / 22:46:19 KST] replace v10 pattern data PNGs`
- Replaced v10 Pattern Data 9 static PNG `require`s with one recolorable `react-native-svg` renderer in `src/components/art/SoulcoreFinalArt.tsx`.
- Deleted the 9 duplicate v10 Pattern Data PNG files, total removed: 15,799,390 bytes / 15.07 MiB.
- Kept v45/v49 preview behavior on existing PNG assets; only production-default `variant="v10"` uses the vector renderer.
- Updated `public/assets/tesseract-v10/manifest.json` and `README.md` so the package no longer advertises missing PNG files.
- Added regression guard: `src/components/art/__tests__/tesseract-v10-asset-weight.test.ts`.

## Acceptance
- `npm test -- --ci src/components/art/__tests__/tesseract-v10-asset-weight.test.ts` PASS, 2 tests.
- `npm run type-check` PASS.
- `npm run verify` PASS: 130 suites / 1129 tests, lint 0 errors / 4 existing unused-disable warnings.
- `public/assets/tesseract-v10` now contains only core PNGs plus README/manifest; no `pattern_data_*.png` files remain.

## Notes For Merge
- Current `codex/work` is `ahead 5, behind 3` against `origin/main` because earlier Codex T1/T4 commits were already cherry-picked to `main` with different hashes, while one T3 contract commit remains Codex-only. Claude should cherry-pick `62505c1` onto `d419889` or reconcile the existing stack.
- No online git push or PR was performed by Codex.

## Links
- Preview report: `agents/codex/outbox/preview/20260613-224706-t4-v10-pattern-data-asset-weight.html`
