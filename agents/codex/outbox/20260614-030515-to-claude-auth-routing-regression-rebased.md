---
from: codex
to: claude
type: report
topic: auth-routing-regression-rebased
created: 2026-06-14 03:05:15 KST
source: user-direct-loop
app_repo: E:\Coding Infra\_worktrees\2ndB-codex
app_branch: codex/poll-native-ui-safety-20260614
app_base: origin/main@32db97b
app_commit: aaaa3e4 test(auth): guard pre-auth routing links
---

# Codex report - auth routing regression rebased

[2026-06-14 / 03:05:15 KST]

## Summary

Codex continued the loop and reconciled the pending auth-routing regression test branch with the now-updated `origin/main`.

- `origin/main` now includes the first-glimpse records handoff as `32db97b fix(capture): clarify first-run records handoff`.
- The Codex worktree branch `codex/poll-native-ui-safety-20260614` had a separate test-only commit for the Antigravity auth-routing QA follow-up.
- Rebased that branch onto `origin/main@32db97b`.
- Resolved the same-file test conflict by keeping both contracts:
  - first-run capture copy promises a saved record in Records, not guest/local/graph storage;
  - sign-in exposes `Create one` as `/sign-up`, while `Forgot password?` remains inline reset help.

## App Change For Review

Branch:

`codex/poll-native-ui-safety-20260614...origin/main [ahead 1]`

Commit:

`aaaa3e4 test(auth): guard pre-auth routing links`

Changed file:

`src/lib/__tests__/visible-trust-copy.test.ts`

The added regression test checks:

- sign-in submit control exists before account-creation link;
- `Create one` is a real `<Link href="/sign-up" asChild>`;
- reset help is driven by `handleForgotPassword` / `setResetHelpVisible(true)`;
- there is no visible `<Link href="/reset-password"` on the sign-in screen;
- EN/KO `signUpLink` locale strings remain present.

No runtime auth code was changed in this pass.

## Verification

Focused:

`npm test -- visible-trust-copy.test.ts --runInBand`

Result: PASS, 1 suite / 6 tests.

Full:

`npm run verify`

Result: PASS, 131 suites / 1140 tests. Lint remains 0 errors / 4 existing warnings.

`git diff --check origin/main...HEAD`

Result: PASS.

## Claude/AG Hand-off

This branch is ready for Claude to merge/cherry-pick if the team wants a code-level guard around Antigravity's auth QA observation. Antigravity should still rerun native taps on current main or this branch, because this pass proves the route contract in source/tests, not device-level tap behavior.

