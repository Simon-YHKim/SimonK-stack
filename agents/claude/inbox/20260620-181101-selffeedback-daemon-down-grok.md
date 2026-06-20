---
from: hub-watchdog
to: claude
type: selffeedback
priority: high
status: open
id: 20260620-181101-selffeedback-daemon-down-grok
created: 2026-06-20 18:11:01 KST
---

# [self-feedback] Daemon 'grok' is not running

[2026-06-20 18:11:01 KST] The hub detected this on its own (no user paste needed).

- **Issue**: No hub-daemon.ps1 -Only grok process alive (auto-restart skipped: hub paused or -NoAutoRestart).
- **Suggested action**: If intended, ignore. Else set CONTROL state=running, or relaunch via HUB-STARTUP.html.

(Auto-filed by tools/hub-watchdog.ps1. Re-files only after a 120m cooldown if unresolved. Delete this note once handled.)