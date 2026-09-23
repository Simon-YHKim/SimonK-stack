# Main orchestration contract

## Contents

- Ownership
- Request schema
- Runtime snapshot
- Budget and selection
- Execution and evidence
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
One coordinator serializes changes to the run. Multiple unrelated runs need a
shared account budget reservation service before claiming a global hard cap.
The current helper verifies a plan, not atomic cross-process billing limits.

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
to task ID/spec, then call run_dispatch on ready nodes only. Calling
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

## Completion boundary

Discovery and plan tests do not prove that a provider, GUI session or Bot
transport executed successfully. Report preflight, dispatch, received output
and verified completion separately. Keep effective model/effort and actual
money null until evidence establishes them. Do not launch paid preflight calls
outside the user-approved budget. User authorization outranks skill defaults.
