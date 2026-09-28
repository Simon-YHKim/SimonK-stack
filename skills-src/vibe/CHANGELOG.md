# Changelog

## 2.13.0 - 2026-09-28

- Add peer sessions (hub D-31, Simon 2026-09-28: R1 inside /vibe, R3 alert
  allowed, R6 round trips bounded by context). `peer_state.py` reads Codex and
  Claude Code session records first: turn_id pairing for overlapping turns,
  fork/orphan files as unknown, question calls only from real
  `request_user_input*` tool calls, a 30 s quiet check with two stable stats,
  and UTC→KST display. `peer_link.py` discovers Orca terminals read-only and
  sends one fixed alert line only through an exact argv allowlist, behind
  target, record, quota, context and idempotency gates, dry-run unless
  `--send`, never resending. `peer_setup.py` previews protocol files (creates
  missing ones only), compares MCP transports without secrets and reports
  free memory. The raw Orca terminal-send block and its tests are unchanged.
- Document the peer protocol, trust boundary (peer text is data; a peer's
  "Simon GO" needs user confirmation), git-less folders, the session watcher
  versus daemon distinction and the unverified `orchestration send` and
  `@worktree` paths in `references/peer-sessions.md`.
- From usage feedback: show per-lane availability and continue on the current
  host when no external lane is dispatchable; list the only reasons to stop and
  ask; add a GUI fallback ladder; strengthen the completion report; batch
  progress summaries; report the running-versus-source version gap
  (`version_gap.py`).
- Mark quarantined (⛔) and outside-allowlist (⚠) prescriptions in
  `references/pitfalls.md` with a regression test; make `check_tooling.py`
  print UTF-8 and answer `--help` without side effects; align the SKILL.md,
  evals and CHANGELOG versions and check them with `version_gap.py check`.

## 2.12.1 - 2026-09-28

- Recheck current GPT, Claude, Gemini and Grok provider facts on 2026-09-28
  and refresh the seven-day model-registry evidence window. Public model
  support still does not establish subscription access or permit API billing.
- Explicitly warn that non-interactive Claude Fable can charge usage credits
  without a consent prompt; keep exact-model inclusion and overage gates.

## 2.12.0 - 2026-09-28

- Block pinned Gstack design API-key setup, generation and checks under subscription-only USD 0; require transitive local-command cost evidence.

## 2.11.13 - 2026-09-27

- Make Play Console and other GUI requests discover the `/vibe` coordinator
  even without a slash invocation. Check authorized CLI/API/MCP first and name
  only the actual `vibe-bot` adapter for GUI-only steps.
- Add a natural-language GUI routing evaluation and a description regression
  after a tool-less Claude subscription probe invented a nonexistent specialist.
  This metadata change is not a measured improvement in live selection accuracy.
- Add the exact skill-name question as a second evaluation. A follow-up
  isolated probe with `Skill` available selected the real `/vibe` on both the
  old and revised metadata. The tool-less probe disabled automatic skill use;
  it cannot establish a regression or a metadata-driven improvement.

## 2.11.12 - 2026-09-27

- Admit only locally measured Antigravity CLI 1.2.12 for zero-turn, zero-token
  `/usage` metadata collection. Keep account, model and billing verification
  unavailable; the observed quota buckets do not authorize generation.
- Record the installed CLI's rejection of `agy models --output-format json`;
  do not infer executable model routes from the text-only listing.

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
