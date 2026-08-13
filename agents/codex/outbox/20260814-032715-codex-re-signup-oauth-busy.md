---
id: 20260814-032715-codex-re-signup-oauth-busy
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-08-14 03:27:15 KST
---

# Codex poll cycle: sign-up OAuth busy accessibility

Ran one autonomous poll cycle. Codex inbox was empty; peer outbox scan found no new actionable open request addressed to Codex/all beyond stale or already answered rows, so I did one in-lane UI/a11y anti-slop task.

Result:
- Worktree: `C:\2ndB\.worktrees\codex-qa-20260814-031920`
- Branch: `codex/qa-cycle-20260814-031920`
- Base: `origin/main 5ba0cdd905ec3e9e2d5aac0fceb17830c556ab09`
- Local app commit: `4634d56bb83101c69a25fbfab747a74984c55346`
- Change: `src/app/(auth)/sign-up.tsx` now passes `loading={oauthSubmitting}` to all six legacy social sign-up buttons, so the shared `Button` exposes OAuth pending state as `accessibilityState.busy` and shows the existing spinner.
- Regression: added `src/lib/__tests__/signup-oauth-busy-a11y.test.ts`.

Verification:
- `npm test -- --runTestsByPath src/lib/__tests__/signup-oauth-busy-a11y.test.ts --ci --runInBand` PASS
- `npx eslint 'src/app/(auth)/sign-up.tsx' --format stylish` PASS
- `npx eslint src/lib/__tests__/signup-oauth-busy-a11y.test.ts --format stylish` PASS
- `npm run type-check` PASS
- `npm run check:i18n && npm run check:i18n-untranslated` PASS
- `npm run check:lexicon && npm run check:emdash && npm run check:anti-anthro && npm run check:mascot-voice` PASS
- `npm run check:constraints && npm run check:cycles` PASS
- `git diff --check` PASS
- Changed-file secret-pattern scan: no matches

Known note:
- `npx prettier --check 'src/app/(auth)/sign-up.tsx'` still warns due existing file formatting drift. Running Prettier on that file created large review noise, so I restored it and kept only the six semantic lines. The new test file passes Prettier.
- No 2nd-B push, no hub branch switch, no destructive/cost/secret action.

## Links

- HTML report: `agents/codex/outbox/preview/20260814-032715-signup-oauth-busy.html`
