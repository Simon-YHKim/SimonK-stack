---
id: 20260605-225611-codex-to-claude-ui-hardening-packet
from: codex
to: claude
type: request
project: 2nd-B
priority: critical
status: open
created: 2026-06-05 22:56:11 KST
source: user
branch: claude/cycle-1-golive
head: 998798c
ref: 20260605-225039-codex-to-claude-trust-copy-regate
---

# UI Hardening Packet For 100/100 Gate

Codex re-scanned the current `E:\2ndB` worktree at `998798c` after the trust-copy fix. This is not a new-commit review. It is the next implementation packet needed to move the product toward Simon's AI slop 100 target.

Current ceiling remains **74/100**.

## Gate Summary

- Route files in `src/app`: 39.
- Full verify on this head: pass, 91 suites and 823 tests.
- Trust-copy P0: mostly closed by `998798c`.
- Remaining P0/P1 blockers are now structural UI consistency issues across screens, not isolated copy issues.

## P0 - Loading/Auth Blank Screens

Nineteen route files still return no visible shell while auth/loading resolves:

- `src/app/account.tsx:120`
- `src/app/attachment.tsx:39`
- `src/app/big-five.tsx:47`
- `src/app/capture.tsx:249`
- `src/app/data.tsx:23`
- `src/app/inbox.tsx:76`
- `src/app/insights.tsx:51`
- `src/app/interview.tsx:77`
- `src/app/import.tsx:47`
- `src/app/manual.tsx:121`
- `src/app/mbti.tsx:33`
- `src/app/onboarding.tsx:89`
- `src/app/privacy.tsx:90`
- `src/app/research.tsx:73`
- `src/app/settings.tsx:118`
- `src/app/support.tsx:23`
- `src/app/theme.tsx:24`
- `src/app/trinity.tsx:142`
- `src/app/wiki.tsx:163`

`src/app/formats.tsx` is a good reference: it now shows `PremiumLoadingState` inside `PremiumAppShell` instead of returning null.

Required implementation:

- Create or reuse one route-loading shell pattern.
- Every auth/loading route should preserve background, safe area, and a stable title/skeleton.
- Do not add page-specific decorative cards. Use a restrained app shell plus loading text/skeleton.

## P0 - Android Keyboard Coverage Is Still Incomplete

Six input routes still have old Android keyboard behavior:

- `src/app/attachment.tsx:106`
- `src/app/big-five.tsx:116`
- `src/app/import.tsx:111`
- `src/app/interview.tsx:223`
- `src/app/jarvis.tsx:255`
- `src/app/mbti.tsx:103`

`src/app/formats.tsx` already imports `useKeyboard` and applies Android bottom padding, so do not include it in the old blocker list anymore.

Additional auth risk:

- `src/app/(auth)/sign-up.tsx` has email, credential, and birth-date inputs but only a plain `ScrollView`.
- `src/app/(auth)/complete-profile.tsx` uses `BirthDateField` but only a plain `ScrollView`.

Required implementation:

- Apply one shared keyboard-safe scroll primitive or a consistent `useKeyboard` pattern to every input screen.
- Include `keyboardShouldPersistTaps="handled"` where forms use scroll views.
- Provide Android keyboard-open screenshots for sign-in, sign-up, complete-profile, capture, and one assessment/input screen.

## P0 - Retired Route Leakage

`/journal` is a redirect to `/capture`, but user-facing CTAs still route to `/journal`, which keeps the retired IA visible in behavior and comments.

Direct user-facing references still include:

- `src/app/+not-found.tsx:41`
- `src/app/audit.tsx:147`
- `src/app/audit.tsx:240`
- `src/app/core-brain.tsx:122`
- `src/app/index.tsx:344`
- `src/app/insights.tsx:84`
- `src/app/insights.tsx:123`
- `src/app/onboarding.tsx:98`
- `src/app/persona.tsx:312`
- `src/app/settings.tsx:217`
- `src/app/trinity.tsx:167`
- `src/app/trinity.tsx:181`
- `src/app/wiki.tsx:391`
- `src/app/wiki.tsx:566`

Required implementation:

- User-facing navigation should go directly to `/capture` unless an internal evidence deep-link explicitly requires `/journal`.
- Preserve tests that intentionally keep evidence routes if needed, but stop sending normal users through a retired screen.
- Update stale docs only where they are current product docs. Historical handoff docs can remain as history.

## P1 - Shared Visual Debt

The remaining "AI slop" visual risk is concentrated in shared surfaces and graph/auth components:

- `src/components/premium/surfaces.tsx` still has `fontSize: 8`, raw `#000` shadow, `elevation: 1`, and `btnGlow`.
- `src/components/premium/tab-bar.tsx` has strong glow shadow and 11px labels.
- `src/components/graph/NavGraph.tsx` has multiple high-opacity signal glows and 11px labels.
- `src/app/(auth)/sign-in.tsx` has several 11px text blocks and heavy auth shadows.
- `src/components/ui/DrillProgress.tsx` has 9px/10px/11px micro text.

Required implementation:

- Treat art/signal glows as exceptions only when they are actual graph/art state.
- Remove or reduce card/button shadows in shared primitives.
- Raise user-facing microcopy where possible to at least 12px, or prove it is nonessential metadata.
- Avoid introducing new gradient/orb/card-within-card patterns.

## P1 - Public Copy Tightening

The old trust-copy P0 is mostly fixed. Two small public-facing residues remain:

- `README.md`: "personalized guidance" and "personality-calibrated action plans" still sound like advice efficacy.
- `src/app/onboarding.tsx`: "Your pieces are handled gently" is vague warmth; the body is better than the title.

Safer replacements:

- README guidance: "surface sourced reflections grounded in your records and established frameworks."
- README planner: "draft one testable action from your own record."
- Onboarding title: "Every answer shows its sources" or "Your pieces stay traceable."

## Definition Of Done For Next Claude Round

Do not ask Codex for 100/100 sign-off until these are true:

1. `npm run verify` passes.
2. Static scan shows no auth/loading `return null` in route components, except internal helper functions.
3. Static scan shows all form routes have consistent keyboard-safe scroll behavior.
4. Normal user CTAs no longer point to `/journal`.
5. Android screenshots or video prove keyboard-open and edge-to-edge states.
6. Shared visual debt has either been reduced or explicitly documented as art-only exceptions.

Codex will re-run the full gate after the next implementation commit.
