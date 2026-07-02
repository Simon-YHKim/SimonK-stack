---
from: hub-watchdog
to: claude
type: selffeedback
priority: high
status: open
id: 20260703-012840-selffeedback-ai-failing-antigravity
created: 2026-07-03 01:28:40 KST
---

# [self-feedback] 'antigravity' failing every recent cycle

[2026-07-03 01:28:40 KST] The hub detected this on its own (no user paste needed).

- **Issue**: Last 3 antigravity exits all nonzero (1, 1, 1) and NOT in quota backoff.
- **Suggested action**: Spawn antigravity once manually to read the real error (see tool_headless_ai_spawn), or check its model in models.json is callable.

(Auto-filed by tools/hub-watchdog.ps1. Re-files only after a 120m cooldown if unresolved. Delete this note once handled.)