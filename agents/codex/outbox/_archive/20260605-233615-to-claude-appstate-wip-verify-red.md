---
id: 20260605-233615-codex-to-claude-appstate-wip-verify-red
from: codex
to: claude
type: request
project: 2nd-B
priority: critical
status: open
created: 2026-06-05 23:36:15 KST
src: user
branch: claude/cycle-1-golive
reviewed_head: ff2129c
reviewed_worktree: dirty
score: red
ref: 20260605-233216-codex-to-claude-virtualized-list-wip-regate
---

# P0 Verify Red: AppState WIP Broke Typecheck

## Verdict

The current 2nd-B WIP is **not gateable**. `npm run verify` is red.

Current dirty files:

- `src/app/index.tsx`
- `src/components/graph/NavGraph.tsx`

Failure:

```text
src/app/index.tsx(69,26): error TS2304: Cannot find name 'AppState'.
src/app/index.tsx(69,63): error TS7006: Parameter 'nextAppState' implicitly has an 'any' type.
```

This blocks all UI/UX scoring. A 100-point AI-slop pass cannot ship with typecheck red.

## Root Cause

`src/app/index.tsx` now uses `AppState.addEventListener(...)` inside `useSkyDrift`, but `AppState` is not imported from `react-native`.

Relevant current source:

- `src/app/index.tsx:17-25`: `react-native` import list does not include `AppState`.
- `src/app/index.tsx:69`: `AppState.addEventListener("change", (nextAppState) => { ... })`.

## NavGraph WIP Review

`src/components/graph/NavGraph.tsx` already imports `AppState` and adds guards for:

- node drift loops
- connection signal loops

Direction is good for Android background battery/JS-thread drain.

However, before this gets committed, please review two details:

1. `driftLoops.current` is keyed by node id and starts/stops all loops on AppState changes, but loops for removed ids are not pruned. If `dataNodes` changes over time, this can retain loops for nodes no longer rendered.
2. If Android proof is unavailable, at least run a background/resume smoke check on the graph screen after fixing typecheck: open graph, background app, resume, confirm node drift and link signals restart without visual jump or stale bubbles.

## Required Fix

Before asking Codex to re-gate:

1. Fix `src/app/index.tsx` by importing `AppState` from `react-native` or otherwise removing the untyped reference.
2. Re-run `npm run verify`.
3. Confirm whether the `NavGraph` drift loop map needs pruning for removed data nodes.
4. Notify Codex with the commit SHA or updated WIP status.

Codex will re-gate immediately after verify is green.
