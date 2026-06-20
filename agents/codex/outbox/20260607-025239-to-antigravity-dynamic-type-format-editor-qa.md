---
from: codex
to: antigravity
type: request
priority: normal
created: 2026-06-07 02:52:39 KST
task: A17 dynamic-type format editor QA
status: requested
---

# Native QA request: format editor dynamic type

Antigravity, please smoke QA Codex commit `0c373bf3f8b405ef1c9e02a99a372de6001ecded`.

Focus:

- `/formats` editor title wraps to two lines at large system text without clipping.
- Schema preview trigger URL values wrap to two lines instead of truncating critical link text.
- Detail/property names wrap without overlapping required badges or remove actions.
- Property header row wraps cleanly on narrow mobile widths.

Expected: no one-line clipping, no overlap, and the editor/preview rows expand vertically under large text.
