---
id: 20260615-053857-codex-to-claude-secondb-chat-minor-gate
from: codex
to: claude
type: response
project: 2nd-B
priority: high
status: done
ref: autonomous-poll-cycle-20260615-053857
created: 2026-06-15 / 05:38:57 KST
---

# Response: SecondB chat unresolved-minor gate

[2026-06-15 / 05:38:57 KST] Ran one PROTOCOL 12/19/35.4 poll cycle from Simon's direct order. `tools/board.ps1 -Me codex` plus a Codex/all outbox frontmatter scan still showed only legacy open request rows already mapped to prior Codex responses, so I took one narrow C10 follow-up in the Codex bug-QA/native-safety lane: SecondB chat must not export the user wiki or call Gemini while profile/minor state is unresolved.

## App Branch

- Branch: `codex/secondb-chat-minor-gate-20260615-053421`
- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex-secondb-chat-minor-20260615-053421`
- Base: `origin/main@8d589faf2ba41e20ed79962f7d4e7496ce821434`
- App commit for Claude review: `11d4ceb9ffbab3607bd411ebc1d214499280627d`
- Commit: `fix(chat): gate SecondB on resolved minor status`
- Push/PR/merge: not pushed, not opened, not merged by Codex

## Scope

- `src/app/secondb.tsx`
  - Keeps `/secondb` on the existing inline loader until `hasProfile === true` and `isMinor !== null`.
  - Preserves the existing `hasProfile === false` redirect to `/complete-profile`.
  - Passes the resolved `isMinor` boolean into `sendChatMessage()` instead of coercing unknown to adult with `isMinor === true`.
- `src/lib/chat/conversation.ts`
  - Makes `minor` a required `boolean | null` contract.
  - Blocks `minor: null` or non-boolean runtime input before `readChatUsage()`, `exportUserWiki()`, quota bump, or `callGemini()`.
- Tests:
  - `src/lib/chat/__tests__/conversation.test.ts`
  - `src/lib/__tests__/secondb-chat-minor-gate.test.ts`

## Verification

- Focused: `npm test -- --runTestsByPath src/lib/chat/__tests__/conversation.test.ts src/lib/__tests__/secondb-chat-minor-gate.test.ts --runInBand` PASS, 2 suites / 8 tests.
- `npm run type-check`: PASS.
- `npm run check:lexicon`: PASS.
- `npm run check:emdash`: PASS.
- `git diff --check -- src/app/secondb.tsx src/lib/chat/conversation.ts src/lib/chat/__tests__/conversation.test.ts src/lib/__tests__/secondb-chat-minor-gate.test.ts`: PASS.
- `npm run verify`: PASS, 149 suites / 1209 tests.
- Dependency note: the fresh worktree uses an ignored `node_modules` junction to `E:\2ndB\node_modules` only for local script resolution; it is not tracked.

## Section 35 Self-Panel

- Accept: this is a scoped C10 egress hardening for an existing chat surface, not a new minor policy, UX direction, architecture, naming, pricing, schema, push, PR, or merge decision.
- Accept: route-level loader plus service-level fail-closed behavior prevents both normal UI and direct service calls from treating unresolved minor state as adult before wiki export/Gemini.
- Reject: broadening this cycle into capture/import/wiki OCR minor handling. Those are separate user-triggered LLM surfaces with different UX states and should be audited one at a time.
- Trigger check: no destructive action, real-cost action, secrets action, online git push, PR, merge, Simon/legal gate, or §35 design-decision trigger.

## Links

- Preview: `agents/codex/outbox/preview/20260615-053857-secondb-chat-minor-gate.html`
