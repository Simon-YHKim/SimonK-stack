---
name: grill-me
description: >
  Use when the user wants their plan, design, or spec interrogated before
  implementation — triggers "그릴미", "꼬치꼬치 물어봐", "내가 놓친 거 찾아줘",
  "구멍 메워줘", "이 계획 깨봐", "스트레스 테스트", "grill me", "interrogate
  this plan", "stress test my design", "find holes", or "/grill-me". Produces
  a relentless one-question-at-a-time interview that walks every branch of
  the decision tree, with the agent providing its recommended answer for
  each question. Inspired by mattpocock/skills grill-me. Different from
  office-hours (YC partner style) and plan-ceo-review (one-shot reviewer) —
  this is interactive interview that pauses for each user answer before
  proceeding. Use proactively before simon-tdd RED phase whenever the spec
  has unresolved ambiguity.
version: 1.0.0
author: simon-stack
---

# Grill Me

Relentless interview to surface every unresolved decision in a plan **before** code is written. Adapted from [mattpocock/skills `grill-me`](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md).

## Why this skill exists

The most common AI-coding failure mode is *misalignment* — the agent thinks it understood, builds the wrong thing, and the user discovers it after the fact. Grilling reverses this: force every decision branch to be resolved **before** RED in TDD.

This skill complements three existing ones, with different scopes:

| Skill | Scope | Mode |
|---|---|---|
| `office-hours` | YC partner asking "what would kill this product" | Strategic, broad |
| `plan-ceo-review` | One-shot review of a finished plan | Reviewer, one-pass |
| **`grill-me`** | **Interactive interview, one question at a time** | **Interviewer, multi-turn** |
| `autoplan` | Generate plan from scratch | Planner |

Pick `grill-me` when the *user* already has a plan and wants it *stress-tested* by Q&A.

## Behavior

Interview the user relentlessly about every aspect of the plan until shared understanding is reached. Walk down each branch of the decision tree, resolving dependencies between decisions one-by-one. For each question, **provide the agent's recommended answer** so the user can react fast (agree/disagree/extend).

### Rules

1. **One question at a time.** Wait for the user's answer before asking the next. No batches.
2. **Recommended answer included.** Every question ends with "My recommendation: X, because Y."
3. **Codebase exploration first.** If a question can be answered by reading the codebase, read it instead of asking.
4. **Branch-first traversal.** When the user's answer opens a new branch (e.g., picking framework A vs B), drill into A's sub-decisions fully before backtracking.
5. **Concrete scenarios.** When domain relationships are discussed, stress-test with specific scenarios. Invent edge cases that force the user to be precise.
6. **Cross-reference with code.** When the user states how something works, check whether the code agrees. Surface contradictions immediately.

### Areas to grill

- **Scope** — what is in, what is out
- **Failure modes** — what happens when X breaks
- **Data shape** — exact schema, nullable fields, defaults
- **Edge cases** — empty, max-size, concurrent, race, permission-denied
- **Migration** — how does existing data behave
- **Rollback** — what if this ships and we need to undo
- **Observability** — how will we know it broke in production
- **Naming** — does this term clash with `CONTEXT.md` glossary

## Composition with simon-stack

- **Before `simon-tdd` RED phase** — call `/grill-me` if the spec has any handwaving. RED requires a concrete failing test; ambiguity blocks that.
- **Inside `app-dev-orchestrator` planning phase** — slot between research and design. Output feeds into PRD draft.
- **With `domain-glossary`** — when grilling surfaces a new domain term, append it to `CONTEXT.md` inline (don't batch).
- **With `simon-research`** — if a question requires external data (library comparison, regulation lookup), call `/simon-research` first, then resume grilling.

## Termination

Stop when:
- All decision tree branches have an answer
- Remaining open questions can be deferred without blocking RED phase
- User says "enough" or "we have what we need"

Produce a final summary: decisions resolved, decisions deferred, open risks.

## When NOT to use

- User explicitly says "just do it" — they have authority, don't second-guess via interview
- Trivial change (single-line fix, typo, dependency bump)
- Time-sensitive incident response (use `/debug` directly)
- User already finished planning and wants review, not interview (use `plan-ceo-review`)
