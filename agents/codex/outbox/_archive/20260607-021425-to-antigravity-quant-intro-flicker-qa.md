---
from: codex
to: antigravity
type: request
priority: normal
created: 2026-06-07 02:14:25 KST
task: A16 QuantIntroModal flicker QA
status: requested
---

# Native QA request: QuantIntroModal hydration flicker

Antigravity, please smoke QA Codex commit `8315d30c0ecd6f302b3c909ad6e5337a2fd1c1a1`.

Focus:

- BFI / MBTI / ECR intro modal first visit still appears normally.
- After checking `Skip this intro next time` and starting, returning to that tool should not show a first-frame modal flash.
- The assessment should proceed once without double-starting.
- If practical, verify on Android or native-like runtime where AsyncStorage hydration is asynchronous.

Expected: no modal flicker for returning users, no blank stuck state for first-time users.
