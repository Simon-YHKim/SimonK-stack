---
to: claude
type: fyi
subject: "Graph Animation Crash Resolved + E16/E20"
timestamp: "2026-06-07 / 19:00:00 KST"
---

## Overview
The user experienced a reproducible crash when closing the IslandSheet (Modal) in `NavGraph.tsx`.
The error was: `"Attempting to run JS driven animation on animated node that has been moved to 'native' earlier by starting an animation with useNativeDriver: true"`.

## Root Cause
- The `<AnimatedLine>` component in `NavGraph.tsx` was receiving both JS-driven and Native-driven properties simultaneously.
- `x1`, `y1`, `x2`, `y2` were driven by `driftValues` (JS thread).
- `strokeOpacity` was driven by `connGlow` (Native thread).
- React Native's `Animated` engine marked the SVG element as Native due to `connGlow`, but when `driftValues` restarted its ambient loop, it attempted to attach a JS listener to the now-native node, causing a hard crash.

## Fix
- Changed `useConnectionGlow` in `useSignatureMotion.ts` to use `useNativeDriver: false`. 
- This ensures all animated properties on `<AnimatedLine>` reside in the JS thread, resolving the conflict.
- The user has tested and confirmed the fix.

## E16 / E20 Verification
- **E16 (Data Hints)**: Verified that `autoComplete="email"`, `textContentType="emailAddress"`, and `autoComplete="new-password"` are already correctly implemented in both `sign-in.tsx` and `sign-up.tsx`.
- **E20 (RTL Layout)**: Replaced absolute LTR margins (`marginLeft`/`marginRight`) with RTL-compliant (`marginStart`/`marginEnd`) and paddings (`paddingStart`/`paddingEnd`) in 6 UI components across the app to fully support E20 RTL mirroring. Absolute position attributes (`left`/`right`) were intentionally preserved for graph components and symmetric visual elements where RTL flip is not desired.

## Next Steps
Standing by for further instructions or specific QA tasks for Graph Performance (§19).
