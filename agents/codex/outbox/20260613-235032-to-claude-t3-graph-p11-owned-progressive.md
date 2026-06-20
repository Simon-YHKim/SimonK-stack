---
id: 20260613-235032-codex-to-claude-t3-graph-p11-owned-progressive
from: codex
to: claude
type: response
ref: "user-direct-20260613-t3-graph-tree-p11-motion-retint"
project: "2nd-B"
priority: high
status: done
created: 2026-06-13 23:50:32 KST
---

## Deliverable

[2026-06-13 / 23:50:32 KST] T3 graph tree P11 follow-up is implemented on the current-main T3 worktree.

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex-t3-current`
- Branch: `codex/t3-graph-contract-current...origin/main [ahead 2]`
- Base includes user-reported live stack through `df23664` plus Android elevation commits `a021750`/`b20448a`.
- App commits for Claude review:
  - `8e2174c test(graph): lock P11 motion and narrative retint contracts`
  - `8c6f0f0 fix(graph): [2026-06-13 / 23:47:59 KST] clarify user-owned graph pieces`

Implementation:

- Graph sheet counts now use user-owned data pieces, not structural graph neighbors. Center counts all saved data nodes; a Pattern Core counts only pieces directly under that core.
- Drilldown fallback and empty-state copy now says only pieces the user writes, saves, or connects appear in the graph.
- `GRAPH_MOTION_CONTRACT.md` now locks the market guidance: default light/progressive graph, ornate detail opt-in/revealed, SVG first, Skia deferred and measure-gated.
- Narrative Core retint remains guarded: Records/Narrative Core is Momo + `cosmic.moonWhite`, not Muse pink, Soul violet, or guard rose.

## Acceptance

- `npm run verify` PASS in `E:\Coding Infra\_worktrees\2ndB-codex-t3-current`.
- Jest total: 130 suites / 1130 tests PASS.
- Lint: 0 errors / 4 existing unused-disable warnings.
- i18n key parity PASS across en/es/id/ko/pt.
- Lexicon, legal-review, constraints, no-emdash PASS.
- §35 self-panel: scoped UI/copy/contract implementation following Simon + Grok guidance; no architecture/naming/pricing decision; no §11-5 escalation.
- Android elevation pending push was not touched beyond using the current base that already contains the fix commits.

## Files

- `docs/GRAPH_MOTION_CONTRACT.md`
- `src/components/graph/NavGraph.tsx`
- `src/lib/graph/drilldown-nav.ts`
- `src/lib/graph/__tests__/drilldown-nav.test.ts`
- `locales/en/common.json`
- `locales/ko/common.json`
- `locales/es/common.json`
- `locales/pt/common.json`
- `locales/id/common.json`

## Links

- Preview: `agents/codex/outbox/preview/20260613-235032-t3-graph-p11-owned-progressive.html`
- Older original worktree backup commit also exists: `8f5bd77` on `E:\Coding Infra\_worktrees\2ndB-codex`, but Claude should prefer current-main branch commit `8c6f0f0`.
