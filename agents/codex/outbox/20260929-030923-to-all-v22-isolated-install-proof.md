---
id: 20260929-030923-codex-to-all-v22-isolated-install-proof
from: codex
to: all
type: fyi
ref: ""
project: SimonK-stack
priority: normal
status: done
created: 2026-09-29 03:09:23 KST
---

## Context
Simon authorized all nonpaid continuation. v22 had fresh Claude init proof, but the current candidate and Codex overlay had not received their own isolated install/uninstall byte-parity rehearsal.

## Deliverable
Two separate fresh Windows Sandbox guests, each with networking disabled, no account credentials and read-only candidate/executable mappings, ran local marketplace + five-plugin install/uninstall rehearsals. Claude Code 2.1.283 enabled five plugins and matched all 736 candidate files by path, size and SHA-256; uninstall left plugin and marketplace lists empty, with 741 CLI-retained cache files inside the disposable guest. Codex CLI 0.155.0 installed five plugins and matched all 742 overlay files; uninstall left plugin, marketplace and cache counts zero. Both guest network-adapter counts were zero before/after. Both exact Sandbox IDs were stopped. Candidate and overlay receipts reverified unchanged, readiness remains false.

Source README/INSTALL proof `6e70dee` pushed to clean, remote-equal `feat/skill-context-budget-260925`. Repository regression 329=326 pass/3 candidate-gated skips; pinned v22 preview6/6. This proves only empty-guest local install/copy/list rollback, not existing user-profile migration, skill behavior, default Codex catalog, Gstack runtime, safety hooks, model responses or billing. No user install, main merge, model/Bot/Orca generation, extra paid usage or payment-setting change.

## Links
- HTML: `agents/codex/outbox/preview/20260929-030923-v22-isolated-install-proof.html`
- Full report: `E:/Coding Infra/Releases/SimonK-stack/20260929-v22-html-pr54/report.html`
- Claude raw: `E:/Coding Infra/Releases/SimonK-stack/20260929-v22-html-pr54/sandbox-install-v22/output/result.json`
- Codex raw: `E:/Coding Infra/Releases/SimonK-stack/20260929-v22-html-pr54/sandbox-install-codex-v22/output/result.json`
- Source: `docs/INSTALL.md` at `6e70dee`
