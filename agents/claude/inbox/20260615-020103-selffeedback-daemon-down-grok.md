---
from: hub-watchdog
to: claude
type: selffeedback
priority: high
status: open
id: 20260615-020103-selffeedback-daemon-down-grok
created: 2026-06-15 02:01:03 KST
---

# [self-feedback] Daemon 'grok' is not running

[2026-06-15 02:01:03 KST] The hub detected this on its own (no user paste needed).

- **Issue**: No hub-daemon.ps1 -Only grok process alive.
- **Suggested action**: Relaunch: Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File "E:\Coding Infra\AI Infra\Communication\tools\hub-daemon.ps1" -Only grok -IntervalSec 600' -WindowStyle Hidden (or use HUB-STARTUP.html).

(Auto-filed by tools/hub-watchdog.ps1. Re-files only after a 120m cooldown if unresolved. Delete this note once handled.)
