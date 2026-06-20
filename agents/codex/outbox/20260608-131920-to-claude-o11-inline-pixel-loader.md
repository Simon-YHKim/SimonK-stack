---
to: claude
from: codex
type: handoff
priority: normal
status: sent
created: 2026-06-08 13:19:20 KST
topic: O-11 P2 inline pixel loader
---

# O-11 P2 inline pixel loader patch

[2026-06-08 / 13:19:20 KST]

Claude, Codex closed another O-11 P2 autonomous item: pixel loader.

## App commit

- `a9576a1 fix(ui): replace inline spinner with pixel loader`
- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/core-label-tail-cleanup`
- Base: `origin/main@03078f8`
- Branch status after commit: clean
- Divergence: `origin/main...HEAD = 0 9`
- Codex did not push or open PR.

## Scope

- `src/components/ui/InlineLoader.tsx`
  - Removed the system `ActivityIndicator`.
  - Added a framed 3-cell pixel indicator using `gameboy` geometry and `pixelShadowStyle()`.
  - Root remains the accessible progressbar; the decorative pixel cells are hidden from accessibility traversal.
- `src/components/ui/__tests__/inline-loader.test.ts`
  - Locks that `InlineLoader` no longer uses `ActivityIndicator`.
  - Locks the `PIXEL_CELLS`, `pixelFrame`, and active-cell contract.

## Verification

- `npm test -- --runTestsByPath src/components/ui/__tests__/inline-loader.test.ts` PASS.
- `npm run type-check` PASS.
- `npm run lint` PASS.
- `git diff --check` PASS with CRLF warnings only.
- `npm run verify` PASS.
  - 105 Jest suites PASS.
  - 892 tests PASS.
  - i18n 828 keys / 22 namespaces PASS.
- Changed-file secret scan found only `tokens` import false positives, no credential patterns.

## Notes

This intentionally avoids the two Simon-decision lanes from the O-11 report: font-size strategy and Game Boy intensity policy. It only removes a system-loader look from the already branded route/auth loader.

