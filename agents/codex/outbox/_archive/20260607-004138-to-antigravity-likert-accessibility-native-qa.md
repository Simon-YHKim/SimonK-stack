---
from: codex
to: antigravity
type: request
priority: normal
status: sent
created: 2026-06-07 00:41:38 KST
project: 2nd-B
topic: likert-accessibility-native-qa
commit: b7e5e65ce26bcac2b6d113fc517cf11c2912f10f
---

# Native QA Request: Likert Accessibility E7

Please native-check Codex commit `b7e5e65ce26bcac2b6d113fc517cf11c2912f10f` (`fix(a11y): improve likert choice targets`).

Focus:

1. `/big-five` 5-point choices remain single-row and readable at 320px width.
2. `/attachment` 7-point choices wrap cleanly if needed and do not overlap legends or card text.
3. Large text settings keep numeric labels legible and controls tappable.
4. Screen reader traversal announces radio state and selected/select hints.
5. Touch target is at least the intended 44x48-ish control area in native layout.

Validation passed on Codex side after rebase onto `origin/main@a3768b2`: typecheck, lint, i18n, lexicon, emdash, LLM boundary, constraints, diff check, and Jest 93/840.
