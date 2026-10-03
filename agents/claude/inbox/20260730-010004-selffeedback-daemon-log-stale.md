---
from: hub-watchdog
to: claude
type: selffeedback
priority: high
status: open
id: 20260730-010004-selffeedback-daemon-log-stale
created: 2026-07-30 01:00:04 KST
---

# [self-feedback] Daemon log stale while daemons alive

[2026-07-30 01:00:04 KST] The hub detected this on its own (no user paste needed).

- **Issue**: hub-daemon.log last write 12,145m ago but 2 daemon(s) alive -- likely hung on a CLI call.
- **Suggested action**: Inspect tail of hub-daemon.log; if a CLI is wedged, safe-restart the daemons (the Start-Job timeout should prevent this).

(Auto-filed by tools/hub-watchdog.ps1. Re-files only after a 120m cooldown if unresolved. Delete this note once handled.)