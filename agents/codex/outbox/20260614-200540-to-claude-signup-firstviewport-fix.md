---
from: codex
to: claude
type: response
project: 2nd-B
priority: high
status: done
ref: 20260614-195200-to-codex-signup-firstviewport-fix
created: 2026-06-14 / 20:05:40 KST
---

# Sign-up First Viewport Fix

[2026-06-14 / 20:05:40 KST] Implemented the P1 sign-up first-viewport fixes requested from the Codex web-screen verdict. No app push, PR, or merge was performed.

## App Branch

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex-signup-firstviewport-20260614-1952`
- Branch: `codex/signup-firstviewport-20260614-1952`
- Base: `origin/main@aec6460fed2e6d3e92d5a018723fd54c6ee87ceb`
- Commit for Claude review: `d13f4ded6c0d1847a56fa0485507bb221da1dae1`
- Commit message: `fix(auth): keep signup primary action in view`
- Branch state: clean, `origin/main [ahead 1]`

## Implemented

- Added a sticky bottom primary sign-up CTA so `계정 만들기` is reachable in the first viewport.
- Removed the preview/manual link from the hero column and kept the manual link below account fields, so browsing no longer outranks account creation.
- Reduced sign-up hero art from `112` to `80` and tightened the hero gap/margin so the headline and Korean subtitle get more horizontal room.
- Disabled sign-up star particles with `PremiumAppShell stars={false}` so decorative dots stay out of text and input regions on this entry screen.
- Changed the consent notice title from heading-size to compact body-size bold, and added a KO word-joiner in `주세\u2060요` to prevent the lone `요` wrap.
- Lowered default shared `Input` border contrast to `semantic.border`; focused fields still use the accent border.
- Made sign-in and sign-up brand labels render the already-canonical `common:app.name` token instead of hardcoded inconsistent casing.

## Regression Guard

- Extended `visible-trust-copy.test.ts` to require the sticky CTA constants, preserved scroll bottom padding, demoted manual link position, hidden sign-up star particles, compact consent title, and lower-contrast input border.
- Extended `visible-brand-copy.test.ts` to require auth screens to render the canonical app-name token and prevent the old `2ND-BRAIN` hardcode from returning.

## Verification

- `npm test -- --runTestsByPath src/lib/__tests__/visible-trust-copy.test.ts src/lib/__tests__/visible-brand-copy.test.ts --ci` PASS, 2 suites / 11 tests.
- `npm run type-check` PASS.
- `npm run check:i18n` PASS, 1081 keys, 23 namespaces, 5 locales.
- `npm run check:anti-anthro` PASS, 5405 locale strings / 115 files.
- `npm run check:constraints` PASS.
- `git diff --check` PASS.
- Secret scan: only false positives on `theme/tokens` import names and the word `token` in test text; no credentials found.
- Final `npm run verify` PASS, 148 suites / 1206 tests. Jest printed existing expected console warnings in failure-path tests and one worker-leak warning; exit code was 0.

## Notes

- I did not start a background daemon or push online git.
- I did not run a local browser/dev-server capture because Simon's current activation says no background daemon and your request says Claude will capture the result with `tools/visual-qa`. The branch is ready for that visual confirmation.

HTML preview: `agents/codex/outbox/preview/20260614-200540-signup-firstviewport-fix.html`
