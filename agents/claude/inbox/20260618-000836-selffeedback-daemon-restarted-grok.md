---
from: hub-watchdog
to: claude
type: selffeedback
priority: high
status: open
id: 20260618-000836-selffeedback-daemon-restarted-grok
created: 2026-06-18 00:08:36 KST
---

# [self-feedback] Daemon 'grok' was down -- auto-restarted

[2026-06-18 00:08:36 KST] The hub detected this on its own (no user paste needed).

- **Issue**: hub-watchdog found no 'grok' daemon and relaunched it (hub is running, drain mode).
- **Suggested action**: No action needed. If 'grok' keeps needing restarts, tail hub-daemon.log to find why it dies.

(Auto-filed by tools/hub-watchdog.ps1. Re-files only after a 120m cooldown if unresolved. Delete this note once handled.)