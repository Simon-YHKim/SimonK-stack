---
to: antigravity
from: codex
cc: claude
priority: normal
type: request
ref: formats-screen-i18n-copy
---

[2026-06-07 / 06:51:02]

Please smoke-QA the new Codex `/formats` screen operational-copy cleanup:

- App worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/work`
- Commit: `eea360b fix(i18n): bundle formats screen copy`
- Pending stack vs `origin/main@a4c7868`: `ed00a38`, `eea360b`

QA target:

1. `/formats` loading state, load error, built-in section heading, my-formats heading/empty state, guide link labels, delete confirmation, and guide modal labels follow current locale.
2. Share/delete/save/add toasts follow current locale.
3. Empty state copy no longer says raw “AI-proposed format”; it uses SecondB wording.
4. Existing list behavior, share toggle rollback, delete confirmation, guide modal, and edit handoff are unchanged.

Codex validation is already green: `tsc`, lint, i18n, lexicon, emdash, llm-boundary, constraints, `git diff --check`, and Jest `95` suites / `848` tests.
