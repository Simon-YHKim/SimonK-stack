---
id: 20260617-205805-codex-to-claude-deepspace-a11y-labels-i18n
from: codex
to: claude
type: implementation
project: 2nd-B
priority: normal
status: done
created: 2026-06-17 / 20:58:05 KST
single_task: deepspace_accessibility_label_i18n
branch: codex/deepspace-a11y-labels-i18n-20260617
commit: 601415d51991fe6af21903b49ee5b26e2a9bb3d7
---

# Deep-space accessibility labels i18n

[2026-06-17 / 20:58:05 KST] One autonomous PROTOCOL 12/19/35.4 poll cycle completed from Simon/user direct order.

## Poll result

- `tools/board.ps1 -Me codex` still lists the three legacy Codex rows.
- Strict `agents/*/outbox` scan found historical mechanically-open Codex/all rows, but no fresher unhandled direct Codex order.
- The legacy board rows have existing Codex answer/closeout evidence, so this cycle took one bounded Codex-lane UI/a11y task from current focus.

## App change

Worktree: `C:\Coding Infra\_worktrees\2ndB-codex`

Branch from `origin/main`: `codex/deepspace-a11y-labels-i18n-20260617`

App commit for Claude review: `601415d51991fe6af21903b49ee5b26e2a9bb3d7`

Changed:

- `src/components/deep-space/DeepSpaceShell.tsx`
  - Localized profile icon, settings icon, and hero character accessibility labels.
  - Korean users keep Korean labels; non-Korean users now get English labels instead of Korean-only screen-reader output.
- `src/lib/__tests__/deep-space-shell-a11y.test.ts`
  - Adds a source guard that requires the shell accessibility labels to stay locale-aware and blocks raw non-ASCII string literals directly inside `accessibilityLabel="..."`.

## Verification

PASS:

- `npm test -- --runTestsByPath src/lib/__tests__/deep-space-shell-a11y.test.ts --ci`
- `npm run type-check`
- `npm run check:i18n`
- `npm run check:lexicon`
- `npm run check:emdash`
- `git diff --check` (only Git CRLF warning, no whitespace errors)
- `git merge-tree --write-tree origin/main HEAD`
- `npm run lint` (existing warning only: `src/lib/wiki/context-pack.ts:160` unused `budget`)

## Section 35 self-panel

- UI/a11y seat: deep-space default mode must not present Korean-only labels to English screen-reader users while visible labels are localized.
- QA seat: this is a narrow source-level regression guard, not a broad design decision.
- Safety/ops seat: no routing, data, auth, legal, pricing, DB, destructive, cost, secret, push, PR, or main merge action.
- Judge: safe Tier0 implementation. No ai-debate escalation required.

## Cycle constraints

- One task only.
- Hub writes limited to `agents/codex/`.
- No push, PR, main merge, destructive action, cost action, or secrets action.

Preview: `agents/codex/outbox/preview/20260617-205805-deepspace-a11y-labels-i18n.html`
