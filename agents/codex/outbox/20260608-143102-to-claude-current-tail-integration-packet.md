---
from: codex
to: claude
type: handoff
priority: normal
created: 2026-06-08 14:31:08 KST
status: sent
project: 2nd-B
branch: codex/core-label-tail-cleanup
base: origin/main@71ae00b
---

# Current Codex Tail Integration Packet

[2026-06-08 / 14:31:08 KST]

Claude, here is the current integration packet for the Codex app tail. Codex is at the eight-commit throttle limit, so I am not starting new app code until this tail is integrated, compacted, or otherwise reduced.

## State

- CONTROL: `running`.
- App worktree: `E:\Coding Infra\_worktrees\2ndB-codex`.
- Branch: `codex/core-label-tail-cleanup`.
- Base: `origin/main@71ae00b`.
- Worktree: clean.
- Divergence: `origin/main...HEAD = 0 8`.
- Cumulative scope: 19 files, 305 insertions / 82 deletions.
- `git diff --check origin/main...HEAD`: PASS.
- Fresh `npm run verify`: PASS, 109 Jest suites / 896 tests, i18n 828 keys / 22 namespaces.

## Tail Order

1. `b045ce8 fix(ui): consolidate low-risk polish`
   - Files: `src/app/capture.tsx`, `src/app/index.tsx`, `src/app/onboarding.tsx`, `src/components/ui/BackArrow.tsx`.
   - Risk: medium, because it touches route-level copy/action polish.

2. `d1daa86 fix(graph): consolidate pixel motion and drilldown a11y`
   - Files: `src/components/graph/NavGraph.tsx`, `src/lib/motion/pixel-physical.ts`, `src/lib/motion/__tests__/pixel-physical.test.ts`.
   - Risk: medium-high if upstream graph work lands first; otherwise isolated.

3. `20eba54 fix(theme): consolidate gameboy motion contracts`
   - Files: `src/components/premium/feedback.tsx`, `src/lib/theme/gameboy-tokens.ts`, `src/lib/theme/__tests__/gameboy-tokens.test.ts`.
   - Risk: medium, overlaps premium feedback and token contracts.

4. `5bbf057 fix(ui): consolidate pixel loader docs`
   - Files: `DESIGN.md`, `src/components/ui/InlineLoader.tsx`, `src/components/ui/__tests__/inline-loader.test.ts`.
   - Risk: low-medium, doc plus shared loader.

5. `9fc68d0 fix(ui): pixelize premium loading state`
   - Files: `src/components/premium/feedback.tsx`, `src/components/premium/__tests__/feedback.test.ts`.
   - Risk: medium, later refactored by shared glyph commit.

6. `ac8e5c4 fix(ui): pixelize premium button loading`
   - Files: `src/components/premium/surfaces.tsx`, `src/components/premium/__tests__/surfaces.test.ts`.
   - Risk: medium, later refactored by shared glyph commit.

7. `c9f33b0 refactor(ui): share pixel loader glyph`
   - Files: `src/components/ui/PixelLoaderGlyph.tsx`, `InlineLoader`, premium feedback/surfaces tests and callers.
   - Risk: medium, but it removes duplicate loader code and should be integrated with the preceding loader commits as a unit.

8. `3a8487d fix(ui): pixelize capture journal loading`
   - Files: `src/app/capture.tsx`, `src/lib/__tests__/capture-loader-contract.test.ts`.
   - Risk: low-medium, route file already touched by the first polish commit.

## Recommended Grouping

- Group A, low-risk route polish: `b045ce8` and `3a8487d`.
- Group B, graph motion/a11y: `d1daa86`.
- Group C, token and premium sheet contract: `20eba54`.
- Group D, loader cleanup: `5bbf057`, `9fc68d0`, `ac8e5c4`, `c9f33b0`.

If you cherry-pick rather than merge the whole branch, Group D should stay together because the final shared `PixelLoaderGlyph` commit intentionally deduplicates the intermediate loader work.

## Conflict Watch

- `src/components/graph/NavGraph.tsx`: likely conflict point if any AG/Claude graph QA patch lands.
- `src/components/premium/feedback.tsx`: touched by sheet motion and premium loading glyph.
- `src/app/capture.tsx`: touched by low-risk polish and capture journal loader.
- `DESIGN.md`: doc-only but frequently edited by design-phase updates.

## Verification Notes

The fresh verification run passed end-to-end:

- `npm run lint`
- `npm run type-check`
- `npm run check:i18n`
- `npm run check:lexicon`
- `npm run check:llm-boundary`
- `npm run check:constraints`
- `npm run check:emdash`
- `npm test -- --ci`

Known console noise is existing mocked failure-path coverage: storage fallback, safety classifier fallback, ai audit log mock failure, consent retry failure, privacy prefs fallback.

Codex did not push, open a PR, or edit Claude-owned files.
