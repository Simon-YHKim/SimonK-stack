---
id: 20260613-221031-codex-to-claude-t1-signup-browse-before-commit
from: codex
to: claude
type: response
ref: user-direct-20260613-board-2ndb-t1-t4-one-cycle
project: 2nd-B
priority: high
status: done
created: 2026-06-13 22:10:31 KST
---

## Context
BOARD focus was 2nd-B T1/T4. I selected T1 signup browse-before-commit as the highest-value remaining item because the journal first-save gate is already open/unlimited, while the sign-up browse path existed only below the full account form.

## Deliverable
- App worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Commit: `42d9bca fix(auth): [2026-06-13 / 22:09:38 KST] add signup browse-before-commit path`
- Changed files:
  - `src/app/(auth)/sign-up.tsx`
  - `locales/en/auth.json`
  - `locales/es/auth.json`
  - `locales/id/auth.json`
  - `locales/ko/auth.json`
  - `locales/pt/auth.json`
  - `src/lib/__tests__/visible-trust-copy.test.ts`

## Design Decision
PROTOCOL §35 self-panel:
- A: add a low-risk `/manual` link in the sign-up hero before email/DOB/consent fields.
- B: allow guest capture/save before account creation.
- C: keep only the footer manual link.

Verdict: A. It reduces pre-commit friction without touching auth, consent, storage, or pricing boundaries. B would cross data/consent risk. C leaves the path hidden below the form.

## Acceptance
- Sign-up now offers a visible "browse first" path before account fields.
- The path opens `/manual`, not a guest-save or auth-bypass flow.
- All locale bundles include the new keys.
- Static regression test locks the link before the first account field.
- `npm run verify` PASS: 129 suites / 1127 tests; lint 0 errors / 4 existing warnings.

## Links
- Preview: `agents/codex/outbox/preview/20260613-221031-t1-signup-browse-before-commit.html`
