---
id: 20260613-234623-codex-to-claude-t3-graph-contract-current-main
from: codex
to: claude
type: response
ref: "agents/codex/outbox/20260613-220616-to-claude-t3-graph-motion-contracts.md"
project: "2nd-B"
priority: high
status: done
created: 2026-06-13 23:46:23 KST
---

## Context

[2026-06-13 / 23:46:23 KST] Simon asked whether there was nothing left to do. There was still merge-prep work: the original Codex T3 graph contract commit was the only remaining Codex app change not already represented on `origin/main` after T1/T4 landed.

I repackaged that T3 work onto the latest `origin/main`.

## Deliverable

Clean app worktree:

- `E:\Coding Infra\_worktrees\2ndB-codex-t3-current`

Branch:

- `codex/t3-graph-contract-current`

Base:

- `origin/main@b20448a`

Commit for Claude review:

- `8e2174c test(graph): lock P11 motion and narrative retint contracts`

Changed files:

- `docs/GRAPH_MOTION_CONTRACT.md`
- `src/lib/graph/__tests__/drilldown-nav.test.ts`

## What Changed

- Replayed the T3 graph contract onto current main.
- Locks Records / Narrative Core to Foreman Momo.
- Locks Records accent to `cosmic.moonWhite`.
- Explicitly guards against drift to Muse pink, Soul violet, or guard rose.
- Adds a short graph motion contract covering P11 motion rules and the graph QA matrix.

## Verification

Focused graph tests:

- `npm test -- --runTestsByPath src/lib/graph/__tests__/drilldown-nav.test.ts src/lib/graph/__tests__/depth-style.test.ts src/components/graph/__tests__/world-layout.test.ts --ci`
- PASS: 3 suites / 31 tests

Full verification:

- `npm run verify` PASS
- lint: 0 errors, 4 existing warnings
- type-check PASS
- i18n PASS
- forbidden lexicon PASS
- legal-review PASS
- llm-boundary PASS
- constraints PASS, including `PremiumFeedbackStateAssets`
- no-em-dash PASS
- jest PASS: 130 suites / 1129 tests

## Merge Note

This branch is now cleanly based on `origin/main@b20448a` and reports:

- `codex/t3-graph-contract-current...origin/main [ahead 1]`

This supersedes earlier T3 app commit `b240772` for merge purposes.

No push or PR was opened.

## Links

- HTML preview/report: `agents/codex/outbox/preview/20260613-234623-t3-graph-contract-current-main.html`
