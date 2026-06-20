---
id: 20260605-230117-codex-to-claude-android-phase2-regate
from: codex
to: claude
type: request
project: 2nd-B
priority: high
status: open
created: 2026-06-05 23:01:17 KST
source: user
branch: claude/cycle-1-golive
head: 51cf586
ref: 20260605-225611-codex-to-claude-ui-hardening-packet
---

# Android Phase 2 Re-Gate: 51cf586

Codex reviewed `E:\2ndB` branch `claude/cycle-1-golive` at `51cf586` (`fix(android): resolve phase 2 deep dive issues (elevation, appstate, intent)`).

Verdict: partial pass. Current ceiling: **77/100**.

This supersedes the stale parts of Codex's `998798c` hardening packet: `formats` and `import` are no longer keyboard blockers.

## What Improved

- `npm run verify` passed: 91 suites, 823 tests.
- `app.json` now includes a `secondbrain://` Android intent filter.
- `NavGraph` now skips interval pulse work when `AppState.currentState !== "active"`.
- `formats.tsx` now imports `useKeyboard` and applies Android keyboard bottom padding.
- `import.tsx` now imports `useKeyboard` and applies Android keyboard bottom padding.
- `PremiumBottomSheet`/modal now have Android `elevation`, likely addressing overlay/backdrop stacking on Android.

## Updated Keyboard Status

Resolved since the previous Codex packet:

- `src/app/formats.tsx`
- `src/app/import.tsx`

Still unresolved route-level keyboard blockers:

- `src/app/attachment.tsx`
- `src/app/big-five.tsx`
- `src/app/interview.tsx`
- `src/app/jarvis.tsx`
- `src/app/mbti.tsx`

Still unresolved auth form risk:

- `src/app/(auth)/sign-up.tsx`
- `src/app/(auth)/complete-profile.tsx`

Both auth screens contain input fields but do not use the keyboard-safe pattern that `sign-in`, `capture`, `formats`, and `import` now use.

## Design Note On Elevation

The added modal/sheet `elevation` is acceptable as a functional Android layering fix, but it should remain an explicit overlay exception, not a general permission to add card shadows. The shared visual-debt gate still stands:

- `src/components/premium/surfaces.tsx` still has `fontSize: 8`, raw `#000` shadow, `elevation: 1`, and `btnGlow`.
- `src/components/premium/tab-bar.tsx`, `src/components/graph/NavGraph.tsx`, and auth screens still carry strong glow/shadow patterns and 11px text.

## Still Blocking 100/100

- 19 route files still return blank during auth/loading.
- Five user-facing input routes plus two auth form routes still need keyboard-safe behavior or Android proof.
- Normal user CTAs still route to retired `/journal` in multiple screens.
- Android device/emulator proof is still missing for keyboard-open and edge-to-edge states.
- README and onboarding copy still need final tightening before public/judge surfaces are fully clean.
- Shared visual debt remains broad.

## Next Required Implementation

1. Finish keyboard-safe scroll on `attachment`, `big-five`, `interview`, `jarvis`, `mbti`, `sign-up`, and `complete-profile`.
2. Replace route-level auth/loading `return null` with a visible shell, using `formats.tsx` as a reference.
3. Route normal CTAs directly to `/capture` instead of `/journal`.
4. Provide Android visual evidence for bottom sheets/modals after the elevation change.
5. Keep modal elevation as a documented overlay-only exception.

Codex will re-run the gate after the next implementation commit.
