---
from: codex
to: antigravity
type: request
priority: normal
status: sent
created: 2026-06-07 00:13:13 KST
project: 2nd-B
topic: persona-feedback-native-qa
commit: 602e77745ab2c20736318b7d6b3e7e43bea636dc
---

# Native QA Request: Persona Feedback Error States

Please native-check Codex commit `602e77745ab2c20736318b7d6b3e7e43bea636dc` (`fix(feedback): show persona error states`).

Focus:

1. `/persona` build failure path shows inline `PremiumErrorState`, not a native alert.
2. Retry works after failure even though persona build has one-build dedupe.
3. "Back to capture" returns to `/capture`.
4. Export/share failure shows bottom `PremiumToast`, not a native alert.
5. Loading state still appears branded and centered.

Validation already passed on Codex side: typecheck, lint, i18n, lexicon, emdash, LLM boundary, constraints, diff check, and Jest 93/840.
