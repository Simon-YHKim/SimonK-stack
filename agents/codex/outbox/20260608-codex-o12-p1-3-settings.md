# Codex O-12 P1-3 Settings

- Branch: `codex/o12-p1-3-settings`
- Worktree: `E:/Coding Infra/_worktrees/2ndB-o12-p1-3-settings`
- Commit: `2d59338 refactor(settings): O-12 P1-3 collapse settings wall to progressive disclosure`
- Scope: `src/app/settings.tsx`

## Changes

- Added a local `DisclosureSection` wrapper with `accessibilityState={{ expanded }}`.
- Kept the primary settings content as the existing 7-row nav hub.
- Put theme and graph crew controls behind separate default-closed collapsible sections.
- Put all destructive delete controls and the full-wipe input behind a default-closed warning-colored `Data management` disclosure.
- Preserved existing delete handlers, confirmation flow, copy strings, and `/data` plus `/records` nav routes.

## Verification

- `npm run verify` passed.
- Note: lint still reports the pre-existing warning at `src/components/graph/NavGraph.tsx:723` for an unused eslint-disable directive. There are no lint errors.
