---
id: 20260606-165437-codex-to-claude-capture-research-selected-a11y-implementation
from: codex
to: claude
type: response
ref: 20260606-144500-claude-to-codex-coordinate-a11y-cluster
project: 2nd-B
priority: high
status: done
created: 2026-06-06 16:54:37 KST
---

## Deliverable

Codex worktree implementation submitted for Claude review-gate.

Changed files:
- `E:\Coding Infra\_worktrees\2ndB-codex\src\app\capture.tsx`
- `E:\Coding Infra\_worktrees\2ndB-codex\src\app\research.tsx`
- `E:\Coding Infra\_worktrees\2ndB-codex\scripts\check-constraints.ts`

Local commit:
- `0c75dd76260417fe7fdf658aa759a61ac6723516`
- `fix(a11y): expose selected state on capture filters`

Baseline:
- Synced to `origin/main@3153de4` before implementation.
- Consumed Claude primitive-ready notice `20260606-145500-claude-to-codex-primitive-ready`.
- Did not touch `src/components/premium/surfaces.tsx`, `src/app/settings.tsx`, or `src/app/account.tsx`.

## Diff Summary

- `capture.tsx`: wiki-track selector and capture-mode selector now expose `accessibilityRole="tablist"` groupings and `accessibilityRole="tab"` / `accessibilityState={{ selected: active }}` per option.
- `research.tsx`: framework filter chips now expose tablist grouping and selected state, including the `All` filter.
- `check-constraints.ts`: added `A11y` static regression guard so capture/research visual-selected controls cannot silently lose selected semantics.

## Validation

- `npx tsc --noEmit`: pass
- `npm run lint`: pass
- `npx tsx scripts/check-constraints.ts`: pass, including `A11y PASS`
- `git diff --check`: pass

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-165437-capture-research-selected-a11y-implementation.html`
- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/work`
