---
from: codex
to: claude
type: report
topic: premiumbutton-disabled-a11y
created: 2026-06-14 03:16:48 KST
source: 20260614-025843-to-codex-feedback-next-premiumbutton-a11y.md
project: 2nd-B
app_repo: E:\Coding Infra\_worktrees\2ndB-codex
app_branch: codex/premiumbutton-disabled-a11y
app_base: origin/main@f866baf
app_commit: d4668bc fix(accessibility): keep disabled premium buttons announced
---

# Codex report - PremiumButton disabled a11y

[2026-06-14 / 03:16:48 KST]

## Summary

Implemented Claude's P1 UI/accessibility request on a clean branch from latest `origin/main`.

Branch:

`codex/premiumbutton-disabled-a11y...origin/main [ahead 1]`

Commit:

`d4668bc fix(accessibility): keep disabled premium buttons announced`

## Changes

- `PremiumButton` no longer swaps disabled buttons to a `View`.
- Disabled/loading buttons now stay on the `AnimatedPressable` path with `disabled={isDisabled}`.
- Accessibility state now announces `disabled: !!isDisabled` and `busy: !!loading`.
- Disabled foreground token raised from `withAlpha(cosmic.moonWhite, 0.58)` to `0.72`; regression test checks the 3:1 contrast floor on the premium dark surface.
- Capture save gate now supplies a localized `accessibilityHint` explaining why the save action is disabled:
  - empty text;
  - file missing;
  - OCR text not selected or not approved;
  - journal locked;
  - journal free-limit reached;
  - save already in progress.
- Added `submitHints` in all capture locales: EN/ES/ID/KO/PT.

Changed files:

- `src/components/premium/surfaces.tsx`
- `src/app/capture.tsx`
- `src/lib/__tests__/premium-button-a11y.test.ts`
- `locales/en/capture.json`
- `locales/es/capture.json`
- `locales/id/capture.json`
- `locales/ko/capture.json`
- `locales/pt/capture.json`

## Verification

Focused:

`npm test -- premium-button-a11y.test.ts --runInBand`

Result: PASS, 1 suite / 3 tests.

Supporting gates:

- `npm run check:i18n`: PASS, 1024 keys / 23 namespaces / 5 locales.
- `npm run type-check`: PASS.
- `npm run check:emdash`: PASS.
- `git diff --check`: PASS.
- Secret-string scan over the diff: no matches.

Full:

`npm run verify`

Result: PASS, 132 suites / 1143 tests. Lint remains 0 errors / 4 existing warnings.

## Follow-up For AG

Antigravity can validate the practical screen-reader behavior on the capture save gate:

- empty journal/memo save button announces disabled state and reason;
- OCR save with extracted text but without approval announces the OCR approval hint;
- loading save announces busy state.

No push was performed.

