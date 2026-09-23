# Main orchestration contract

## Contents

- Ownership
- Request schema
- Runtime snapshot
- Budget and selection
- Execution and evidence
- Durable state and recovery
- Guarded Orca adapter
- Completion boundary

## Ownership

The host LLM interprets the request, reads selected skills, and executes work.
`orchestrate.py` is an offline preflight/readiness helper, not an autonomous
daemon or a replacement for provider-specific dispatch. It does not fabricate
runtime observations or send tasks. The host owns one run and its budget.

## Request schema

```json
{
  "run_id": "unique-run-id",
  "ancestor_skills": [],
  "budget": {"mode": "balanced", "approved_usd": 0, "spent_usd": 0,
             "external_reserved_usd": 0, "max_attempts": 2, "max_parallel": 2},
  "steps": [{"id": "inspect", "task": "Explain the repository structure",
             "kind": "llm", "skills": ["explain"], "needs": ["reasoning"],
             "demand": "routine", "depends_on": [], "writes": false}]
}
```

`kind`: local, llm or gui. A local node supplies an `argv` list and `software`
names checked against runtime tools. Runtime tool_costs must include the exact
argv_sha256 (`orchestrate.digest(argv)`), verified=true, evidence, observed_at
and upper_usd_per_attempt. Local execution does not imply zero cost. A GUI node supplies target, gui_reason,
tool_route_available=false and vibe-bot in its skill list. `verify_of` names
the predecessor being independently reviewed and must also be a dependency.
The host includes scope and acceptance evidence in each task handoff. It must
include every billed coordinator, review and synthesis call in the plan.

## Runtime snapshot

Pass `candidates`, `tools`, `observed_at`. Each candidate has a unique id,
surface (claude/codex/antigravity/grok/grok-bot), transport (host/cli/orca/bot),
model, lifecycle=active, available=true, observed_at and evidence.
Declare capabilities, quality_tier (1 routine, 2 reasoning, 3 critical),
resource_rank, provider_efforts, transport_efforts and effort_by_demand.
These are observed/configured facts, not inferred from a model name. Candidate
observations and quota have a conservative 15-minute validity window.

Billing fields are `mode` (subscription/api/metered/unknown), `verified`,
`account_ref`, and `extra_usage_enabled`. Included subscription routing requires
verified=true and extra_usage_enabled=false. A paid candidate supplies
upper_usd_per_attempt including reasoning, tool use and transport charges.
The quote belongs to this task/run snapshot, not a permanent model price.
Quota supplies used_pct, observed_at and an optional bucket ID. Unknown is null,
never zero. Both quota exhaustion and unverified billing exclude the route.

Demand maps to an actual provider-specific effort. Its value must appear in
both effort allowlists. Host reuse additionally requires a matching observed
effective_effort; the helper cannot change a running host. A Bot candidate uses
transport=bot, bot_id, bot_status=active and gui capability; model and effort
are null if the provider does not expose them.

For Orca supply proc/class per node plus quota_checked_vendors and quota_states
in runtime. The existing complete-plan guard must pass. Legacy gates remain
in effect; newly announced model IDs cannot bypass them through this helper.

### One-shot metadata collection

```text
python "<skill>/scripts/runtime_collect.py" --surface codex --surface claude
python "<skill>/scripts/runtime_collect.py" --surface grok --surface antigravity
```

Select surfaces explicitly. The command prints one redacted JSON snapshot to
stdout and exits 2 if any selected surface fails. It does not save credentials,
install software, dispatch work or start a daemon. Exit 0 means the metadata
request succeeded, not that a model is available or a task was completed.
Account/profile references are opaque hashes, not authentication credentials;
do not publish them as anonymous identifiers. Raw provider errors are omitted.

| Surface | Read-only observation | Not established |
| --- | --- | --- |
| Codex | Same app-server connection: profile match, account before/after, model/list, rate-limit and credit buckets | Generation, model-to-quota binding, disabled overage/API fallback |
| Claude | auth status --json; observed identity and subscription type | Model access, quota, per-model inclusion, extra usage |
| Grok | ACP billing; alternate method only after method-not-found | Missing account identity or overage flag; no session/prompt |
| Antigravity | Version-gated /usage, successful command, zero turns and all token counters zero | Account identity, model access and billing authorization |

Antigravity accepts only locally measured /usage contract versions. An unknown
version stops before sending the slash command. A nonzero turn/token response
fails closed without retry; it cannot undo usage already reported by that CLI.
Grok billing metadata may be read while generation is suspended, but quota
recovery must be observed again before reconsidering a route. A reset timestamp
is not proof of recovery. Grok Bot has no collector here and never inherits the
CLI account/quota. Claude Widget bridge data is not joined without identity and
bucket-binding evidence. No provider's subscription label proves a free model.

Only models actually returned by Codex model/list and present in the registry
become candidates; this is not an exhaustive cross-provider model inventory.
All collected candidates have available=false, billing.verified=false, unknown
model quota and no effective model/effort. Keep those gates until separate
evidence establishes them. The planner reads the central registry by default;
API capabilities and CLI-reported efforts are distinct constraints.

The collector uses an allowlisted child environment and a temporary working
directory. It bounds stdout, writes and process lifetime. Windows probes start
suspended inside a kill-on-close Job Object before their code can run; POSIX
probes own a process group. Cleanup targets only the probe's own tree, including
descendants that outlive its root. Server tool/auth requests are refused, not
executed. An unavailable containment primitive fails closed. Offline subprocess
tests cover timeouts, inherited pipes, hostile request IDs and environment
filtering. These are transport-safety tests, not provider generation canaries.

## Budget and selection

Default: balanced, USD 0 additional billing, two attempts, two concurrent jobs.
Filter capability/quality/effort/availability first. Among eligible candidates,
minimize the full-attempt incremental bound, avoid quota pressure above 80%,
then use the declared resource rank. Quality mode raises the routine quality
floor; it does not authorize paid calls. API price equivalents are not actual
subscription spending. Never use an invented multiplier for high reasoning.

Reserve sum(per-attempt bound × max_attempts) for all nodes, plus already spent
and externally reserved amounts, before dispatch. Keep failed-attempt spend.
Review and fallback work are not free; add their cost before starting them.
One coordinator owns each run. `run_state.py` serializes cooperating runs and
account reservations in one local database. This is admission control, not a
provider-enforced or cross-device billing hard cap. Outside CLI calls and a
different database are not covered.

## Execution and evidence

Save plan and event snapshots with the host's authorized file tools. Events
contain run_id, plan_digest, id, status, verified and evidence. A result from
another run or changed plan is rejected. Only done + verified=true + nonempty
evidence establishes output-readiness. For a writing node this does not establish
approval: only nodes with verify_of pointing to that writer may consume its
unapproved output. General successors, including transitive ones, wait for all
its required LLM reviews to finish successfully. A local test needed by a review
also declares verify_of; it does not replace that review. Persist running/waiting_external events before
dispatch and inspect their job IDs on resume to avoid duplicate work. Failed
nodes do not retry automatically; refresh runtime and budget first.

For Orca, validate the entire plan before every ready wave. Use node ID to map
to task ID/spec, then use the guarded adapter below for its supported lanes. Calling
validate_and_dispatch on the entire DAG starts later phases too early; calling
it on coding alone drops required security gates. Preserve its full-plan
validation before using the ready-node dispatch primitive.

Blocked plans start no nodes; independent safe work needs a separately valid
plan. A local test cannot substitute for an independent LLM reviewer.

For a Bot, read the resolved vibe-bot skill, select an active roster entry,
create the console spec and link nonce/meta/result paths to the run. Supply
verify-bot with --evidence pointing to JSON containing nonce, target and images
(PNG/JPEG paths inside the result directory). Inspect the images and apply
acceptance criteria; file/signature checks alone do not verify pixels. A missing
result remains waiting_external, even if collect returned exit code 0.

## Durable state and recovery

`run_state.py` is a one-shot coordinator utility, not a dispatcher. Its default
Windows DB is `%LOCALAPPDATA%/SimonK/vibe/runs.sqlite3`; elsewhere it uses
`~/.local/state/SimonK/vibe/runs.sqlite3`. All cooperating coordinators must use
the same canonical local fixed-disk DB. `--db` is for an explicitly scoped
alternative or isolated tests, never a way to bypass an exhausted grant.
Network paths, symlink files, unsupported journals/schema and corrupt DBs fail
closed. Never reset a failed DB or copy it while active to clear reservations.

SQLite rollback journal, synchronous=FULL and BEGIN IMMEDIATE make the run,
account, reservation and intent update one transaction. The grant is immutable:
initialize once with the existing authorized scope, default USD 0. A nonzero
grant requires an approval reference; the helper trusts the coordinator's
authorization evidence and does not itself obtain permission. Money is stored
as integer nanoUSD: approval caps round down, cost/reservations round up. Use
decimal strings for exact monetary inputs; lossy JSON numbers are rejected
instead of silently underflowing, overflowing or changing the approved amount.
Do not reuse one grant as a new allowance per run. Plan spent_usd and
external_reserved_usd cover costs outside this DB only, to avoid double counting.

```text
python "<skill>/scripts/run_state.py" init
python "<skill>/scripts/run_state.py" register --plan plan.json
python "<skill>/scripts/run_state.py" ready --run run-id
python "<skill>/scripts/run_state.py" claim --run run-id --node node-id --request stable-key --plan-digest digest
python "<skill>/scripts/run_state.py" status
```

Registration reserves the full run, all nodes and attempts, atomically against
run and shared grant limits. Account identity is the surface plus a non-secret
account_ref. Separate surfaces are not assumed to share a quota bucket. Pending
intents count toward concurrency (default two global and two per account).
`ready` and first `claim` repeat runtime, quota, billing, model/effort and
dependency checks. An identical claim returns its existing dispatch_id and
dispatch_allowed=false; a changed payload/key binding is rejected. Only a first
successful claim grants permission to send, after the intent is committed.

| Command | Trusted coordinator input / required evidence |
| --- | --- |
| bind --dispatch ID --input handle.json | Exactly kind, id, identity; original provider task ID or process ID plus start identity, not PID alone |
| observe --dispatch ID --input observation.json | state, observed_at, evidence, matching handle; resolved_model and effective_effort for controlled model execution |
| settle --dispatch ID --input receipt.json | actual_usd and nonempty evidence; unknown is not zero |
| verify --dispatch ID --input acceptance.json | evidence after inspecting output; observed model/effort must match the requested route |
| reject --dispatch ID --input rejection.json | evidence explaining why an unverified succeeded result failed acceptance |
| refresh --plan refreshed-plan.json | Same task intent/policy; refreshed route and runtime evidence, new plan digest |
| cancel or complete --run ID --input evidence.json | Nonempty evidence list, terminal execution and settled costs |

Input files contain JSON objects, with an evidence array where listed. Observe
accepts running, unknown, succeeded, failed or not_started; unknown becomes
uncertain. not_started requires a null handle, proof_kind=transport-not-accepted
and evidence from the transport. It still needs explicit cost settlement before
release. No timeout or process disappearance establishes non-acceptance.
Receipts and bound handles are immutable. Late observations cannot rewrite a
terminal result. Accepted output cannot later be rejected to create another try.

The external send cannot share the DB transaction. A crash after intent, or
after provider acceptance before handle binding, therefore leaves an unresolved
intent. Lookup using the original dispatch identity and bind that job; do not
automatically resend. If the transport cannot prove acceptance/non-acceptance,
pause that node for reconciliation. This is duplicate-send prevention, not an
exactly-once provider delivery guarantee.

Terminal execution and cost settlement are separate. An unknown actual amount
retains its reservation and blocks new admissions. Actual overrun is persisted
even when it exceeds the estimate, then further admissions halt. Verified,
settled success releases unused future attempts; failed/rejected attempts keep
their actual spend and remaining attempt allowance. Refresh is conservative:
no attempt in that run may still be active/uncertain or have unknown cost. It
preserves completed routes and cannot change intent, budget or max attempts.
Fallback gets a fresh plan digest and billing/account checks before another
claim. cancel only releases unused allowance after reconciliation. complete
requires every node, including all required reviewers, succeeded and verified,
all costs settled and the run budget satisfied.

Only the trusted coordinator writes this DB. Worker output is untrusted; inspect
and reduce it to evidence references, never feed raw responses or credentials
into these commands. Records reject sensitive keys/patterns, duplicate JSON
keys, non-finite numbers, oversized/deep structures and malformed JSON embedded
in strings. This guard is not a comprehensive DLP or hostile-user security
boundary. Output schema/secret screening does not prove a screenshot, receipt,
account binding or user authorization is genuine.

Offline crash/concurrency tests and a real local Python fixture cover this
state lifecycle. They do not establish provider adapters, five-surface live
generation, true provider spend caps or installation parity. Keep those gates
separate; Grok generation stays on hold while the user's USD 0 constraint and
exhausted quota apply.

## Guarded Orca adapter

`execute_orca.py` is a one-shot local transport, not a scheduler. Read the
installed version-matched Orca orchestration guide first. This initial adapter
supports only registered Claude/Codex lanes whose effort_style is flag. Grok,
Antigravity, remote placements, prompt-keyword/ultracode lanes and automatic
retry/fallback are deliberately unsupported. It creates no Run, Task, workspace
or terminal outside the single guarded worker-start. The coordinator prepares
the unique native Run/Task and exact existing workspace using the normal Orca
contract. Do not reuse a Task with any previous Dispatch.

Each request node preserves an `orca` manifest in its registered plan:

```json
{"run_id":"native-run", "task_id":"native-task",
 "worktree_id":"exact-native-workspace-id", "worktree_path":"absolute-resolved-path",
 "workspace_instance":"native-instance-id",
 "executable":"absolute-native-orca-executable", "executable_sha256":"sha256",
 "runtime_id":"observed-runtime-id", "app_version":"observed-app-version",
 "account_ref":"opaque-account-reference", "profile_ref":"opaque-launch-profile",
 "guards":{"quota_checked_vendors":["claude","codex","grok","gemini"], "quota_states":{}}}
```

These are placeholders, not runtime facts. Supply actual quota_states and all
normal plan inputs from evidence. The entire plan still passes the legacy
policy, dependency, quota and budget guards. Plan registration durably fixes
the manifest, route and spec intent before the first claim. Use
`execute_orca.py spec --plan plan.json --node ID` to print the exact Task spec;
it includes the complete node intent, skill paths and handoff, excluding only
transport fields and planner diagnostics. Set that exact spec on the prepared
native Task before dispatch. No unrelated prompt is accepted at send time.

The coordinator supplies a separate certificate for the exact Orca launch
account/profile, not a generic subscription label or direct-CLI login. Required
fields are verified=true, binding_sha256 (`binding_digest(plan, node_id)`),
account_ref, profile_ref, observed_at, valid_until, billing (exact route billing
object) and a nonempty evidence array. Evidence must establish model inclusion,
quota, the launch profile/account mapping and disabled overage/API fallback for
a subscription route. No helper creates or upgrades this certificate. Unknown
facts block dispatch; do not relabel metadata-only observations as verified.
The certificate is trusted coordinator evidence, not a cryptographic provider
attestation or an atomic lock on external account settings. Profile changes
require revalidation. There is no claim of a provider-enforced spend cap.

```text
python "<skill>/scripts/execute_orca.py" dispatch --plan plan.json --node ID --db shared-runs.sqlite3 --certificate account-proof.json
python "<skill>/scripts/execute_orca.py" reconcile --plan plan.json --node ID --db shared-runs.sqlite3
```

Before sending, the adapter compares the pinned executable hash, runtime ID and
version, native Task ID/spec, and native workspace ID/path/local host/instance.
It repeats freshness checks after these reads and after its internal claim.
Only that call's fresh claim permits one worker-start with an exact `id:`
workspace selector and stable --retry-request identity. A persisted true flag,
timeout, nonzero CLI exit or missing lookup cannot authorize another send.
Repeated dispatch calls and reconcile use only task-list, worker-list,
worker-show, worker-read, status and worktree show. Missing/ambiguous/incomplete
lookup stays uncertain. Pagination is bounded and incomplete pages fail closed.
Orca --retry-request is additional deduplication, not exactly-once proof.

`worker-show` structured launch.requested/effective must both match. Effective
settings prove Orca's applied launch configuration, not the internal reasoning
of a model or a provider invoice. Missing/mismatched settings remain uncertain
and can be observed again later. Task/Dispatch completion requires matching
native identity, worker state, dispatch status and projection outcome; PTY exit
or prose claiming success is insufficient. It never calls settle or verify.

Worker output is read in a bounded call, but raw text, cursor, provider errors
and tool inputs are not copied into stdout or the DB: arbitrary prose can
contain credentials. Returned metadata includes a digest, completeness and
warning flags, text byte count and a native read argv. The coordinator must
inspect the actual result through that authorized reader, handle clipping and
then attach acceptance evidence. A digest is not content acceptance. Unknown
actual cost retains the reservation even after native success.

The adapter uses routing's argv builder and full-plan guards, but not its
legacy PATH-resolved run_orca runner. Its separate native runner fixes the
executable for this run and stops its own CLI client when stdout exceeds 1 MiB
or a call exceeds 45 seconds. It never kills the Orca-owned worker process tree.
The runtime can still accept work after a client timeout; lookup remains the
only automatic recovery. No stop, abandon, release, retry, payment, reset,
installation or worktree deletion is automatic. After accepted settlement the
coordinator still owes the cleanup decision required by the Orca guide.

This adapter assumes cooperating coordinators share the same DB and own the
unique native Task. It cannot stop another tool/user from editing the native
Task, changing account settings, or independently launching its own worker.
Those external races need reconciliation, not a claim of global exactly-once.
Offline fixtures cover crashes, concurrency, mismatched identity, output limits
and missing evidence; they are not live provider generation or billing tests.

## Completion boundary

Discovery and plan tests do not prove that a provider, GUI session or Bot
transport executed successfully. Report preflight, dispatch, received output
and verified completion separately. Keep effective model/effort and actual
money null until evidence establishes them. Do not launch paid preflight calls
outside the user-approved budget. User authorization outranks skill defaults.
