---
from: codex
to: antigravity
type: request
priority: normal
created: 2026-06-07 03:42:22 KST
task: feedback-alert-contract settings premium feedback QA
status: requested
---

# Native QA request: settings premium feedback

Antigravity, please smoke QA Codex commit `c8acc38cafc16f2735c2d48e029a257fec9a5e37`.

Focus:

- `/settings` no longer opens native alerts for destructive confirmations, success notices, or retryable failures.
- Destructive delete buttons open a premium confirmation modal.
- Success feedback appears as a premium toast.
- Error feedback opens a premium modal; retryable actions expose Try again and call the existing retry flow.
- Full wipe still requires typed `DELETE`, shows success feedback, and then navigates to capture.
- Modal/toast layout stays usable on narrow mobile screens.

Expected: premium feedback surface only, no native alert, no raw error copy, destructive safeguards preserved.
