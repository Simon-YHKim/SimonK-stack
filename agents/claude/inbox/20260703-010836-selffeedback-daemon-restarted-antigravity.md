---
from: hub-watchdog
to: claude
type: selffeedback
priority: high
status: open
id: 20260703-010836-selffeedback-daemon-restarted-antigravity
created: 2026-07-03 01:08:36 KST
---

# [self-feedback] Daemon 'antigravity' was down -- auto-restarted

[2026-07-03 01:08:36 KST] The hub detected this on its own (no user paste needed).

- **Issue**: hub-watchdog found no 'antigravity' daemon and relaunched it (hub is running, drain mode).
- **Suggested action**: No action needed. If 'antigravity' keeps needing restarts, tail hub-daemon.log to find why it dies.

(Auto-filed by tools/hub-watchdog.ps1. Re-files only after a 120m cooldown if unresolved. Delete this note once handled.)