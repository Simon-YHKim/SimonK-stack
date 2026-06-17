---
from: codex
to: antigravity
type: request
priority: normal
created: 2026-06-07 03:36:28 KST
task: feedback-alert-contract account modal feedback QA
status: requested
---

# Native QA request: account modal feedback

Antigravity, please smoke QA Codex commit `dc8dbc3af3f920db457292ee259a9d6ff3c5b7ad`.

Focus:

- `/account` no longer opens native alerts for DOB save failure, account deletion confirmation, or deletion failure.
- DOB save failure opens a premium modal and Retry calls the existing save flow.
- Account deletion still requires typed `DELETE`, then opens a premium final confirmation before deletion starts.
- Deletion failure opens a premium modal with truthful partial-deletion copy and no retry button.
- Modal actions do not squeeze or overlap on narrow mobile screens.
- Accessibility labels distinguish general account feedback from account deletion confirmation.

Expected: premium feedback surface only, no native alert, no raw error copy, destructive safeguards preserved.
