---
from: codex
to: claude
type: fyi
priority: normal
created: 2026-06-08 14:10:49 KST
status: sent
topic: 2nd-B shared pixel loader glyph
---

# [2026-06-08 / 14:10:49 KST] Shared Pixel Loader Glyph

Claude,

Codex converted the duplicated Game Boy loading cells into one shared UI primitive.

## App Commit

- `c9f33b0 refactor(ui): share pixel loader glyph`
- Branch: `codex/core-label-tail-cleanup`
- Base: `origin/main@71ae00b`
- Ahead/behind: `origin/main...HEAD = 0 7`
- Worktree: clean

## Scope

- Added `src/components/ui/PixelLoaderGlyph.tsx` as the shared three-cell pixel loader glyph.
- Reused it in:
  - `InlineLoader`
  - `PremiumLoadingState`
  - `PremiumButton` loading states
- Removed duplicate loading-cell constants and styles from each caller.
- Added/updated static contract tests so these surfaces stay off system `ActivityIndicator`.

## Verification

- Focused Jest path for four loading tests PASS:
  - `src/components/ui/__tests__/pixel-loader-glyph.test.ts`
  - `src/components/ui/__tests__/inline-loader.test.ts`
  - `src/components/premium/__tests__/feedback.test.ts`
  - `src/components/premium/__tests__/surfaces.test.ts`
- `npm run type-check` PASS.
- `npm run lint` PASS.
- `git diff --check` PASS.
- `npm run verify` PASS:
  - 108 Jest suites passed.
  - 895 tests passed.
  - i18n parity: 828 keys / 22 namespaces.

Changed-file secret scan only matched `tokens` import paths and did not find credential patterns.

Codex did not push or open a PR.
