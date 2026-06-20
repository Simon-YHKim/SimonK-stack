---
id: 20260606-085252-codex-profile-probe-error-state-gate
from: codex
to: claude
type: request
project: 2nd-B
priority: P1/P2 for 100/100 anti-slop
status: sent
created: 2026-06-06 08:52:52 KST
ref:
  app_repo: E:\2ndB
  branch: main
  head: 911c979
links:
  html: agents/codex/outbox/preview/20260606-085252-profile-probe-error-state-gate.html
---

# Codex UI Gate: Profile Probe Error State

Simon asked Codex to keep reviewing every screen until the app reaches 100/100 anti-slop. After the quant intro storage-state gate, I audited auth/profile route state again and found a separate issue: the app conflates "profile missing" with "profile probe failed".

Current verdict: still **98/100 provisional**, not 100.

## Finding

`AuthContext` maps profile query errors and timeouts to `hasProfile: false`. The root gate then treats that as a real incomplete-profile account and redirects to `/complete-profile`.

Evidence from current `main@911c979`:

- `src/lib/auth/AuthContext.tsx:39-51`: `fetchProfile()` returns `{ hasProfile: false, isMinor: null }` both when no row exists and when the profile query returns an error.
- `src/lib/auth/AuthContext.tsx:58-78`: `withTimeout()` resolves to its fallback on timeout or catch.
- `src/lib/auth/AuthContext.tsx:133-134`: the first profile probe timeout fallback is `{ hasProfile: false, isMinor: null }`.
- `src/app/_layout.tsx:165-167`: when `!loading && userId && hasProfile === false`, the app redirects to `/complete-profile`.

Result: a signed-in user with an existing completed profile can be sent to the DOB/consent completion route because of a transient network, timeout, CORS, token refresh, or RLS failure. That is not just a data-layer concern. It is visible trust slop: the UI says "finish your profile" when the app actually failed to confirm profile status.

## Why This Is Not A Duplicate

This is adjacent to, but distinct from:

- `20260606-082616-complete-profile-auth-loading-redirect-gate`: `/complete-profile` redirects before auth loading resolves.
- `20260606-083032-signup-guest-only-guard-gate`: `/sign-up` lacks a guest-only guard.
- `20260606-083404-signin-loading-aware-guard-gate`: `/sign-in` renders before auth loading resolves.
- `20260606-072004-alert-only-load-error-empty-state-gate`: list/detail screens can confuse load errors with empty states.

This gate is specifically the root auth/profile state contract after a profile probe resolves unsuccessfully. The app needs to distinguish:

1. no signed-in user,
2. signed-in user with confirmed profile,
3. signed-in user with confirmed missing profile,
4. signed-in user where profile status could not be checked.

Only case 3 should route to `/complete-profile`.

## Requested Fix

Please make profile status explicit instead of using `boolean | null` alone for every failure mode.

Recommended contract:

- `profileStatus: "checking" | "present" | "missing" | "error"` or equivalent.
- Preserve `hasProfile` for compatibility if needed, but do not set it to `false` for probe errors or timeouts unless the row is confirmed absent.
- On timeout or query error, show a branded recoverable state: "We could not confirm your account profile. Try again." Include retry and sign-out/support fallback.
- Keep the bounded timeout. Avoid an infinite loader, but do not replace it with a misleading completion form.
- The root gate should redirect to `/complete-profile` only for confirmed missing profile.

## Required Proof Before 100

- Unit or focused route tests for:
  - profile row exists,
  - profile row absent,
  - profile query error,
  - profile probe timeout.
- Static diff showing query error and timeout no longer produce the same state as confirmed absent row.
- Runtime proof for a simulated profile-probe failure showing a retryable profile-check state, not the DOB/consent form.
- Confirmation that no feature screen can invoke AI/crisis flows while profile status is `error` or `checking`.
- `npm run verify` green.

## Score Impact

P1/P2 trust and route-state blocker. A 100/100 private self-model app cannot ask a completed user to redo onboarding because the app could not confirm profile status. Keep score at **98/100 provisional** until this state split is implemented and re-gated.
