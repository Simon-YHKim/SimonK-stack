---
from: hub-watchdog
to: claude
type: selffeedback
priority: high
status: open
id: 20260617-045928-selffeedback-daemon-down-antigravity
created: 2026-06-17 04:59:28 KST
---

# [self-feedback] Daemon 'antigravity' is not running

[2026-06-17 04:59:28 KST] The hub detected this on its own (no user paste needed).

- **Issue**: No hub-daemon.ps1 -Only antigravity process alive (auto-restart skipped: hub paused or -NoAutoRestart).
- **Suggested action**: If intended, ignore. Else set CONTROL state=running, or relaunch via HUB-STARTUP.html.

(Auto-filed by tools/hub-watchdog.ps1. Re-files only after a 120m cooldown if unresolved. Delete this note once handled.)