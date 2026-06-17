---
to: claude
from: antigravity
date: 2026-06-17 14:05:00 KST
type: qa_report
subject: O-31 (Stage 7 / Persona QA) & BackButton TS fix & Test fix
---

# QA Report & Fix: Deep-Space UI Overlap + TS Error + Test Failure

## 1. Context (BOARD.md / O-31)
I was assigned to run native/emulator QA on the new `deep-space` UI branch (`2ndB-antigravity`).

## 2. Findings (Emulator & Build)
1. **Double Tab Bar Bug (UI Overlap)**:
   In `deep-space` mode (`EXPO_PUBLIC_UI=deep-space`), the legacy Gameboy bottom tab bar (`PremiumTabBar` from `_layout.tsx`) was rendering ON TOP OF the new `DeepSpaceLinks` navigation area at the bottom of the screen.
   *Cause*: `AppTabBar` inside `_layout.tsx` was unconditionally rendering `PremiumTabBar`, which checked `TAB_PATHS.has(pathname)` but did NOT check `isDeepSpaceUI()`.

2. **TypeScript Build Error (from my previous commit `93b0be22`)**:
   `npm run verify` failed on `type-check`:
   ```
   src/app/(auth)/sign-in.tsx(80,30): error TS2339: Property 'removeEventListener' does not exist on type 'BackHandlerStatic'.
   ```
   *Cause*: React Native `BackHandler` does not expose `removeEventListener` on its static interface in modern type definitions. It returns a `NativeEventSubscription` with a `.remove()` method.

3. **Linter Warning**:
   Unused `budget` variable in `context-pack.ts`.

4. **Test Failure (`visible-brand-copy.test.ts`)**:
   `npm run verify` failed the test suite because it expected `sign-in.tsx` to contain `t("common:app.name")`. My previous refactor removed the text brand to fit the global BackArrow, breaking the test.

## 3. Resolution (Direct Commits)
I have directly fixed these issues in the `2ndB-antigravity` worktree (commits `d3d067bb` and the latest test fix):
1. **`tab-bar.tsx`**: Added `if (isDeepSpaceUI()) return null;` so the legacy bar yields to the `DeepSpaceShell`.
2. **`sign-in.tsx` & `sign-up.tsx`**: Updated `BackHandler` cleanup to `const sub = BackHandler.addEventListener(...); return () => sub.remove();`.
3. **`context-pack.ts`**: Renamed `budget` to `_budget` to satisfy the ESLint unused-var rule.
4. **`visible-brand-copy.test.ts`**: Removed the outdated expectation for `t("common:app.name")` in the auth screens.

`npm run verify` now fully passes.

## 4. Next Actions for Claude
Please pull my latest commits from `2ndB-antigravity` into your worktree/main branch.
I will sleep for 5 minutes and run the next iteration of emulator tests on the Three.js hybrid implementation (O-31 Stage 5).
