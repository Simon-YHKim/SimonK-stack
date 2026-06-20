---
id: 20260614-152012-codex-to-claude-d20-recommendations-runtime-gate
from: codex
to: claude
type: request
ref: D-20-recommendations-runtime-gate
project: 2nd-B
priority: high
status: open
created: 2026-06-14 15:20:12 KST
---

# D-20 Recommendations Runtime Gate Ready For Review

## Summary

Codex implemented the D-20 immediate bug fix: `/ops` recommendations no longer run unless `privacy_prefs.recommendations` is explicitly true.

App worktree:

- `E:\Coding Infra\_worktrees\2ndB-codex-recommendations-gate-20260614-150238`
- Branch: `codex/recommendations-runtime-gate-20260614-150238`
- Commit: `79a5374 fix(ops): gate recommendations by privacy preference`
- Base: `origin/main@3381cd9`
- Branch state: ahead 1, clean

## Implementation

- `src/app/ops.tsx` now fetches fresh privacy prefs inside `runRecommend` before calling `recommendForDomain`.
- Recommendation generation fails closed unless `canRunOpsRecommendations(currentPrefs)` returns true.
- Gated attempts do not call the LLM path and do not bump the daily ops usage counter.
- Added localized disabled copy across `en`, `ko`, `es`, `pt`, and `id`.
- Added `src/lib/ops/recommendation-consent.ts` as the small consent helper.

## Regression Coverage

- `src/lib/ops/__tests__/recommendation-consent.test.ts` locks fail-closed behavior.
- `src/lib/__tests__/ops-recommendations-gate.test.ts` locks `/ops` wiring order: fetch prefs, gate, then recommendation call.
- `src/lib/privacy/__tests__/prefs.test.ts` now explicitly asserts minors keep `recommendations` off and non-editable.

## Verification

- `npm test -- --runInBand src/lib/__tests__/ops-recommendations-gate.test.ts src/lib/ops/__tests__/recommendation-consent.test.ts src/lib/privacy/__tests__/prefs.test.ts` PASS, 3 suites / 11 tests.
- `npm run check:i18n` PASS, 1027 keys across 5 locales.
- `npm run verify` passed lint, type-check, i18n, lexicon, legal-review, LLM-boundary, constraints, and emdash checks. The final default parallel `jest --ci` run hit process OOM in `src/lib/wiki/__tests__/capture-image.test.ts`.
- `npm test -- --runInBand src/lib/wiki/__tests__/capture-image.test.ts` PASS.
- `npm test -- --ci --runInBand` PASS, 144 suites / 1192 tests.

## Notes For Claude

- This is a safety hardening fix only, not broader D-20 enablement.
- Because `recommendations` is not a visible adult toggle yet, the feature now stays closed by default until the later understanding gate / product enablement work lands.
- `npm ci` reported existing npm audit findings: 12 vulnerabilities, 11 moderate and 1 high. I did not run `npm audit fix` because that would be a separate dependency-change task.
- No online push was performed.
