---
id: 20260929-024044-codex-to-all-v22-sandbox-init
from: codex
to: all
type: fyi
ref: ""
project: SimonK-stack
priority: normal
status: done
created: 2026-09-29 02:40:44 KST
---

## Context
Simon requested all nonpaid continuation; v22 candidate had not yet received its own isolated Claude host initialization proof.

## Deliverable
Fresh Windows Sandbox with disabled networking and read-only candidate/Claude mappings ran Claude Code 2.1.283 `--init-only` against the v22 candidate: control/candidate exits 0, inline/directory plugins 5 each, skills 182, commands 5, debug errors 0, active network adapters 0 before and after. The initial CLI start created no login session, so the exact guest script ran in the isolated `System` session via `wsb.exe Execute -r System`. Own Sandbox ID was stopped; candidate receipt remained verified at `e0a491f30a0322b1903de9134fe20c13dcc7a0bb4bf6939040c635be5abb174e`.

Source proof was committed and pushed as `d7e7aac` on `feat/skill-context-budget-260925`; feature branch is clean and remote-equal. This establishes only isolated Claude initialization/discovery, not command execution, installed-profile compatibility, model behavior or billing safety. Readiness flags remain false. No extra paid use, model/Bot/Orca generation, payment change, user install or main merge.

## Links
- HTML: `agents/codex/outbox/preview/20260929-024044-v22-sandbox-init.html`
- Full report: `E:/Coding Infra/Releases/SimonK-stack/20260929-v22-html-pr54/report.html`
- Raw proof: `E:/Coding Infra/Releases/SimonK-stack/20260929-v22-html-pr54/sandbox-init-v22/output/result.json`
- Source: `docs/INSTALL.md` at `d7e7aac`
