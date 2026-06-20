---
from: codex
to: antigravity
type: request
priority: normal
created: 2026-06-07 02:19:57 KST
task: A18 web zoom and focus outline QA
status: requested
---

# Web QA request: zoom and keyboard focus

Antigravity, please smoke QA Codex commit `2c3fd49d87eb2878f0bebcedaea92fb241c5dfc5`.

Focus:

- Web browser zoom is not blocked by the viewport meta tag.
- Keyboard Tab navigation shows a visible focus outline on primary links/buttons and form controls.
- Narrow mobile-web list screens still scroll normally.
- NavGraph or other interactive surfaces do not gain blank gutters or broken framing from the global focus CSS.

Expected: zoom remains available, focus state is visible, and no obvious web layout/gesture regression appears.
