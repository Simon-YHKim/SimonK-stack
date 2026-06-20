[2026-06-08 / 11:49:35 KST]

## DONE

O-10 mechanical decisions 1, 2, 3, 5 applied on new worktree branch `codex/o10-mechanical-decisions`.

Worktree:
`E:/Coding Infra/_worktrees/2ndB-o10-mechanical-decisions`

Commits:
- `1d6f7a0` fix(color): danger buttons solid zoneRed
- `32dc4de` fix(type): snap off-scale sizes to token scale
- `534ce5e` fix(icon): glyph X/check to svg path

Verification:
- `npm run verify` PASS
- `NavGraph.tsx` unchanged
- Commit messages have no body, so no double quote or em dash in commit bodies

Notes:
- Danger buttons now use solid `semantic.zoneRed` with `gameboy.ink` text.
- Type tokens now match 12, 14, 16, 20, 25, 31, 39, and 11 or 13 font sizes outside `NavGraph.tsx` were snapped to token sizes.
- Capture check and tag remove glyphs now render with `react-native-svg` Path. The duplicate empty-graph top-right close button was removed, leaving the skip button as the dismiss action.
