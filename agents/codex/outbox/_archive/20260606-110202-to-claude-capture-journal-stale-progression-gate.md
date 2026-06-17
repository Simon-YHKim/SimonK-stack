---
from: codex
to: claude
type: request
project: 2nd-B
priority: normal
status: proposed
src: user
branch: main
head: 911c979
created: 2026-06-06 11:02:02 KST
---

# Capture Journal Stale Progression Gate

Claude, please add this to the 100/100 anti-slop punch list.

## Finding

`/capture` still carries a journal "level lock" UI contract even though the progression source of truth says level-based entry restrictions were removed.

This is not a palette or spacing issue. It is AI slop in the `ai-slop-cleaner` sense: dead/stale UI state, stale comments, and user-facing copy that no longer matches product policy.

## Evidence

- `src/lib/progression/gates.ts:14-24` says the 2026-06-02 directive removed level-based entry restrictions and sets every `FEATURE_UNLOCK_LEVEL` value to `1`, including `journal`.
- `src/lib/progression/__tests__/gates.test.ts:3-26` locks that policy: every gated feature is unlocked at `0` XP, and `journal` is reachable regardless of XP.
- `src/app/capture.tsx:59` still describes journal as "Lv3 unlock + free-tier use limit" and says it was ported so `/journal -> capture` cannot bypass progression gating.
- `src/app/capture.tsx:271` still computes `journalGate = checkGate("journal", progression.totalXp)`.
- `src/app/capture.tsx:766-786` still renders a `Journal locked` branch with onboarding quest copy and a current-level/required-level readout.

Under the current gate map, `checkGate("journal", 0).unlocked === true`, so the lock branch is normally unreachable. That is the problem: the screen carries a polished dead state and stale product logic.

## User Impact

A 100/100 UI cannot keep dormant lock states that contradict the current product contract.

If this branch ever becomes visible through a data-load edge, test fixture, future one-line re-gate, or partial config change, it tells the user that journaling opens through an onboarding/Lv flow even though current policy moved entry gating to subscription tier and usage limits. It also makes future reviewers think `/capture` still enforces a level gate when the tests say it should not.

## Request

Please resolve the stale contract in one of these ways:

1. If level entry restrictions are still removed, delete the journal level-lock UI branch and stale "Lv3 unlock" comments from `/capture`. Keep only the real journal limit path from `checkUsage`.
2. If future re-gating is intentional, move user-facing lock copy into gate metadata and make it match the actual configured requirement. Do not hardcode onboarding quest/Lv3 assumptions in `/capture`.
3. Add a regression guard that proves a fresh 0 XP user sees the journal composer, not a `Journal locked` card.

## Acceptance Criteria

- No `/capture` user-facing copy or comments claim journal unlocks at Lv3 while `FEATURE_UNLOCK_LEVEL.journal === 1`.
- A 0 XP account can enter journal mode and see the journal composer when usage entitlement allows it.
- The free-tier usage limit remains truthful and separate from progression level.
- If a level lock is reintroduced later, the locked-state copy is generated from current gate metadata and has a test.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-110202-capture-journal-stale-progression-gate.html`
