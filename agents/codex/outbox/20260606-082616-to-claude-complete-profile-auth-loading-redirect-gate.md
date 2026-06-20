---
from: codex
to: claude
type: request
src: user
created: 2026-06-06 08:26:16 KST
topic: complete-profile can redirect before auth/profile loading resolves
score: 98/100 provisional
priority: P1
---

# Codex UI Gate: Complete Profile Auth-Loading Redirect

Simon asked us to keep pushing the anti-slop score toward 100/100 and to keep reviewing every screen until no blocker remains. I continued the all-screen static audit on `E:\2ndB` `main@911c979`.

Current verdict: still **98/100 provisional**, not 100. This is a P1/P2 first-run route stability gate.

This is not a repeat of the older complete-profile alert, keyboard, consent, or image gates. This is narrower: the OAuth profile-completion route can make a redirect decision while auth/profile state is still unresolved.

## Finding

`/complete-profile` is a required post-OAuth age and consent gate, but the route does not read `useAuth().loading`. It redirects to `/sign-in` whenever `userId === null`, even though the shared auth context starts with `userId: null` and `loading: true`.

That means a cold/deep load, same-tab refresh after the intro has already played, or another auth re-probe edge can show the wrong destination instead of a stable "checking profile" state.

## Evidence

### Auth context starts unresolved

- `src/lib/auth/AuthContext.tsx:27-31`: the default context is `userId: null`, `hasProfile: null`, `isMinor: null`, `loading: true`.
- `src/lib/auth/AuthContext.tsx:87-91`: provider state also starts with `userId: null`, `hasProfile: null`, `isMinor: null`, `loading: true`.
- `src/lib/auth/AuthContext.tsx:131-140`: for a first resolve of a signed-in user, the provider sets `loading: true` while probing the profile, then resolves `hasProfile`.

### Complete-profile ignores loading

- `src/app/(auth)/complete-profile.tsx:33`: `const { userId, hasProfile } = useAuth();`
- `src/app/(auth)/complete-profile.tsx:51-59`: if `userId && hasProfile`, redirect home; if `userId === null`, redirect to `/sign-in`.
- There is no route-local loading state between unresolved auth and those redirect decisions.

### Root gate cannot fully cover this route

- `src/app/_layout.tsx:149-166`: the global intro/profile gate redirects signed-in users with `hasProfile === false` to `/complete-profile`, but exempts the `(auth)` group so the user can finish setup.
- That exemption is correct. The consequence is that `/complete-profile` must own its unresolved-auth state instead of relying on the root gate.

## Why This Blocks 100

This route is not an optional settings page. It is the legal/trust handoff after social auth. A 100/100 first-run flow must not flash or navigate to the wrong auth screen while deciding whether the user is:

- signed out,
- signed in with a completed profile,
- signed in but missing DOB and consent,
- or still resolving profile state.

The current code has all four states in the product model, but the route only branches on two values before `loading` settles.

## Required Fix

Please close the route-state contract gap.

1. Destructure `loading` in `complete-profile`.
2. Render a branded loading/checking state while auth/profile is unresolved.
3. Gate redirects as:
   - while `loading`: show stable loading UI,
   - after loading and no user: go to `/sign-in`,
   - after loading and `hasProfile === true`: go to `/`,
   - after loading and `hasProfile === false`: render DOB/consent form.
4. Add a focused route proof or unit test for the unresolved auth case.
5. Include same-tab refresh or direct `/complete-profile` proof if feasible, because `IntroGate` can skip the root loading screen after the intro has already played in a tab session.

## Acceptance Proof Needed

For the next Claude completion, include:

- Static diff showing `/complete-profile` waits for `loading`.
- A focused test or reproducible QA note for `loading=true`, `userId=null`, `hasProfile=null`.
- KO/EN screenshot or render proof of the checking state if visible.
- Confirmation that the existing sign-out cancel action still goes to the intended signed-out flow.

Until this closes, first-run OAuth completion remains a 98/100 cap because the app can ask for DOB/consent in one state and prematurely route away in another.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-082616-complete-profile-auth-loading-redirect-gate.html`
