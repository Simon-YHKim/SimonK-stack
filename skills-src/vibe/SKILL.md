---
name: vibe
description: 'Use when asked for SimonKStack "메인 오케스트레이터", "/vibe", "바이브로 알아서", Play Console/GUI orchestration, or task-wide skill/model/effort routing. Produces one verified plan and artifacts under $0 extra spend. Check CLI/API/MCP first; simonk is sprint-only and vibe-bot GUI-only.'
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 2.12.38
author: simon-stack
---

# vibe — Main skill orchestrator

Simon supplies an outcome. Own skill selection, software selection, model and
reasoning allocation, execution, verification and reporting until that outcome
is met. Use Claude, Codex (GPT), Antigravity (Gemini), Grok and Grok Bot as five
execution surfaces, not five independent model vendors.

## Entry points

- `/vibe <task>`: use the current context, make a small plan, then execute.
- `/vibe`: resume the active request when one exists. If there is no task,
  create the existing intake form or ask for the desired outcome once.
- `/vibe 실행 …`: consume the supplied task and choices without another form.
- `/vibe-bot`: remains a compatible direct entry point. Under /vibe it is the
  internal GUI adapter; the user does not need a second invocation.
- An explicit request for a report or plan ends with that artifact. A build/fix
  request continues through implementation and verification.

Default to `balanced`, two attempts per task, two simultaneous external tasks
and **USD 0 additional metered spend** unless an existing user-approved budget
covers this run. An approved budget persists within its original scope.
Quality preference is not spending authorization.

## 1. Discover the needed skills and software

Run `python -B "<skill>/scripts/orchestrate.py" catalog` to inspect skill metadata.
For separately installed plugins, compose explicit roots from the current host's observed, authorized paths before invoking the helper.
Own this step; do not ask Simon to maintain paths already supplied by the host. Follow the split-home procedure in [discovery](references/orchestration.md).
Inside an intact five-plugin candidate, default catalog/plan uses that bundle's
five skill roots only. Its receipt, planner, manifests and SKILL metadata must
match; missing/drifted inputs stop discovery without falling back to home.
For the D-29 Codex general-skill subset, accept the five documented safety-skill
omissions only when `subset.json` matches the verified overlay's exact members.
This metadata check is not full package, installation or host-behavior verification.
This is candidate discovery, not approval to install or execute its skills.
For other layouts, root order is the current skill's sibling directory, then .agents,
.codex, .claude and .codex/skills/.system roots. Supply repeated `--root` flags
for other flat parents, including plugin skill directories. First declared
name wins; alternatives and resolved aliases remain visible. Before scanning,
pass `--exclude-root` for protected repositories/backups: exclusion also applies
to symlink targets before content reads. Nothing is recursively imported.

Use `inventory` with explicit roots for scope/errors, and `coverage` with
explicit source, plugin and installation roots to detect missing/shadowed/drifted
SKILL files. Read the [discovery contract](references/orchestration.md) for the
CLI and trusted current-host snapshot format. Host-native skills keep their exact
qualified names and resource URIs in typed bindings, not filesystem paths.
Only the matching, freshly observed host may plan them; workers cannot inherit
the host's resource access. Discovery never establishes behavior or cost.

Honor user-named skills, then use descriptions to select the smallest complete
set. Read each selected SKILL.md and its required references before execution.
Do not load every skill body. Do not restrict discovery to a hardcoded list or
a historical skill count. Missing skills are explicit blockers for their step.
For GUI requests, enter through /vibe even without a slash invocation, check
CLI/API/MCP first, and name the actual discovered vibe-bot adapter only when
the step is GUI-only. Never invent a specialist skill name from a console name.

Treat `simonk`, `app-dev-orchestrator` and `dev-orchestrator` as procedures
owned by the current coordinator. Reuse their planning and verification; never
spawn a second coordinator or recursively invoke /vibe. Carry ancestor skill
IDs into child handoffs. Ordinary leaf skills can be composed freely.

Check actual CLI/API/MCP availability and credentials without printing secrets.
Deterministic scans, builds, tests, conversions and file operations use the
appropriate software directly. Small reasoning tasks stay in the current
session when its observed capabilities suffice. Independent substantial tasks
can use workers. GUI-only steps use the Bot adapter in section 4.

## 2. Plan model, effort and cost together

Read [orchestration contract](references/orchestration.md) before constructing
a run. The helper implements metadata discovery, route preflight, dependency
readiness and Bot result checks; the host executes its handoffs.

For each node record its outcome, selected skills, dependencies, needed
capabilities/software, scope, acceptance evidence, writes, demand level and
verification relationship. Use unique node IDs even when two nodes share the
same legacy process (for example coding).

Supply a runtime snapshot from observed local catalogs and transport probes.
Model IDs, provider-supported efforts, transport-supported efforts, billing
mode, quota, lifecycle and observation evidence are data, not guesses.
Use `scripts/runtime_collect.py --surface <name>` for explicit, one-shot CLI
metadata collection; repeat `--surface` for other providers. Read the runtime
snapshot section of the orchestration contract for its safety boundaries.
Metadata-only candidates stay unavailable until separate generation, billing,
model-to-quota and task-policy evidence is verified. This collector does not
dispatch tasks, change payment settings or prove zero-cost model access.
Grok's no-auto-update model list is metadata only: listed models have no
verified CLI effort, account binding or subscription inclusion.
Do not turn a newly announced model into an active route without availability
and transport evidence. Do not inherit an old model's effort mapping blindly.

Routine, reasoning and critical demand map to provider-specific effort values.
Both the model and the transport must support that value. The current host
cannot silently switch itself to the requested model or effort: reuse it only
when its actual settings match, otherwise use a verified worker.
Record requested effort separately from effective effort; unknown stays null.
Bot model/effort remains provider-managed unless a real control is verified.

Classify by deliverable before choosing a model. The planner accepts
`PLAN_ARCHITECTURE`, `CODE_COMPLEX`, `CODE_SIMPLE` and `WRITING` as distinct
model-fit profiles in addition to its older category IDs. `IMAGE_GENERATION`
is a separate image-tool profile. Typed profiles set minimum
capabilities and routine/reasoning demand; a high-stakes node may explicitly
raise demand to critical. `proc` is a legacy Orca guard label, not a claim that
planning or writing performed web research. A named, discovered Core
`model-router` may supply a dated shortlist, but `/vibe` still owns eligibility,
the single budget and execution. If it is absent, use the same criteria without
inventing a skill binding.
For coding, effort and quality are separate: `CODE_SIMPLE` starts at routine
effort but requires observed quality tier 2 or higher; `CODE_COMPLEX` starts at
reasoning effort and requires tier 3. A caller may strengthen but not lower
these quality floors. This prevents quota optimization from silently choosing
an underqualified model. Quality tiers are runtime evidence, not inferred from
a model name or benchmark headline.

| Deliverable | Advisory starting points, never active routes | Initial reasoning |
| --- | --- | --- |
| Architecture / ambiguous plan | Claude Opus 5.5 or GPT-6 Astra | reasoning; critical only for consequential, falsifiable decisions |
| Difficult, multi-file coding | Claude Opus 5.5 or GPT-6 Astra; scoped Sonnet 5.5 if it meets the quality floor | reasoning; escalate after bounded failure or demonstrated risk |
| Focused bug fix | Claude Sonnet 5.5 or GPT-6 Sol | routine, then raise only if tests or ambiguity require it |
| Polished writing | Claude Sonnet 5.5; Opus 5.5 for complex judgment; GPT-6 Sol when eligible | reasoning, not automatic max |
| Bulk transform | Deterministic software first; then an eligible light model such as GPT-6 Luna | routine |
| Image creation/editing | A real image-generation skill/tool with verified subscription inclusion | tool-managed; text models only plan or critique |
| Recent X discourse | Verified Grok CLI or current-host browsing, corroborated with primary sources | reasoning if controllable |

The [model-release watch](references/model-release-watch.md) records the dated
sources and shadow-effort limits behind this shortlist. Claude and Codex use
the same task/acceptance standard but may have different eligible routes.
`IMAGE_GENERATION` compiles to `kind=image`, never text-model `VISION`.
The planner accepts a current-host `host-image` route only with exact account,
interaction, entitlement, quota, disabled API/credit fallback, a provider-enforced
$0 hard cap and an atomic/idempotent host adapter. In-process `execute_image.py`
claims once and rechecks before send; it has no default host or CLI and never
settles or verifies output. See [orchestration](references/orchestration.md).
The exposed `image_gen__imagegen` lacks that hard cap and request lookup, so
`IMAGE_GENERATION_REQUIRES_VERIFIED_TOOL` remains blocked. Do not fake an
observation, substitute an API wrapper or call it under the $0 policy.

The source-dated [task-fit hypothesis](references/task-fit-policy.json) is
deliberately **shadow-only**. For `PLAN_ARCHITECTURE`, `CODE_COMPLEX`,
`CODE_SIMPLE` and `WRITING`, the planner checks its exact model/effort entry
only after all route-eligibility guards, preserves monetary and >80% quota
priority, then emits `shadow_task_fit` with the policy digest, source URLs,
active candidate and advisory alternative. It does **not** change `route` or
authorize a worker. Expired, unmatched or unranked-winning evidence produces
no advisory alternative. `IMAGE_GENERATION` explicitly requires a verified
subscription-included image tool and must not be routed through text `VISION`.
Public manufacturer/Artificial Analysis claims are hypotheses across different
harnesses; direct X posts were inaccessible, so X contributes no rank. Promote
each task profile only after the same skill bundle, task, tools and rubric are
compared on Claude and Codex with exact model/effort and $0-extra-cost proof.
Until then `selection_quality_verified=false` and installation readiness stay
unproven even when the shadow alternative differs.

At invocation, use the [model-release watch](references/model-release-watch.md)
to refresh official-release evidence without model calls. A Friday local check
and subsequent pending checks only create candidates and unreviewed public-post captures; they do not alter a
route. For a newly released model, require a prospective 24-hour public
feedback window, exact subscription/effort evidence and same-task host tests
before updating the routing policy. A `review_ready` watch record is not a
validated model, installation or merge authorization. Existing work continues
on verified routes while a new model is pending.

Validate with:
```text
python -B "<skill>/scripts/orchestrate.py" plan --input request.json --runtime runtime.json
python -B "<skill>/scripts/orchestrate.py" ready --input plan.json --events events.json
```

For consequential `ai-debate`, supply a `debate` object with five distinct LLM
step IDs: `proposer`, `challenger`, `proposer_rebuttal`, `challenger_rebuttal`,
`judge`. Both rebuttals depend on both openings; the judge depends on both
rebuttals. The two openings need different vendors, and each rebuttal retains
its opening surface/account. The judge is a separate invocation even if its
vendor matches an opening. Give both openings the same question, evidence and
rubric; feed verified actual outputs into the rebuttals and judge.
`ready` releases successors only after verified predecessor evidence. A
five-node plan or simulated personas are **not** a completed model debate:
record the five actual dispatch/session identities, output evidence, minority
view and separate judge verdict. Missing subscription-safe execution for any
node blocks that debate; do not relabel a single-host simulation as Claude↔GPT
or borrow another vendor's quota. Formal hub D-code recording remains the
`ai-debate`/PROTOCOL requirement, not something this planner performs.

The output is a preflight decision, not proof of dispatch. Refresh runtime and
budget immediately before external execution. Reserve the entire run's upper
estimate, including attempts, reviews, coordinator calls and Bot work, before
starting a paid wave. Only one coordinator may own a run's budget.

Unknown price, billing mode or exhausted/stale quota excludes that route.
Subscription usage is not free: report included quota separately from extra
money. Zero incremental spend is valid only when the exact resolved LLM model (or
provider-managed Bot usage) is included in the subscription and both overage
and API fallback are verified disabled. Codex, Antigravity, Grok CLI and Grok Bot also need
separate proof that purchased-credit fallback cannot spend existing credits;
automatic reload OFF alone does not provide that proof.
For Antigravity and xAI, bind quota evidence to the exact surface,
transport and account. A reset clock or the other surface's quota cannot lift a
hold; reobserve the selected account and bucket before planning.
Unknown is blocked. Do not silently fall back to an API key, paid overage or
a new subscription.
With the default USD 0 grant, API/metered model routes stay blocked even when
a quote claims zero cost; this user's route is subscription usage only.

Choose among routes that meet the quality/capability floor, then minimize
incremental cost and quota pressure. Lower unnecessary effort, trim context,
reuse verified results, limit parallelism and cap retries before dropping
quality. Never remove required verification to reduce cost.

Before a Codex worker start, run `python -B scripts/check_tooling.py --local-codex`.
It compares the PATH-selected CLI with its adjacent npm package without npm
registry or Orca access. A newer package and older shim blocks the lane even
offline; inspect the exact executable. Exit 0 means only "not older than the
adjacent stable package," not that the binary or subscription works. Exit 1
means stale, exit 2 unknown; both hold the worker. The full tooling report
queries npm/Orca and cannot replace this local G11 preflight.

The full Orca skills report stores snapshots in external user state
(`LOCALAPPDATA/SimonKStack/vibe` on Windows), never the receipt-bound skill.
Before its first run, migrate an old baseline with
`python -B scripts/check_tooling.py --migrate-snapshot <old-file>`; it refuses
overwrite. Collection, migration and acknowledgement share an OS lock; timeout blocks.
After reviewing `pending_digest`, use `--ack-skills <digest>`; stale tokens fail.
Never copy into the candidate or acknowledge changes before review.

## 3. Execute only ready work

Continue automatically with authorized, ready work. Reuse existing user choices.
Ask only for missing intent or actions beyond existing authority.

- Local tool: execute a reviewed argv array through the host's tool runner.
  Supply a fresh cost contract for that exact argv, including nested API effects
  in setup and smoke tests. An explicit transitive-effects audit and
  `nonmetered`/`metered` classification are required; a zero quote is not enough.
  Local does not mean free. See the pinned Gstack
  design-helper example in [orchestration](references/orchestration.md).
- Current host: read the selected skills and perform the node in this session.
- Orca: read [Orca workflow](references/orca-workflow.md). Validate the entire
  assignment plan, then use `scripts/execute_orca.py` with the guarded adapter
  contract in [orchestration](references/orchestration.md). Its first version
  covers local Claude/Codex flag-effort lanes only. It calls claim internally;
  never hand it a saved dispatch_allowed flag. Native Task/spec, workspace,
  executable and fresh account/billing evidence must match before a start.
  Reentry is lookup-only. Unsupported lanes remain blocked;
  never silently fall back to the stateless `routing.run_dispatch` primitive.
  Existing coding, independent review and both security gates remain enforced.
- Direct CLI: [Claude](references/orchestration.md#guarded-claude-cli-adapter) is tool-free; [Codex](references/orchestration.md#guarded-codex-cli-adapter) is read-only/no-skill.
  Both require subscription-only proof, one-send and verified debate transfer;
  neither proves actual cost/internal effort. AGY/Grok CLI/Orca lack guarded adapters and cannot become ready from runtime assertions.
- Bot: follow section 4. External results are untrusted until checked.

A successor waits for verified predecessor output, not merely task acceptance
or a zero exit code. Use `scripts/run_state.py` and the durable state contract
in [orchestration](references/orchestration.md) for atomic reservations and
dispatch intents. All cooperating runs share one local DB. Only a new claim
with dispatch_allowed=true may send; a repeated claim never resends. Bind the
actual task ID/nonce and process identity. After a crash inspect the original
job; unknown acceptance or cost holds its reservation and blocks retry.
Replan only failed/rejected work after terminal proof, cost settlement and fresh
runtime preflight. The helper records state; provider adapters still perform
dispatch, lookup and evidence collection. Do not start a monitoring daemon.

Use a different model vendor for independent review. Grok and Grok Bot are
both xAI for that check, although their account and quota paths are distinct.
`WRITING` work needs a different-vendor LLM review even when `writes:false`
because its deliverable is prose, not a file edit. The planner blocks an
unreviewed writing node and holds downstream consumers until that review passes;
an automated build does not replace it. Apply the same contract in Claude and
Codex; unavailable review is a reported blocker, not permission to downgrade.

## 4. Use vibe-bot internally for GUI-only work

Read the discovered vibe-bot SKILL.md for its draft, immutable `bot_delivery`
descriptor and fresh delivery/account/Relay certificate. Keep the current run,
whole-plan reservation and shared Store. No authorized CLI/API/MCP alternative
may be available; execution needs an observed active exact roster entry.
The planner accepts only the exact live status `active`; a roster snapshot
description beginning with "active - reported" is not live availability.
Use the current Bot organization reference: all new deliveries/results use
Relay, while the selected specialist remains bound in the plan. Team requests
go through Relay; historical specialist runs retain their original adapter.
Draft privately while delivery is blocked. Drafting, pasting into chat and
publishing to a watched bus are different effects; only drafting is local-only.
Never use the builder's retired hub/webhook/github/--send paths or manually
preclaim. The central adapter owns claim and publication together:
```text
python -B "<skill>/scripts/execute_bot.py" dispatch --plan plan.json --node screen --db shared-runs.sqlite3 --certificate bot-evidence.json
python -B "<skill>/scripts/execute_bot.py" reconcile --plan plan.json --node screen --db shared-runs.sqlite3
python -B "<skill>/scripts/execute_bot.py" check-result --plan plan.json --node screen --db shared-runs.sqlite3 --evidence screens.json
```
Reentry is lookup-only, never a new nonce or resend. Exact publication remains
waiting_external with unknown cost; it does not prove Bot acceptance. The legacy
`orchestrate.py verify-bot` and builder `--verify/--collect` do not bind the Store,
plan or pinned helper and must not replace `check-result` for this workflow.
`check-result`'s result_checks_passed is structural evidence only: inspect actual screenshots
and task criteria, establish terminal and cost evidence, then observe/settle/
verify through the Store. Required reviews still apply. No automatic completion,
login/payment/Submit authorization, settlement or provider-model selection.

For an authorized ongoing Bot collaboration, follow the discovered vibe-bot skill's Relay handshake reference for saved-state watching, timely replies, duplicate-write checks and `교훈` results; existing approval gates still apply.

## 5. Account and finish

Keep an orchestration run-state for host/tool/Bot tasks, costs and evidence.
Keep the existing routing ledger for legacy LLM worker rows only; its strict
schema does not accept Bot lanes or money fields. Link both with run/node IDs.

Record billing mode, account reference (non-secret alias), quota bucket,
estimated upper amount, actual amount (null when unknown), tokens/credits when
reported, retries, requested/resolved model and requested/effective effort.
Grok CLI and Grok Bot do not share a budget bucket unless observed evidence
establishes it. Reasoning tokens already included in output billing are not
charged twice in estimates.

Provider costs can exceed estimates. Set real provider output/spend caps when
available; pause new paid work if observed spend breaches the run budget.
The planner's reservation is not a provider-enforced billing hard cap.

Mark a node done only after checking its own output and attaching evidence.
For a writer this means output-ready, not approved: only its explicit verifiers
may consume it until all required LLM reviews pass. General and transitive
successors remain blocked. Declare the whole task complete only after those
reviews and the user's acceptance criteria pass.
For Orca rounds retain the existing decision sheet, ledger and release steps.
Report the result, verification, selected routes, additional spend, subscription
usage, and remaining waiting/blocked work. Never call an accepted job complete.

## Legacy Orca routing

Legacy live entrypoints are quarantined: `run_dispatch`, `run_codex_exec`,
`validate_and_dispatch`, `probe_orca_efforts`, and adversarial evaluation live
`--preflight`/`--run`. Dry builders remain simulations, not execution or cost
proof. Legacy plan validation treats omitted quota checks as G5, never as
permission to dispatch; a dry simulation is not evidence of checked quotas.
The raw Orca helper accepts only a small exact read-only grammar; all
writes, including `worker-stop`, are disabled. `kill_worker.py` is a retired,
inert compatibility entrypoint: every request returns nonzero except standalone
help. It does not scan processes, terminate, fence or verify cleanup. No flag or
environment variable re-enables it. The G8 safe-stop requirement is still unmet;
retirement is not an implemented or authorized replacement stop adapter.

The Orca workflow, evaluation reference, pitfalls and effort-cap history now
mark retired live-call examples as non-executable. Historical observations are
not current cost or transport evidence. Do not copy raw CLI examples around the
quarantine. Use the guarded adapter only where
its actual capabilities and fresh account/cost evidence permit it. A schema2
preparation journal and host-injected protocol core now exist. There is no
operational preparation bridge or CLI: `prepare_orca.py` requires a reviewed
host and cannot instantiate the raw Orca runner. Its default owned-v1 contract
is unchanged. Explicit observable-v2 PC trust records the user's decision and
matches native session/Run/Task/request observations without claiming process
ownership or loaded-code attestation. A separate, scoped native-effects grant
is still required; trust approval does not authorize DB initialization or sends.
Missing preparation evidence blocks dispatch, not permission to use old helpers.
Read the preparation contract before integrating this library. Fixture evidence
does not establish a live caller, loaded runtime, OS isolation or free access.
An explicit schema3 validation overlay permits same-intent runtime freshness
renewal without resetting native UUIDs or reservations. It requires a newly
validated central plan; never edit timestamps to bypass expired evidence.
Registry/model/account/budget changes and operational migration remain outside
this renewal path. Expired or unresolved work never authorizes a replacement run.

The generated table is historical compatibility policy, not present-day availability, and cannot bypass central guards.

Read the [generated legacy Orca routing table](references/legacy-routing.md) only for historical policy.
The current registry, runtime and transport/account guards decide present-day routes.

## Verification and references

```text
python -B "<skill>/scripts/test_runtime_collect.py"
python -B "<skill>/scripts/test_run_state.py"
python -B "<skill>/scripts/test_execute_orca.py"
python -B "<skill>/scripts/test_model_registry.py"
python -B "<skill>/scripts/test_orchestrate.py"
python -B "<skill>/scripts/test_execute_codex_cli.py"
python -B "<skill>/scripts/selftest.py"
python -B "<skill>/scripts/sync_skill_table.py" --check
# Process-denied preparation fixtures, from the skill's scripts directory:
python -B -m unittest discover -s tests -p "test_prepare*.py"
# Secret detection equivalence/latency; denies child processes and networking:
python -B -I -S tests/test_ledger_scan.py
```

When testing an immutable bundle, also set `PYTHONDONTWRITEBYTECODE=1` for
child Python processes and reverify its receipt afterward. `-B` on the parent
command alone does not propagate to subprocesses. Plain Python invocation of
legacy CLI entrypoints now blocks bytecode before their first local import;
module imports by other callers still need the caller's own no-bytecode policy.

- [Orchestration schema and cost policy](references/orchestration.md)
- [Guarded Orca workflow and preparation limits](references/orca-workflow.md)
- [D-28 route decisions](references/d28-routing.md)
- [Astra effort transport cap](references/v2.2-astra-effort-cap.md)
- [Adversarial evaluations](references/adversarial-eval.md)
- [Operational pitfalls](references/pitfalls.md)
