## Codex O-9 Phase4 Pixel Physical

Branch: codex/o9-phase4-anim
Worktree: E:/Coding Infra/_worktrees/2ndB-o9-phase4-anim
Commit: ad07d00 feat(motion): O-9 Phase4 pixel-physical timing

### Done

- Added shared pixel physical motion timing helper.
- PremiumButton press now uses Animated.timing with 60ms linear timing.
- Reduced motion sets the new button press duration to 0ms.
- Root and auth expo-router Stack transitions now use 100ms animationDuration.
- Reduced motion sets Stack animation to none and duration to 0ms.
- Existing fade routes use the same reduced-motion aware timing helper.
- NavGraph.tsx was not modified.

### Verify

- npm run verify passed.
- Test suites: 102 passed.
- Tests: 887 passed.
