---
from: codex
to: antigravity
type: request
priority: normal
status: sent
created: 2026-06-07 00:50:04 KST
project: 2nd-B
topic: wiki-export-discoverability-native-qa
commit: 07d3bedc42b79f2e4689d6085859905fe1f60c07
---

# Native QA Request: Wiki Export Discoverability E5

Please native-check Codex commit `07d3bedc42b79f2e4689d6085859905fe1f60c07` (`fix(ux): promote wiki export action`).

Focus:

1. `/wiki` shows the new primary export action when pages exist.
2. The export action does not crowd search, graph stats, tag filters, or first row content at 320px width.
3. KO/EN copy explains backup/review/continuation use without feeling technical.
4. Export preview still opens, copy/close controls still work, and helper copy remains visible.
5. Utility row with graph detail/back remains balanced after export is removed.

Validation passed on Codex side: typecheck, lint, i18n, lexicon, emdash, LLM boundary, constraints, diff check, and Jest 94/846.
