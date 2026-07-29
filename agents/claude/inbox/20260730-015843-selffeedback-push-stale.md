---
from: hub-watchdog
to: claude
type: selffeedback
priority: high
status: open
id: 20260730-015843-selffeedback-push-stale
created: 2026-07-30 01:58:43 KST
---

# [self-feedback] Hub master is 22 commits ahead of origin

[2026-07-30 01:58:43 KST] The hub detected this on its own (no user paste needed).

- **Issue**: Local hub commits are not reaching the comm-hub remote (HubBackup dead, rejected push, or divergence). They pile up locally and are not backed up off-machine.
- **Suggested action**: Run tools/hub-backup.ps1 manually and read tools/hub-backup.log; if the push is rejected non-fast-forward, Claude must git fetch + merge origin/master (never force), then push.

(Auto-filed by tools/hub-watchdog.ps1. Re-files only after a 120m cooldown if unresolved. Delete this note once handled.)