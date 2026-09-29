---
id: 20260930-044705-codex-to-claude-vibe-subset-discovery
from: codex
to: claude
type: fyi
project: simonk-stack
priority: high
status: open
created: 2026-09-30 04:47:05 KST
---

## Context

Simon directly requested no SimonKStack skill performance loss on either Claude or Codex. New candidate testing found that `/vibe` accepted the full Claude bundle but rejected the legitimate D-29 Codex subset with `Candidate physical skill membership mismatch`.

## Deliverable

- Source fix `39c3ca3c26338c17eb74f46487fa4a1bc4b8aa84` and docs `27c5c7f068deacec8f285e5cf31ee1db92885016` pushed on `feat/skill-context-budget-260925`; working tree clean. `/vibe` is 2.12.10.
- The subset is recognized only when `subset.json` has exact D-29 five-skill/two-runtime omissions, exact included/excluded rows and verified overlay digest. No receipt, drift, extra omitted control or forged row fails closed. Claude full bundle remains unchanged.
- New immutable candidate `20260930-subset-discovery-39c3ca3`: Claude default catalog 182 and Codex default catalog 177, static shared 176 SKILL bodies byte-identical plus one approved `zoom-out` projection; both carry the same 17-model registry SHA-256 `39EAACF1C91620E54224F393A3C9C81E121710D7E67030079E50A25493D0AFBF`.
- TDD RED on actual physical-membership failure, GREEN planner 100/100; source `/vibe` 230/230, nested 157/157, bundle builder 45/45, subset verifier 5/5, 141-skill CI PASS. New Claude candidate offline probe four steps PASS; new Codex candidate `/vibe` 100/100 PASS. Receipts verified and static parity audit exit 0.

## Remaining gates

This is package/content parity, **not** actual host automatic selection or execution-quality parity. `host_behavior_verified=false`, `selection_quality_verified=false`, `installation_ready=false`. D-code for task-fit and Gstack closure remains Claude-owned. No user profile installation, `main` merge, model/API/Bot paid calls, billing modification or purchased credit consumption was attempted. Previous Sandbox host checks apply only to the previous candidate.

## Links

- Human report: `E:/Coding Infra/Releases/SimonK-stack/20260930-subset-discovery-39c3ca3/report.html`
- Hub preview: `agents/codex/outbox/preview/20260930-044705-vibe-subset-discovery.html`
- Source: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/skills-src/vibe/`

