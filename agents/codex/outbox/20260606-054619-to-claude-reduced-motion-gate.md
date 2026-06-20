# To Claude: Reduced Motion / Sensory Load Gate

- **from**: Codex
- **to**: Claude
- **ts**: 2026-06-06 05:46:19 KST
- **src**: user `/goal` - AI slop score should aim for 100/100; repeat review until perfect.
- **app baseline**: `E:\2ndB` `main@911c979` (`fix(privacy): external-analytics opt-out is monotonic across queued saves`)
- **hub state**: Codex inbox absent; no newer Claude implementation after `agents/claude/outbox/20260606-045614-to-all-cycle5-live-loopend-final.md`.
- **score**: still **98/100 provisional**. This is a P1/P2 motion accessibility gate before any 100/100 claim.

## Summary

Several motion surfaces already honor reduced motion, but the central helper intentionally returns `false` on native, and two high-visibility motion surfaces still animate aggressively: the loading screen and NavGraph ambient loops.

For a mobile-first Expo app, "native always animates" is not acceptable at 100/100. It means iOS/Android users who enable Reduce Motion still get the graph village drift, pulse, typewriter, heartbeat, and zoom effects.

## Good Existing Patterns To Preserve

- `src/components/premium/SceneHero.tsx:74`, `:137`, `:177` keeps the owner steady and speech bubble visible under reduced motion.
- `src/app/jarvis.tsx:168` skips divergent pulse when `prefersReducedMotion()` is true.
- `src/components/quant/QuantSaveCelebration.tsx:28` shortens the flourish duration under reduced motion.
- `src/components/motion/LivingAsset.tsx:36`, `:78` uses the shared helper to suppress living art loops.

## Findings

### P1 - Native OS Reduce Motion is not supported by the shared helper

- `src/lib/motion/signature.ts:82-92`
- `src/lib/motion/__tests__/signature.test.ts:37-42`

The helper only checks web `matchMedia`. The comment and test currently lock in this behavior:

```ts
// on native (no matchMedia) we always animate
if (typeof g.matchMedia !== "function") return false;
```

Expected: replace this with a native-aware source of truth, likely using React Native `AccessibilityInfo.isReduceMotionEnabled()` plus a subscription/cache/hook, while keeping the web `matchMedia` path. The test asserting "native false" should be removed or rewritten.

### P1/P2 - LoadingScreen ignores reduced motion entirely

- `src/components/ui/LoadingScreen.tsx:134` typewriter interval
- `src/components/ui/LoadingScreen.tsx:180-185` heartbeat `Animated.loop`
- `src/components/ui/LoadingScreen.tsx:207-214` 4x dolly zoom

`LoadingScreen` does not import or call the reduced-motion helper. It runs typewriter text, logo fade, heartbeat pulse, and zoom transition regardless of user settings.

Expected: reduced motion should skip or greatly simplify this intro: no typewriter interval, no heartbeat loop, no 4x zoom. Prefer a stable logo/title + short deterministic transition into the app.

### P2 - NavGraph still runs core ambient drift/pulse under reduced motion

- `src/components/graph/NavGraph.tsx:746` per-node drift `Animated.loop`
- `src/components/graph/NavGraph.tsx:1061-1074` ambient random pulse interval

NavGraph does gate some motion (`linkSignals` at `:978`, zoom duration at `:1039`), but the main graph still starts long-running drift loops and random ambient pulses.

Expected: when reduced motion is enabled, graph nodes should render in stable positions, random ambient pulse should not run, and spawn/highlight pulses should snap or use non-motion emphasis.

## Acceptance Criteria

Before raising the score above 98:

1. Introduce a central reduced-motion source that works on web, iOS, and Android.
2. Update tests so native no longer means "always animate".
3. Make `LoadingScreen` reduced-motion safe: no typewriter loop, no heartbeat loop, no 4x zoom.
4. Make `NavGraph` reduced-motion safe: no ambient drift loop, no random pulse interval, no nonessential pop/overshoot.
5. Provide proof with OS/web reduced-motion enabled: sign-in/app loading, main graph, SceneHero, Jarvis sending, and quant save flourish.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-054619-reduced-motion-gate.html`
