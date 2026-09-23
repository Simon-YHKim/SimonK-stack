# Changelog

## 2.8.0 - 2026-09-23

- Add durable local run/account reservations and dispatch intents in one SQLite
  transaction; keep the authorized grant immutable and default to USD 0.
- Prevent repeated claim sends and unsafe retries after uncertain acceptance;
  require original-job lookup, terminal proof, cost settlement and fresh plans.
- Separate execution success, acceptance/rejection and actual-cost evidence.
  Preserve unknown cost and observed overruns; never release them on timeout.
- Add crash, concurrent-process, local CLI lifecycle and sensitive-payload
  regression tests. Strict embedded JSON parsing rejects duplicate keys and
  non-finite values; exact nanoUSD conversion never rounds approval caps up.
- Document trusted-coordinator and single-local-DB boundaries. No provider
  generation adapter, live five-surface E2E, installation or main promotion is
  implied by these state tests.

## 2.7.0 - 2026-09-23

- Add a central model/effort registry with separate provider and transport facts;
  reject stale alias/access evidence again when work becomes ready.
- Collect explicit one-shot Codex, Claude, Grok and Antigravity CLI metadata.
  Preserve observed quota buckets, credit fields and opaque account references.
- Keep unknown billing, missing identity and unverified generation unavailable;
  do not equate subscription usage or metadata success with zero-cost execution.
- Bound probe I/O and lifetime; contain owned Windows process trees before
  launch and reject server-initiated actions or unknown Antigravity contracts.
- Add offline collector regression tests. Actual metadata observations are not
  five-surface task E2E, cost authorization or deployment-parity evidence.
- Leave legacy Orca defaults unchanged. Persistent execution/budget state,
  all-consumer migration and validated installation remain separate work.

## 2.6.0 - 2026-09-23

- Introduce the umbrella skill entry point, discovered skill composition,
  five execution surfaces, dependency preflight and total-run cost bounds.
- Integrate the vibe-bot handoff and result-verification contract.
