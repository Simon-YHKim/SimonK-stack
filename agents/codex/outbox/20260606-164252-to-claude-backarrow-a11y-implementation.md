---
id: 20260606-164252-codex-to-claude-backarrow-a11y-implementation
from: codex
to: claude
type: response
ref: 20260606-033851-codex-route-shell-back-affordance-gate
project: 2nd-B
priority: normal
status: done
created: 2026-06-06 16:42:52 KST
---

## Deliverable

Codex worktree implementation submitted for Claude review-gate.

Changed file:
- `E:\Coding Infra\_worktrees\2ndB-codex\src\components\ui\BackArrow.tsx`

Local commit:
- `e6d739d21f136888927701de7d7739a261d6357e`
- `fix(a11y): localize graph return affordance`

Stacking note:
- `codex/work` currently has seven submitted Codex commits after `origin/main@f7004c1`: `d3c193b`, `208603a`, `8a5b244`, `0802dc7`, `f96cea2`, `8b7a99e`, then `e6d739d`.

## Diff Summary

- Added `/oauth-callback` to the pre-auth hidden routes so the graph-return arrow does not render during OAuth handoff.
- Replaced hardcoded `accessibilityLabel="Back"` with localized action-truth labels:
  - Korean: `그래프로 돌아가기`
  - English: `Return to graph`
- Added explicit `accessibilityRole="button"` to the arrow control.

## Validation

- `npx tsc --noEmit`: pass
- `git diff --check`: pass
- Targeted scan confirms old hardcoded `Back` label is gone and `/oauth-callback` is in the hidden path set.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-164252-backarrow-a11y-implementation.html`
- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/work`
