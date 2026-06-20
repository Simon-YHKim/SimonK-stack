# O-12 Phase D PowerOnOverlay

- Branch: codex/o12-poweron
- Worktree: E:/Coding Infra/_worktrees/2ndB-o12-poweron
- Commit: e46b6bb feat(ui): O-12 power-on scanline overlay
- Verify: npm run verify pass

## Done

- Added src/components/premium/PowerOnOverlay.tsx.
- First graph mount shows a full black overlay with a gameboy.accent scanline sweeping top to bottom over 180ms, then fading out.
- Reduced motion skips the sweep and hides the overlay immediately.
- One-time guard uses sessionStorage on web and a module flag for native or remount fallback.
- Mounted PowerOnOverlay above the graph screen layer in src/app/index.tsx.
- NavGraph.tsx was not modified.

## Tests

- Added src/components/premium/__tests__/power-on-overlay.test.ts for reduced-motion and one-time start-state branches.
- npm test -- --ci src/components/premium/__tests__/power-on-overlay.test.ts pass.
- npm run verify pass.
