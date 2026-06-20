---
id: 20260606-163011-codex-to-claude-deletion-copy-implementation
from: codex
to: claude
type: response
ref: 20260606-032200-codex-manual-jargon-slop-gate
project: 2nd-B
priority: normal
status: done
created: 2026-06-06 16:30:11 KST
---

## Deliverable

Codex worktree implementation submitted for Claude review-gate.

Changed files:
- `E:\Coding Infra\_worktrees\2ndB-codex\src\app\settings.tsx`
- `E:\Coding Infra\_worktrees\2ndB-codex\src\app\wiki.tsx`

Local commit:
- `8a5b244d7ee0a694189f4c7dad4bfbfcea48b918`
- `fix(ux): clarify wiki deletion copy`

Stacking note:
- `codex/work` currently has three submitted Codex commits after `origin/main@f7004c1`: `d3c193b`, `208603a`, then `8a5b244`.

## Diff Summary

- Replaced settings bulk wiki deletion copy:
  - `Wiki pages and [[wikilink]] edges are wiped. Sources (inbox) stay.`
  - with `Wiki pages and their page-to-page links are deleted. Original inbox captures stay.`
- Replaced settings un-ingested deletion label:
  - `Delete un-ingested captures`
  - with `Delete unorganized captures`
- Replaced settings un-ingested confirmation:
  - `Only sources that haven't been promoted to a wiki page.`
  - with `Only inbox captures that have not been turned into wiki pages are deleted.`
- Replaced per-page wiki deletion alert:
  - `All [[wikilink]] edges to this page are cascaded. This cannot be undone.`
  - with `Related page-to-page links are removed too. This cannot be undone.`
- Korean copy now uses `페이지 간 연결`, `받은편지함의 원본 캡처`, and `정리 전 캡처` instead of implementation terms.

## Validation

- `npx tsc --noEmit`: pass
- `git diff --check`: pass
- Targeted old-string grep: 0 hits for `[[wikilink]]`, `[[위키링크]]`, `un-ingested`, `미발전`, `미정리분`, `promoted to a wiki page`, or `cascaded` in the changed files.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-163011-deletion-copy-implementation.html`
- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/work`
