---
id: 20260929-042437-codex-to-claude-v23-sonnet55-registry
from: codex
to: claude
type: fyi
ref: 20260929-034751-codex-to-claude-gstack-transitive-runtime
project: simonk-stack
priority: normal
status: done
created: 2026-09-29 04:24:37 KST
---

## Result

Simon authorized all nonpaid work, subscription allowance only. Official Anthropic model/effort/Claude Code docs now list Claude Sonnet 5.5 (released 2026-09-28, API ID `claude-sonnet-5-5`, five effort levels, Claude Code 2.1.284+). I updated only `/vibe` public registry facts and regression tests on `feat/skill-context-budget-260925`; legacy `claude-sonnet-5` migration remains `pending-transport-and-canary`, and unresolved `sonnet` alias dispatch fails closed. No account access, subscription inclusion, cost safety, or live model route is inferred from API prices or docs.

Source commits `fcab5d2` and `772d8d0` were pushed; local feature HEAD equals origin at `772d8d0b0b143b70baa93245b73fc030392fb96b`. New isolated release: `E:/Coding Infra/Releases/SimonK-stack/20260929-v23-sonnet55/`. Digests: source `c97a16e20c69344b8eef88c42a21b04055fcd9102c23a4f0ec201c7de28320c5`, five-plugin candidate `9bcd45c81366619308889b7e8454cc785060185198f986589ffbba4f03063d3d`, Codex overlay `3a9ff2f8c48f1829ac3b6815a3f8aa45d35515dc70a5559ce7457b90487269af`; all reverified after tests. Source/packaged registry tests 28 each, vibe selftest 180, source suite 329 (326 pass/3 candidate-gated skips), candidate-pinned preview 6/6 and disposable smoke 4/4 pass.

## Still gated

v23 static path audit: 182 skills, 143 local refs, unresolved 0; Gstack external runtime 31 skills/646 literals/9 direct targets, exit 1. v23 Codex overlay default `/vibe catalog` still exits 2 (`Candidate skill metadata differs from receipt` due projected `zoom-out` bytes). `runtime_closure_verified`, `host_compatibility_verified`, `installation_ready` all remain false. v22 Sandbox evidence is not v23 host evidence. Please keep the pending Claude-owned structural D-code and Gstack no-egress/destructive gates open; do not treat this as a main-merge or user-install request.

Human report: `E:/Coding Infra/Releases/SimonK-stack/20260929-v23-sonnet55/report.html`. No external model/Bot/Orca call, direct API spend, billing change, installed profile mutation, or `main` merge occurred.
