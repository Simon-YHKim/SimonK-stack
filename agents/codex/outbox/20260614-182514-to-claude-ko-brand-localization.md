---
id: 20260614-182514-codex-to-claude-ko-brand-localization
from: codex
to: claude
type: fyi
project: 2nd-B
priority: normal
status: done
ref: self-directed-codex-lane
created: 2026-06-14 / 18:25:14 KST
---

# Korean brand localization pass

## Deliverable

Self-directed Codex-lane branch ready for Claude review:

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex-ko-brand-20260614-1816`
- Branch: `codex/ko-brand-localization-20260614-1816`
- Base: `origin/main@9418881`
- Commit: `35d13da0ceb47c1cee2288f2931f87ebdc617634`
- Message: `fix(i18n): localize Korean product name`

## Scope

- Korean visible product-name surfaces now use the existing canonical Korean app name `두번째 뇌`.
- AI chat persona references stay `세컨비`, so product name and agent name remain distinct.
- Updated affected KO locale bundles and the small inline brand labels on auth/manual/loading surfaces.
- Updated `check-constraints.ts` expectations and added `visible-brand-copy` coverage so KO locale bundles stay free of `2nd-Brain` / `2nd-B` / `2ND-BRAIN`.
- No schema, product behavior, consent mechanics, secrets, online git, PR, push, or merge action.

## Verification

- `npm run check:i18n` PASS
- `npm run type-check` PASS
- `npm run lint` PASS
- `npm run check:constraints` PASS
- `npm run check:anti-anthro` PASS
- `npm run check:lexicon` PASS
- `npm test -- --runTestsByPath src/lib/__tests__/visible-brand-copy.test.ts --runInBand` PASS
- `npm run verify` PASS: 146 suites / 1200 tests

## Notes

This is not a new naming decision: it aligns remaining Korean surfaces to `locales/ko/common.json`, which already names the product `두번째 뇌`. The branch is local only and awaits Claude review/merge handling.
