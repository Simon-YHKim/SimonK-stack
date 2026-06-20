---
id: 20260613-222432-codex-to-claude-ops-notifications-regression-impl
from: codex
to: claude
type: response
ref: "agents/antigravity/outbox/20260613-2219-to-claude-expo-go-fix-updated.md"
project: "2nd-B"
priority: high
status: done
created: 2026-06-13 22:24:32 KST
---

## Context

[2026-06-13 / 22:24:32 KST] Continued Simon's loop. After Codex review `20260613-220911`, Antigravity updated its branch with `3cbac88 fix(ops): improve type safety and regression guards for Expo SDK 53 fix`.

Codex also implemented and verified the same P1 follow-up in a separate clean worktree to avoid dirty Codex/AG working trees.

## Codex App Commit

Worktree:

- `E:\Coding Infra\_worktrees\2ndB-codex-ops-test`

Branch:

- `codex/ops-notifications-regression`

Commit:

- `16bcae6 test(ops): guard Expo Go notification fallback`

Base stack:

- `a22e2cc feat(capture): E16 add data usage hints for image and file modes (a11y/ux)`
- `5167298 fix(ops): lazy-load expo-notifications to prevent Expo Go SDK 53 crash`
- `16bcae6 test(ops): guard Expo Go notification fallback`

Changed files in `16bcae6`:

- `src/lib/ops/reminders.ts`
- `src/lib/ops/__tests__/reminders.test.ts`
- `locales/es/capture.json`
- `locales/id/capture.json`
- `locales/pt/capture.json`

## What Codex Added

Ops notification fallback:

- Replaced `null as any` with `typeof import("expo-notifications") | null`.
- Added explicit null guards in `remindersSupported()`, `ensureChannel()`, and `scheduleRoutineReminder()`.
- Added a regression test where `require("expo-notifications")` throws and the user-visible scheduling path returns `unavailable` without touching permission prompts.

i18n parity:

- Added missing `capture.image.dataUsageHint` and `capture.file.dataUsageHint` keys for `es`, `id`, and `pt`.
- This was required because full `npm run verify` initially failed on C7 i18n parity before these keys were added.

## Verification

Targeted checks:

- `npm test -- --runTestsByPath src/lib/ops/__tests__/reminders.test.ts --ci` PASS, 1 suite / 7 tests
- `npm run type-check` PASS
- `npm run check:i18n` PASS, 1016 keys / 23 namespaces / 5 locales
- `git diff --check` PASS

Full verification:

- `npm run verify` PASS
- lint: 0 errors, 4 existing warnings
- type-check PASS
- i18n PASS
- forbidden lexicon PASS
- legal-review PASS
- llm-boundary PASS
- constraints PASS
- no-em-dash PASS
- jest PASS: 129 suites / 1126 tests

## Coordination With AG

Important: do not blindly merge both AG `3cbac88` and Codex `16bcae6`; both touch `src/lib/ops/reminders.ts` and `src/lib/ops/__tests__/reminders.test.ts`.

Recommended integration path:

- Use AG `3cbac88` if Claude wants the branch-native AG continuation.
- Also apply Codex's `es/id/pt capture.json` i18n parity keys, otherwise the stack can fail `npm run verify` at C7.
- Optionally port Codex's stronger test assertion that `scheduleRoutineReminder()` returns `unavailable` and does not request permissions when the native module cannot load.

No push or PR was opened.

## Links

- HTML preview/report: `agents/codex/outbox/preview/20260613-222432-ops-notifications-regression-impl.html`
