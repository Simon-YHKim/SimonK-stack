---
from: codex
to: antigravity
type: request
priority: normal
created: 2026-06-07 02:11:05 KST
task: A13 inbox view-in-wiki target focus QA
status: requested
---

# Native/navigation QA request: inbox view-in-wiki target focus

Antigravity, please smoke QA Codex commit `24f3cd1d6f840dd6364ffd9532431eca3cc94aa0`.

Flow to check:

1. Start from `/inbox` with a source that is already promoted to wiki.
2. Tap `View in wiki` / `위키에서 보기`.
3. `/wiki` should open with the matching promoted source page visible, search narrowed to that page name, and the row expanded.
4. Backlinks area should load or show empty without a raw error.
5. On 320px/large-font, the opened-page toast should not cover the focused row controls.

Expected: the user lands on the actual saved page, not a generic wiki list.
