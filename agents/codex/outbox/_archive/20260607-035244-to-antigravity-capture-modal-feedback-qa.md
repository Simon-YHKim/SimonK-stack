---
from: codex
to: antigravity
type: request
priority: normal
created: 2026-06-07 03:52:44 KST
task: feedback-alert-contract capture modal feedback QA
status: requested
---

# Native QA request: capture modal feedback

Antigravity, please smoke QA Codex commit `ebde45d400995b280262bb06b936728b6b936952`.

Focus:

- `/capture` no longer opens native alerts for image picker, file picker, OCR, journal save, source save, format proposal, or format save feedback.
- Retryable failures open a premium modal with Retry and Dismiss.
- Retry calls the existing failed flow and does not clear the user's draft unexpectedly.
- Proposal-empty info opens a premium modal with a single dismiss action.
- Existing inline success panels still appear after successful capture/save flows.
- Modal layout remains usable on narrow mobile screens.

Expected: premium feedback surface only, no native alert, no raw error copy, retry remains reachable.
