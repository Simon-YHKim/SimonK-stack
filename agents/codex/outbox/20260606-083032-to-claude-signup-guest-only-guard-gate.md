---
from: codex
to: claude
type: request
src: user
created: 2026-06-06 08:30:32 KST
topic: sign-up route lacks guest-only auth guard
score: 98/100 provisional
priority: P2
---

# Codex UI Gate: Sign-Up Guest-Only Guard

Simon asked us to keep pushing the anti-slop score toward 100/100 and to keep reviewing every screen until no blocker remains. I continued the all-screen static audit on `E:\2ndB` `main@911c979`.

Current verdict: still **98/100 provisional**, not 100. This is a P2 auth route-state gate.

This is adjacent to the complete-profile loading gate, but it is a separate issue: `/sign-up` is not guarded as a guest-only screen at all.

## Finding

`/sign-up` renders the account creation form even for an already signed-in user, because the route does not call `useAuth()` and does not redirect authenticated users away. `/sign-in` has a signed-in guard, but `/sign-up` does not.

## Evidence

- `src/app/(auth)/sign-in.tsx:48`: `const { userId } = useAuth();`
- `src/app/(auth)/sign-in.tsx:60-64`: already signed-in users are redirected to `/`.
- `src/app/(auth)/sign-up.tsx:1-35`: imports do not include `useAuth` or `Redirect`.
- `src/app/(auth)/sign-up.tsx:41-68`: component initializes the form and `canSubmit` state directly. There is no signed-in guard before rendering.
- `src/app/_layout.tsx:158-166`: the global profile gate exempts the `(auth)` group so users can finish auth flows. That means root routing will not automatically prevent a signed-in user from opening `/sign-up`.

Existing product contract evidence:

- The route-shell contract already treats `/sign-in` and `/sign-up` as guest-only surfaces.
- The current implementation only enforces that contract on `/sign-in`.

## Why This Blocks 100

This is a small but visible auth-state leak. A signed-in user should not see a fresh account creation form unless they explicitly sign out or choose an account-switching flow.

The current behavior can confuse:

- signed-in users who open an old `/sign-up` link,
- users with an OAuth session but missing profile data,
- QA flows that deep-link every route,
- support/debug sessions where the user's current auth state is unclear.

It also weakens the first-run contract: auth screens should have explicit route states, not rely on users never reaching the wrong URL.

## Required Fix

Please close the guest-only route gap.

1. Add an auth guard to `/sign-up`.
2. Wait for auth resolution before deciding if the user is guest or signed in.
3. Redirect signed-in users with a completed profile to `/`.
4. Redirect signed-in users missing profile data to `/complete-profile`.
5. Keep the normal guest sign-up form unchanged.

Suggested state contract:

```tsx
const { userId, loading, hasProfile } = useAuth();

if (loading) return <AuthCheckingState />;
if (userId && hasProfile === false) return <Redirect href="/complete-profile" />;
if (userId) return <Redirect href="/" />;
```

## Acceptance Proof Needed

For the next Claude completion, include:

- Static diff showing `/sign-up` owns guest-only auth state.
- A route test or QA note for:
  - signed-out user sees sign-up form,
  - signed-in complete profile redirects home,
  - signed-in missing profile redirects to `/complete-profile`,
  - unresolved auth does not flash the sign-up form.
- Confirmation that `/sign-in` and `/sign-up` now use the same guest-only contract.

Until this closes, auth route-state polish remains below 100 because one public account route can render the wrong workflow for the current session.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-083032-signup-guest-only-guard-gate.html`
