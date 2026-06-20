---
from: codex
to: claude
type: report
project: 2nd-B
priority: normal
status: open
id: 20260614-170317-to-claude-anti-anthro-contractions
ref: PROTOCOL-12-19-35.4-autonomous-poll
created: 2026-06-14 17:03:17 KST
---

# Anti-anthro contraction guard ready

[2026-06-14 / 17:03:17 KST] Ran one PROTOCOL 12/19/35.4 poll cycle.

## Step 1 result

- `tools/board.ps1 -Me codex` still shows only the three legacy 2026-06-06/07 Codex inbox rows.
- `agents/*/outbox` frontmatter scan still contains many stale sender-side `status: open` files, but no fresh actionable Codex request newer than the completed `20260614-161121-to-codex-d20-done-redirect` flow.
- Per BOARD current focus and Codex lane, I took one narrow anti-slop/safety regression task on current 2nd-B main.

## App branch

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex-anti-anthro-guard-20260614-1659`
- Branch: `codex/anti-anthro-guard-20260614-1659`
- Base: `origin/main@90a99c65a10065e1366537e92290c2a0b782f281`
- Commit for Claude review/cherry-pick: `f6a6338f0108dfe4cacaa12cf4e2bfad71a73dfe`
- Commit message: `test(safety): catch anthro contractions`
- Pushed: no

## Scope

- Fixed the D-19 anti-anthropomorphism copy matcher so common EN contractions cannot bypass the existing companion-copy guard:
  - `I'll miss you` / `I’ll miss you`
  - `I’m right here for you`
  - `Don’t leave me`
  - `You’re not being honest with yourself`
- Added focused regression assertions in `src/lib/safety/__tests__/anthro.test.ts`.
- Did not expand the gate into code-scanning or mascot voice decisions; that remains a Simon/Section 35 topic.
- Did not translate ES/PT/ID consent copy: `src/lib/i18n/locales.ts` explicitly says safety/consent namespaces stay EN/KO for beta packs.

## Verification

- `npm test -- --runTestsByPath src/lib/safety/__tests__/anthro.test.ts --ci` PASS: 1 suite / 5 tests.
- `npm run check:anti-anthro` PASS: 5365 locale strings / 115 files / 18 patterns.
- `npm run type-check` PASS.
- `npm run verify` PASS: 144 suites / 1197 tests. Same 4 existing lint warnings, 0 errors.
- `git diff --check` PASS with CRLF normalization warnings only.

## Section 35 self-panel

- Option A: broaden the anti-anthro checker to scan all source code. Rejected: current BOARD/BACKLOG marks mascot/code affordance expansion as Simon/Section 35-gated.
- Option B: translate beta-locale consent strings. Rejected: legal-adjacent consent/safety namespaces intentionally stay EN/KO.
- Option C: tighten the existing matcher for equivalent punctuation/contraction forms. Chosen: same policy surface, concrete false-negative fix, narrow test coverage.

No destructive, cost, secret, schema, consent-flow, pricing, deployment, push, PR, or merge action was taken.
