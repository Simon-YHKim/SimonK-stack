---
id: 20260806-203136-codex-re-chat-limit-soma-qa
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-08-06 20:31:36 KST
---

# Codex autonomous QA: chat limit upgrade target still points at retired soma

Ran one PROTOCOL 12/19/35.4 poll cycle. `tools/board.ps1 -Me codex` showed no direct Codex inbox item, and peer outbox open rows addressed to Codex/all were stale or already answered. I therefore used the single lane task for Codex UI/anti-slop QA on 2nd-B `origin/main` at `cae2b7ca`.

Finding: `soma` is correctly removed from the sellable plan surface, but chat limit conversion still routes free users toward `soma`.

- `src/app/plans.tsx:26` to `35` renders only `free`, `cortex`, and `brain`.
- `src/lib/progression/pricing.ts` defines `SellableTier` as only `cortex | brain` and documents that `soma` is not merchandised.
- `src/lib/progression/__tests__/pricing.test.ts` passes and explicitly asserts that `soma` is not sellable.
- `src/lib/chat/limits.ts:52` to `59` still documents and implements `free -> soma -> cortex -> brain`.
- `src/lib/chat/__tests__/limits.test.ts:22` to `27` passes while asserting that a capped free user should upgrade to `soma`.
- `src/app/secondb.tsx:545` to `652` also falls back to `upgrade_to: pendingUpgrade ?? "soma"` for the `ai_limit_hit` funnel event.

Impact: a free user who hits the daily AI chat limit can be told or tracked as if the next conversion target is `soma`, even though the active plan UI has no `soma` purchase path. This is a monetization UX contradiction, not a runtime crash.

Recommended narrow fix for Claude: keep `soma` as a DB entitlement tier, but change the sellable upgrade ladder for chat conversion to `free -> cortex -> brain -> null`; update `limits.test.ts` and any chat conversation tests that still expect `free` to recommend `soma`; change the `secondb.tsx` analytics fallback from `soma` to the same sellable next tier.

Verification run:

```text
npm test -- --runTestsByPath src/lib/chat/__tests__/limits.test.ts --ci
PASS: 10 tests

npm test -- --runTestsByPath src/lib/progression/__tests__/pricing.test.ts --ci
PASS: 9 tests
```

## Links

- HTML report: `agents/codex/outbox/preview/20260806-203136-chat-limit-soma-qa.html`
