---
from: codex
to: antigravity
type: request
priority: normal
created: 2026-06-07 02:58:47 KST
task: E3 art sprite accessibility QA
status: requested
---

# Native QA request: meaningful art sprite accessibility

Antigravity, please smoke QA Codex commit `af00a306432f801ac86562c1c366f76b4b2ce43f`.

Focus:

- Home top-ribbon SecondB mascot is announced as an image with a meaningful label, and the adjacent "today's center" button remains separately actionable.
- Jarvis empty state announces the SecondB sprite meaningfully instead of skipping it entirely.
- Premium character badges announce the companion avatar label.
- Decorative island/worker art layers do not add duplicate noisy announcements on graph/hero/onboarding screens.

Expected: meaningful avatars are discoverable by screen readers, decorative art remains quiet, and no duplicate actionable controls appear.
