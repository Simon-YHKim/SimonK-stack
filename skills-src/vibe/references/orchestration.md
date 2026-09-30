# Main orchestration contract

## Contents

- Ownership
- Skill discovery and scoped coverage
- Request schema
- Runtime snapshot
- Budget and selection
- Execution and evidence
- Durable state and recovery
- Guarded Bot adapter
- Conditional host image adapter
- Guarded Orca adapter
- Preparation journal and host-injected core
- Completion boundary

## Ownership

The host LLM interprets the request, reads selected skills, and executes work.
`orchestrate.py` is an offline preflight/readiness helper, not an autonomous
daemon or a replacement for provider-specific dispatch. It does not fabricate
runtime observations or send tasks. The host owns one run and its budget.

## Skill discovery and scoped coverage

One scanner backs `catalog`, `inventory`, `coverage` and `plan`. It visits only
direct children of each supplied flat skill root, never arbitrary recursive
directories, scripts or package imports. Add nested system/plugin roots
explicitly. `catalog`/`plan` retain default sibling and home roots (including
`.codex/skills/.system`) outside intact candidates; audit commands require explicit roots so a report
cannot silently change scope with the current machine. Names and descriptions
are discovery hints, never an automatic skill-name-to-model policy.

When the resolved planner is exactly at
`<bundle>/plugins/SimonKCore/skills/vibe/scripts/orchestrate.py`, default
catalog/plan uses only that bundle's five plugin skill roots, Core first.
`bundle.json` must be present and valid (v1 or safety-v2, strict JSON, at most
8 MiB). Discovery checks the planner and plugin manifest hashes, exact physical
skill membership, declared owners/names and SKILL byte hashes against that
trusted local receipt. Links and excluded paths are rejected before reading
their contents. Missing, extra or changed metadata fails with exit 2; no home
fallback occurs. The plan's discovery records the receipt path/hash and narrow
verification scope. This is not a signature, a full scripts/assets verifier,
host compatibility proof or an installation/dispatch grant. Use the existing
bundle verifier before use; keep the trusted single-writer boundary throughout.
For a Codex overlay, `overlay.json` must bind the sole allowed `zoom-out`
projection and generated manifests. For its D-29 general-skill subset,
`subset.json` must bind the same overlay digest and exact included/excluded
member lists. The only accepted omissions are Core `careful`/`unfreeze`, Stack
`freeze`/`guard`/`investigate`, and the two Core/Stack safety runtimes; Claude
manifests remain unchanged. Discovery exposes a separate subset receipt hash,
but full subset byte verification and host policy/selection checks remain
separate gates. A missing, forged or extra omission fails closed.
Invoke candidate Python helpers with `python -B`. For test suites or helpers
that spawn child Python processes, also set `PYTHONDONTWRITEBYTECODE=1` in the
parent environment: `-B` is not inherited by children. Re-verify the receipt
afterward. Bytecode is an extra package file even when the scan is read-only.

Repeated explicit `--root` flags override candidate inference entirely. This
is also required for plugin homes installed separately (e.g. separate cache
directories), where the enclosing bundle receipt is absent. No ancestor search,
global roots-file installation or PowerShell entry migration is implied.

For split homes, the current host coordinator owns root production and refresh:

1. Use the active host's observed, authorized filesystem skill locations and
   approved plugin scope, not guessed cache/version paths or all installed records.
   Preserve supplied order and identify the flat parent of each SKILL directory.
   Deduplicate the same physical root without changing priority. Never scan a
   broader home/cache tree to fill a gap or include disabled/out-of-scope skills.
2. Run `inventory` with those repeated `--root` values and all required
   `--exclude-root` values. Check declared roots, selected names/paths, aliases,
   alternatives and issues against the observed host scope. Exit 0 means a
   complete scan, not a verdict that duplicate names are safe. Resolve an intended
   winner explicitly; unresolved conflicts or missing scope block this handoff.
3. Pass the identical ordered roots and exclusions to `plan`. Match its discovery
   inventory digest and selected bindings to the inspected inventory; if paths,
   scope or content changed, reobserve and replan. A timestamp or old saved root
   list is not fresh host evidence. Do not persist another global root registry.
4. `simonK -Root <array>` forwards roots but **does not forward exclusions**.
   Use it only with dedicated plugin roots whose contents are all permitted to
   scan. When exclusions are needed, use Python `plan --root ... --exclude-root ...`
   directly; an excluded inventory does not authorize an unexcluded PS rescan.

This is an LLM-coordinator procedure using existing arguments, not a new native
host registry collector or automatic installer. It does not prove that the host
loaded/enabled those skills or that their hooks/policies are enforced. If the host
cannot expose a trustworthy scope, report that gap instead of manufacturing one.
Do not invoke default catalog/plan with an empty root list to bypass that gap.
Keep resource-only skills in the trusted host-native snapshot below; never turn
their URIs into filesystem roots. Explicit split roots do not carry candidate
receipt validation, so full release/installation verification remains separate.

```text
python -B scripts/orchestrate.py inventory --root /source/skills-src --root /source/.claude/skills --exclude-root /protected
python -B scripts/orchestrate.py coverage --source-root /source/skills-src --source-root /source/.claude/skills --root /installed/skills --plugin-root /plugin/skills --exclude-root /protected
python -B scripts/orchestrate.py plan --root /installed/skills --host-skills host-skills.json --input request.json --runtime runtime.json
```

Repeat root/exclusion flags as needed. Supply every expected source/install/plugin
root; no registry of old hardcoded skill counts is authoritative. Protected paths
must be excluded before scanning; lexical paths and resolved symlink/junction
targets are both checked before content reads. Missing/unreadable/limited roots,
excluded paths and malformed files remain explicit issues. `complete` means
only the declared flat scope was observed, never that all machine/host skills
were found. No host snapshot means nonfilesystem exposure was not inspected.

The scanner supports scalar names and inline or folded/literal descriptions,
not a full YAML interpreter. Malformed/unsupported required metadata is reported,
not replaced by a guessed directory name. Reads are bounded to 2 MiB per SKILL,
10,000 entries and 64 roots. It emits metadata and raw-byte SHA-256, not bodies.
Same physical paths become aliases; distinct same-name files remain alternatives.
The first valid declared name wins as before. `plan` can use a valid selected
leaf despite unrelated scan issues; its discovery summary and selected bindings
are included in the plan digest. Review alternatives and choose explicit root
order when a shadowed skill is the intended one. Do not silently rename a skill.

Coverage compares each declared source name against the **selected** installed
copy, not any matching shadow. Ambiguous source names, missing/drifted installs,
host-only observations, missing/duplicate physical plugin homes and plugin SKILL
drift are distinct. Extra installed/plugin names are retained separately, not
discarded. With no plugin roots, that comparison is not checked. `inventory`
and `catalog` exit 2 on incomplete scope; `coverage` exits 2 on gaps. A metadata
match is not approval to install, overwrite, dispatch or mark the goal complete.

Hashes cover SKILL.md bytes only, not scripts/assets/dependency closure or host
resource content. Equal SKILL hashes do not prove package parity or quality.
Every compared skill's economy/balanced/quality result is `not_evaluated`, with
quality, actual_usd and latency_ms null. An eval file's existence or schema PASS
cannot upgrade that state. Actual per-skill/mode evaluation and release checksum
parity require separate measured evidence; this utility never fabricates them.

### Host-native instructions

Only a trusted coordinator may build this snapshot from the **current host's
actual tool/skill catalog**, not from worker prose, guessed URIs or an arbitrary
external JSON file. Resolve the instructions through that host's supported
resource reader and read required references before using them. Example shape:

```json
{"schema_version":1,"host_ref":"current-session-reference",
 "observed_at":"2026-09-24T00:00:00+09:00","evidence":["current host catalog observation"],
 "skills":[{"name":"documents:documents","canonical_name":"documents",
            "description":"Read and edit documents","uri":"skill://documents/main"}]}
```

These values are examples, not live evidence. Preserve exact qualified names,
the actual declared canonical name and the actual resource URI. A URI cannot
claim two different canonical identities. Stable identity and host_ref travel
in `skill_bindings`; refreshable snapshot digest, timestamp and evidence travel
in `handoff.host_skills`. Both are bound by the plan digest. This separation lets
the durable Store refresh observations without changing task intent, while a
different resource/host identity remains an intent change. Native bindings
have `path=null` and `sha256=null`; `read_skills` remains filesystem paths only.
The helper never fetches a URI or materializes native instructions for workers.

Native nodes require `kind=llm`, a candidate with `transport=host`, matching
`host_ref`, and fresh snapshot/runtime evidence. Canonical names and resource
identities participate in ancestor/vibe recursion checks. Native snapshot expiry
also caps `route.valid_until`, so existing readiness/claim gates reject an expired
plan. Immediately before host execution reobserve the same host/session, skills
and access; if anything changed, refresh/replan instead of executing stale input.
The snapshot is trusted input, not cryptographic attestation or a resource-access
lock. It never proves available models, billing, skill behavior or authority.
When the host cannot establish provenance, use inventory-only metadata and do
not manufacture a host snapshot to force an executable plan.

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

`kind`: local, llm, gui or typed-only `image`. An `IMAGE_GENERATION` step
compiles to `kind=image` with the `image_generation` capability. Without a
current-host atomic subscription-only image tool it returns a blocked plan
with `IMAGE_GENERATION_REQUIRES_VERIFIED_TOOL`. Untyped `kind=image` is invalid.
Text-model `vision`, a local API wrapper, or a GUI Bot must not silently
substitute for it. A local node supplies an `argv` list and `software`
names checked against runtime tools. Runtime tool_costs must include the exact
argv_sha256 (`orchestrate.digest(argv)`), verified=true, evidence, observed_at
and upper_usd_per_attempt. It must also set `transitive_effects_audited=true`
after reviewing the command and nested setup/smoke-test calls, and set
`billing_mode` to `nonmetered` or `metered`. `nonmetered` requires a zero upper
quote and means no incremental billable effect was found; it does not require
the command to be network-free. `metered` requires a positive upper quote and
an explicit nonzero approved budget. Missing/unknown classification, a zero
metered quote, or an unaudited effect chain blocks planning. Existing quotes
without these fields must be re-audited; do not label an opaque wrapper
`nonmetered` just to pass preflight. This is a host-supplied audit assertion,
not automatic proof that arbitrary nested programs are free.
Local execution does not imply zero cost. A GUI node supplies target, gui_reason,
tool_route_available=false and vibe-bot in its skill list. `verify_of` names
the predecessor being independently reviewed and must also be a dependency.
The host includes scope and acceptance evidence in each task handoff. It must
include every billed coordinator, review and synthesis call in the plan.

Audit the exact local command's transitive effects before assigning a zero-cost
contract; `setup`, smoke tests and validation commands can themselves call an
API. In pinned Gstack `01593aa` (v1.91.2.0), `design/src/cli.ts` runs image
generation during `setup`; `generate.ts` posts to OpenAI Responses API with an
API key, and `check.ts` posts to OpenAI Chat Completions API. An installed CLI
or a ChatGPT subscription does not convert those API-key calls into included
subscription use. For Simon's USD 0 subscription-only grant, keep these
Gstack `design` setup/generate/check commands unavailable, do not collect or
reuse an API key, and do not label them free local tools. Other design work may
continue locally; image generation requires separately observed subscription
inclusion and disabled overage on the exact alternative surface. Inspect any
other Gstack command separately instead of treating the whole suite as paid.

## Runtime snapshot

Pass `candidates`, `tools`, `observed_at`. Each candidate has a unique id,
surface (claude/codex/antigravity/grok/grok-bot), transport (host/cli/orca/bot),
model, lifecycle=active, available=true, observed_at and evidence.
Declare capabilities, quality_tier (1 routine, 2 reasoning, 3 critical),
resource_rank, provider_efforts, transport_efforts and effort_by_demand.
These are observed/configured facts, not inferred from a model name. Candidate
observations and quota have a conservative 15-minute validity window.

Billing fields are `mode` (subscription/api/metered/unknown), `verified`,
`account_ref`, `extra_usage_enabled`, `model_included`, `included_model`, `bot_usage_included`,
`api_fallback_disabled`, and `paid_credit_fallback_disabled`. Included subscription routing requires all of
`verified=true`, `extra_usage_enabled=false`, `api_fallback_disabled=true` for
the account/transport, plus `model_included=true` and `included_model` equal to
the resolved exact LLM model (or requested exact ID without an alias), or
`bot_usage_included=true` for the provider-managed Grok Bot. Missing or uncertain
values block that route. Codex, Grok CLI and Grok Bot additionally require
`paid_credit_fallback_disabled=true` for their **exact account and transport**.
This field needs current evidence that existing purchased credits cannot be
drawn when included usage is exhausted; automatic reload OFF and a nonzero
quota snapshot are insufficient. Missing or contradictory credit evidence is
`PAID_CREDIT_FALLBACK_UNVERIFIED`, not a zero-cost route. A paid candidate supplies
upper_usd_per_attempt including reasoning, tool use and transport charges.
For Claude Fable, a subscription login and the model picker are not inclusion
proof: Anthropic documents that non-interactive `-p`/SDK requests can bill
usage credits without a consent prompt. Never dispatch that route until the
exact model's included-usage and disabled-overage evidence is positive.
Do not set `extra_usage_enabled=false` merely because **automatic top-up/reload**
is off. Existing purchased credits can still be spent after included usage:
OpenAI documents this for Codex and xAI for Grok. Claude's *usage credits*
toggle must be off separately from auto-reload, and an `ANTHROPIC_API_KEY`
can make Claude Code use metered API authentication instead of the subscription.
Antigravity's applicable **AI Credit Overages = Never** / CLI
`useG1Credits=false` must be observed for the actual account and transport;
an absent setting is unknown, not false. For Codex, a positive credit balance
or an unverified account-level credit fallback blocks the zero-extra-spend
route even when auto-reload is off. For Grok/Grok Bot, check purchased
Extra Usage Credits/on-demand fallback separately from Auto Top Up and keep
the CLI and Bot account/quota evidence distinct. Grok ACP billing places
`onDemandEnabled` beside `config`; the collector prefers that outer boolean,
falling back to a legacy nested value only when the outer field is absent.
Missing/nonboolean values remain unknown, and even `false` does not prove
account identity, model inclusion or purchased-credit fallback safety. None of
these settings is changed by the planner or collector. Sources:
https://help.openai.com/en/articles/12642688-using-credits-for-flexible-usage-in-chatgpt-personal-plans ;
https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan ;
https://support.claude.com/en/articles/12429409-manage-usage-credits-for-paid-claude-plans ;
https://docs.x.ai/grok/faq ;
https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-shell/src/extensions/billing.rs ;
https://antigravity.google/docs/plans ;
https://www.antigravity.google/docs/cli/credits/ .
The quote belongs to this task/run snapshot, not a permanent model price.
With approved_usd=0, API and metered LLM routes are excluded even when their
claimed per-attempt upper quote is zero. A positive metered grant is a separate
user decision; it is never inferred from a free-tier claim.
Quota supplies used_pct, observed_at and an optional bucket ID. Unknown is null,
never zero. For Grok CLI and Grok Bot, quota must additionally bind its own
`surface`, `transport`, billing `account_ref`, `state=observed` and nonempty
observation `evidence`. A CLI quota cannot unlock a Bot route or vice versa;
an elapsed reset time with `state=reset-unobserved` is not recovery evidence.
These are coordinator-supplied assertions, not provider attestations. Both quota
exhaustion and unverified billing exclude the route.

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
| Grok | ACP billing; alternate method only after method-not-found; separate `--no-auto-update models` list | Model-to-account/usage binding, supported CLI efforts, subscription inclusion or overage safety; no session/prompt |
| Antigravity | Version-gated /usage, successful command, zero turns and all token counters zero | Account identity, model access and billing authorization |

Antigravity accepts only locally measured /usage contract versions. An unknown
version stops before sending the slash command. A nonzero turn/token response
fails closed without retry; it cannot undo usage already reported by that CLI.
CLI 1.2.12, 1.2.13 and 1.2.14 were measured on Windows with a successful `/usage`
result, zero turns and zero in every token counter. The CLI's `/help` also
reported `/usage` as a local command on 1.2.13 with zero turns/tokens. The
upstream documentation describes `/usage` as CLI-handled; these observations
add only the measured versions to the exact allowlist, not to available model
routes. Version 1.2.14 still supplies no verified account, subscription-included
model or disabled credit-overage evidence; a guarded AGY generation adapter is
not implemented. On the earlier installed CLI,
`agy models --output-format json` exits nonzero even though the upstream
changelog describes a machine-readable subcommand; plain `agy models` lists
slugs, but this collector does not parse them or infer account/model billing.
Grok billing metadata may be read while generation is suspended. The 1.0.41
ACP display tiers `SuperGrok Plus` and `SuperGrok Heavy` normalize to stable
identifiers; account identity, overage controls and model inclusion remain unverified.
The separate CLI model list is parsed as metadata only. It can populate
registry-matched Grok candidates, but each stays `available=false` with empty
transport effort evidence and no account/usage-bucket binding. A listed model
does not authorize generation, even when the CLI offers it as its default.
Quota recovery must be observed again before reconsidering a route. A reset
timestamp is not proof of recovery. Grok Bot has no collector here and never
inherits the CLI account/quota. Claude Widget bridge data is not joined without identity and
bucket-binding evidence. No provider's subscription label proves a free model.

Only models actually returned by Codex model/list or Grok CLI models and present
in the registry become their respective candidates; this is not an exhaustive
cross-provider model inventory.
All collected candidates have available=false, billing.verified=false, unknown
model quota and no effective model/effort. Keep those gates until separate
evidence establishes them. The planner reads the central registry by default;
API capabilities and CLI-reported efforts are distinct constraints.

The collector uses an allowlisted child environment and a temporary working
directory. It bounds protocol stdin/stdout and process lifetime. Windows probes start
suspended inside a kill-on-close Job Object before their code can run; POSIX
probes own a process group. Cleanup targets only the probe's own tree, including
descendants that outlive its root. Server tool/auth requests are refused, not
executed. An unavailable containment primitive fails closed. Offline subprocess
tests cover timeouts, inherited pipes, hostile request IDs and environment
filtering. These are transport-safety tests, not provider generation canaries.
Process containment and a temporary cwd are not an OS filesystem/network
sandbox. Native CLIs may still discover real user profiles, skills or startup
configuration; overriding HOME/USERPROFILE/CODEX_HOME does not prove isolation.
When protected paths or startup side effects cannot be excluded, keep the
probe blocked until a real isolation boundary is available. Do not retry a
native host probe just to turn an unverified claim into PASS.

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
to task ID/spec, then use the guarded adapter below for its supported lanes.
Preserve routing.validate_plan's full-plan checks, including both security
gates, and dispatch only ready nodes through the adapter's internal claim.
Legacy validate_and_dispatch and run_dispatch live calls are disabled; a dry
argv or a stored dispatch_allowed flag is never an execution authorization.

Blocked plans start no nodes; independent safe work needs a separately valid
plan. A local test cannot substitute for an independent LLM reviewer.

For a Bot, use the guarded Bot adapter below and read the resolved vibe-bot
skill before drafting or dispatch. Bind the private draft and exact published
nonce/meta/result paths to the registered GUI node. Structural result checks,
including PNG/JPEG signatures, do not establish pixels, terminal execution,
cost or acceptance. Missing results remain waiting_external; collect exit 0
does not prove that any result was found.

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
python "<skill>/scripts/run_state.py" status
```

These state-changing commands are not an offline planning/dry-run sequence.
For Orca or Bot, do not call the low-level claim command manually before dispatch:
the adapter owns claim and send together. A manually committed intent without
a send can become unresolved; its repeated claim does not authorize sending.
The claim API is for reviewed adapter integration, not a standalone runbook step.

Registration reserves the full run, all nodes and attempts, atomically against
run and shared grant limits. Account identity is the surface plus a non-secret
account_ref. Separate surfaces are not assumed to share a quota bucket. Pending
intents count toward concurrency (default two global and two per account).
`ready` and first `claim` check the stored plan's freshness/validity windows,
dependency/review state, shared budgets, reservations and concurrency. They
do not contact providers or reobserve account settings, quota or model access.
Registration validates the supplied plan; each guarded adapter separately
checks its fresh account/billing authority and transport-specific identity before send.
Resolved model/effective effort and actual cost require post-send observation
and settlement; none are established by a successful claim.
An identical claim returns its existing dispatch_id and
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
separate. A past Grok quota hold is not permanent, but a reset timestamp or
user report alone does not verify current quota, model inclusion or disabled
overage for a new generation request under the USD 0 additional-spend limit.

## Guarded Bot adapter

`execute_bot.py` consumes the registered GUI plan and shared Store. The discovered
vibe-bot SKILL.md owns the exact `bot_delivery` descriptor and certificate schema;
read it rather than reconstructing these from legacy examples. A private draft
may precede account/approval evidence, but publication may not. Include all Bot,
Relay, attempt and review costs in the whole-plan reservation. This adapter requires
Bot and Relay account_ref to match; separate-account Relay is unsupported.

Only a fresh internal claim can publish. Immutable draft/helper/roster pins and
delivery authority are rechecked before metadata-first, no-replace `.md`-last
publication. This makes local files visible to a consumer; it does not prove
actual Relay/Bot acceptance. The real consumer's staging/marker behavior must
be verified separately. Reentry reconciles the same intent without another send,
even when a marker or result is missing. Unknown cost keeps the reservation.

Use `execute_bot.py check-result --plan ... --node ... --db ... --evidence ...`
for exact first-line nonce and bound publication checks, pinned builder console
checks and bounded image evidence. `result_checks_passed` is not Store verified
success. Inspect the actual pixels and task criteria; obtain matching terminal
and cost evidence before Store observe/settle/verify and required reviews.
The adapter never automatically accepts, settles, retries, stops or completes.
Reconcile/check-result may bind and observe unknown state in the existing Store;
they are not read-only queries. Inspect the JSON status even when exit code is 0.

Legacy `orchestrate.py verify-bot` and builder `--verify/--collect` remain separate
unbound helpers; they do not check the registered plan/Store/pinned helper. Do not
use their exit codes as completion or as a substitute for this adapter. No helper
result, historical pilot or manual paste grants permission to bypass a delivery
hold. Source fixtures are not account, generation, OS-isolation or installation proof.

## Conditional host image adapter (D-32)

The planner accepts `runtime.image_tools` only from the trusted *current host*.
Each observed tool needs a unique `id`, `surface=codex|claude`,
`transport=host-image`, exact `tool_ref`, `host_ref`, `interaction_ref`, fresh
`observed_at`, availability and evidence. `runtime.host_ref` and
`runtime.interaction_ref` must match. The tool must expose
`adapter_contract=image-host-atomic-subscription-v1`, `idempotent_request=true`
and `lookup_by_request=true`. Its billing object must prove `mode=subscription`,
the exact account, `image_included=true`, extra usage off, API and purchased-credit
fallback disabled, and a **provider-enforced** hard cap of USD 0 for the image
request. The billing proof itself needs a fresh `observed_at` and evidence;
route expiry uses the oldest tool, billing or quota observation. A fresh
nonexhausted image quota bucket must carry evidence and the same account,
surface and `host-image` transport as the billing/tool observation.
Generic login, local boolean assertions, auto-top-up OFF, a dated quota snapshot
or a text-model capability are not that provider proof. The host must review the
actual tool contract and provide its own trusted observation; worker prose may
not populate this snapshot. No currently exposed Codex/Claude image tool on this
PC meets the atomic cap/lookup contract, so normal plans remain blocked.

`execute_image.py` is an **in-process integration point, not a usable CLI or
provider implementation**. A reviewed host injects methods to reobserve the
same account/tool/interaction, atomically generate with `subscription_only=true`
and `provider_hard_cap_usd=0`, and look up a stable request ID without resend.
The host must ensure the provider enforces these flags in the same generation
operation. The adapter registers no account and changes no payment setting.
After a shared-Store registration, it checks the plan and host, commits one
claim, rechecks the host, then sends once. `reconcile()` looks up the original
request without requiring remaining generation quota or a fresh generation plan;
it still requires the exact host/tool/account identity and never resends. For
an already terminal request, a fresh lookup must match the stored request,
handle, state and result digest; the immutable Store proof is returned without
writing a newer observation. A rejected successful image remains rejected on
reentry while its original success receipt is checked; rejection never triggers
a resend or rewrites the proof. A changed account/cap after claim or ambiguous
send leaves the original
intent/reservation unresolved; never mint a replacement ID to try again.
Returned image bytes and task acceptance are checked separately; an output
digest is not verification.
Actual extra charge remains null and the Store does not settle or verify it.
Claude-to-Codex handoff needs a fresh recipient-host plan and evidence; the
Claude host's image proof cannot be inherited by a Codex recipient.

OpenAI currently documents that Codex image generation uses included limits
but may draw from purchased credits after exhaustion, while an API-key route
uses API pricing. Neither `image_gen__imagegen`'s present tool contract nor
an automatic-reload-OFF setting supplies the required per-request hard cap or
idempotent lookup. Do **not** wrap or call that tool through this adapter under
the USD 0 subscription-only grant. Sources:
https://learn.chatgpt.com/docs/image-generation ;
https://learn.chatgpt.com/docs/pricing ;
https://help.openai.com/en/articles/12642688-using-credits-for-flexible-usage-in-chatgpt-personal-plans .

## Guarded Claude CLI adapter

`execute_cli.py` is a one-send, tool-free Claude Code subscription path for a
read-only `kind=llm` node with no skills, software or `verify_of`. An ordinary
node has no dependencies. In a five-node debate, Claude may take an opening,
its own rebuttal, or the separate judge node. Rebuttal and judge prompts are
constructed only from the registered Store's verified, settled predecessor
artifacts; the judge sees both openings and both rebuttals. The judge is a
different call, but a same-vendor judge is not independent vendor review.
This adapter accepts only canonical debate dependencies (no auxiliary edges),
even if the broader planner accepts them.
Codex has a separate guarded source adapter below. Antigravity and Grok CLI
execution are not implemented here, so a full five-surface debate is not
automatic. Neither adapter manufactures account/billing proof.

The trusted coordinator puts this exact `cli` manifest in the node *before*
planning and Store registration:

```json
{"executable":"/absolute/claude.exe","executable_sha256":"64 lowercase hex",
 "cwd":"/absolute/private-workdir","profile_path":"/absolute/claude-profile",
 "profile_ref":"opaque collector profile reference",
 "account_ref":"opaque collector account reference",
 "result_path":"/absolute/private/result.json"}
```

These are placeholders. Paths must be canonical local directories, the result
parent must already exist, and the result file must not exist. The executable
is pinned by SHA-256 and checked again before each CLI call. Use a private
result directory outside any watched Bot bus or public repository; output may
contain sensitive model prose. Never add that result to Git without review.

A separate certificate requires `verified=true`, `subscription_only=true`,
exact `binding_sha256`, account/profile references, route `billing` and `quota`,
exact selected `model` and `effort`, fresh `observed_at`, future `valid_until`
and nonempty source evidence. The route itself must prove exact model inclusion,
remaining fresh quota, extra usage OFF and API fallback disabled. The helper
does **not** create this certificate from a login, model picker, user statement
alone or `total_cost_usd` in model output. If proof is absent, do not dispatch.
For a rebuttal or judge, the certificate additionally needs exact
`inputs_sha256=execute_cli.input_digest(plan,node_id,store)` and
`cross_vendor_transfer_authorized=true`. This is a coordinator's actual
authorization to pass those inspected predecessor answers to Claude, not a
flag the helper manufactures from user prose. Recompute after the claim and
block a changed input before send.

Each predecessor must be a successful, verified and cost-settled attempt under
the same registered plan. Claude CLI predecessors retain their pinned JSON
result file and SHA-256; a different reviewed executor can record a canonical
local UTF-8 `.txt` file with `content_path`, `content_sha256` and
`content_format="text/plain;charset=utf-8"` in its Store observation. The
adapter rehashes and bounds each artifact, checks Claude session/model identity
when applicable, screens it for sensitive content, and treats prose as untrusted
data rather than instructions. A file path or `verified=true` without a real
independent execution and acceptance check is not evidence. Store settlement
needs a real additional-charge receipt; never insert fixture zero receipts in
an operational run. Do not put these artifacts in a watched Bot bus or Git.

The adapter rechecks `claude.ai`/`firstParty` auth for the same profile/account
using the same sanitized child environment. It strips API-key and alternate
provider variables, sets the pinned `CLAUDE_CONFIG_DIR`, uses `--safe-mode`
(customizations disabled), `--tools ""`, `--strict-mcp-config`, a unique
`--session-id`, exact `--model`/`--effort`, and JSON print mode. On this host,
Claude Code 2.1.285 accepted `--safe-mode auth status --json` without model
generation. A separate tool-free Opus 5.5 debate call resolved its model and
accepted `--effort`; the adapter's certificate-to-Store path and actual
subscription invoice still lack live end-to-end verification. Anthropic states
that `ANTHROPIC_API_KEY` overrides a subscription in noninteractive mode:
https://code.claude.com/docs/ko/env-vars .

```text
python -B "<vibe>/scripts/execute_cli.py" spec --plan plan.json --node opening
python -B "<vibe>/scripts/execute_cli.py" dispatch --plan plan.json --node opening --db shared-runs.sqlite3 --certificate cli-evidence.json
python -B "<vibe>/scripts/execute_cli.py" reconcile --plan plan.json --node opening --db shared-runs.sqlite3
```

`spec` is opening-only; it does not print dependent model prose to stdout.
For a dependent node, dispatch builds the prompt privately after verifying its
certificate and Store inputs. The registered task and input digest are bound to
the send's handle. The bounded prompt is piped over standard input, not placed
in the Windows command line; its input digest is persisted before the send.
Reentry never resends even when an upstream artifact later
disappears or changes. A same-vendor judge is marked in the observation, not
misreported as an independent third-vendor verdict.

Only a newly committed Store claim can send. Reentry never sends again; an
ambiguous response, mismatch, collision or timeout stays `uncertain` with its
reservation held. A matching complete JSON result is written once to the
private path, and its hash/session/model are recorded, not its raw prose. CLI
acceptance of `--effort` is recorded as CLI-level setting evidence, **not**
provider-internal reasoning telemetry. The output remains unverified and its
actual additional charge is `null`: the adapter never auto-settles, verifies,
passes a successor or asserts a $0 invoice. Inspect the output and obtain
post-call terminal/cost evidence before the coordinator settles/verifies. The
CLI's list-price cost field is not an invoice. Offline fixtures prove one-send
and failure behavior, not live account billing or five-surface execution.

## Guarded Codex CLI adapter

`execute_codex_cli.py` is a source-only, one-send read-only `kind=llm` path for
Codex. It accepts no skill/software binding, writes, independent reviewer node
or arbitrary dependent node. A canonical debate opening, own rebuttal or judge
may use it after the registered, verified, settled predecessor artifacts and
explicit cross-vendor transfer authorization are bound. It reuses the same
task/acceptance and Store as Claude, not a second budget.

The node's `cli` manifest pins absolute `codex.exe` bytes, private canonical
`cwd`, actual `CODEX_HOME` profile path, opaque profile/account references,
and separate private `result_path` (`.jsonl`) and `content_path` (`.txt`). Both
artifacts must be directly inside the verified private `cwd`; nested or external
directories, including a watched Bot bus or public repository, are rejected.
Use the same certificate shape as the Claude adapter, but Codex additionally
requires `billing.paid_credit_fallback_disabled=true` for this exact account,
profile, model and CLI transport. `codex login status` or auto-reload OFF is not
that proof. A fresh model/list and ChatGPT account observation must agree with
the pinned profile and route; their metadata does not establish model inclusion,
credit fallback or a USD 0 invoice.

After a Store claim, the adapter repeats the account/model and certificate
checks, persists the original predecessor-input digest, then runs the pinned
native CLI once with `codex exec --json --ephemeral --ignore-user-config
--skip-git-repo-check --sandbox read-only -C <private-cwd> -m <model>
-c model_reasoning_effort=<effort> -`. The bounded task is piped on stdin,
not put in the process command line. The child environment is allowlisted and
sets the pinned `CODEX_HOME`, never forwarding an API key. No wrapper, API/OSS
fallback, broad workspace grant or approval bypass is permitted. This is a
read-only sandbox, not a guarantee that the model cannot attempt a read or
network tool; select only reviewed transferable input. Unknown JSONL items,
tool activity, failed turns, changed account or ambiguous output stay uncertain
without a new request ID or automatic retry.

Only a single JSONL `thread.started`/`turn.started`/final assistant message/
`turn.completed` sequence is accepted. The private raw trace and final UTF-8
content are hashed into the Store; on reentry only those original artifacts are
inspected. CLI flag acceptance is recorded as such, **not** proof of the
provider-internal resolved model or reasoning effort. Output remains unverified,
additional charge remains null and successors stay blocked until a separate
real billing receipt, output acceptance and any required independent reviews
are recorded. The current source tests use a fake transport only; there has
been no operational Codex generation or subscription invoice verification.

```text
python -B "<vibe>/scripts/execute_codex_cli.py" spec --plan plan.json --node opening
python -B "<vibe>/scripts/execute_codex_cli.py" dispatch --plan plan.json --node opening --db shared-runs.sqlite3 --certificate codex-cli-evidence.json
python -B "<vibe>/scripts/execute_codex_cli.py" reconcile --plan plan.json --node opening --db shared-runs.sqlite3
```

Codex CLI JSONL event shapes and tool-event caveats are documented by the
[OpenAI Codex SDK](https://github.com/openai/codex/blob/main/sdk/typescript/src/thread.ts)
and [OpenAI skill-eval guide](https://developers.openai.com/blog/eval-skills).

## Guarded Orca adapter

`execute_orca.py` is a one-shot local transport, not a scheduler. Read the
installed version-matched Orca orchestration guide first. This initial adapter
supports only registered Claude/Codex lanes whose effort_style is flag. Grok,
Antigravity, remote placements, prompt-keyword/ultracode lanes and automatic
retry/fallback are deliberately unsupported. It creates no Run, Task, workspace
or terminal outside the single guarded worker-start. It requires a unique
existing native Run/Task and exact workspace. The central guarded preparation
lifecycle for these resources is not yet implemented. If an independently
reviewed, authorized preparation path and its evidence are absent, block this
node; do not revive raw run-create/task-create helpers as a workaround. Read
the native contract to interpret supplied resources, not as blanket authority
to create them. Do not reuse a Task with any previous Dispatch.

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
transport fields and planner diagnostics. It only prints the spec; it does not
set a native Task. A reviewed preparation path must establish that exact spec
on the native Task before dispatch. No unrelated prompt is accepted at send time.

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

New sends also require `certificate.request_identity`, separate from account
proof. It must contain `contract="caller-chosen-uuid-first-worker-start-v1"`,
`supported=true`, nonempty `evidence`, fresh `observed_at`, future `valid_until`,
and exact `binding_sha256`, `runtime_id`, `app_version`, `executable_sha256`.
This is a local coordinator-evidence schema, **not an Orca capability name**.
Evidence must establish that the pinned native runtime supports a caller-chosen
UUID on the **first** worker-start. General retry support or UUID syntax alone
does not establish that. Missing/unknown/mismatched evidence blocks before the
first native read and before claim. No helper manufactures this certificate.
Installed Orca 1.4.206 server-source inspection now establishes first-use UUID
handling, scoped by `(callerFingerprint, requestId)`, plus same-payload replay
and mismatch rejection. This does not establish that the running runtime loaded
those inspected bytes or prove account/cost/owned-caller readiness. New native
sends remain on hold until those operational bindings are verified. Fixture proofs
are synthetic test inputs, not operational evidence or authorization.

The adapter deterministically derives a UUID5 from the complete binding with
the versioned `simonk:vibe:orca:worker-start:v1:` prefix and URL namespace.
Previously persisted exact `vibe-orca-<binding_digest>` intents are recognized
only for lookup/reconciliation. Their request ID, dispatch ID, history and
reservations are never rewritten, released or resent under a new UUID. Both
formats for one current run/node/plan, or an unrelated ID, fail closed. The
ready-wave consumer shares this exact classification; a legacy unresolved
sibling forces lookup-only for that whole invocation. Existing intents can
still reconcile without the new first-use certificate. No worker found means
uncertain, never permission to issue a fresh request.

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
Legacy `kill_worker.py` is now an inert retired entrypoint. Every invocation,
including no arguments, former preview, `--handle`, `--dispatch`, `--kill`,
`--fence`, mixed help or force options, returns nonzero with no process/native
access. Only standalone `--help` or `-h` returns zero as documentation. The fixed
error `LEGACY_WORKER_TERMINATION_DISABLED` and `termination_verified=false`
are not a cleanup receipt or budget settlement. Old imported process helpers
and the mutable home routing import are removed; there is no env/force override.
Historical examples must not be redirected to an old installed copy.

The old environment match was not ownership: it allowed a handle to bypass the
dispatch lookup, ignored unreadable processes and could report success even
when native fencing failed. Pair validation alone cannot fix process lineage or
identity races. No diagnostic here now scans environments or concludes that an
unreadable process is absent. This retirement does **not** satisfy G8 or implement
termination automation. Raw worker-stop remains disabled too.

Installed Orca 1.4.206 code/guide inspection distinguishes official supervised
stop from the retired OS-tree killer: `worker-stop` fences a Dispatch and closes
its exact proven owned supervised terminal; an unsupervised/context-only
Dispatch can be fenced without stopping a process. A `stop_unknown` result is
not a proven exit. Native CLI success alone therefore is not sufficient either.
These are package-source observations, not proof of loaded runtime identity or
all descendant processes being dead.

A future native stop adapter needs explicit exact-target authorization, the
Store-bound run/node/attempt/native Dispatch, pinned runtime/executable/workspace,
verified owned caller scope and a durable stop request identity. It must inspect
typed stop receipts and matching post-state, distinguish fenced-only/unknown
from a proven supervised stop, and keep unknown cost reserved. No such adapter
ships in this unit. Never replace it with psutil, PID/ENV matching, manual raw
commands or a synthetic certificate. Do not kill, submit input, release or resend
automatically to resolve uncertainty. Stop is not output acceptance or settlement.

This adapter assumes cooperating coordinators share the same DB and own the
unique native Task. It cannot stop another tool/user from editing the native
Task, changing account settings, or independently launching its own worker.
Those external races need reconciliation, not a claim of global exactly-once.
Offline fixtures cover crashes, concurrency, mismatched identity, output limits
and missing evidence; they are not live provider generation or billing tests.
Adapter tests deny process launch before imports and during each case except
three exact `python -I -S -c` pipe fixtures. Wave unit tests deny all children;
its three shell integration cases are separate, default-skipped tests requiring
`VIBE_REVIEWED_SHELL_INTEGRATION=1` after independent isolation review. Setting
that flag is not a sandbox or spending approval. Keep it unset for offline
validation under the current hold. A reported skip is not a passed integration.

## Preparation journal and host-injected core (schema 2/3; native bridge pending)

`run_state.Store` now exposes a preparation lifecycle, not a native Run/Task
creator. `execute_orca.py` still accepts already-bound Tasks only; there is no
operational `prepare` command or automated native preparation yet. The library
`prepare_orca.py` connects this journal to a host-injected protocol core, not an
implemented native bridge. This section supersedes
older statements that **all** preparation state is unimplemented, not the
remaining prohibition on ad-hoc Run/Task creation or manual preclaim.

An operational schema migration requires explicit review/authorization, a
validated backup and quiesced old coordinators. Existing `init` remains schema1;
only `run_state.py --db <same-shared-db> upgrade-preparations --approval-ref <ref>`
opts into additive schema2. It never changes the grant, existing runs/attempts,
or a profile. Old schema1-only code rejects schema2; do not downgrade user_version
or create an alternative DB to evade holds. **No operational migration has been
performed by the development fixture tests.**

The trusted coordinator API is:

1. `begin_preparation(draft, caller)`: ready, fresh, all-Orca Claude/Codex draft,
   with native `run_id`/`task_id` absent (not fabricated placeholders). Nodes must
   share exact runtime/executable/workspace/guard pins. Full-plan attempt reserves,
   prior spend and external holds enter shared budget accounting atomically.
   No ordinary `runs` row exists yet; public registration of that run ID is fenced.
2. `preparation_intent(run, "run"|"task:<node>", caller)`: derive and persist exact
   canonical argv and stable UUID before returning `send_allowed=true` once.
   Tasks reference positively bound native dependencies and the same spec renderer
   as dispatch. Re-entry, restart or concurrent claims return false with the same
   identity; never execute a stored true response. An absent receipt is unknown.
3. `observe_preparation(...)`: accept coordinator-verified matching
   `operation_sha256`, immutable native ID, fresh time, evidence, non-generating
   metadata and actual cost exactly zero. Unknown observations retain hold/slot
   and block further new operations until reconciled. Missing/positive cost is not
   relabeled as zero. Global `actual_total_usd` is null while metadata intents are
   unresolved; `unknown_attempts` also counts those metadata operations.
4. `finalize_preparation(...)`: require all operations bound, fresh exact
   `bound_sha256` proof, `scope_verified`, `no_workers`, `non_generating`, verified
   zero actual metadata cost and evidence. Store injects **only** native Run/Task
   IDs into its current validation plan (the original draft until renewed),
   revalidates/re-hashes, and transfers the preparation
   hold into ordinary run/node reservations in one transaction. Any failure rolls
   back both sides. It neither claims workers nor verifies their outputs.

Default owned-v1 `caller` has exactly `handle` and `identity_sha256`. The latter must fingerprint
the verified transport/runtime/owned-coordinator scope; a made-up digest or
`--from` handle is not ownership proof. Orca's receipt key is caller-scoped, not
globally scoped by UUID. All cooperating callers must use this same DB. Raw
native receipts must pass the protocol core's scope/ownership/spec/dependency
checks before entering these trusted observation APIs. These local proof fields
are **not** an Orca response schema or cryptographic attestation.

There are at most grant.parallel unfinished preparations, including zero-cost
and uncertain ones. A caller handle or identity cannot own another unfinished
preparation or registered-but-active run. Finalization does not release that
caller fence while the ordinary run remains active. Native IDs have exclusive
same-DB owners, including manual bound registrations and registered/closed
history: a Run belongs to one logical run, a Task to one logical run/node.
Even identical IDs on different runtimes are conservatively fenced; this is
not a claim that Orca IDs are globally unique. Fresh native current-Run and
owned-pane checks are still mandatory; local closure is not native cleanup.
Admission verifies the full DAG, at most32 Task nodes and
worst-length journal serialization <=768KiB and final-plan projection <=1MiB;
each observation/final proof is
<=4096 UTF-8 JSON bytes. There is no automatic expiry, cancellation, budget
release, UUID reset or draft rewrite. Expired drafts retain their reservation;
the explicit schema3 validation overlay below is not permission to create another
run. `snapshot.preparations` exposes these holds separately from ordinary runs;
the global budget includes them. The existing `accounts` view covers registered
node/attempt reserves only, not preparation-level holds.

The default owned-v1 preparation core validates coordinator evidence of zero-cost,
non-generating execution and pinned first-use Run/Task request support before
**any** native call. It must prove the caller owns the pane and refuse an unrelated
current Run: installed run-create can unbind that pane's previous Run. Persisted
intent comes before each send, with readback/recovery via exact caller-scoped
receipts and Run/Task evidence. Native mutations/receipt completion are separate
transactions, so partial Run/DAG state is expected after a crash. Missing,
pending, pruned or ambiguous receipts never authorize replacement UUIDs.

### Host-injected preparation protocol core — not an operational CLI

`PreparationAdapter(store, host, clock)` provides `begin(draft)`,
`prepare_one(draft, "run"|"task:<node>")`, `reconcile(draft)` and
`finalize(draft)`. This is a library with **no main/CLI, JSON certificate factory,
default host or raw Orca fallback**. No helper builds operational evidence.
Do not implement a bridge by returning fixture certificates or merely copying
the inherited environment into the old subprocess runner.

The trusted host's in-process `open(expected)` returns an exclusive owned local
session with an immutable `scope_id`, `attest()`, `read_exact(tuple_argv)` and
`mutate_exact(tuple_argv)`. Open/attest must not spawn processes, discover/read
credentials, change profiles or generate provider requests. Before operational
use, the host must independently prove bounded I/O, fixed executable/hash,
fixed local runtime/transport/user-data context, startup isolation, owned pane
and process incarnation, exclusive mutation authority, matching loaded/inspected
server bytes, first-use UUID support and zero incremental metadata cost. This
bridge is **not shipped**; its Python interface cannot authenticate assertions.

Expected binding includes the draft digest and exact runtime/app/executable/
workspace pins. Attestation contract `owned-local-orca-preparation-v1` includes
that digest, scope_id, fresh observed_at/future valid_until, nonempty evidence,
verified/owned/exclusive/startup_reviewed/non_generating/first_use_uuid=true and
actual_usd exactly zero. Its immutable context contains those pins plus local
target, handle, pane_key, process_incarnation, transport_id, and equal 64-hex
loaded_server_sha256/inspected_server_sha256. Caller identity is the digest of
that whole context, not a claim that `--from` authenticates the process.
All of this is a **local trusted-host contract**, not fields or capabilities
advertised by native Orca.

Attestation also carries `request_identity` with contract
`caller-chosen-uuid-first-run-task-create-v1`, exact methods
`orchestration.runCreate`, `orchestration.taskCreate`, `orchestration.requestShow`,
matching runtime_id/app_version/server_sha256 and separate nonempty evidence.
The enclosing fresh proof binds it to this owned session and loaded server.
Worker-start-only UUID evidence or a generic first-use boolean is insufficient.
The worker-launch-preferences capability is not required or accepted as proof
of metadata preparation support; actual worker dispatch retains its own gate.

Each session reply wraps the unchanged native JSON envelope as
`{scope_id, context_sha256, envelope}`. The core checks the host context before
and after every call and native `_meta.runtimeId`. Only exact fixed status,
worktree show, current/show Run, full task-list, empty worker-list and saved
request-show lookups are expressible by its read transport. The only mutations
are the freshly claimed, byte-for-byte stored Run/Task creation argv, including
one `--json`. No worker start/stop, run-use, task-update, input or payment command
is forwarded. Re-checking current Run and graph after intent prevents a changed
pane association from being silently rebound; exclusivity still needs the host.

Every new mutation first reconciles all existing operations. A newly missing
receipt on a historically complete operation blocks the next send, even though
the Store correctly preserves the completed historical binding. Recovery
invocations never add another operation, including when lookup just recovered
the old one. Crash-before-send can remain unresolved indefinitely: receipt
absence is not non-effect proof and no new UUID or automatic reservation release
is provided. Finalization repeats the full receipt/resource graph and no-worker
checks, then uses Store's atomic IDs-only projection; it does not dispatch.

Native 1.4.206 `request-show` has no `--from`, and exposes no caller fingerprint.
The checked host session must establish same-caller scope independently.
Completed receipt method/requestId and stored mutation requestId must match;
Run current/show must match objective, coordinator handle, numeric legacy=0 and
generation=1. Task list is unpaginated: require exact count and unique IDs, full
spec/title/deps (native deps is JSON TEXT), no parent/Dispatch, ready root Tasks
and pending dependent Tasks. This restricted core also requires positive matching
Task created_by handle/pane/process/run-generation. Native provenance fields
can be null: null stays **unknown**, not a fabricated match. Missing provenance,
changed generation, extra Tasks, any worker, partial list or pruned receipt blocks
progress. This deliberate limitation is not general native preparation support.

Without a fresh validation overlay, stale drafts may reconcile using fresh
owned-session observations but cannot create more operations or finalize.
Registry-changing rebase and native caller cleanup remain unimplemented.
A session must remain valid/exclusive for the whole invocation;
retention/release belongs to the future reviewed host integration, not this core.

### Opt-in observable local preparation (v2; native bridge still pending)

The user may explicitly trust the current PC's Orca runtime and choose observed
session/Run/Task/request consistency instead of process ownership or loaded-code
attestation. This is a different assurance contract, not a successful v1 proof.
Select it only through `PreparationAdapter(store, host, clock,
contract="observable-local-orca-preparation-v2", approval_ref=<user-decision-ref>)`.
Unknown contracts, missing approval and automatic v1-to-v2 fallback are rejected.
The default v1 and its valid caller/argv/UUID bytes remain unchanged.

The host open request includes the contract and approval_ref. Its immutable
context must carry the same two values, all existing local runtime/executable/
workspace pins, an observed ambient managed handle and transport identifier.
Pane key and process incarnation must be present but may be null. Require an
inspected_server_sha256 at-rest review pin and explicit loaded_server_sha256=null.
Do not copy the disk hash into the loaded field. This is trusted local metadata,
not proof against another process controlled by the same OS user.

The proof retains draft/scope/freshness/evidence/startup_reviewed/non_generating/
first_use_uuid and actual_usd=0. Instead of owned/exclusive it explicitly asserts
local_runtime_trusted and coordinator_serialized. Serialization covers this
coordinator's cooperating Store users, not global exclusive control of Orca.
The request_identity method list/runtime/app binding is unchanged, but v2 uses
`basis="at-rest-unloaded"` and `reviewed_package_sha256` matching the inspected
pin; the v1 `server_sha256` field is forbidden. This proof is not generated by a
JSON factory or authenticated by Python. Never substitute synthetic fixtures.

Trust approval alone allows **no native call**. Before begin, every native read,
every mutation, its response and finalization, the proof needs a separate exact
`effects_grant` with these fields:

| Field | Required meaning |
| --- | --- |
| approval_ref | Separate actual effects approval, not the trust decision reference |
| authorized | True only after reviewing and authorizing the permitted read effects |
| draft_digest / context_sha256 | Exact immutable draft and complete context digest |
| observed_at / valid_until / evidence | Fresh scoped authority and supporting review, never guessed |
| read_methods | Exact ordered READ_METHODS from prepare_orca.py, including workerList |
| mutation_methods | Empty for read-only recovery; exactly runCreate and taskCreate to authorize new metadata writes |
| accepted_effects | Exact INITIALIZATION_EFFECTS list from prepare_orca.py |
| external_transmission / generation / installation | All false, independent prohibited effects |

The initialization list covers DB open/create, schema migration, federation relay
startup, restored-message repoint scheduling and repository/status probes. This
list is an admission boundary, **not proof that all installed startup/read paths
have already been audited**. In particular worker-list and identity fallback
effects still need version-matched review before a live grant can be issued.
Relay startup must not imply permission to transmit. If external transmission,
unreviewed probes or any other unapproved effect cannot be excluded in the actual
runtime, do not issue this grant. User trust approval is not DB migration,
credentials, external delivery, model generation or a spending authorization.
No operational grant, DB initialization or native preparation has been performed
by these source fixtures. Open/attest remain in-process and non-generating.

V2 persists an exact four-key caller: handle, identity_sha256, contract and
approval_ref. Contract and decision stay visible in the Store instead of only
inside an opaque hash. Canonical Run/Task creation argv omits --from so the CLI
uses its managed-context resolution path. The UUID namespace is explicitly
`simonk:vibe:orca:preparation:v2:`; v1 remains `...:v1:`. Existing preparations
cannot switch contracts or approval references. Their UUIDs, reservations and
unknown effects are never migrated, cleared or resent. A new run is not a way
around the existing caller fence or unresolved budget reservation.

Use run-current without --from and task-list without --run/--from. The former's
ambient caller and the latter's current-consumer fence are part of this lower-
assurance protocol; a named inspection alone is insufficient. Exact Run ID,
objective, coordinator_handle, generation1, receipt UUID/method, Task spec/title/
deps/parent/status, full graph and empty worker checks still apply. Scope/runtime
correlation wrappers do not authenticate the caller. Public receipt namespace is
PC-local/shared: another same-user process with the exact same UUID and payload
cannot be distinguished through these public results. This limitation is accepted
only by the explicit PC-trust decision, not described as global exactly-once.

Task created_by_terminal_handle must match the observed handle. The three pane,
process and generation provenance fields must exist with null or the correct
string/integer type. Receipt and resource values must agree exactly. Non-null
values must match the observed context/current Run; a non-null value with unknown
context is rejected. Matching nulls remain unobserved, not verified ownership.
Missing fields, booleans used as generation, contradictory observations or
unexpected Tasks/workers block progress. No-workers is not weakened to an empty
Task assignee field. Read-only effects authority permits receipt/resource recovery
and local finalization of an already bound graph, but no new native intent or
send. Recheck mutation authority before creating an intent and immediately before
the actual send. If revoked after intent, retain that UUID and budget hold for
lookup-only recovery. Losing read authority blocks even lookup without changing
the original intent; a failed lookup does not permit reissue.

Persisted observation/final evidence names the trust contract, trust approval,
last-checked effects approval and observed session, with ownership/loaded-code
explicitly unproven. It never emits the v1 owned-session label. Full budget holds,
freshness overlays, exact one-send claims, receipt/resource reconciliation and
IDs-only atomic finalization are shared unchanged. Worker dispatch/account
certificates and safe-stop requirements remain separate and are not upgraded by
observable preparation. Actual native bridge, effects audit, installation and
live model/cost tests remain incomplete.

### Explicit freshness overlay (schema 3; source-only)

After authorized backup and coordinator quiescence, the separate command
`run_state.py --db <same-shared-db> upgrade-preparation-refresh --approval-ref <ref>`
upgrades **schema2 to schema3**. It adds only `preparation_validations` with plan,
revision and proof, leaving all original preparation rows and grants unchanged.
`init` still creates schema1; ordinary preparation does not auto-upgrade.
Old schema2 readers reject schema3. Do not downgrade `user_version`, remove this
table, reset UUIDs, release holds or switch DBs to recover. No operational DB has
been migrated by these fixtures; database rollback needs a separate reviewed
procedure that preserves any subsequent reservations/native effects.

The coordinator must rerun the central planner against **newly observed** runtime,
quota, billing and applicable alias/access/quote evidence. Supplying a plan with
edited timestamps is not revalidation. The source core cannot authenticate the
coordinator's assertions or recover alias/access evidence omitted from a plan.
The actual owned-host bridge and zero-additional-cost evidence remain required.

`renew_preparation(run, fresh_plan, caller, proof)` accepts only the same original
intent. Canonical JSON comparison masks exactly `planned_at`, derived
`plan_digest`, and each route's `runtime_observed_at`, `quota.observed_at`,
`valid_until`. Paths must already exist. All other keys, values and numeric types
are frozen: registry identity/check time, quota usage/bucket, billing/account,
model/effort, budget, order/DAG, native pins, skills, exact task text and handoff.
Changed quota usage or registry data requires a different reviewed recovery path,
not weakening this comparison. Host-native skills are unsupported in Orca
preparation; central planning requires a host route for them.

The new plan must be ready, fresh and fit worst-ID final projection/journal
limits. Its expiry cannot exceed the unchanged registry's seven-day lifetime or
either runtime/quota observation's 900-second TTL. Observation times cannot go
backwards; a fresh observation **may shorten** expiry, and that shorter boundary
is enforced. Once the frozen registry expires, this path stays blocked. Opaque
registry SHA changes are not accepted as timestamp-only updates.

Proof fields are `verified=true`, `runtime_revalidated=true`, fresh
`observed_at`, nonempty `evidence`, original `draft_digest`, `previous_digest`,
integer `previous_revision` and new `validation_digest`. A transaction checks
caller identity, the prior digest/revision and the unchanged shared budget.
An exact replay of a committed proof/plan is idempotent. A different stale writer
loses the CAS. Renewal changes **no** operation, native ID, state, reserve, spend
or unknown-cost flag; absent/pruned/pending requests remain lookup-only.

`PreparationAdapter.renew(original_draft, fresh_plan, revalidation_evidence)` is
the trusted in-process coordinator entry. It checks the owned session, records
the proof and does **no native read or mutation**; explicit reconciliation is
still necessary. Do not construct a bridge from synthetic tests or worker data.
`preparation_validation(run, caller)` returns current plan/revision;
`preparation(run)` exposes original and validation digests/revision separately.

New intents validate this overlay atomically but derive argv/UUID/spec/native
markers from the **original draft**. A claim returns its validation digest and
revision separately from immutable operation identity. The adapter checks the
same revision and freshness again immediately before send. If changed, the
intent remains unresolved and recovery is lookup-only, not a resend. All calls
still require the documented exclusive, serialized coordinator/host scope;
SQLite CAS is not a network transaction or a provider-enforced spending cap.

Finalization on schema3 requires both `bound_sha256` and exact current
`validation_digest`/integer `validation_revision` in its final proof. It projects
existing native IDs onto the fresh overlay, then atomically transfers the same
hold to the registered run. The event records original/validation/final digests.
The native Run/Task markers remain original. Subsequent dispatch must use the
registered **final** plan and new exact account/worker-start proof bindings;
never transplant an older final plan's certificate. Registered preparations
cannot renew; ordinary registered-run refresh retains its existing contract.

Offline check: `python -B -m unittest discover -s tests -p "test_prepare*.py" -v` from this skill's
`scripts` directory. It denies subprocess launch before imports and throughout
each test; SQLite files and all proofs are temporary synthetic fixtures. It does
not test live Orca creation, the running backend, provider billing or OS isolation.

## Completion boundary

Discovery and plan tests do not prove that a provider, GUI session or Bot
transport executed successfully. Report preflight, dispatch, received output
and verified completion separately. Keep effective model/effort and actual
money null until evidence establishes them. Do not launch paid preflight calls
outside the user-approved budget. User authorization outranks skill defaults.
