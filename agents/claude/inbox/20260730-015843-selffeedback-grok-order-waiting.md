---
from: hub-watchdog
to: claude
type: selffeedback
priority: high
status: open
id: 20260730-015843-selffeedback-grok-order-waiting
created: 2026-07-30 01:58:43 KST
---

# [self-feedback] 4 open request(s) addressed to grok with no server

[2026-07-30 01:58:43 KST] The hub detected this on its own (no user paste needed).

- **Issue**: grok is request-only (excluded from default lanes); nothing serves its queue automatically.
- **Suggested action**: Spawn once: powershell -ExecutionPolicy Bypass -File tools/hub-daemon.ps1 -Only grok -MaxCycles 1 (its ref-aware counter + NO-OP rule make this safe), or answer/close the request as Claude.

(Auto-filed by tools/hub-watchdog.ps1. Re-files only after a 120m cooldown if unresolved. Delete this note once handled.)