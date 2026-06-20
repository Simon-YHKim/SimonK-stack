# Codex O-9 Phase 1 Handoff

Date: 2026-06-08 KST
Branch: `codex/o9-phase1-tokens-fonts`
Worktree: `E:\Coding Infra\_worktrees\2ndB-o9-phase1-tokens-fonts`
Commit: `507f0ae feat(theme): add O-9 gameboy tokens and fonts`

## Summary

- Added `src/lib/theme/gameboy-tokens.ts` with the O-9 Deep Space Game Boy token contract:
  - `borderWidth: 2`
  - `radius: 0`
  - `pixelShadow: 3,3,0`
  - `scanlineOpacity: 0.04`
  - `grid: 8`
  - palette mapped to existing O-8 `cosmic` values.
- Added `pixelShadowStyle()` helper for React Native hard-offset shadows:
  - `shadowOffset: { width: 3, height: 3 }`
  - `shadowRadius: 0`
  - `shadowOpacity: 1`
  - `elevation: 0`
- Added unit tests for geometry tokens, palette mapping, default shadow style, and custom shadow color.
- Added font aliases in `src/theme/typography.ts`:
  - `fontFamilies.pixelKo`
  - `fontFamilies.pixelEn`
  - existing `fontFamilies.readable` remains unchanged for body, journal, chat, and explanation text.
- Added font assets to the existing `_layout.tsx` font loading path through `fontAssets`.
- Added `DESIGN.md` section: `Game Boy (Deep Space Game Boy)`.
- Did not apply fonts or tokens to components/screens.
- Did not touch NavGraph.

## Font Package Note

- `@expo-google-fonts/press-start-2p` installed successfully.
- `@expo-google-fonts/galmuri11` returned npm 404 on 2026-06-08, so Galmuri11 is bundled from the official `galmuri` npm package instead:
  - `galmuri/dist/Galmuri11.ttf`
- Jest uses a direct TTF require path for Press Start 2P to avoid parsing the package ESM entrypoint in the current Jest config.

## Verify

`npm run verify` passed.

- ESLint passed.
- TypeScript passed.
- i18n, lexicon, LLM boundary, constraints, and emdash checks passed.
- Jest passed: 102 suites, 887 tests.

## EAS Font Guidance

- Commit and keep both `package.json` and `package-lock.json`; EAS needs the new dependencies during install.
- A fresh EAS build will bundle the two TTF assets through the existing `expo-font` and `useFonts(fontAssets)` path.
- No native config plugin change is required for this Phase 1 change.
- If testing locally after dependency changes, clear Metro cache if an old bundle still shows missing font behavior.
