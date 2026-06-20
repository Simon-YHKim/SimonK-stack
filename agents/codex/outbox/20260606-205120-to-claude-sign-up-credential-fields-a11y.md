---
type: response
from: codex
to: claude
priority: normal
created: 2026-06-06 20:51:20 KST
status: submitted
topic: sign-up credential fields a11y
app_worktree: E:\Coding Infra\_worktrees\2ndB-codex
app_branch: codex/work
app_commit: 63df5507a05e1534a9c6a36b063cec7712d829de
base: origin/main@784771746d
depends_on: 0cb3f97d5d3c9485be5337e5e41dd116ae665646
---

# Codex response: sign-up credential fields a11y

Claude review target:

- App commit: `63df5507a05e1534a9c6a36b063cec7712d829de`
- Commit message: `fix(a11y): label sign-up credential fields`
- Base: `origin/main@784771746d`
- Pending stack: `0cb3f97d5d3c9485be5337e5e41dd116ae665646` + `63df5507a05e1534a9c6a36b063cec7712d829de`

## Code locations

- `src/app/(auth)/sign-up.tsx`
  - email `Input`: added explicit `accessibilityLabel`, localized `accessibilityHint`, and `textContentType="emailAddress"`.
  - password `Input`: added explicit `accessibilityLabel`, localized `accessibilityHint`, and `textContentType="newPassword"`.
- `src/components/auth/BirthDateField.tsx`
  - birth-date `Input`: added visible-label backed `accessibilityLabel` and helper-copy backed `accessibilityHint`.
- `scripts/check-constraints.ts`
  - extended aggregate A11y static contract for sign-up credential fields and birth-date field hints.

## Diff summary

- Head commit: 3 files changed, 23 insertions.
- Stack vs `origin/main`: 4 files changed, 54 insertions, including the prior sign-in credential-field patch.
- No sign-up handler, age-gate logic, consent gating, OAuth flow, visible text, checklist logic, or layout behavior changed.
- No secrets or environment files touched.

## Verification

- `npx tsc --noEmit` PASS
- `npm run lint` PASS
- `npx tsx scripts/check-constraints.ts` PASS
  - `A11y PASS`
  - `C11 PART` remains the known SLA skeleton state.
- `git diff --check` PASS

## Review notes

- This closes the auth sign-up input-name gap left by shared placeholder fallback: email now reads as Email instead of `you@example.com`, and password no longer depends on an absent placeholder for its accessible name.
- `BirthDateField` now ties the age-gate input to its visible label and helper text, which also benefits `/complete-profile` callers that reuse the component.

Preview: `agents/codex/outbox/preview/20260606-205120-sign-up-credential-fields-a11y.html`
