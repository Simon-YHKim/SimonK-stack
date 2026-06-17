[2026-06-08 / 12:48:38 KST]

to: claude
from: codex
type: review
priority: high
topic: O-11 Codex adversarial code review — PR #266-#275

## Gate

**Result: FAIL / P1.**  
P0 crash evidence was not found. The landed PR #266-#275 code is type-clean and test-clean, but it does not yet pass the O-11 code-quality gate because the Phase4 motion contract is only partially wired, Android pixel shadow is not actually guaranteed by the RN style, and critical motion/shadow behavior lacks tests.

Reviewed range:

- Base: `6ae837c^` = `6d4adb1 docs(orders): O-8 simon-design-first audit + non-graph UX (O-6 integrated)`
- Head: `b24b970 feat(motion): O-9 Phase4 pixel-physical timing (#275)`
- Scope: 36 files, 656 insertions, 374 deletions
- Verification after current O-11 rebase: `npm run verify` PASS, 104 suites / 890 tests

## Findings

### P1 — Phase4 motion helper is not fully wired into direct transitions

`src/lib/motion/pixel-physical.ts` at `b24b970` exports `BUTTON_PRESS_MS = 60`, `SCREEN_TRANSITION_MS = 100`, `pixelMotionDuration()`, and `pixelStackTransition()`, but no steps/linear easing abstraction beyond stack options:

- `src/lib/motion/pixel-physical.ts:3-18`

The reviewed landed `NavGraph.tsx` still has direct interaction transitions outside the 80-120ms pixel-physical contract:

- `src/components/graph/NavGraph.tsx:620-621` pan settle = 350ms cubic.
- `src/components/graph/NavGraph.tsx:629-632` reset camera = 400ms cubic.
- `src/components/graph/NavGraph.tsx:677-680` programmatic focus = 450ms cubic.
- `src/components/graph/NavGraph.tsx:1098-1104` tier fades = 180ms quad.
- `src/components/graph/NavGraph.tsx:1226-1249` zoom/drilldown reveal = 200-280ms cubic/quad.
- `src/components/graph/NavGraph.tsx:2011-2015`, `2117-2121`, `2224-2228` sheet slides = 220ms cubic.

This is not a P0 crash, but it is a gate fail against O-9 Phase4's direct-screen-transition requirement. Local Codex tail `3c4f0d3 fix(motion): tighten nav graph transitions` already addresses the narrow NavGraph slice; Claude should integrate or supersede it before marking O-11 PASS.

### P1 — Android hard pixel shadow is likely a no-op

`pixelShadowStyle()` returns RN shadow props plus `elevation: 0`:

- `src/lib/theme/gameboy-tokens.ts:21-42`

On Android, `shadowColor`, `shadowOffset`, `shadowRadius`, and `shadowOpacity` do not render the same way they do on iOS/web, and `elevation: 0` means there is no platform shadow. So all `...pixelShadowStyle()` callers may lose the required 3px hard-offset pixel shadow on Android. This aligns with the AG QA item that specifically asks Android drop shadow rendering to be checked.

Suggested fix: render a real offset backing layer for pixel shadows, or add a platform-specific helper that uses an absolutely positioned square shadow View behind the component instead of relying on RN native shadow props.

### P1 — Motion/shadow test coverage is too thin

The #266-#275 range only adds/updates these tests:

- `src/lib/theme/__tests__/gameboy-tokens.test.ts`
- `src/theme/__tests__/theme.test.ts`

There is no landed test for:

- `pixelMotionDuration()` reduced-motion behavior.
- `pixelStackTransition()` reduced-motion output.
- NavGraph direct transition constants using the pixel contract.
- Android pixel shadow contract or a platform-safe fallback.

Given O-11 explicitly asks Codex to review `pixel-physical.ts` and animation regressions, this is a gate-level gap, not just polish.

## Non-Findings

- No new `as any` was introduced in the reviewed diff.
- `useNativeDriver` did not show a P0-level mismatch: transform/opacity paths use `true`; SVG prop animations keep `false` and are documented.
- Render-cost scan did not find a new obvious unbounded computation in render. The graph still does array/map work per render, but most structural transforms are under `useMemo` and existing LOD gates remain.
- `npm run verify` is green after rebasing Codex tail onto `origin/main@1819300`.

## Recommendation

Do not mark O-11 Codex gate PASS on PR #266-#275 alone. Treat as **FAIL / P1** until:

1. Motion helper is either wired into all direct NavGraph/sheet transitions or explicitly scoped with documented exceptions.
2. Android pixel shadow is implemented with a real platform-rendered offset layer.
3. Tests cover `pixel-physical.ts` and at least one NavGraph/sheet timing contract.

Codex local tail currently has relevant follow-up work:

- `3c4f0d3 fix(motion): tighten nav graph transitions`
- `b2b3107 fix(profile): make plan card primary CTA`

Codex did not push or open PR.
