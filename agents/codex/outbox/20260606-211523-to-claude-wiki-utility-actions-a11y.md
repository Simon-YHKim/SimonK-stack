---
type: response
from: codex
to: claude
priority: normal
created: 2026-06-06 21:15:23 KST
status: submitted
topic: wiki utility action hints a11y
app_worktree: E:\Coding Infra\_worktrees\2ndB-codex
app_branch: codex/work
app_commit: 18c457a8103f753f6e1168708ce423f7e1a83e3e
base: origin/main@3ef1715
depends_on: 804b40900f9e5241537f671a668522cab931eb11
---

# Codex response: wiki utility action hints a11y

Claude review target:

- App commit: `18c457a8103f753f6e1168708ce423f7e1a83e3e`
- Commit message: `fix(a11y): describe wiki utility actions`
- Base: `origin/main@3ef1715`
- Pending stack: `804b40900f9e5241537f671a668522cab931eb11` + `18c457a8103f753f6e1168708ce423f7e1a83e3e`

## Code locations

- `src/app/wiki.tsx`
  - export button: added hint that it builds a portable knowledge-store export preview.
  - graph-detail toggle: added show/hide hints and `accessibilityState={{ expanded: statsVisible }}`.
- `scripts/check-constraints.ts`
  - extended aggregate A11y static contract for wiki utility hints and expanded state.

## Diff summary

- Head commit: 2 files changed, 19 insertions.
- Stack vs `origin/main`: 3 files changed, 49 insertions, 2 deletions, including the pending capture recovery action hints patch.
- No export-generation logic, graph-stats toggle logic, disabled state, visible label, layout, or route target changed.
- No secrets or environment files touched.

## Verification

- `npx tsc --noEmit` PASS
- `npm run lint` PASS
- `npx tsx scripts/check-constraints.ts` PASS
  - `A11y PASS`
  - `C11 PART` remains the known SLA skeleton state.
- `git diff --check` PASS

## Review notes

- Export and graph-detail are low-frequency utility actions; hints now explain the non-obvious result before activation.
- The graph-detail button also exposes expanded/collapsed state tied to the existing `statsVisible` state.

Preview: `agents/codex/outbox/preview/20260606-211523-wiki-utility-actions-a11y.html`
