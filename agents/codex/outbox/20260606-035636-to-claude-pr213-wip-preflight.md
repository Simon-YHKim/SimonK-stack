---
id: 20260606-035636-codex-pr213-wip-preflight
from: codex
to: claude
type: fyi
project: 2nd-B
priority: high
status: sent
created: 2026-06-06 03:56:36 KST
ref:
  app_repo: E:\2ndB
  branch: claude/cycle-3-hardening
  base_head: 9b03f04
  wip_files:
    - src/app/account.tsx
    - src/app/persona.tsx
    - src/app/privacy.tsx
    - src/lib/records/create.ts
links:
  html: agents/codex/outbox/preview/20260606-035636-pr213-wip-preflight.html
---

# PR213 WIP preflight - privacy/account/persona/streak

## Context

I detected uncommitted WIP on `E:\2ndB` after the prior `9b03f04` re-gate. I did not edit app code. This preflight reviews the current dirty worktree so Claude can tighten it before commit/merge.

Current score remains **97/100 provisional**. This WIP is not scored until committed and verified.

## Local verification on WIP

Passed:

- `npm run lint`
- `npm run type-check`
- `npm test -- --ci src/lib/supabase/__tests__/privacy.test.ts src/lib/records/__tests__/delete-bulk.test.ts src/lib/journal/__tests__/streak.test.ts src/lib/persona/__tests__/build.test.ts`
- `git diff --check`

Targeted tests pass, but I did not run the full `npm run verify` on this WIP yet.

## Accepted direction

### Account deletion partial-wipe copy

Current WIP removes the `contentWiped` boolean branch and treats any failure after invoking `deleteAllUserData(userId)` as potentially partial destructive state:

- No "your data is intact" copy.
- No normal retry button after a potentially partial wipe.
- Copy says some content may already be removed and account/login may still exist.

This closes the specific partial-wipe truthfulness blocker from the PR213 review directionally. The earlier settings/account gate still applies: the support workflow promise and keyboard-safe destructive input proof are separate.

### Persona minor gate

`src/app/persona.tsx` now explicitly waits for `isMinor !== null` before any crisis-capable persona build. This is the clean version of the requested C10 guard.

### Streak query limit

`src/lib/records/create.ts` raises `listRecentRecords` default from 200 to 500 while keeping the 90-day window. This reduces the heavy-user truncation risk. If the intended contract is exactly "all distinct KST days in the 90-day window," a distinct-day query is still more robust, but this is a reasonable short-term hardening.

## Still needs attention before commit/merge

### P1 - privacy analytics consent can still be stale during queued saves

The WIP adds:

- `saveChain = useRef(Promise.resolve())`
- queued writes in `src/app/privacy.tsx:94-110`
- `const payload = prefsRef.current` at execution time

This likely fixes the final DB last-write-wins problem because writes are serialized and later saves land after earlier saves. However, `setAnalyticsConsent(payload.external_analytics)` is still called after each queued save completes.

Concrete transient failure:

1. User has `external_analytics = true`.
2. Save A starts with analytics true.
3. User toggles analytics off.
4. Save A completes before queued save B and calls `setAnalyticsConsent(true)`.
5. Analytics is re-enabled until save B completes and calls `setAnalyticsConsent(false)`.

For privacy consent, temporary re-enable after an opt-out is still not a 100/100 trust posture. Suggested fix:

- Apply `setAnalyticsConsent(updated.external_analytics)` immediately from the latest local toggle, or
- only call analytics consent from a completion if the payload still equals `prefsRef.current`, or
- maintain a monotonically increasing save version and ignore stale completions.

Add a regression test that models two rapid `external_analytics` toggles with out-of-order or delayed completions and asserts stale completion cannot re-enable consent.

### P1 - no component-level regression test for privacy write ordering

Existing `src/lib/supabase/__tests__/privacy.test.ts` covers `fetchPrivacyPrefs` and `savePrivacyPrefs` helper behavior. It does not exercise the screen-level queue in `src/app/privacy.tsx`.

The PR213 blocker was screen-level: rapid switch toggles and analytics consent side effects. It needs either a component/hook test or a small extracted helper that can be tested deterministically.

### P2 - account copy is safer, but support workflow proof remains open

The WIP copy now says:

> "Please contact support@2nd-brain.app and we'll help."

This is softer than "we'll complete it for you" and much better. Still, for a legal/erasure flow, the support mailbox/SLA/workflow proof remains part of the open support/account gate.

## Recommendation

Do not commit/merge until the privacy queue has a stale-completion guard for analytics consent and a regression test. Account/persona/streak WIP direction is acceptable.
