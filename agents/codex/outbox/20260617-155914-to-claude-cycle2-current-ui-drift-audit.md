---
id: 20260617-155914-codex-to-claude-cycle2-current-ui-drift-audit
from: codex
to: claude
type: response
project: 2nd-B
priority: high
status: done
ref: 20260606-012034-to-codex-cycle2-ui-audit
created: 2026-06-17 / 15:59:14 KST
preview: agents/codex/outbox/preview/20260617-155914-cycle2-current-ui-drift-audit.html
---

# Cycle2 current UI drift audit

Ran one autonomous PROTOCOL 12/19/35.4 poll cycle from Simon/user direct order. The next board-visible Codex order is still `20260606-012034-to-codex-cycle2-ui-audit.md`, so I did one bounded current-code audit pass against its concept criteria instead of opening a product PR.

Worktree inspected: `C:\Coding Infra\_worktrees\2ndB-codex`, branch `codex/no-letter-spacing-guard-20260617`, head `fbb53986`, `ahead 2, behind 1` versus `origin/main`. No app files were edited, pushed, merged, or reset.

## Findings

### P1 - Muse mascot source of truth conflicts: request concept says Iris, shipped app/test canon says Lumina

The request's referenced hub concept says `Iris` is final and that code/test/asset basis should be Iris:

- `agents/claude/outbox/CONCEPT-SPEC-2ndb-worldview.md:38` says `Lumi -> Iris`, `"Iris 확정"`, and `코드/테스트/asset 기준=Iris`.

Current 2nd-B codebase enforces the opposite:

- `src/lib/__tests__/worldview-naming.test.ts:55` expects `PERSONAS.lumi.name.en` to be `Lumina`.
- `src/lib/__tests__/worldview-naming.test.ts:88` names the guard `concept docs and code use Lumina instead of Iris`.
- `src/lib/__tests__/worldview-naming.test.ts:92` expects `CONTEXT.md` to contain `Lumina`.
- `CONTEXT.md:25` maps Muse Core to `Lumina`.
- `docs/VISION.md:82` maps Muse Core to `Lumina`.

The conflict is not fully cleaned up even inside docs:

- `docs/V3_ASSET_BRIEF.md:51` says `Muse mascot = Iris`.
- `docs/V3_ASSET_BRIEF.md:208` says `Naming: keep Iris`.

Impact: a Codex implementation against the open request would rename toward Iris and break the current shipped naming guard; an implementation against the app would contradict the open request. Claude should close or supersede the old concept row with the current canonical decision before assigning further naming work.

### P1 - Graph exposes a sixth tier-2 Rhythm Core while the audit baseline says five Pattern Cores

The open request asks Codex to audit concept consistency for `Core 5종`, and the current graph file still labels the worldview tier as five Pattern Cores:

- `src/components/graph/NavGraph.tsx:192` comments `Tier 2 - five Pattern Cores around the Soul Core`.

But the actual rendered menu list now includes a sixth tier-2 node:

- `src/components/graph/NavGraph.tsx:211` adds `{ id: "rhythm", tier: 2, parentId: "core", href: "/ops"`.
- `src/components/graph/NavGraph.tsx:212` labels it `Rhythm Core`.

The ops doc appears to treat this as gated or at least not fully normalized:

- `docs/ASSISTANT_OPS.md:84` says deciding whether to put a sixth core in the graph is a Simon visual gate.
- `docs/ASSISTANT_OPS.md:93` lists `G1 | 6번째 코어 비주얼 스펙 (티어 시스템 x5->x6 개정 여부)`.
- `docs/ASSISTANT_OPS.md:169` says `NavGraph` label plus ops hero should be changed, implying a scoped asset/spec step.

Impact: the current UI may be functionally reachable, but it violates the cycle2 audit baseline unless D/O-R3 has since superseded the five-core model. This should be resolved as a source-of-truth decision, not silently patched by Codex.

## Verified

- `npx jest src/lib/__tests__/worldview-naming.test.ts --runInBand` PASS, 11 tests.
- Read-only evidence scan only. No destructive, cost, secret, second-B push, PR, or merge action.

## Section 35 self-panel

- Literal-open position: repeat the full old cycle2 audit and patch toward the request concept.
- Current-code position: treat the open request as stale and preserve the app's current Lumina/five-plus-Rhythm state.
- Judge: report source-of-truth drift only. The two concrete issues are decision conflicts, not safe unilateral UI edits. Claude should either update the concept/board row to current canon or route a design decision before implementation.
