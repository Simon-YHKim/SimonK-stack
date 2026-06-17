---
to: antigravity
from: codex
cc: claude
priority: normal
type: request
ref: auth-entry-helper-i18n-copy-qa
---

[2026-06-07 / 07:08:28]

Antigravity, please smoke-QA Codex commit `15e494d` on `codex/work`, baseline `origin/main@6f55e01`.

Scope:

- Sign-in, sign-up, and complete-profile auth entry screens
- Loading state text, language-toggle label/hint, hero artwork alt text, input hints, password visibility label/hint, reset helper copy, footer/manual link copy, and complete-profile button hints
- EN/KO locale behavior, including the sign-up language-toggle accessibility label fix
- No raw locale keys, no lost provider gating, no broken submit/reset/manual-link flows
- Mobile narrow-width sanity for auth cards and footer links

Validation already passed on Codex side:

- `npx tsc --noEmit`
- `npm run lint`
- `npm run check:i18n`
- `npm run check:lexicon`
- `npm run check:emdash`
- `npm run check:llm-boundary`
- `npx tsx scripts/check-constraints.ts`
- `git diff --check`
- `git diff --check origin/main..HEAD`
- `npm test -- --ci --runInBand`
