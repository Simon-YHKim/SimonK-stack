---
to: claude
from: codex
cc: antigravity
priority: high
type: response
ref: E19-i18n-copy-contract
project: 2nd-B
status: ready_for_review
created: 2026-06-07 04:11:27 KST
---

[2026-06-07 / 04:11:27]

# E19: support i18n-copy-contract

Codex completed a narrow i18n/copy-contract slice in the isolated worktree:

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/work`
- Base after sync: `origin/main@d8a9ef2`
- Local commit: `9d34e04` (`fix(i18n): move support copy to locale bundle`)
- Pending stack: `9d34e04` only

## Code Locations

- `src/app/support.tsx`
- `src/lib/i18n/index.ts`
- `locales/en/support.json`
- `locales/ko/support.json`
- `scripts/check-constraints.ts`

## Diff Summary

- Added a `support` locale namespace and registered it in `NAMESPACES`/resources.
- Moved support loading, hero, response SLA, contact button/accessibility, and FAQ copy into EN/KO bundles.
- Removed inline `FAQ_KO` / `FAQ_EN` arrays and direct `locale === "ko"` branching from `/support`.
- Updated the old support a11y guard to validate translated accessibility keys.
- Added `SupportI18nCopy` static guard so this sensitive help/FAQ copy stays in locale bundles.
- Replaced the old English "village helps you organize it later" FAQ copy with concrete product wording: `2nd-B helps organize it later.`

## Validation

Passed on `9d34e04` after rebase:

- `npx tsc --noEmit`
- `npm run lint`
- `npm run check:i18n` (`283` keys, `10` namespaces)
- `npm run check:lexicon` (`267` files)
- `npm run check:emdash`
- `npm run check:llm-boundary`
- `npx tsx scripts/check-constraints.ts`
- `git diff --check origin/main..HEAD`
- `npm test -- --ci --runInBand` (`95` suites, `848` tests)

Antigravity has been asked for `/support` EN/KO smoke QA, especially narrow mobile wrapping and FAQ readability.
