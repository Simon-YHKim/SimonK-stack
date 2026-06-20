---
id: 20260614-214434-codex-to-claude-firstsave-copy-claims-guard
from: codex
to: claude
type: fyi
project: 2nd-B
priority: normal
status: open
ref: PROTOCOL-12-19-35.4-autonomous-poll
created: 2026-06-14 / 21:44:34 KST
---

# Codex poll cycle - first-save copy claims guard

[2026-06-14 / 21:44:34 KST] Ran ONE PROTOCOL 12/19/35.4 poll cycle from Simon's direct order.

## Step 1 - inbox and outbox scan

- `tools/board.ps1 -Me codex` still reports the same three legacy open rows:
  - `20260606-012034-to-codex-cycle2-ui-audit.md`
  - `20260606-024749-to-codex-65e5ac4-regate.md`
  - `20260607-112720-to-codex-gtm-trust-copy-dispatch.md`
- Raw `agents/*/outbox` frontmatter scan still shows many old `status: open` files because sender request files are not closed in place. The newest direct Claude-to-Codex order remains `20260614-195200-to-codex-signup-firstviewport-fix.md`, already answered by the first-viewport and non-overlay branches.
- Newer Grok packets `20260614-211325-*` and `20260614-213045-*` are addressed to Claude and recommend first-save local ownership / temporal memory wording. They are useful advisory input, not a Codex order.

## Single task this cycle

I took the highest-value Codex-lane follow-up from current BOARD T1 first-save / Lever B focus: prevent first-run capture and first-save copy from adopting unsupported "local device", "not the app", or "no account" ownership claims before Lever B and local-first storage are real.

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex-firstsave-claims-20260614-214007`
- Branch: `codex/firstsave-copy-claims-guard-20260614-214007`
- Base: `origin/main@8af8725f53f6de1b5d855d98df99b48e790bbae5` (`fix(auth): keep signup primary action in view (#381)`)
- App commit for Claude review: `77f6d810ea2ca1eeacc2e8e12b4820800272d197`
- Commit message: `test(capture): guard first-save ownership claims`
- Scope: test-only update to `src/lib/__tests__/visible-trust-copy.test.ts`.
- Guard expanded: first-run capture and saved-records copy must not promise graph lighting, local/local-first/local-only storage, on-device storage, "not the app", anonymous/no-account/account-free/no-sign-up capture, or the Korean equivalents `로컬`, `기기`, `내 기기`, `기기 안`, `계정 없이`, `계정 없이도`, `가입 없이`.

No app copy changed, no product/architecture decision made, no design debate outcome assumed, no push, no PR, no merge.

## Verification

- Focused: `npm test -- --runTestsByPath src/lib/__tests__/visible-trust-copy.test.ts --runInBand` PASS, 1 suite / 8 tests.
- Full: `npm run verify` PASS, 148 suites / 1206 tests.
- Whitespace: `git diff --check` PASS.
- App branch state after commit: clean, `ahead 1`.

## Section 35 self-panel

- Option A: implement Grok's exact first-save local/on-device/"not the app" wording now. Rejected because current app storage is account-backed and export-capable, not local-first file ownership or account-free capture.
- Option B: add a regression guard so future first-save copy can discuss Records/export honestly without unsupported local/no-account claims. Accepted as a narrow anti-slop/data-truth guard inside Codex lane.
- Option C: escalate to Simon. Not needed for this test-only guard. No destructive action, real-cost action, secrets, DB, consent, pricing, or safety-routing change occurred.

## Claude action

If this guard matches the current T1/Lever B direction, review or cherry-pick `77f6d810ea2ca1eeacc2e8e12b4820800272d197`. Keep the actual first-save local/temporal ownership copy decision on the §35/Claude gate until the product path is real.

## Links

- Preview: `agents/codex/outbox/preview/20260614-214434-firstsave-copy-claims-guard.html`
