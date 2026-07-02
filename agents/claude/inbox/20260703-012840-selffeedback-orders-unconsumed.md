---
from: hub-watchdog
to: claude
type: selffeedback
priority: high
status: open
id: 20260703-012840-selffeedback-orders-unconsumed
created: 2026-07-03 01:28:40 KST
---

# [self-feedback] Simon's remote order(s) waiting with NO consumer (O-31)

[2026-07-03 01:28:40 KST] The hub detected this on its own (no user paste needed).

- **Issue**: ORDERS.md has 1 unconsumed order(s); no consumer heartbeat file (no director /loop has ever polled with -Heartbeat). The remote-order pipeline is effectively DOWN.
- **Suggested action**: Start the Claude /loop director session (HUB-STARTUP.html remote-orders card) or handle the order directly, then have the loop poll with -Heartbeat.

(Auto-filed by tools/hub-watchdog.ps1. Re-files only after a 120m cooldown if unresolved. Delete this note once handled.)