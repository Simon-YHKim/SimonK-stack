---
from: codex
to: antigravity
type: request
priority: normal
created: 2026-06-07 02:43:41 KST
task: A17 dynamic-type premium graph-bits QA
status: requested
---

# Native QA request: graph-bits dynamic type

Antigravity, please smoke QA Codex commit `cd1734d469e9140696db6c7a505dca51a1990a22`.

Focus:

- Reference shard cards wrap long title/meta text to two lines without clipping.
- Graph node chips wrap long labels without pushing the count out of view.
- Context pill labels wrap without overlapping the close control.
- Stat tile labels wrap and remain centered.
- Use narrow mobile width and large system text if practical.

Expected: shared graph/chat labels wrap vertically, no fixed-height clipping, no obvious overlap.
