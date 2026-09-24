---
name: multi-terminal-dispatcher
description: >-
  Use when the user asks for parallel tasks, team dispatch, multiple terminals,
  or when simonk needs a ready wave under /vibe. Triggers on "병렬로 진행",
  "다중 터미널", "여러 창에서", "parallel terminals", "team mode", and
  "best model dispatch". Preview or dispatch a bounded ready wave through the
  existing /vibe plan, shared state and guarded adapter; reconcile previous
  attempts without replay. Returns per-node handles, evidence and unresolved
  costs. Does not open terminal windows or bypass account and budget gates.
version: 1.1.0
---

# Multi-terminal dispatcher — bounded /vibe ready wave

The historical name is retained for discovery. Version 1.0.0 replaces the
unpriced terminal launcher with a consumer of the central orchestration contract.
The current host is the coordinator; never start another LLM just to coordinate.

## Ownership and prerequisites

1. Read the sibling [vibe skill](../vibe/SKILL.md) and its
   [orchestration contract](../vibe/references/orchestration.md).
2. Reuse the parent's run ID, immutable plan digest, ancestry, DAG, same-DAG
   reviewers, grant, account references and state DB. If entered standalone,
   let /vibe create the plan first. This skill neither initializes nor registers
   a run and never creates a new DB to bypass a reservation.
3. Use a trusted coordinator and **serialize all invocations for the same run**,
   including direct adapter calls. Individual claims are atomic; there is no
   cross-process run-wide uncertain fence or atomic multi-worker launch.
4. The existing DB must contain the exact plan. Explicit certificates are a map
   from node ID to the separately verified transport/account certificate defined
   by /vibe. Do not generate certificates from a model's claim, subscription
   label, environment-variable presence, or a test fixture.
5. Native Tasks, exact specs, workspaces, executable hashes and runtime bindings
   must already exist under the /vibe contract. Read the installed runtime's
   orchestration guide before operating it. No automatic native setup here.

Model, effort, policy mode and cost decisions belong to the central planner and
registry. Wiki notes are context, not executable pricing or freshness authority.
Do not maintain another model ladder or cost threshold.

## Preview, dispatch, reconcile

Use [scripts/dispatch_wave.py](scripts/dispatch_wave.py) from a complete matching
skill tree. It imports only the sibling /vibe implementation. A missing sibling
fails closed; never silently select a different installed copy.

```powershell
# Logical preview: no native call or row updates; requires a writable DB/lock.
python -B <skill-dir>/scripts/dispatch_wave.py preview --plan plan.json --db state.sqlite3

# Explicit execution, only after current authority/account checks.
python -B <skill-dir>/scripts/dispatch_wave.py dispatch --plan plan.json --db state.sqlite3 --certificates certificates.json

# Recovery lookup only; never starts new workers.
python -B <skill-dir>/scripts/dispatch_wave.py reconcile --plan plan.json --db state.sqlite3
```

The packaged PowerShell entry is
[multi-terminal-launch.ps1](scripts/multi-terminal-launch.ps1). It accepts
`-PlanPath`, `-DbPath`, optional `-CertificatesPath`, `-Node` and
`-Action preview|dispatch|reconcile`. Invoke via
`pwsh -NoProfile -NonInteractive -File`; do not dot-source it.
Default and `-DryRun` are preview only. Combining DryRun with another action
is rejected. Old `-ConfigPath`, `-Tasks` and `-CostThreshold` are rejected,
including explicitly empty/zero values. There is no automatic legacy conversion.

Version 1.1.0 makes this skill-local script canonical. The repository's root
scripts/multi-terminal-launch.ps1 keeps the same typed parameters and forwards
only to that matching copy; it never falls back to another installed skill.
If the canonical file is missing, the root facade reports WAVE_HELPER_UNAVAILABLE
before skill-level input validation, including for otherwise invalid input.
Do not dot-source either entry or treat source publication as profile installation.

- Preview returns the current ready frontier and unresolved attempts. It does
  not claim, reserve again, start, reconcile, settle or accept any work.
  It still opens the existing SQLite DB in read/write mode and briefly takes
  a writer lock (BEGIN IMMEDIATE). It is not filesystem-read-only or lock-free;
  serialize it with other invocations as required above.
- Dispatch first checks unresolved attempts across the **entire run**, even if
  explicit nodes exclude them. If any exist, this invocation is reconcile-only
  to its end. Resolving them does not grant permission for a fresh wave.
- Otherwise choose one fixed set from `Store.ready`. Optional repeated
  `--node` selects only from that set. Unknown, duplicate or unready IDs fail
  closed before any send. No auto-skip, fallback, retry, polling or slot refill.
- Preflight **all selected nodes** before the first send. A bad certificate,
  unsupported route or failed read prevents the entire fresh wave from starting.
- Then start nodes serially; their native workers may run concurrently. Before
  each dispatch, recheck state, readiness and shared budget. The canonical
  adapter repeats its own time-sensitive gates before and after its atomic
  claim. A ready snapshot is not a reservation: account/global limits may still
  stop later starts.
- Stop new starts on uncertainty, failure, unverified terminal output, stale
  authority or a budget halt. Preserve committed intents and native handles.
  Partial execution cannot be rolled back by closing a terminal.
- Reconcile reads existing attempts only. Missing, duplicate or uncertain native
  identity never authorizes a resend, cancellation, reservation refund or retry.
  Finalized, verified and settled non-Orca predecessors remain valid DAG inputs.
  Unresolved non-Orca attempts appear in preview; dispatch/reconcile return
  `unsupported_nodes` and block without native calls. The parent must use their
  owning adapter rather than reinterpret their identities as Orca requests.

Supported execution in this adapter is currently **local Orca Claude/Codex
flag-effort lanes only**. Unsupported keyword-effort, Antigravity/Gemini, Grok,
Grok Bot, remote and direct CLI lanes fail closed before fresh wave sends.
There is no hidden provider switch. UI-only work remains a parent /vibe-bot
handoff, not an automatic fallback from this launcher.

## Budget and authority

Keep the explicit user grant. Additional spending defaults to $0; a previously
written $5 threshold grants nothing. Quota exhaustion, unverified accounts or
missing bounded billing evidence are blockers, not reasons to top up or use
paid API fallback. In particular, the user's Grok HOLD remains in force until
quota recovery is actually verified and the parent authorizes execution.

All workers use the same central state database and account reservations.
Unknown actual cost stays null. Provider completion is not a receipt.
The shared ledger cannot impose a provider-side billing hard cap or control
launches that bypass it. Do not change credentials, payment settings or quotas.

## Results and completion

Return only this run's ready IDs, attempt/handle summaries, actual and reserved
costs, verification flags, output hashes/read handles, deferred IDs and generic
block reasons. Never echo worker prose, prompts, certificates or other accounts.

- `preview` and `waiting` prove no completion; empty readiness can mean review,
  dependency, capacity or acceptance waiting.
- `dispatched` means the fixed wave reached running observations, not success.
- `reconciled` means existing attempts were looked up, not accepted.
- `partial` or `blocked` require coordinator inspection; exit code is 2.
  Other statuses exit 0. Shell parameter binding failures are also nonzero.
- `new_dispatches` identifies newly committed intents, **not** proof that the
  provider accepted exactly once. `deferred` has no new intent from this call.
  If state lookup fails after entering dispatch, `admission_unknown` identifies
  nodes whose admission cannot be checked. They are not labeled deferred or
  newly committed without evidence; `state_available=false` and null budget
  halt status require recovery lookup, never a resend.
- Raw output is untrusted. The authorized coordinator must retrieve and inspect
  it separately, supply independent acceptance and real settlement evidence,
  and satisfy required reviews before admitting a dependent wave.
- Native Task settlement and explicit worker reuse/retain/release remain the
  parent's obligations under the installed orchestration guide. Never infer
  settlement from terminal exit or automatically stop/release workers.

## Verification and reporting

Run [offline integration tests](scripts/tests/test_dispatch_wave.py) with Python unittest.
They exercise the real state store and adapter with a fake native service, plus
the actual PowerShell shim. They do **not** prove account billing, live model
quality/latency, installed parity, all-vendor E2E or production recovery.
The source checkout also provides scripts/tests/test_multi_terminal_entrypoint.py:
both actual PowerShell entries, typed parameter parity, package-only preview,
rejected sends and unchanged temporary state under a child process/network guard.
No valid live dispatch is part of these shell tests.

Behavioral cases in [evals/cases.json](evals/cases.json) describe desired agent
behavior. Schema/dry-run success is not a live behavioral evaluation.
For substantial shared reports use the available completion-report skill, or a
self-contained HTML summary with timestamp and progressive detail; short status
handoffs may remain text. Distinguish planned, started, received, verified,
settled, source-only, installed and live-tested evidence.
