---
name: vibe-bot
description: "Use when a task needs Grok Bot's cloud computer for a GUI-only step, or the user invokes \"/vibe-bot\", \"봇한테 시켜\", \"그록 봇으로 돌려\", or \"console task\". Works inside the current /vibe run: drafts a scoped console task, selects an active roster entry, publishes through the shared budget and durable-claim adapter only with fresh account/Relay/delivery evidence, and checks the exact nonce and screen evidence on return. Produces a task sheet and an honest queued/uncertain/verified result. NOT for work an authorized CLI/API/MCP can perform, direct webhook sends, or local repository changes."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 0.8.1
author: simon-stack
---

# vibe-bot — GUI adapter under /vibe

Use the current /vibe coordinator, run, budget, shared Store and review graph.
A direct `/vibe-bot` invocation enters that same workflow; never start a second
coordinator or create another budget to evade a hold. Grok CLI and Grok Bot
are different account paths. Never inherit CLI quota or billing for a Bot.

Choose this adapter only when the required screen operation has no usable,
authorized CLI/API/MCP route. Keep deterministic and repository work in /vibe.
A screen session is not permission to log in, pay, publish, delete or change
permissions. Honor current user holds even when a previous pilot succeeded.

## 1. Prepare the task without delivery

Read `bots.json` and select the exact owning bot. Keyword matching is a draft
suggestion only: it can return inactive entries. For execution require an
observed active bot and account; reject HOLD, WITHDRAWN and not-created entries.
Target/URL keyword hits weigh more than incidental tool names in task prose.
The project belongs to the task, not to the bot.

Use `scripts/make_bot_spec.py --mode console --target ... --task ... --bot ...`
with an explicit private `--out` directory. `--hub` selects a bus parent for
draft routing; project routing otherwise follows `bots.json`. Inspect the
generated result path before registering a plan. No argument here authorizes
delivery. The console sheet contains:

- exact console/app target and goal;
- read-only scope, or narrowly authorized changes that still stop before Save/Submit;
- forbidden buttons, login/2FA/payment stop points;
- menu path, observed values and a screenshot for each screen;
- expected result path, exact first-line nonce and independent review.

The builder refuses legacy `--deliver hub|webhook|github` and every `--send`
before writing. `send_webhook()` cannot be reenabled with
`TRANSPORT_VERIFIED` or environment values. Manual draft output is rejected
inside configured or explicitly supplied buses, including resolved aliases.
The coordinator must also exclude other watched folders: this is not an
all-filesystem monitor or a sandbox. Do not paste a draft into Bot chat to bypass
the central gates; pasting also dispatches work.

Inspect every field, not just the task. Never include credentials, company
process/LOT/equipment/cost/customer data or unapproved operations. Existing
B1/B2/B3/B8 checks assist review but are not comprehensive DLP or authorization.

## 2. Register immutable delivery intent

Read the discovered /vibe orchestration contract. Build a GUI node with
`kind=gui`, `skills=["vibe-bot"]`, `tool_route_available=false`, a
`gui_reason`, exact `task` and `target`. Use fresh observed Bot runtime,
account/quota and billing evidence in the central planner; unknown is not free.
The route must be `grok-bot` / `bot`, with provider-managed model and effort
left null. This first hub adapter does not control Bot model settings.

Before planning/registration, add `bot_delivery` to the node with exactly:

| Key | Trusted coordinator input |
| --- | --- |
| nonce | Existing draft nonce, `vb-` plus 8–64 lowercase hex digits |
| bot_root | Reviewed vibe-bot package's absolute canonical directory |
| bus_root | Exact authorized bus, e.g. the hub's bots directory or project's .bots directory |
| spec_path / meta_path | Private reviewed draft files outside that bus |
| spec_sha256 / meta_sha256 | SHA-256 of those exact file bytes |
| helper_sha256 / roster_sha256 | SHA-256 of bot_root/scripts/make_bot_spec.py and bot_root/bots.json |

Use actual hashes, never example values. The plan digest fixes these values.
The adapter uses bounded, link/reparse-rejecting local fixed-disk paths; it does
not discover home/cache roots. Keep cooperating single-writer ownership of the
package, drafts, bus and Store throughout the invocation. These checks do not
defend against a hostile process with the same OS user's filesystem rights.

Register the whole plan in the existing shared Store to reserve attempts,
reviews and all delivery/Relay/Bot costs. No helper initializes, migrates or
resets an operational DB. Do not manually claim before using the adapter.

## 3. Publish through the single guarded adapter

Resolve `execute_bot.py` in the discovered /vibe package's scripts directory. It imports
only the pinned reviewed builder bytes from `bot_root`; no mutable home fallback.

Supply a separate trusted coordinator certificate, not worker prose or a
generated fixture. It contains `verified=true`, `binding_sha256` from
`execute_bot.binding_digest(plan,node)`, the exact route's `account_ref`,
`billing` and `quota`, matching `bot_id` and `bus_root`,
`delivery_authorized=true`, a real `approval_ref`,
`relay_verified=true`, `all_delivery_costs_included=true`,
fresh `observed_at`, future `valid_until` and nonempty `evidence`.
The same-account Relay limitation and required relay_account_ref are enforced
by this adapter; separate or unknown Relay billing needs another reviewed route.

Evidence must establish the actual account/profile and quota mapping, target
and Relay availability, full cost bound including retries/reviews/Relay work,
and permission to publish this exact task to this exact watched bus. Included
subscription use additionally needs disabled overage/API fallback. These fields
are trusted assertions, not provider attestations, credential discovery or a
factory that turns unverified observations into permission.

```text
python "<vibe-script-dir>/execute_bot.py" dispatch --plan plan.json --node screen --db shared-runs.sqlite3 --certificate bot-evidence.json
python "<vibe-script-dir>/execute_bot.py" reconcile --plan plan.json --node screen --db shared-runs.sqlite3
python "<vibe-script-dir>/execute_bot.py" check-result --plan plan.json --node screen --db shared-runs.sqlite3 --evidence screens.json
```

Only the call that commits a fresh Store claim can publish. It rechecks pins
and authority after the claim and before the visible task marker. Metadata
gets the exact run/node/plan/dispatch/binding identifiers. Complete temporary
files are fsynced, metadata is published first, then the `.md` file last through
atomic no-replace hard links. Existing files are never overwritten. The consumer
must ignore `.tmp` files and metadata-only orphans. Test that contract against
the actual Relay before activation; filesystem tests alone cannot prove it.

A crash, missing marker, partial pair, collision, expired authority or failure
does not authorize another send. Reentry and `reconcile` inspect the exact nonce
and byte hashes only. Even an intact pair proves local publication, not Bot
acceptance: output stays `waiting_external`, `bot_acceptance_verified=false`,
and unknown actual cost stays null. Store intent/uncertain holds remain reserved.
No automatic retry, new nonce, webhook fallback, stop, cleanup, settlement or
acceptance occurs. Keep the original private drafts for reconciliation.

## 4. Collect, inspect and account

Use the adapter's exact result and metadata paths, not another result found by
a broad scan. `--collect` is a legacy convenience scan: exit0 can mean no result,
and missing metadata can downgrade its mode. It is not completion evidence.
`reconcile` and `check-result` may bind and record unknown state in the existing
Store; they are not read-only queries. Their exit0 can still mean waiting_external.

Use `check-result` to require the exact first-line nonce and pinned published
metadata (bot/target/task and nested vibe run/node/plan/dispatch identifiers),
then reuse the pinned builder's console checks and the adapter's bounded image
checks. Put the evidence JSON and its images under the exact result directory.
Inspect the screenshots, reported values and task acceptance criteria yourself.
The legacy `orchestrate.py verify-bot` and builder `--verify` are unbound helpers,
not substitutes for this registered-plan check. PNG/JPEG signatures or a prose
claim alone cannot prove the screen state or that the operation finished.

Reject missing nonce, unscoped absence, unsupported conclusions, leaked secrets
and missing console evidence. Escalate any report of Submit/Reply/Publish/Delete/
Payment; it is not retroactive authorization. Only after actual terminal and
cost evidence should the coordinator use Store observe/settle/verify. Unknown
cost is never settled as zero. Required independent reviews remain separate.

## Relay and historical evidence

Read [Relay standing instructions](references/relay-charter.md) only when
reviewing Relay behavior or an explicitly authorized profile update. That file
records the earlier 2026-09-20 arrangement; it is not a fresh account, cost or
transport observation and does not override the current central contract.
Do not update a cloud profile, start routines or contact a Bot merely to test
this skill. Bots sharing an account/computer are not separate security boundaries.

Earlier local records describe successful manual and hub pilots on
2026-09-19/20. They are historical evidence, not current generation authorization
or proof that this new adapter is deployed. `evals/cases.json` evaluates the current
draft/route/publication/recovery/result/account boundaries. Its schema dry-run is
not behavioral validation. Record each observed outcome and distinguish an offline
fixture or current-host response from actual Relay/provider behavior; never grade
unperformed actions as passed or infer cross-model quality from one host.

## Verification and current limits

```text
python -B -I -S "<bot>/scripts/tests/test_execute_bot.py"
python -B "<bot>/scripts/selftest.py"
```

Run tests with process/network denial before imports, using only disposable
local drafts, buses and DBs. Never substitute operational hub/project paths.
The source adapter and fixtures do not establish native host compatibility,
installation parity, real Relay receipt, generation success, screenshots,
account costs or all-skill optimization. Keep user $0/Grok/no-model-call holds.
