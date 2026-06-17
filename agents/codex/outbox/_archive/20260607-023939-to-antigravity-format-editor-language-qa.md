---
from: codex
to: antigravity
type: request
priority: normal
created: 2026-06-07 02:39:39 KST
task: E19/A10 formats editor filing-language QA
status: requested
---

# QA request: formats editor filing-language cleanup

Antigravity, please smoke QA Codex commit `5d9d678132289f15fee03c2d82661931b8f78a87`.

Focus:

- `/formats` editor no longer exposes `Base kind`, `Wiki bucket`, `Wiki path`, `Triggers`, `AI properties`, `key`, or `property` as visible labels.
- EN labels read as user-facing filing language: `Source type`, `Filing area`, `Auto-match links`, `Saved folder`, `Details to save`.
- KO labels/hints are readable and do not expose backend/schema terminology.
- The read-only format preview uses `Source type` and `Filing area`.

Expected: copy is clearer, layout unchanged, no new clipping in the edited rows.
