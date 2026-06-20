---
to: claude
from: codex
type: handoff
priority: normal
status: sent
created: 2026-06-08 13:06:38 KST
topic: O-11 Premium bottom sheet pixel motion
---

# O-11 premium bottom sheet motion patch

[2026-06-08 / 13:06:38 KST]

Claude, Codex continued the O-11/O-10 Phase4 cleanup with a small low-overlap motion slice.

## App commit

- `bba0a8e fix(motion): pixelate premium sheet transition`
- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/core-label-tail-cleanup`
- Branch status after commit: clean
- Divergence: `origin/main...HEAD = 0 7`
- Codex did not push or open PR.

## Scope

- `src/lib/motion/pixel-physical.ts`
  - Added `SCREEN_TRANSITION_DISTANCE_PX = 8` for the O-10 8px block-slide contract.
- `src/lib/motion/__tests__/pixel-physical.test.ts`
  - Locks the 8px distance alongside 60/80/100ms timing tokens.
- `src/components/premium/feedback.tsx`
  - `PremiumBottomSheet` now opens with 100ms linear pixel timing instead of 240ms cubic.
  - Translate distance is 8px instead of 60px.
  - Reduced-motion behavior still snaps to the final state.

## Verification

- `npm test -- --runTestsByPath src/lib/motion/__tests__/pixel-physical.test.ts` PASS.
- `npm run type-check` PASS.
- `npm run lint` PASS.
- `git diff --check` PASS with CRLF warnings only.
- `npm run verify` PASS.
  - 104 Jest suites PASS.
  - 891 tests PASS.
  - i18n 828 keys / 22 namespaces PASS.
- Changed-file secret scan found only `tokens` filename/import false positives, no credential patterns.

## Notes

Hub already had staged Grok-owned files when I reported this, so the Codex hub report should be committed with path-limited commit semantics to avoid mixing agent outputs.

