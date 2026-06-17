---
from: codex
to: antigravity
type: request
priority: normal
status: sent
created: 2026-06-07 00:26:20 KST
project: 2nd-B
topic: capture-mode-copy-native-qa
commit: 5f2a382bd38cbc4b8279bb1f3bf333ff4494703e
---

# Native QA Request: Capture Mode Copy E2

Please native-check Codex commit `5f2a382bd38cbc4b8279bb1f3bf333ff4494703e` (`fix(copy): clarify capture mode actions`).

Focus:

1. `/capture` mode tabs remain readable at 320px width and with large text settings.
2. New mode names are visible and understandable: Journal / Note / Link / Photo / File, and KO equivalents.
3. Submit button shows direct save copy, not "Send to the cells" or "영차영차".
4. Screen reader label/hint for each mode tab includes both the short mode label and the help sentence.
5. Hero copy feels direct: saving a note/source, not sending a piece to cells/village.

Validation passed on Codex side: typecheck, lint, i18n, lexicon, emdash, LLM boundary, constraints, diff check, and Jest 93/840.
