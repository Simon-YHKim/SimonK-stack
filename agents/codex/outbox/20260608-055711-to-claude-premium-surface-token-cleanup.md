---
from: codex
to: claude
type: handoff
priority: normal
status: open
created: 2026-06-08 05:57:11 KST
app_worktree: E:\Coding Infra\_worktrees\2ndB-codex
app_branch: codex/core-label-tail-cleanup
base: origin/main@d87476e
head: 92eb46d
---

# Premium Surface Token Cleanup

Codex continued the design-token anti-slop pass and fixed raw colors in shared premium UI primitives.

## App Commits Waiting On Codex Branch

- `14ae739 fix(a11y): label graph drilldown data action`
- `dee2770 fix(theme): tokenise navigation chrome colors`
- `92eb46d fix(theme): tokenise premium surface colors`

`git rev-list --left-right --count origin/main...HEAD` is `0 3`.

## Latest Change

- `src/components/premium/surfaces.tsx`
  - Imports `withAlpha`.
  - Replaces ghost/danger/disabled button `rgba()` literals with `withAlpha(cosmic.*)`.
  - Replaces `BrandChip`, `PixelIconButton`, and input glass `rgba()` literals with token-composed values.
  - Replaces panel `shadowColor: #000` with `cosmic.space950`.

No visual copy, route, layout metric, or behavior changed.

## Verification

- `git diff --check` PASS.
- `npm run type-check` PASS.
- `npm run verify` PASS.
  - Includes lint, type-check, i18n, lexicon, LLM boundary, constraints, emdash check, and Jest.
  - Jest: 99 suites / 866 tests passed.
- Secret scan on changed file found no matches.

## Request

Please review and absorb/push through Claude's normal online flow when ready. Codex did not push or create a PR.
