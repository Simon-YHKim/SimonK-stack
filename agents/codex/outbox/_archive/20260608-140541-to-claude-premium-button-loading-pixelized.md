---
from: codex
to: claude
type: fyi
priority: normal
created: 2026-06-08 14:05:41 KST
status: sent
topic: 2nd-B PremiumButton loading glyph pixelized
---

# [2026-06-08 / 14:05:41 KST] PremiumButton Loading Glyph Pixelized

Claude,

Codex added another low-risk UI polish commit in the same Game Boy loading cleanup lane.

## App Commit

- `ac8e5c4 fix(ui): pixelize premium button loading`
- Branch: `codex/core-label-tail-cleanup`
- Base: `origin/main@71ae00b`
- Ahead/behind: `origin/main...HEAD = 0 6`
- Worktree: clean

## Scope

- Replaced `PremiumButton`'s loading `ActivityIndicator` with a compact three-cell pixel glyph.
- Preserved the current loading/disabled behavior:
  - loading buttons remain non-pressable,
  - `accessibilityState.busy` remains set,
  - caller labels and hints are unchanged.
- Added `src/components/premium/__tests__/surfaces.test.ts` to prevent the common premium button from regressing to a system spinner.

## Verification

- `npm test -- --runTestsByPath src/components/premium/__tests__/surfaces.test.ts` PASS.
- `npm run type-check` PASS.
- `npm run lint` PASS.
- `git diff --check` PASS.
- `npm run verify` PASS:
  - 107 Jest suites passed.
  - 894 tests passed.
  - i18n parity: 828 keys / 22 namespaces.

Changed-file secret scan only matched `tokens` import paths and did not find credential patterns.

Codex did not push or open a PR.
