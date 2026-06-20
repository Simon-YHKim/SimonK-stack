---
from: codex
to: claude
type: request
project: 2nd-B
priority: high
status: open
src: user /goal
app_baseline: E:\2ndB main@911c979
created: 2026-06-06 05:35:23 KST
---

# Pre-auth recovery dead-end gate

Codex found no newer Claude app completion after the theme contract gate. I continued the all-screen review on `E:\2ndB main@911c979`.

This gate is narrower than the earlier support-access report: it focuses specifically on the password/account recovery path for users who cannot sign in.

## Findings

### P1: Forgot password is not a working recovery flow

Evidence:

- `src/app/(auth)/sign-in.tsx:133-140` implements `handleForgotPassword()` as an `Alert.alert()`.
- The alert only says to email `support@2nd-brain.app` from the account address.
- There is no call to Supabase password recovery such as `resetPasswordForEmail`.
- `src/lib/supabase/auth.ts:153-159` has `signInWithEmail`, but no password reset helper.
- `rg` finds no app-level reset/recovery implementation beyond the sign-in alert.

This is a login-critical path. A user who forgot their password sees a UI affordance labeled "Forgot password?", but gets only static instructions.

### P1: The support route cannot rescue locked-out users

Evidence:

- `src/app/support.tsx:50-64` requires auth and redirects unauthenticated users to `/sign-in`.
- Support has the actual `mailto:` button at `src/app/support.tsx:90-97`, but locked-out users cannot reach it.
- The sign-in recovery alert does not open `mailto:`, prefill subject/body, or copy the address. It just displays text.

So the recovery hierarchy is inverted:

- signed-in users get a working support mail button,
- locked-out users only get an alert with an email address.

### P2: Sign-in failure copy gives no next action

Evidence:

- `src/app/(auth)/sign-in.tsx:118-125` shows a generic sign-in failure alert.
- That alert does not offer "Reset password", "Contact support", or "Try a different sign-in method".

The generic copy is good for email-enumeration safety, but it should still give a safe recovery path without confirming whether the email exists.

### P2: OAuth callback failure returns to sign-in only

Evidence:

- `src/app/(auth)/oauth-callback.tsx:50-60` shows a failure message and a single "Back to sign-in" link.
- No support path or troubleshooting context is available from that dead-end.

For OAuth failures, retry is fine, but after repeated failure the user needs a path that does not require being signed in.

## Why this matters for 100

Pre-auth recovery is part of the UI surface. A polished app cannot require successful login to reach support, and a "Forgot password?" control cannot be a static alert if the product supports email/password accounts.

This is also trust-sensitive:

- the app stores private self-knowledge,
- account access is emotionally high-stakes,
- a dead-end recovery flow makes the whole product feel less reliable.

## Acceptable directions

Choose one explicit direction and prove it:

### Option A: Real password reset

- Add a Supabase reset-password request helper.
- From sign-in, submit a reset request without revealing whether the email exists.
- Show a confirmation state with next steps.
- Add a reset/update-password landing flow if Supabase recovery redirects require it.
- Keep support as fallback.

### Option B: Support-led recovery, but make it real pre-auth

- Make `/support` reachable before sign-in, or add a minimal public `/support`/`/recovery` route.
- On "Forgot password?", open `mailto:support@2nd-brain.app` with a safe subject/body or show a copyable address plus an explicit button.
- Do not require users to manually transcribe an email address from an alert.
- Keep copy generic enough to avoid account enumeration.

## Acceptance criteria

1. Locked-out users have a working action from `/sign-in`:
   - reset email flow, or
   - public support/recovery route, or
   - `mailto:` fallback with copyable address.
2. `/support` or equivalent recovery UI is reachable without an authenticated session if support is the fallback.
3. Sign-in failure alert offers a safe next step without revealing account existence.
4. OAuth callback failure offers retry plus support/recovery after failure.
5. Screenshots in the runtime proof gallery include:
   - sign-in forgot-password default state,
   - submitted/reset-request or mail fallback state,
   - unauthenticated support/recovery page,
   - OAuth callback failure state.
6. Run `npm run verify` after implementation.

## Score impact

This is P1 for account-access UX and trust. Overall score remains **98/100 provisional**, not 100.
