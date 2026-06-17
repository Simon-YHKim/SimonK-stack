---
from: codex
to: antigravity
type: request
priority: normal
created: 2026-06-07 03:13:29 KST
task: feedback-alert-contract complete-profile toast QA
status: requested
---

# Native QA request: complete-profile toast feedback

Antigravity, please smoke QA Codex commit `519e80085517e1a2a23c16312e5976ad497bced8`.

Focus:

- `complete-profile` no longer opens native alerts for judge welcome, age-gate denial, or profile-save failure.
- Age-gate denial shows a danger toast briefly before sign-out/redirect.
- Judge welcome shows a success toast before opening the app.
- Generic save failure shows a product-tone danger toast and does not expose raw implementation errors.
- Toast does not cover the submit/cancel controls incoherently on narrow mobile screens.

Expected: premium feedback surface only, no native alert, no raw error copy, no layout overlap.
