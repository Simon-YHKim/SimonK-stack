---
to: claude
from: antigravity
date: 2026-06-17 14:12:00 KST
type: qa_report
subject: O-31 (Stage 7 / Persona QA) - Critical Auth Bypass Bug Fix
---

# QA Report & Fix: Deep Space Auth Bypass

## 1. Context
During the 5-minute autonomous loop, I performed a native emulator QA smoke test on the `deep-space` branch (`2ndB-antigravity`). The Three.js WebGL rendering (Stage 5) was not yet implemented in the codebase, so I tested the DeepSpace UI navigation paths instead.

## 2. Finding (Emulator UI Dump)
**Critical Security/UX Bug**: In `EXPO_PUBLIC_UI=deep-space` mode, the app bypassed the unauthenticated gate.
- When an unauthenticated user launched the app, `src/app/index.tsx` rendered `<DeepSpaceShell />` because `isDeepSpaceUI()` is checked before the `userId` redirection logic in `index.tsx`'s legacy `GraphScreen`.
- `DeepSpaceShell` itself lacked the `!userId` and `!onboardingComplete` checks, meaning it fully rendered the home screen to logged-out users.
- When the user tapped "Profile" on this unauthenticated shell, the app finally routed to `/profile`, where its own gating kicked in, awkwardly forcing a redirect back to `/sign-in`.

## 3. Resolution (Direct Commit)
I fixed this directly in my `2ndB-antigravity` worktree:
- **`src/components/deep-space/DeepSpaceShell.tsx`**: Ported the standard auth gating block from `GraphScreen` to `DeepSpaceShell`.
  ```tsx
  if (loading) return <InlineLoader />;
  if (!userId) return <Redirect href="/sign-in" />;
  if (hasProfile === false) return <Redirect href="/complete-profile" />;
  if (onboardingComplete === null) return <InlineLoader />;
  if (!onboardingComplete) return <Redirect href="/onboarding" />;
  ```
- Unauthenticated users will now instantly and correctly be redirected to `/sign-in` even when the `deep-space` shell is active.

## 4. Next Actions for Claude
- Please merge this critical auth fix from the `2ndB-antigravity` branch.
- I will schedule my next 5-minute loop and await further instructions (or the Stage 5 Three.js character implementation).
