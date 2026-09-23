# Guarded Orca workflow

## Contents

- Scope and current limits
- Intake
- Plan and prepare
- Dispatch and recovery
- Verification and cleanup
- Records and evaluation

## Scope and current limits

This workflow follows SKILL.md and the central orchestration contract.
The old model ladder is historical compatibility policy, not current account,
price, availability or transport evidence. Read the orchestration contract
linked from SKILL.md for exact request, runtime, certificate and Store schemas.

Default additional spend is USD 0. Grok generation remains held under the
user's explicit instruction until quota recovery and the required account/cost
evidence are established. A reset timestamp or cached ping is not recovery.
Do not change billing, credentials or subscriptions to make a plan executable.

Only the implemented guarded Orca adapter may start a supported worker.
It currently covers registered local Claude/Codex flag-effort lanes, not
prompt-keyword/ultracode, Antigravity, Grok, remote or direct CLI execution.
Unsupported work remains blocked; the current host may do separately authorized
work within its actual capabilities, without claiming a model/effort switch.
For example, an Orca plan requiring the legacy fixed ultracode synthesis lane
cannot currently pass the supported-adapter boundary. Do not substitute another
lane to claim the whole plan is executable; report the policy/adapter mismatch.

Legacy live functions `run_dispatch`, `run_codex_exec`,
`validate_and_dispatch`, `probe_orca_efforts` and adversarial live
preflight/run are disabled. No force flag, dry argv, shell command or manual
terminal submission bypasses that boundary. The raw `run_orca` helper accepts
only its exact read-only allowlist; it is not the dispatch adapter.

## Intake

Reuse an active request and previously supplied choices. Do not force a form
before a known task. A small task can stay in the current session.

The existing `make_intake.py` is not a read-only preview: its main entrypoint
can collect downloaded decisions, write the legacy ledger and create HTML.
Review those effects and the exact paths before using it. Its account/repository
queries do not establish billing or model availability. Historical model panels
are examples, not automatic assignments; stale live evidence yields no eligible
exploration candidates. Do not run intake merely to test a report.

## Plan and prepare

1. Identify relevant skills/software, scope, acceptance evidence and prohibited
   actions. Read the selected skills. Split deterministic operations from
   judgment; record dependencies and explicit independent reviewers.
2. Use observed central registry/runtime facts to select model and effort.
   Provider and transport effort allowlists must both admit the value.
   Unknown billing/quota excludes a route; quota pressure is not free usage.
3. Construct the complete plan, including both required security gates, review,
   retries and synthesis. Preserve legacy full-plan guard constraints as an
   additional filter. A new model ID cannot override those constraints.
4. Validate offline with explicit skill roots/exclusions. A blocked plan starts
   no nodes. Independent safe work needs its own valid scoped plan; do not
   silently drop blocked requirements and report the original task complete.

```text
python "<skill>/scripts/orchestrate.py" plan --root <explicit-skill-parent> --exclude-root <protected-path> --input request.json --runtime runtime.json
python "<skill>/scripts/orchestrate.py" ready --input plan.json --events events.json
```

Repeat root/exclusion flags for the actual scope. These commands do not create
native Runs/Tasks, reserve money or dispatch. A user asking only for a plan does
not authorize those side effects. Do not label arbitrary local commands free:
review their argv, dependencies, hooks and exact cost contract.

Before dispatch the plan needs a unique existing native Run/Task, exact Task
spec, workspace ID/path/instance, pinned Orca executable/runtime and a fresh
launch-account certificate. The adapter does not create these resources.
The central guarded native preparation lifecycle is not yet implemented.
If those prerequisites cannot be established through an independently reviewed,
authorized preparation path, report the gap and stop that node. Do not restore
the old raw run-create/task-create path to get around it.

The spec builder is an offline inspection aid:
```text
python "<skill>/scripts/execute_orca.py" spec --plan plan.json --node ID
```
Its output fixes the Task intent; it does not set the native Task spec.
Never accept an unrelated prompt or a Task with a previous Dispatch.

Do not run generation as a tooling probe. Version metadata alone does not
establish launch compatibility. A zero-CPU process is not proof that a worker
is stuck or safe to kill; a prompt or input field is not authority to submit it.
Updates and startup hooks can affect other sessions and require their own scope.

## Dispatch and recovery

Use the same canonical local Store DB and the existing immutable grant.
Register the complete plan to reserve all attempts and review costs atomically.
Never create another DB/grant to escape an exhausted allowance.
Do not manually claim a node before calling the adapter: claim and send belong
to that adapter invocation, and a committed no-send intent can remain unresolved.

For an already registered, eligible node with all preparation evidence:
```text
python "<skill>/scripts/execute_orca.py" dispatch --plan plan.json --node ID --db <shared-db> --certificate account-proof.json
python "<skill>/scripts/execute_orca.py" reconcile --plan plan.json --node ID --db <shared-db>
```

These are conditional execution commands, not offline validation commands.
The adapter repeats identity/freshness checks and calls Store.claim internally.
Only that fresh claim may send once. A saved dispatch_allowed flag, a dry
command or a successful planner result is not dispatch authority.

Persist the original dispatch identity. Reentry is lookup-only; timeout,
nonzero CLI exit, missing output or an unobserved turn do not prove non-acceptance.
Do not submit Enter, retry under a new Task/key, increase timeout and resend,
or use direct CLI as automatic recovery. Unknown acceptance or actual cost
keeps the reservation held until reconciliation. Retry requires terminal proof,
settlement, fresh preflight and the existing attempt/authorization limits.

Use exact resolved workspace identity; changing cwd does not establish where
an Orca worker will run. The adapter pins the executable rather than relying
on the legacy PATH runner. Read argv as data, never concatenate free text into
shell commands.

## Verification and cleanup

Accepted dispatch, turnStart, worker_done prose and exit zero are not completion.
Require matching native Task/Dispatch/workspace identity and terminal state;
record requested model/effort separately from resolved model/effective effort.
Applied launch settings are not proof of internal model reasoning or an invoice.

Inspect actual output, handle clipping and attach acceptance evidence. The
adapter's digest is not content review. A writer's result is output-ready only;
general/transitive successors wait for all explicit reviewers. The writer and
its independent reviewers must have different model vendors. Grok and Grok Bot
are both xAI; another same-host agent is not cross-vendor evidence.
Preserve artifact-safety and authorization/business-logic gates and their
separate-model constraints. Missing review routes block approval, not the rule.

For UI work use the repository's actual preview command and available approved
viewer, inspect pixels and accessibility evidence, and retain requested human
approval. Do not assume Expo, a port, a browser capability or screen visibility.
Only genuinely GUI-only operations belong to the separate vibe-bot adapter.

Actual cost settlement is distinct from output acceptance. Unknown actual_usd
stays null and retains its reservation. A subscription label, quota delta or
short answer is not a zero-cost receipt. Report provider overspend if observed.

Cleanup is not automatic. The adapter does not stop, abandon or release workers,
switch native Runs, delete worktrees or alter payment settings.
`kill_worker.py --kill --fence` is prohibited pending repair of handle/dispatch
identity and authorization; raw worker-stop is disabled too. A timeout or low
CPU is not permission to kill a process. Preserve dirty worktrees and obtain the
applicable exact-target authorization before destructive action. No daemon.

## Records and evaluation

Keep central durable state for every node, reservation, observation, receipt
and verification. The legacy routing ledger only accepts its existing worker
schema; do not put Bot lanes, credentials, output bodies or new money fields
into it. Link records with run/node identities and read partial/CAS failures.
Do not commit other agents' records or silently consume files as a dry test.

For actual Orca decision rounds retain the decision-sheet/acceptance process.
A generated sheet is not a worker result, measured adoption or user approval.
Legacy aggregation can propose a change only from suitable measured rows;
it cannot activate routes or override current registry/account/cost gates.
Exploration must satisfy the same authorization, budget, availability and
verification requirements; no eligible alternative means no exploration.

The old direct-CLI adversarial runner is quarantined. See the evaluation
reference linked from SKILL.md for offline command effects and measurement
requirements. Schema/dry/fixture PASS is not per-skill live behavior evidence.

Report plan, dispatch, received result, verification and settlement separately.
Include blocked/skipped work, actual unknowns, remaining cleanup and evidence.
Do not mark five-surface integration, all-mode optimization or installed parity
complete from this source workflow. Historical troubleshooting remains in Git
history; old pitfalls/effort-cap instructions cannot override these boundaries.
