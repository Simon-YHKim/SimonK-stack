---
to: claude
from: codex
type: handoff
priority: normal
status: sent
created: 2026-06-08 13:00:36 KST
topic: O-11 Android pixel shadow static fix
---

# O-11 Android pixel shadow contract patched

[2026-06-08 / 13:00:36 KST]

Claude, Codex took the narrow O-11 P1 Android shadow finding that was safe to fix in the local tail.

## App commit

- `52ba35c fix(theme): add native pixel box shadow`
- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/core-label-tail-cleanup`
- Branch status after commit: clean
- Divergence: `origin/main...HEAD = 0 6`
- Codex did not push or open PR.

## Scope

- `src/lib/theme/gameboy-tokens.ts`
  - Added `pixelShadowBoxShadow()`.
  - `pixelShadowStyle()` now includes `boxShadow` while keeping the existing RN shadow props.
  - `elevation` remains `0` to preserve the O-9 hard pixel, no-blur/no-soft-shadow rule.
- `src/lib/theme/__tests__/gameboy-tokens.test.ts`
  - Locks default and custom `boxShadow` strings.
  - Locks the contract that `boxShadow` must stay present even when elevation remains zero.

## Verification

- `npm test -- --runTestsByPath src/lib/theme/__tests__/gameboy-tokens.test.ts` PASS.
- `npm run type-check` PASS.
- `git diff --check` PASS with CRLF warnings only.
- `npm run lint` PASS.
- `npm run verify` PASS.
  - 104 Jest suites PASS.
  - 891 tests PASS.
  - i18n 828 keys / 22 namespaces PASS.
- Changed-file secret scan found only `tokens` filename/import false positives, no credential patterns.

## Residual risk

This removes the static no-op risk by adding an explicit native/CSS hard pixel shadow contract. I still recommend AG or Claude attach one Android render screenshot before integration signoff, because platform rendering support can differ by runtime.

