---
from: codex
to: claude
type: request
src: user
created: 2026-06-06 08:13:04 KST
topic: auth launch actions do not share a mutually exclusive busy contract
score: 98/100 provisional
priority: P2
---

# Codex UI Gate: Auth Launch Busy Contract

Simon asked us to keep pushing all screens toward 100/100 anti-slop. I continued from the source-punctuation guard and audited the first public auth surfaces on `E:\2ndB` `main@911c979`.

Current verdict: still **98/100 provisional**, not 100. This is a P2 auth interaction-state gate.

This is not the same as the earlier Pressable semantics report. That report covered role/label/state exposure. This one is about mutual exclusion between competing auth launch paths.

## Finding

`/sign-in` and `/sign-up` have separate `submitting` and `oauthSubmitting` states, but the email submit path does not consider `oauthSubmitting`. Social providers do consider `submitting`. This means an OAuth launch can be in progress while the email submit button remains logically available.

Naver also bypasses the common `oauthSubmitting` state entirely, so its button reads as if it participates in the same disabled contract, but the handler never sets that state.

For auth entry screens, "only one sign-in/sign-up launch can be in flight" should be a hard UI invariant. Otherwise the first impression can become double-submit, double-alert, or competing redirect behavior.

## Evidence

### `/sign-in`

- `src/app/(auth)/sign-in.tsx:51-52`: has both `submitting` and `oauthSubmitting`.
- `src/app/(auth)/sign-in.tsx:66-91`: Google/Apple/Kakao `handleOAuth` sets `oauthSubmitting`.
- `src/app/(auth)/sign-in.tsx:96-107`: `handleNaver` calls `signInWithNaver()` but never sets `oauthSubmitting`.
- `src/app/(auth)/sign-in.tsx:109-128`: email `handleSubmit` sets `submitting` only.
- `src/app/(auth)/sign-in.tsx:131`: `canSubmit = email.includes("@") && password.length > 0 && !submitting`; it ignores `oauthSubmitting`.
- `src/app/(auth)/sign-in.tsx:224-227`: primary email submit is disabled only by `!canSubmit`.
- `src/app/(auth)/sign-in.tsx:241-280`: social buttons are disabled by `oauthSubmitting || submitting`.

Result: starting Google/Apple/Kakao disables social buttons but not the email submit path if the fields are valid. Naver has the same disabled prop, but its handler does not flip the flag.

### `/sign-up`

- `src/app/(auth)/sign-up.tsx:46-47`: has both `submitting` and `oauthSubmitting`.
- `src/app/(auth)/sign-up.tsx:60-68`: `canSubmit` checks form validity and `!submitting`, but not `!oauthSubmitting`.
- `src/app/(auth)/sign-up.tsx:70-109`: email sign-up sets `submitting`.
- `src/app/(auth)/sign-up.tsx:115-140`: Google/Apple/Kakao set `oauthSubmitting`.
- `src/app/(auth)/sign-up.tsx:143-154`: Naver does not set `oauthSubmitting`.
- `src/app/(auth)/sign-up.tsx:257-264`: primary sign-up button uses `disabled={!canSubmit}` and `loading={submitting}` only.
- `src/app/(auth)/sign-up.tsx:275-304`: provider buttons disable on `oauthSubmitting || submitting`.

Result: an OAuth launch can leave the email sign-up CTA available, and Naver again skips the common pending state.

### Naver helper

- `src/lib/supabase/auth.ts:352-370`: `signInWithNaver()` is synchronous and assigns `window.location.href`.
- If navigation is delayed or the user double taps before the browser leaves, the screen has no visible busy state or mutual exclusion for that launch.

## Required Fix

Please implement one auth-launch contract for sign-in and sign-up.

1. Derive a shared `authLaunching = submitting || oauthSubmitting || naverSubmitting` state, or make Naver use the existing `oauthSubmitting` state before assigning `window.location.href`.
2. Email submit buttons must be disabled and announce busy/disabled while any provider launch is pending.
3. Social provider buttons must stay disabled while email submit is pending.
4. The visible loading label should preserve provider identity. Avoid turning every provider button into the same `...` label.
5. Naver should get the same one-tap guard as Google/Apple/Kakao, even if the expected next step is a browser redirect.
6. Add a focused test or static assertion for sign-in and sign-up: with `oauthSubmitting=true`, email CTA is disabled; with `submitting=true`, provider CTAs are disabled; Naver flips a pending guard before redirect.

## Acceptance Proof Needed

For the next Claude completion, include:

- Code evidence that `/sign-in` email submit is disabled during any OAuth launch.
- Code evidence that `/sign-up` email submit is disabled during any OAuth launch.
- Code evidence that Naver sets or shares a pending guard.
- UI proof or test output showing provider-specific busy feedback, not anonymous `...` on every provider.
- `npm run verify` pass after the change.

Until this is closed, the auth entry flow is not 100/100 because competing launch paths can remain active during a pending auth transition.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-081304-auth-launch-busy-contract-gate.html`
