---
name: model-router
description: >-
  Use when choosing model/effort assignments: "which model", "모델 추천",
  "route tasks". Returns an evidence-bound /vibe plan with quota, cost and
  blocked reasons; never launches workers or treats unknown billing as free.
version: 0.2.1
---

# Model Router — one typed request, one central plan

## Scope and source of truth

This skill classifies tasks; it does not own a second coordinator, model catalog,
budget ledger or dispatch engine. Resolve the active `vibe` skill home from the
skill inventory, read its instructions, then use its [planner](../vibe/scripts/orchestrate.py).
Use the same approved skill installation and registry as the parent run. Do not
silently combine a development planner with an older installed skill home.

- Model IDs, lifecycle, provider effort and public reference prices:
  [model-registry.json](../vibe/references/model-registry.json), through the planner's loader.
- Account availability, resolved aliases, transport effort, billing, overage and
  quota: fresh, account-bound runtime evidence. Unknown is blocked, not zero.
- Task-type defaults: `TASK_TYPE_MAP` in the central planner. The mirror below is
  checked against that executable contract by offline integration tests.
- Wiki benchmarks are historical research, not dispatch authority. A fetch time
  or `last-updated` date alone does not prove that benchmark rows were updated.
  Do not run a fetcher to manufacture freshness or claim an unverified score.

**Migration status:** source-only consumer migration. Do not install or promote
this change to main until simonk, multi-terminal and their legacy launcher have
also migrated and passed review. Never translate this plan into an old terminal
config or invoke the legacy launcher.

## 1. Classify and scope

Read the actual task before classifying. Keywords are hints, not authorization.
Split mixed tasks into steps. Prefer authorized deterministic CLI/API/MCP work
over adding an LLM or GUI worker. A local tool step uses the canonical local
contract without `task_type`; its exact argv cost still needs verification.

| Type | Meaning |
|---|---|
| CODE_NEW | Implement new code; writing scope must be explicit |
| CODE_FIX | Diagnose or repair code; distinguish advice from edits |
| CODE_REVIEW | Read-only code review; link `verify_of` when reviewing a writer |
| RESEARCH | Gather and synthesize sourced evidence |
| AGENTIC | Judgment within a tool workflow; split code and GUI substeps |
| COMPUTER_USE | Screen-only operation after authorized tool alternatives are checked |
| DESIGN_UI | Visual design reasoning or critique; code implementation is a separate CODE step |
| KOREAN_DOC | Korean document reasoning; language alone is not a model ranking |
| BULK_LIGHT | Low-risk repetitive language work; use local tools when deterministic |
| REASONING_ABSTRACT | Difficult abstract reasoning requiring the critical quality floor |
| VISION | Image/OCR/diagram interpretation, not authority to control a screen |

The planner fills omitted canonical fields from the following contract. Explicit
`kind`, `proc` and `class` must agree; `needs` may only add capabilities, and
`demand` may only increase. Contradictions or unknown types are errors. For work
outside these categories, the parent may use an explicitly reviewed canonical
step; never omit a type merely to bypass a rejected requirement.

<!-- task-type-contract:start -->
```json
{
  "CODE_NEW": {"kind": "llm", "needs": ["code"], "demand": "reasoning", "proc": "coding", "class": "B"},
  "CODE_FIX": {"kind": "llm", "needs": ["code"], "demand": "reasoning", "proc": "coding", "class": "B"},
  "CODE_REVIEW": {"kind": "llm", "needs": ["code", "reasoning"], "demand": "reasoning", "proc": "claim-verify", "class": "A-verify"},
  "RESEARCH": {"kind": "llm", "needs": ["research", "reasoning"], "demand": "reasoning", "proc": "research-deep", "class": "B"},
  "AGENTIC": {"kind": "llm", "needs": ["reasoning"], "demand": "reasoning", "proc": "terminal-ci-git", "class": "B"},
  "COMPUTER_USE": {"kind": "gui", "needs": ["gui"], "demand": "reasoning", "proc": "ui-visual", "class": "C-platform"},
  "DESIGN_UI": {"kind": "llm", "needs": ["vision", "reasoning"], "demand": "reasoning", "proc": "ui-visual", "class": "C-platform"},
  "KOREAN_DOC": {"kind": "llm", "needs": ["reasoning"], "demand": "reasoning", "proc": "research-deep", "class": "B"},
  "BULK_LIGHT": {"kind": "llm", "needs": ["reasoning"], "demand": "routine", "proc": "bulk-transform", "class": "A"},
  "REASONING_ABSTRACT": {"kind": "llm", "needs": ["reasoning"], "demand": "critical", "proc": "research-deep", "class": "B"},
  "VISION": {"kind": "llm", "needs": ["vision"], "demand": "reasoning", "proc": "ui-visual", "class": "C-platform"}
}
```
<!-- task-type-contract:end -->

Every typed step must explicitly set boolean `writes`. Classification does not
infer permission. Set it true for actual edits or external mutations, and provide
a separate LLM reviewer in the same DAG (`verify_of` plus `depends_on`). The
planner requires a different model vendor, not just another model name. A Grok
Bot and Grok CLI do not count as independent reviewers. Destructive actions,
publishing, credential changes and payment retain their separate approval gates.
CODE_REVIEW is always read-only; the compiler rejects `writes: true`. Split
repairs into a CODE_FIX step and review the resulting changes independently.

For COMPUTER_USE also supply the `vibe-bot` skill, exact `target`, evidence-based
`gui_reason`, and `tool_route_available: false`. Otherwise planning blocks. Do not
invent Bot model/effort controls or substitute Bot quota for Grok CLI quota.
For DESIGN_UI follow `simon-design-first` before implementation.

## 2. Submit the whole DAG to the existing coordinator

Preserve the parent's `run_id`, budget, dependencies, `verify_of`, scoped skill
list and `ancestor_skills`. Include `vibe`, `model-router` and any active parent
orchestrator in the ancestry; do not dispatch them as new nested coordinators.
Do not split a writer and its reviewer into independently budgeted plans.

Example request for a recommendation only (not permission to repair files):

```json
{
  "run_id": "parent-run-id",
  "ancestor_skills": ["vibe", "model-router", "simonk"],
  "budget": {"mode": "balanced", "approved_usd": 0, "max_attempts": 2, "max_parallel": 2},
  "steps": [
    {"id": "diagnose", "task_type": "CODE_FIX", "task": "Explain the supplied race condition without edits",
     "skills": ["explain"], "writes": false, "depends_on": []}
  ]
}
```

Resolve the actual script path first; the following uses a placeholder, not a
literal installation directory:

```text
python <resolved-vibe-home>/scripts/orchestrate.py plan --input request.json --runtime runtime.json
```

Use `--root` only for verified skill roots. Normally use the packaged registry;
an approved alternative `--registry` must match the parent's expected digest.
The planner emits JSON to stdout and never launches a worker. Exit 2 means an
invalid or blocked plan; inspect the returned reason, never guess a fallback.
An absent compatible planner is a blocker, not permission to use old routing.

## 3. Report, then hand back the unchanged plan

Return the canonical plan to /vibe. Include its `model_registry.version`,
`model_registry.sha256`, `plan_digest`, same `run_id`, steps and budget. Check the
registry fingerprint against the parent's approved registry before handoff.
Do not reconstruct routes from a Markdown recommendation table. Registration,
atomic budget reservation, readiness, dispatch and acceptance belong to the
parent's existing state/execution workflow, not this skill.

User-facing output should summarize each step's type, selected surface/model,
requested effort, evidence freshness, quota, incremental reservation and blocked
reasons. Distinguish requested, resolved and effective settings. A planned model
or exit code is not a successful execution; `actual_usd: null` means unknown.

- Default additional spending is **$0**, including retries and review. Never use
  a dollar threshold or number-of-tasks exception to authorize extra spending.
- A paid route needs an explicit grant, a conservative bound and valid account
  evidence. Public API prices are not a subscription invoice or hard cap.
- Grok CLI stays on hold while quota is exhausted. A predicted reset time is
  not recovery evidence. Do not top up, enable overage or change credentials.
- No API key, environment file, password vault or login-cookie reads are needed
  for this classifier. No automatic fallback to the current host's model.
- `economy`, `balanced` and `quality` use the central policy, not local scoring.
  Mode choice never overrides cost, capability or review gates. Measured
  quality/cost/latency optimization remains separate validation work.

## Verification and limits

In the source repository, the model-router integration test invokes the actual
planner CLI for all eleven types and compares this contract to executable code.
It covers registry identity, aliases, effort, $0, quota, recursive coordinators
and independent review using fixtures only. Evals cover classification intent;
their dry-run is schema validation, not a real-model quality evaluation.

Run from the source repository (not the installed skill directory):

```text
python -m unittest discover -s scripts -p test_model_router_integration.py
python -m unittest discover -s skills-src/vibe/scripts -p test_orchestrate.py
```

The eleven-type positive fixtures use the CLI planning path, not eleven live
Orca workers. Orca's existing process, lane and security gates still apply.

Natural-language classification, truthful `writes`, exact account-to-transport
binding and final user authorization remain coordinator responsibilities. This
skill does not prove real provider E2E, install parity or universal skill quality.

For a substantial shareable report, use a self-contained HTML summary with
progressive disclosure and an actual local timestamp. Use an installed
completion-report skill if available; do not claim one exists without checking.
Short routing answers and machine-readable plans need no separate HTML file.
