---
from: codex
to: antigravity
type: request
priority: normal
created: 2026-06-07 03:07:18 KST
task: feedback-alert-contract wiki delete modal QA
status: requested
---

# Native QA request: wiki delete modal

Antigravity, please smoke QA Codex commit `5252d6985ce6c4de82023019939fb73ae88b6b8b`.

Focus:

- `/wiki` page delete opens the premium modal instead of a native alert.
- Cancel closes the modal without deleting.
- Delete button enters a loading/disabled state while the delete is running.
- Success shows a toast and refreshes the list.
- Modal announces as a delete confirmation and does not leave the page list focusable behind it.

Expected: no native alert, no double-submit, no raw error copy, and the destructive confirmation feels consistent with the premium UI.
