---
from: codex
to: claude
type: handoff
priority: P0
topic: main graph reference component review
created: 2026-06-08 03:39:04 KST
app_worktree: E:\Coding Infra\_worktrees\2ndB-codex
branch: codex/core-label-tail-cleanup
app_commit: 3bd45e4
---

# Main Graph Reference Component Review

[2026-06-08 / 03:39:04 KST]
#comm #codex #claude-handoff #2nd-B #ui-ux #graph #art #verify-pass

## Summary
- Implemented Codex lane for `agents/claude/outbox/20260608-codex-ag-main-graph-reference-doublecheck.md`.
- `origin/main` now includes the graph reference tail as `bf8bee0` / #250.
- Current local branch after rebase on `origin/main@74e2f91`: `0 1` ahead.
- Remaining local app commit:
  - `3bd45e4 fix(copy): replace README Advisor residue with SecondB`
- Graph reference implementation no longer remains local-only.
- Scope is limited to NavGraph art/component behavior and Pattern Link styling.
- No push/PR by Codex.

## What Changed
- `src/components/graph/NavGraph.tsx`
  - Increased graph node drawing sizes so the live graph reads closer to Simon refs: Soul Core `112`, Pattern Core `58`, tier-3 `46`, Pattern Data `42`.
  - Swapped real tier-4 saved-piece nodes from `FinalLogArtV49` to Pattern Data crystal art, then wrapped them with `FinalPatternDataSnowflakeArt`.
  - Tier-4 Pattern Data now keeps color-key classification via `resolvePatternDataColor`, using title/summary/tags/domain id.
  - Centered tier-4 hit/art wrappers on the new `DATA_NODE_SIZE`.
  - Rounded Pattern Link strokes and strengthened active/flow/highlight widths.
  - Added proximity-derived edge styling per edge, so child tier, zoom bucket, active focus, ambient glow, and relation opacity affect Pattern Link strength.
- `src/app/index.tsx`
  - Added two persistent bottom `Touch!` insight cards when the empty-graph modal is not showing.
  - First card opens SecondB from Soul Core context.
  - Second card opens the featured Pattern Core character context, derived from the latest data-node village.
- `src/lib/graph/pattern-link.ts`
  - Raised default link width/opacity/saturation range from thin ambient lines to thicker conduit-like links:
    - width `1..3` -> `2..5`
    - opacity `0.18..0.95` -> `0.3..1`
    - saturation floor `0.35` -> `0.5`
- `src/lib/graph/__tests__/pattern-link.test.ts`
  - Updated regression expectations for the new Pattern Link bounds.

- `src/components/art/SoulcoreFinalArt.tsx`
  - Added `FinalPatternDataSnowflakeArt` as a snowflake/flower wrapper over the existing variant-aware Pattern Data art.
  - Follow-up fix keeps the underlying image sourced from `PATTERN_DATA_ART_BY_VARIANT[variant][colorKey]`, so production stays on v10 rather than hardwiring v45 wisdom art.

## Reference Fit
- Ref images read as crystal objects, not dot/log markers. Current live components already have v10 crystal core assets, so the main mismatch was size/readability plus tier-4 using logbook art.
- This pass makes the saved data nodes visually align with the small blue/pattern-data crystal language in both Simon references.
- The stronger rounded Pattern Link styling better matches the glowing conduit feel in the refs without wiring the unused standalone `PatternLink` tile component into the live SVG layer.
- The bottom `Touch!` cards are now represented in the graph home surface, matching the reference structure while staying above the existing bottom tab bar.

## Verification
- Targeted first: `npm test -- --ci pattern-link depth-style tier-visibility world-layout` PASS, 4 suites / 33 tests.
- Targeted first: `npm run type-check` PASS.
- Final before rebase: `npm run verify` PASS.
  - lint PASS
  - type-check PASS
  - i18n/lexicon/LLM-boundary/constraints/emdash checks PASS
  - Jest PASS, 98 suites / 859 tests
- Final after rebase on `origin/main@4738a26` / #248: `npm run verify` PASS.
  - lint PASS
  - type-check PASS
  - i18n/lexicon/LLM-boundary/constraints/emdash checks PASS
  - Jest PASS, 98 suites / 859 tests
- Final after #249 and rebase on `origin/main@a9cd070`: `npm run verify` PASS.
  - lint PASS
  - type-check PASS
  - i18n/lexicon/LLM-boundary/constraints/emdash checks PASS
  - Jest PASS, 98 suites / 859 tests
- Later rebase on `origin/main@7f56c5d` was docs-only (`ORDERS.md`); code diff unchanged from the verified graph tail.
- After #250 absorbed the graph tail, `npm run verify` PASS again on `origin/main@bf8bee0` + local README cleanup.
  - lint PASS
  - type-check PASS
  - i18n/lexicon/LLM-boundary/constraints/emdash checks PASS
  - Jest PASS, 98 suites / 859 tests
- After rebase on `origin/main@74e2f91`, `npm run verify` PASS again with only local README cleanup.
  - lint PASS
  - type-check PASS
  - i18n/lexicon/LLM-boundary/constraints/emdash checks PASS
  - Jest PASS, 98 suites / 859 tests
- `git diff --check` PASS before commit.
- Secret scan on changed files: no secret addition. Only false positive was import path text `theme/tokens`.

## Visual QA Notes
- Expo web was started from Codex worktree on `http://localhost:19007` with `EXPO_PUBLIC_USE_V3_ART=true`; bundle completed.
- Browser MCP backends `iab` and `chrome` were unavailable in this session.
- Headless Edge screenshots worked, but unauthenticated root redirects to `/sign-in`, so Codex could only confirm the auth gate render, not NavGraph itself, without using credentials or session state.
- AG's signed device render lane should perform the final visual comparison against:
  - `agents/claude/refs/main-graph-reference-20260608.png`
  - `agents/claude/refs/main-graph-reference2-drilldown-20260608.png`

## Remaining Visual QA
- Bottom cards, snowflake Pattern Data, and proximity links are implemented, merged to `origin/main` via #250, and verified by code/tests.
- Latest revalidation is on `origin/main@74e2f91`; graph implementation remains upstream and local branch carries only README copy cleanup.
- Final visual judgment still belongs to AG's signed device render lane because Codex could not access an authenticated graph session through Browser/Chrome MCP in this environment.
