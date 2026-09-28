---
id: 20260929-033553-codex-to-all-v22-profile-preservation
from: codex
to: all
type: fyi
ref: ""
project: SimonK-stack
priority: normal
status: done
created: 2026-09-29 03:35:53 KST
---

## Context
Simon requested all nonpaid continuation. Empty-guest v22 install/rollback passed, but preservation of unrelated existing profile state had only been rehearsed for v20. Claude Code also updated locally from 2.1.283 to 2.1.284 during this work.

## Deliverable
The old SHA-pinned Claude test stopped before candidate operations with `EXE_HASH_MISMATCH`; its raw failure remains preserved. A separate signed-2.1.284/hash-pinned offline Sandbox confirmed Claude v22 `--init-only`: 5 plugins/182 skills/5 commands/debug errors0, and fresh local install/uninstall: 736/736 payload bytes exact. Separate synthetic-profile guests for Claude 2.1.284 and Codex 0.155.0 installed the five v22 plugins alongside an unrelated fixture, then removed only the candidates. Existing fixture plugin/cache and personal-skill hashes remained; Claude settings marker and enabled state remained; Codex candidate cache ended at zero. Four passing guests had zero active network adapters before and after and were stopped. No real user profile or credentials were copied.

Source README/INSTALL evidence is pushed as `8802d19` on clean, remote-equal `feat/skill-context-budget-260925`. Base/overlay receipts reverified unchanged; readiness remains false. This does not prove real-profile migration, concurrent writes, recovery after interruption, default Codex catalog, Gstack closure, host safety hooks or billing. No user install, main merge, model/Bot/Orca generation, payment change or extra paid use.

## Links
- HTML: `agents/codex/outbox/preview/20260929-033553-v22-profile-preservation.html`
- Full report: `E:/Coding Infra/Releases/SimonK-stack/20260929-v22-html-pr54/report.html`
- Raw results: `E:/Coding Infra/Releases/SimonK-stack/20260929-v22-html-pr54/sandbox-profile-claude-v22-284/output/result.json`, `sandbox-profile-codex-v22/output/result.json`, `sandbox-install-claude-v22-284/output/result.json`, `sandbox-init-v22-284/output/result.json`
- Source: `docs/INSTALL.md` at `8802d19`
