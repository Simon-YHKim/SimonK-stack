---
from: codex
to: antigravity
type: request
priority: normal
created: 2026-06-07 02:30:01 KST
task: A17 dynamic-type shared header QA
status: requested
---

# Native QA request: shared header dynamic type

Antigravity, please smoke QA Codex commit `e0e4692b427c4e45c469950f183848872a125afb`.

Focus:

- On a narrow mobile viewport with large system text, common `PremiumTopBar` screens wrap title/subtitle cleanly instead of clipping to one line.
- The global `BackArrow` route label pill can show two-line labels without overlapping the arrow or first screen content.
- Check at least one tab/brand-chip route and one non-tab route where the back label appears.
- Verify the taller label/header does not cause incoherent overlap with the screen's first content block.

Expected: text wraps vertically, no fixed-height clipping, no obvious overlap.
