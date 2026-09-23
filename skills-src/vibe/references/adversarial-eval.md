# Evaluation contract — offline checks and measured behavior

## Current execution boundary

The old direct-provider evaluator is quarantined. Its live `--preflight`
and `--run` return exit 2 before cache, truth-command or provider access;
`--force` cannot override this. Do not use its old module examples, printed
recommendations or historical cache as a live runbook. Do not replace it with
hand-written provider calls. SKILL.md and the central execution contract govern.

The user's additional-spend allowance is USD 0 and Grok generation is held.
Even a one-line ping can consume quota or money and trigger startup hooks.
No cached ANSWER line, subscription label, due date or reset timestamp supplies
fresh account/billing authorization. Evidence from an unauthorized call cannot
be reused as approval or a successful authorized E2E test.

## What the existing utilities actually establish

| Utility / mode | Effects and limits |
| --- | --- |
| Skill test harness `--dry-run` | Parses cases and prints assertions; no model invocation or behavioral grading |
| Legacy `--plan` | Reads probes and constructs historical matchups; no provider or truth command, no current availability proof |
| Legacy `--due`, `--report` | Read historical ledger; a due recommendation or aggregate never authorizes execution |
| Legacy `--validate` | Executes each probe's truth_cmd and postprocessor; not a schema-only check or automatic zero-cost operation |
| Legacy `--run --dry` | Executes truth_cmd, uses simulated model answers, does not append the ledger; not a subprocess/network sandbox |
| Legacy `--preflight --dry` | Returns synthetic vendor availability; not observed account access |
| Legacy live `--preflight`, `--run` | Disabled; no automatic replacement runner exists |

Before any truth-command test, inspect the complete argv, cwd, scripts, hooks
and cost implications. Use a scoped isolated fixture and deny unintended child
processes before importing the runner. Mocking a final provider function alone
does not intercept earlier preflight or startup paths. Do not run unreviewed
truth commands merely because the command is named validate or dry.

The skill-case schema check, after reviewing the harness, is:
```text
python "<repository>/.claude/skills/skill-gen-agent/scripts/test_skill.py" "<skill>" --cases "<skill>/evals/cases.json" --dry-run
```
Exit zero means schema acceptance only. The non-dry harness writes a pending
grading scaffold; it also does not invoke or grade a model by itself.
No pending assertion may be reported as PASS.

## Behavioral cases

`evals/cases.json` defines outcome assertions for orchestration behavior:
scope/skill selection, central model/effort evidence, zero-budget holds,
review dependencies, duplicate-send recovery, unknown cost, GUI-only Bot
routing, native skill boundaries and honest completion reporting.
Fixtures describe required pre-state; a test runner must actually supply and
verify that state. They are not measured facts about this machine.

Run cases only through an authorized isolated harness that captures the
resulting actions/artifacts, not merely an answer agreeing with the rules.
Record source version, skill, case, mode, requested/resolved model and
requested/effective effort, fixture identity, action trace, grader evidence
and observed outcome. Preserve failed and blocked cases, with reasons.
A same-host text-only review is a limited review, not cross-vendor execution.

To measure economy/balanced/quality, use comparable tasks, fixtures and
acceptance criteria. Record quality, actual spend, quota use, retries and
latency from observations; missing values remain null/not_evaluated.
Include coordinator, producer, review and Bot costs. Samples do not establish
all-skill coverage, and metadata hashes do not establish full-package parity.
The current schema tests do not establish an optimal model or mode.

## Adversarial model comparisons

Retain the useful measurement rules when a guarded evaluation executor exists:

- Generate ground truth from a reviewed deterministic fixture in the question's
  unit. The grader does not invent it. Count, exit-status and other truth_post
  transforms must be tested, including empty/absent results.
- Do not hardcode a repository-dependent answer as `manual:<value>`.
- For the existing two-producer protocol, the grader's vendor differs from
  both producers. If the required three vendors are unavailable, mark the
  comparison blocked/skipped; do not silently weaken G10.
- Check whether both answers are wrong. Distinguish UNKNOWN from a confidently
  wrong claim, and require scope/evidence for absence claims.
- Exclude simulated answers and grader failures from measured scores.
  Preserve every skipped probe and its reason in the coverage report.
- Historical minimum sample counts and swap thresholds are proposal heuristics,
  not proof of statistical superiority. Do not automatically rewrite routes.
- Do not create a recurring generation daemon.

A replacement evaluator must use the central plan, shared grant/Store,
implemented guarded transport, launch-account evidence, durable identity,
recovery, settlement and acceptance contract for every billed node.
It must not revive the disabled legacy runner. The current Orca adapter only
covers its supported local flag-effort lanes; native preparation, other
transports, measured all-skill/mode coverage and installation validation are
still separate unfinished work.
