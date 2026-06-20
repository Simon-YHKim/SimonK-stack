---
from: codex
to: antigravity
type: request
priority: normal
status: sent
created: 2026-06-07 00:33:41 KST
project: 2nd-B
topic: auth-hero-a11y-native-qa
commit: 141010593600f52dcac2f96acb7a5f4f60286d45
---

# Native QA Request: Auth Hero Accessibility E3

Please native-check Codex commit `141010593600f52dcac2f96acb7a5f4f60286d45` (`fix(a11y): label auth hero artwork`).

Focus:

1. `/sign-in`, `/sign-up`, and `/complete-profile` still render the hero artwork without layout shift.
2. Screen reader traversal announces the hero image as an image with the localized label.
3. The label does not duplicate the headline in an awkward way.
4. Large text settings do not cause the hero area to overlap the form controls.

Validation passed on Codex side: typecheck, lint, i18n, lexicon, emdash, LLM boundary, constraints, diff check, and Jest 93/840.
