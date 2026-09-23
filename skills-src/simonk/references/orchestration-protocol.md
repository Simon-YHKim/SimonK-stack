# simonk consumer protocol

## Contents

- Ownership and handoff
- Request preparation
- Execution and recovery
- PowerShell contract
- Verification and persistence
- Migration boundary

## Ownership and handoff

There is one current host coordinator per run. simonk supplies a six-phase
procedure; /vibe owns discovery, model/effort selection, budget, state and
provider-specific dispatch.

| Context | Required behavior |
| --- | --- |
| Existing registered /vibe handoff | Keep run_id, node ID, plan_digest, DAG, grant, state DB and ancestor_skills unchanged. Return evidence to the owner. |
| Parent still preparing a plan | Let that owner include simonk in active ancestry before registration. Add tasks/reviewers to its complete DAG, not another run. |
| Standalone /simonk in a current host | Read the /vibe contract, then prepare one request with ancestor_skills containing simonk and the user's budget. |
| Recursive child asks for /vibe or active simonk | Block recursion. Loading their instructions for the current host is not spawning another coordinator. |

A worker cannot enlarge its own scope, replace the plan or register a fresh
grant. If decomposition requires a changed registered intent, return it to the
owner for authorized reconciliation; do not overwrite the old plan. Refresh
supports only the unchanged-intent contract documented by /vibe.

## Request preparation

This is a synthetic shape example, not a dispatch-ready runtime observation:

```json
{
  "run_id": "example-sprint",
  "ancestor_skills": ["simonk"],
  "budget": {
    "mode": "balanced", "approved_usd": "0",
    "spent_usd": "0", "external_reserved_usd": "0",
    "max_attempts": 2, "max_parallel": 2
  },
  "steps": [
    {
      "id": "inspect", "task_type": "CODE_REVIEW",
      "task": "Inspect the authorized files and report findings; do not edit.",
      "skills": ["code-health-guard"], "writes": false,
      "depends_on": []
    }
  ]
}
```

The central compiler maps task_type to kind, capabilities, demand, proc and
class. Preserve explicit writes and stronger requirements; do not copy that
mapping into simonk. A model label in prose is not a route pin. The central
registry fingerprint, observed runtime and exact supported provider/transport
effort intersection determine eligibility.

For writing work include a distinct same-DAG review with verify_of and a
dependency on the writer. Never flatten dependencies to launch everything in
parallel. Missing independent review blocks the writer. Local tests can feed
a review, but cannot replace it.

A handoff includes scope, authorized paths, acceptance criteria, plan/node
identity, read-skills paths and the owner's state references. Account refs
are non-secret identifiers, not credentials or proof of genuine identity.
Real model inclusion, quota binding and disabled overage/API fallback need
separate evidence. API list prices and subscription names cannot supply it.

Use only the user's actual approved budget and existing grant. Unknown spend
is not zero. Count all attempts, reviewers, paid orchestration and fallback.
Do not reset spent/reserved amounts or open a different database to pass a cap.

## Execution and recovery

The offline planner launches nothing. The host admits a valid complete plan
to the canonical state service, then uses a supported guarded adapter for
ready nodes. A worker may not invoke an old raw launcher as a shortcut.

The initial guarded Orca adapter supports only its documented local
Claude/Codex flag-effort lanes. It does not imply that Grok, Antigravity,
remote or Bot execution is available. Respect its certificate, native Task,
workspace, launch-profile and unique dispatch identity checks.

Only a new successful atomic claim grants a send. Reentry and timeout require
lookup/reconciliation, never another send inferred from a missing response.
Unknown provider acceptance or unknown actual cost keeps the reservation.
Plan-ready, process exit, received output, cost settlement and accepted output
are different states. Apply the required independent review before downstream
work consumes a writer's result.

Grok generation remains held until actual quota recovery and verified billing
evidence satisfy the user's additional-cost limit. A predicted reset time is
not recovery. Grok Bot has separate evidence and cannot inherit CLI access.

## PowerShell contract

The profile-compatible simonK function accepts:

- RequestPath: canonical complete request JSON.
- RuntimePath: observed runtime JSON; no implicit collector.
- RegistryPath: optional trusted central registry override.
- Root: optional array of trusted skill catalog roots, in precedence order.

The helper resolves the planner relative to its own checkout, uses a native
Python application (not a same-named shell function), and forwards an argv
array to the central plan command. Input files are not rewritten. No shell
command is constructed from task text or path contents. The current directory
is unchanged; relative paths belong to the caller's directory.

Dot-sourcing defines only the function. It does not load gcloud, discover a
provider, modify environment credentials, initialize state or open a terminal.
Text and empty invocations are deliberately unsupported, returning a migration
hint without echoing the supplied task. There is no hidden interactive mode.

Success stdout is exactly planner JSON. Planner blocked/error JSON remains
planner output and preserves its nonzero code; wrapper-local errors use stderr.
After a normally returning call, check $LASTEXITCODE immediately. PowerShell
parameter-binding errors happen before the function body and do not set that
variable. Batch scripts set $ErrorActionPreference = 'Stop' before invocation
so those exceptions terminate nonzero, then use exit $LASTEXITCODE for native
planner status. Interactive callers handle binding exceptions with try/catch
and must not exit their own host just to inspect a result.

The checkout and Python application on PATH are trusted inputs. This shim is
not a sandbox or protection against a malicious Python binary, altered core
files or forged runtime evidence. Its tests use synthetic observations.

## Verification and persistence

- Run project-specific tests/lint/build and the skill validator as applicable.
- Verify output, effective configuration and cost separately using evidence.
- Treat unsupported execution or a missing result as incomplete, not success.
- Stage only explicit reviewed paths; keep unrelated changes and signing.
- Commit conventionally and push only within the owner's authorized branch.
- Do not create/merge PRs, promote main, publish artifacts or change credentials
  as a side effect of completing this procedure.
- Keep documentation/report claims aligned with source, installed and live
  status. A schema-only eval is not a model behavior test.

## Migration boundary

Version 2.0.0 intentionally removes the old shell's unconditional Claude
startup and implicit cloud bootstrap, independent Task fan-out, USD 5
confirmation exception, catch-all staging and automatic signing override.

The profile installer and root documentation still need a coordinated
follow-up before installation/main promotion. Do not run the old installer
to apply this source-only unit. Existing installed skill/profile paths do not
change merely because these source files changed.

The offline tests prove the shell-to-planner boundary, not five-surface E2E,
actual account billing, global spend caps or cross-provider model quality.
