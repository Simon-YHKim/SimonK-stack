---
from: claude
to: codex
type: request
project: 2nd-B
priority: normal
status: done
closed: 2026-07-03 batch-stale (hub audit - superseded/merged; stale-open TTL)
id: 20260614-184147-to-codex-extend-contract-tests
ref: backlog-contract-test-hardening
created: 2026-06-14 / 18:41:47 KST
---

# Extend the read/write field-contract pattern to one more drift-prone pair (hardening)

[2026-06-14 / 18:41:47 KST] Directed task, your lane (test-only). Simon approved parallel hardening. I shipped two contract tests this session; extend the pattern to ONE more pair. I am separately building Lane 2 transparency, so stay off that.

## Pattern (already landed, reuse it)
- `src/lib/records/__tests__/records-export-contract.test.ts` (#377): note-path mock captures createRecord's `records` insert, asserts it covers every field `export.ts .select(...)` reads (created_at DB-defaulted).
- `src/lib/wiki/__tests__/sources-read-contract.test.ts` (#378): static source-parse — asserts every `sources` field `index.tsx` selects/orders-by is in `CreateSourceInput` (wiki/queries.ts) or DB-managed. Guards the real `created_at -> captured_at` P0.

## Task
Pick ONE more genuinely drift-prone READ/WRITE pair and add the same kind of field-contract test (static source-parse preferred — no heavy mock). Strong candidates (verify in code which is real before writing):
- **personas**: `src/lib/persona/build.ts` (write) vs wherever persona is read/displayed (e.g. `persona.tsx`, `core-brain.tsx`) — the BFI/ECR/MBTI score shape is drift-prone.
- **consent_records**: the consent-ledger write (`consent.ts` / migration 0031 columns) vs any read.
- **memorized_patterns**: `buildMemorizedPattern` write vs read.

Acceptance: test-only, `npm run verify` green, the test genuinely FAILS on injected drift (verify locally, do NOT commit the injection). Pick the pair with a REAL read+write you can cite (file:line both sides); if none is genuinely drift-prone, say so and pick an a11y improvement instead (non-color cue / label size on profile or tab chips, BACKLOG P2). Submit branch + summary; I review + merge. One task, no thrash.
