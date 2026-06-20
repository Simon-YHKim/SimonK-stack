---
from: hub-watchdog
to: claude
type: selffeedback
priority: high
status: open
id: 20260616-022103-selffeedback-control-paused
created: 2026-06-16 02:21:03 KST
---

# [self-feedback] Hub CONTROL is paused

[2026-06-16 02:21:03 KST] The hub detected this on its own (no user paste needed).

- **Issue**: CONTROL.md state=paused -- daemons will skip work cycles.
- **Suggested action**: If unintended, set CONTROL state=running. If intended (migration/maintenance), ignore.

(Auto-filed by tools/hub-watchdog.ps1. Re-files only after a 120m cooldown if unresolved. Delete this note once handled.)