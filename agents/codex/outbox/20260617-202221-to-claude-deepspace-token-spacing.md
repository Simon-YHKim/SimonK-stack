---
id: 20260617-202221-codex-to-claude-deepspace-token-spacing
from: codex
to: claude
type: fyi
project: 2nd-B
priority: normal
status: done
created: 2026-06-17 20:22:21 KST
---

# Deep-Space Token / Spacing Anti-Slop Patch

## Context

Ran one PROTOCOL 12/19/35.4 poll cycle from Simon/user direct order. `tools/board.ps1 -Me codex` still lists the three legacy Codex inbox rows, and strict outbox scan found only historical mechanically-open Codex/all rows, so I took one bounded Codex-lane UI anti-slop task from the current 2nd-B focus.

## Deliverable

App branch for Claude review:

- Worktree: `C:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/deepspace-token-spacing-20260617`
- App commit: `7dc0e8ab6dbcc8c18cb4d4febc4b58427d3eb3a3`
- Commit title: `fix(ui): token deep-space pressed states`
- Files:
  - `src/lib/theme/tokens.ts`
  - `src/components/deep-space/DeepSpaceShell.tsx`
  - `src/components/deep-space/DeepSpaceLinks.tsx`
  - `src/components/deep-space/__tests__/deep-space-style.test.ts`

Changes:

- Added `deepSpace.cardPressed` so deep-space pressed states no longer carry component-local `rgba(...)` literals.
- Routed `DeepSpaceShell` and `DeepSpaceLinks` pressed backgrounds through the token.
- Changed compact deep-space uppercase label tracking from `1.5` to `0`.
- Added a focused Jest guard that fails if deep-space components reintroduce `rgba(` or nonzero `letterSpacing`.

## Verification

PASS:

- `npm test -- --runTestsByPath src/components/deep-space/__tests__/deep-space-style.test.ts --ci`
- `npm run lint` (existing warning only: `src/lib/wiki/context-pack.ts:160` unused `budget`)
- `npm run type-check`
- `npm run check:i18n`
- `npm run check:lexicon`
- `npm run check:emdash`
- `git diff --check`
- `git merge-tree --write-tree origin/main HEAD`
- `rg --pcre2 -n "rgba\(|letterSpacing:\s*(?!0\b)[0-9.]" src/components/deep-space -g "*.tsx"` returned no matches

Not run: full `npm run verify`; the bounded golden set above covers this narrow UI/style patch.

## Section 35 Self-Panel

- Trigger check: no new design, architecture, naming, DB, pricing, secrets, push, PR, or main merge decision. No external debate required.
- Pro: tokenizes a visible deep-space pressed tint and locks recurrence with a focused test.
- Contra: broader scan still finds existing non-deep-space hits in `RatifySheet`, `ConsentDialog`, `CrisisRouter`, and `core-brain`; left untouched because this cycle is one task only.
- Judge: merge-safe local branch, real SHA provided, no destructive/cost/secrets action, no 2nd-B push.

## Links

- Preview: `agents/codex/outbox/preview/20260617-202221-deepspace-token-spacing.html`
