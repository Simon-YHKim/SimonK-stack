---
id: 20260615-214342-codex-to-claude-o28-hybrid-bg-rev
from: codex
to: claude
type: response
project: 2nd-B
priority: high
status: done
ref: ORDERS-O-28-concept-5-hybrid-revision
created: 2026-06-15 / 21:43:42 KST
---

# O-28 Hybrid Background Revision

[2026-06-15 / 21:43:42 KST] One Codex poll cycle completed per PROTOCOL 12/19/35.4 and Simon's direct order.

## Cycle Selection

- `tools/board.ps1 -Me codex` still lists three legacy Codex inbox rows already closed by Codex packets `060740`, `062124`, and `063459`.
- Strict sender-outbox scan found no fresh `status: open` request addressed to `codex` or `all` after the prior Codex packet.
- Current `ORDERS.md` has fresh O-28, with Codex explicitly assigned the visual renderer slice for the selected concept-5 background revision.
- Single task this cycle: implement the Codex visual slice for O-28 on a fresh app branch.

## App Branch

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex-o28-rev`
- Branch: `codex/o28-concept5b-rev-20260615-2137`
- Base: local `origin/main@49d80e76f9cd3921444aecef00b39c0e45c4e4c4`
- Commit: `5d6831735dbad05435876b2379bdc65842e16168`
- Message: `feat(landing): add O-28 hybrid background revision`
- Push/PR/merge: not performed.

## Changes

- Added `public/landing/bg-concepts/concept-5b-hybrid-rev.html`.
- Added generated thumbnail `public/landing/bg-concepts/shot-5b.png`.
- Updated `public/landing/bg-concepts/index.html` from 5 concepts to 6 concepts, placing ⑤ and ⑤-rev side by side.
- Fixed existing concept ⑤ character asset path from missing `character.png` to the same shared head asset used by concepts ①-④.

## O-28 Fit

- Brightness: raised from the dim concept ⑤ toward the requested 2/3 point while keeping glare subdued.
- Randomness: seeded non-grid distribution in the canvas field plus irregular SVG node placement.
- Depth: far, mid, and near layers with different opacity, blur, drift, edge width, and node size.
- Size variety: small distant dots through larger near highlights and bigger graph nodes.
- Brightness variety: low-alpha distant specks through brighter near points, without bloom or glass.
- Visual consistency: keeps deep-space cyan tokens and character rim integration.

## Verification

- `git diff --check HEAD^ HEAD`: PASS.
- Direct Node scan over changed HTML for U+2014 em dash: PASS.
- `check-no-emdash.ts` via existing main checkout `tsx`: PASS.
- Headless Chrome render of `concept-5b-hybrid-rev.html`: generated `shot-5b.png`, nonblank.
- Headless Chrome render of `index.html`: 6-card board renders and shows ⑤/⑤-rev comparison row.
- Full `npm run verify` and `expo export` were not run in this fresh worktree because it has no local `node_modules`; Claude should run normal verify/export gate before merge.

## Section 35 Self-Panel

- Visual lens: ⑤-rev is materially brighter and more varied than ⑤, while still quieter than the earlier high-glow concepts.
- Product lens: this is a static comparison-board candidate, not a shipped app background swap.
- UX lens: board keeps the original ⑤ for direct comparison rather than replacing it.
- Performance lens: renderer uses one canvas paint, SVG layers, slow CSS transforms, and reduced-motion/static fallback behavior.
- Governance lens: Simon selected the direction; final adoption into `buildBackdrop` remains a separate order.

## Section 19

Triggered. O-28 is explicitly a multimodal AG plus Codex task. I found no fresh Antigravity O-28 spec packet in `agents/antigravity/outbox`, so this commit implements Codex's visual slice directly from Simon's concrete O-28 parameters. Recommend Claude request or apply AG review before merging if strict pair signoff is required.

## Actions Not Taken

No push, PR, merge, destructive action, cost action, or secrets action. Hub writes were limited to `agents/codex/`.

## Preview

- HTML preview: `agents/codex/outbox/preview/20260615-214342-o28-hybrid-bg-rev.html`
