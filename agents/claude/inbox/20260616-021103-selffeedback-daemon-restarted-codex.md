---
from: hub-watchdog
to: claude
type: selffeedback
priority: high
status: open
id: 20260616-021103-selffeedback-daemon-restarted-codex
created: 2026-06-16 02:11:03 KST
---

# [self-feedback] Daemon 'codex' was down -- auto-restarted

[2026-06-16 02:11:03 KST] The hub detected this on its own (no user paste needed).

- **Issue**: hub-watchdog found no 'codex' daemon and relaunched it (hub is running, drain mode).
- **Suggested action**: No action needed. If 'codex' keeps needing restarts, tail hub-daemon.log to find why it dies.

(Auto-filed by tools/hub-watchdog.ps1. Re-files only after a 120m cooldown if unresolved. Delete this note once handled.)