---
from: hub-watchdog
to: claude
type: selffeedback
priority: high
status: open
id: 20260615-221102-selffeedback-daemon-down-antigravity
created: 2026-06-15 22:11:02 KST
---

# [self-feedback] Daemon 'antigravity' is not running

[2026-06-15 22:11:02 KST] The hub detected this on its own (no user paste needed).

- **Issue**: No hub-daemon.ps1 -Only antigravity process alive.
- **Suggested action**: Relaunch: Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File "E:\Coding Infra\AI Infra\Communication\tools\hub-daemon.ps1" -Only antigravity -IntervalSec 600' -WindowStyle Hidden (or use HUB-STARTUP.html).

(Auto-filed by tools/hub-watchdog.ps1. Re-files only after a 120m cooldown if unresolved. Delete this note once handled.)