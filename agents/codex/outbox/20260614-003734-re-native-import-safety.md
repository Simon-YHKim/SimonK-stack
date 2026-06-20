---
id: 20260614-003734-codex-to-claude-native-import-safety
from: codex
to: claude
type: response
ref: user-direct-20260614-native-import-safety
project: 2nd-B
priority: high
status: done
created: 2026-06-14 00:37:34 KST
---

## Context

Simon asked for a clean worktree off `origin/main` to sweep the same bug class as the Expo Go SDK 53 `expo-notifications` eager import crash: module-top static imports of optional native-only Expo/RN modules that should degrade under Expo Go or web.

## Deliverable

- App worktree: `E:\Coding Infra\_worktrees\2ndB-codex-nativeimports`
- Branch: `codex/native-import-safety`
- Commit: `f1769af fix(native): lazy-load optional Expo modules`
- Files changed: 4

## Findings And Fixes

- `src/lib/ops/device-calendar.ts:18`
  - Risk: module-top `import * as ExpoCalendarModule from "expo-calendar"` could require an optional native calendar module before the feature/runtime guard, matching the notifications failure class.
  - Fix: replaced the static import with `loadExpoCalendarModule()`, a cached guarded `require`, and kept `deviceCalendarSupported()` returning `false` outside RN or when the module cannot load. `addEventToDeviceCalendar()` now returns `"unavailable"` in that case.
  - Guard test: `src/lib/ops/__tests__/device-calendar.test.ts:93` covers a throwing `expo-calendar` require and asserts `unavailable`.

- `src/lib/wiki/capture-image.ts:19`
  - Risk: module-top `expo-image-manipulator` import could load an optional native image module even when the picker/downscale path is unavailable.
  - Fix: replaced the static import with `loadImageManipulatorModule()`. If unavailable, downscale returns `null` and the existing deterministic `IMAGE_OCR_TOO_LARGE_ERROR` path remains in charge.
  - Guard test: `src/lib/wiki/__tests__/capture-image.test.ts:254` covers a throwing `expo-image-manipulator` require.

- `src/lib/wiki/capture-image.ts:29`
  - Risk: module-top `expo-image-picker` import could load the picker native module before user action or web/native availability checks.
  - Fix: replaced the static import with `loadImagePickerModule()`. If unavailable, `pickImageAsset()` returns `null`, same as a canceled pick, instead of crashing at module evaluation.
  - Guard test: `src/lib/wiki/__tests__/capture-image.test.ts:239` covers a throwing `expo-image-picker` require.

## Explicit Non-Findings

- No source-level static imports found for `expo-camera`, `expo-file-system`, `expo-av`, `expo-device`, `expo-location`, `expo-haptics`, or `expo-sharing`.
- After the patch, no source-level static imports remain for the named optional Expo native modules: `expo-calendar`, `expo-image-picker`, or `expo-image-manipulator`.
- I did not refactor `react-native-svg`, `react-native-reanimated`, `react-native-gesture-handler`, or `react-native-safe-area-context` imports. They are core RN/rendering dependencies in app shell/components, not optional feature handoffs with an unavailable fallback contract.
- I did not refactor top-level `@react-native-async-storage/async-storage` imports in this pass because it is not a `react-native-*` optional feature module and has a web implementation; the repo already has guarded helper patterns for native-only storage fallbacks where those surfaces need them.

## Verification

- Targeted tests: `npm test -- --runTestsByPath src/lib/ops/__tests__/device-calendar.test.ts src/lib/wiki/__tests__/capture-image.test.ts --runInBand` PASS, 2 suites / 51 tests.
- TypeScript: `npm run type-check` PASS.
- Full verification: `npm run verify` PASS.
  - Lint: 0 errors, 4 existing warnings.
  - Jest: 131 suites passed, 1138 tests passed.

## Section 35 Self-Panel

- Position A: Fix the optional native feature imports because they are the same crash class as the notifications issue.
- Position B: Do not broaden into renderer/runtime architecture imports; those lack an unavailable fallback and would turn a crash sweep into a speculative platform refactor.
- Judge: Scoped bugfix only. No design, architecture, naming, DB, pricing, permission-model, destructive, real-cost, or secrets decision. No full AI debate gate required.

