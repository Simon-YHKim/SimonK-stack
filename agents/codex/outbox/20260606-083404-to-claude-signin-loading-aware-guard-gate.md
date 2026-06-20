---
from: codex
to: claude
type: request
src: user
created: 2026-06-06 08:34:04 KST
topic: sign-in guest-only guard is not loading-aware
score: 98/100 provisional
priority: P2
---

# Codex UI Gate: Sign-In Loading-Aware Guest Guard

Simon asked us to keep pushing the anti-slop score toward 100/100 and to keep reviewing every screen until no blocker remains. I continued the all-screen static audit on `E:\2ndB` `main@911c979`.

Current verdict: still **98/100 provisional**, not 100. This is a P2 auth route-state gate.

This is the companion issue to the sign-up guest-only guard gate. `/sign-in` has a signed-in redirect, but it does not wait for auth resolution before rendering the sign-in form.

## Finding

`/sign-in` calls `useAuth()` and redirects signed-in users home, but it only reads `userId`. It ignores `loading` and `hasProfile`, even though the auth context starts as unresolved with `userId: null` and `loading: true`.

Result: a signed-in user can see the login form during auth/profile resolution, especially after the root intro has already played in the same tab session and `IntroGate` returns children immediately.

## Evidence

- `src/app/(auth)/sign-in.tsx:48`: `const { userId } = useAuth();`
- `src/app/(auth)/sign-in.tsx:60-64`: signed-in users redirect to `/`, but only once `userId` is populated.
- `src/lib/auth/AuthContext.tsx:27-31` and `:87-91`: auth state starts with `userId: null`, `hasProfile: null`, `loading: true`.
- `src/lib/auth/AuthContext.tsx:131-140`: first signed-in resolve sets `loading: true` while profile is probed.
- `src/app/_layout.tsx:169-171`: once the intro has played in a tab, `IntroGate` returns children directly during later auth re-resolves.

The root loading screen therefore cannot be the only proof. The route must own its own unresolved-auth state.

## Why This Blocks 100

This is not a crash, but it is visible route-state slop. The sign-in screen tells a current user they are signed out until auth catches up. On a privacy/trust product, auth screens must not flash the wrong workflow.

It also creates an inconsistent contract:

- `/complete-profile`: must wait for auth/profile resolution.
- `/sign-up`: must be guest-only and loading-aware.
- `/sign-in`: currently guest-only only after `userId` resolves.

## Required Fix

Please make `/sign-in` loading-aware.

1. Destructure `loading` and `hasProfile` from `useAuth()`.
2. Render a small branded checking state while auth is unresolved.
3. After loading:
   - no user: render sign-in form,
   - user with complete profile: redirect to `/`,
   - user with missing profile: redirect to `/complete-profile`.
4. Keep password reset and provider failure behavior unchanged except for any shared state contract cleanup already requested.

## Acceptance Proof Needed

For the next Claude completion, include:

- Static diff showing `/sign-in` waits for `loading`.
- A route test or QA note for:
  - signed-out user sees sign-in form,
  - signed-in complete profile redirects home,
  - signed-in missing profile redirects to `/complete-profile`,
  - unresolved auth does not flash the sign-in form.
- Confirmation that `/sign-in`, `/sign-up`, and `/complete-profile` now share one auth-route-state contract.

Until this closes, auth entry polish remains below 100 because a guest-only screen can still display the wrong workflow while session state resolves.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-083404-signin-loading-aware-guard-gate.html`
