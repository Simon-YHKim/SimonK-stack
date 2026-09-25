---
name: simonk
description: >-
  Use when running a bounded sprint: "/simonK", "ultrawork", "팀으로 진행해".
  Produces a six-phase /vibe plan, verified results and scoped Git status under
  the same budget/approval gates; not single lookups or a second coordinator.
version: 2.1.1
---

# simonk — Sprint procedure under /vibe

Use /vibe as the single orchestration owner. This skill contributes the sprint
workflow; it is not a competing router, budget service or provider launcher.
Read [the detailed protocol](references/orchestration-protocol.md) before
planning, delegating or resuming work.

## Entry and ownership

| Entry | Behavior |
| --- | --- |
| /vibe selects simonk | Run this procedure in the existing coordinator; preserve its registered plan, run_id, budget/grant, state database and ancestry. |
| /simonK task in an existing LLM session | Adopt the /vibe contract in that same host. If no parent run exists, prepare one request; do not spawn a second host. |
| PowerShell simonK with request/runtime paths | Forward to the matching distribution's central offline planner. No dispatch, claim, run-state write or provider call. |
| PowerShell simonK with text or no arguments | Fail closed with migration guidance; do not open an interactive or print-mode Claude session. |

Load [vibe](../vibe/SKILL.md) and its execution contract before new planning.
Read [model-router](../model-router/SKILL.md) when mapping task types; it supplies
task semantics, not another model selector. Discover the actual installed paths
instead of assuming a drive, home directory, model name or provider account.
A missing or incompatible core is a blocker, not permission to use old routing.

When already inside a parent handoff, consume only that authorized node.
Do not invoke /vibe or /simonk recursively as a child, reset ancestry, replace
the registered plan, split its review gates, or create a fresh allowance.
Return needed scope changes to the owner. Before first registration, the owner
records active procedures in ancestor_skills; a standalone simonk request
includes simonk. Never mutate ancestry or the plan digest after registration.

## Phase 0 — Context and safety

- Inspect the actual repository root, branch, status, local instructions and
  relevant README. Preserve user changes and other agents' worktrees.
- Read only task-relevant Wiki context through the configured vault path.
  Wiki benchmark dates and public prices are not runtime or billing proof.
- Check needed tools locally. Do not bootstrap cloud authentication, change
  credentials, install plugins or start daemons merely because this skill ran.
- Keep credentials and private company/personal data out of prompts, logs and
  public artifacts. Stop and mask detected secrets.
- Destructive changes, deployment, payments, credential edits and external
  publication still require the applicable authorization. Team/Full Auto
  wording never waives these gates.

## Phase 1 — Clarify

Evaluate goal clarity, scope, acceptance evidence and risk. An internal score
may help, but it grants no execution authority. Ask only consequential missing
questions; do not repeat answers the user already supplied or force a fixed
question count. State small assumptions. Stop on unresolved safety or cost
ambiguity even if the overall task seems clear.

## Phase 2 — Plan once

For a nontrivial task, prepare at most five bounded work items per sprint and
their dependencies, acceptance evidence, file ownership and review nodes.
Keep a short human-readable plan at the owner's existing run location;
.simonk/plan.md may be a standalone summary, never a second execution authority.

Prepare the complete canonical request for the central planner. Preserve the
parent run_id and budget. Include every billed planning, coding, review,
fallback and synthesis call. Use explicit writes, depends_on and verify_of;
typed steps are compiled by /vibe, not a private simonk mapping table.

Default additional approved budget is USD 0, balanced mode, two attempts and
two concurrent jobs. These are centralized defaults, not a fresh per-skill
grant. Preserve stricter parent limits. Unknown cost, account, model access,
effort or quota is not free. The obsolete USD 5 confirmation threshold does
not apply. Economy/balanced/quality changes selection preferences, not authority.

The planner is an offline preflight. A ready plan neither proves provider
generation nor reserves real money. The owner uses the canonical run-state
database and approved shared grant before guarded dispatch.

## Phase 3 — Execute only ready work

Reuse the current host when its observed model/effort and authorization match.
Otherwise use the owner's supported provider-specific adapter, fresh runtime
evidence and atomic state claim. No direct Task-tool fan-out, legacy terminal
launcher or raw provider command bypasses that gate.

Parallelize only independent, authorized nodes within the existing account,
cost, attempt and concurrency limits. Read each selected skill in full and
hand off exact scope, paths, dependencies and expected evidence. Keep writers
isolated where needed. Architecture decisions use the project's debate gate.

For GUI-only work, first check for an authorized CLI/API/MCP route. Use
[vibe-bot](../vibe-bot/SKILL.md) only when a screen is required, through the
same owner's plan. Grok CLI and Grok Bot have distinct account/quota evidence;
Bot is not a workaround for exhausted CLI quota. Keep Grok generation on hold
while the user's USD 0 constraint and exhausted quota apply.

## Phase 4 — Verify and recover

Run relevant repository tests, lint, type checks, builds and skill validation.
A writing node requires its planned independent review; a successful local
test or a worker's self-report does not replace it.

Inspect actual output and record acceptance evidence against the same run,
node, plan digest and dispatch identity. Distinguish requested/resolved model,
effective effort and actual cost; keep unknown values unknown.

On timeout or ambiguous acceptance, reconcile the original handle. Do not
resend, start a new run, reset reservations or assume the work never started.
Retries and fallback need refreshed evidence and the original remaining
budget/attempt allowance. Report unsupported transport or missing evidence.

## Phase 5 — Scoped persistence

After verification and authorization, review the diff and stage only this
task's explicit paths. Preserve signing and hook configuration. Use a
Conventional Commit; push only to the authorized repository/branch when
delegated by the user or owning workflow. Do not auto-create/merge PRs or infer
main promotion from a source-only review. A dirty tree is not permission to
stage unrelated files. Wiki persistence follows that vault's own rules.

## Phase 6 — Honest report

Lead with results and verification evidence. Separate planned, dispatched,
received and accepted work. Report blocked nodes, unknown cost, held quota,
source versus installed versions and Git state without inventing completion.

Use the project's completion-report standard for a substantial deliverable.
Do not send files externally without authorization. A short source-only unit
may use a concise handoff; do not label it a completed deployment or live E2E.

## PowerShell migration (breaking change in 2.0.0)

The packaged shell helper is [simonk.ps1](scripts/simonk.ps1), added in 2.1.0.
For an offline batch script, dot-source that exact trusted skill copy and use:

```powershell
$ErrorActionPreference = 'Stop'
. '<simonk-skill>/scripts/simonk.ps1'
simonK -RequestPath request.json -RuntimePath runtime.json
# In a batch script, propagate native status explicitly:
exit $LASTEXITCODE
```

Optional -RegistryPath and -Root select trusted offline inputs/catalog roots.
An intact five-plugin candidate discovers its receipt-bound sibling catalogs;
separately arranged plugins or a flat skill root require explicit -Root paths.
The source checkout's root scripts/simonk.ps1 remains a compatible entry for
existing profile pins. Both helpers forward to their own matching /vibe copy;
neither falls back to an installed or unrelated planner when that copy is missing.
No argument injects a model, effort, new budget or coordinator. The helper
never gathers runtime facts. Do not fabricate snapshots to make a plan ready.
The Python application on PATH and the distribution must be trusted; this is a
compatibility shim, not a hostile-environment sandbox.

The function preserves planner stdout and native status. Its own failures go
to stderr with LASTEXITCODE=2; blocked/malformed planner input also returns
nonzero. PowerShell parameter-binding errors occur before the function body
and cannot set LASTEXITCODE; the batch error preference above makes them
terminate with nonzero status. In an interactive host use try/catch for those
exceptions and check LASTEXITCODE after normally returning calls; do not run
the batch exit line. The function itself never exits an interactive shell.
Text/empty calls no longer
spawn Claude, and automatic gcloud/helper loading is removed. Use /simonk
inside an already authorized host for natural-language tasks.

This source change does not update profiles, installed skill copies or main.
The explicit-target source profile installer retains the root helper's pin;
it is not automatically run or repointed at a candidate. Package integration
of the separate multi-terminal entry remains a distinct release gate.

## Validation

Run the executable offline integration suite from the stack root:

```text
python -m unittest discover -s scripts/tests -p test_simonk_entrypoint.py
python .claude/skills/skill-gen-agent/scripts/validate_skill.py skills-src/simonk
```

The PowerShell tests exercise both entries and the real central planner with
synthetic runtime/registry facts, an independent package layout, and no provider
calls. A body-parity test allows only the relative planner path to differ.
Missing PowerShell skips that
suite; a skip is not a pass. evals/cases.json describes behavioral scenarios;
schema validation does not prove that any live model followed them.
