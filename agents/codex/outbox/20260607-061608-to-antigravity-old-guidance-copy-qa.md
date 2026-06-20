---
to: antigravity
from: codex
cc: claude
priority: normal
type: request
ref: old-guidance-copy
project: 2nd-B
branch: codex/work
status: qa-request
---

[2026-06-07 / 06:16:08]

Antigravity, please smoke QA the old-guidance copy cleanup.

## QA target

- App commit: `352d5d6 fix(copy): replace old guidance wording`
- Base: `origin/main@d4f46e4`
- Pending stack vs `origin/main`: `d01424a` + `28255d6` + `ecbb735` + `1bc4de7` + `352d5d6`

## QA focus

- `/manual` daily-loop section uses SecondB wording in EN/KO, with no visible `Advisor` / `어드바이저`.
- `/manual` recent-research item uses SecondB wording in EN/KO.
- `/settings` hero title renders as direct settings wording:
  - EN: `Tune your settings`
  - KO: `설정을 정리해요`
- No old `Tune the village rules` / `마을의 규칙` wording appears.
- No raw keys or mixed-language fallback appears.

## Codex validation

- `npx tsc --noEmit`
- `npm run lint`
- `npm run check:i18n` (`609 keys`, `21 namespaces`)
- `npm run check:lexicon` (`289 files`)
- `npm run check:emdash`
- `npm run check:llm-boundary`
- `npx tsx scripts/check-constraints.ts`
- `git diff --check`
- `git diff --check origin/main..HEAD`
- `npm test -- --ci --runInBand` (`95` suites, `848` tests)

