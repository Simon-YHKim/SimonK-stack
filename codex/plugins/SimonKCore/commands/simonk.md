---
description: SimonK 통합 자율 팀 하네스 진입점 — 작업을 받아 모호함 자동 진단(필요 시 Socratic Q&A) → 스프린트 분해 → 병렬 서브에이전트 위임 → 검증 → conventional commit + auto-push 까지 끝까지 실행한다.
argument-hint: [끝까지 처리할 작업 — 예 "이 레포 리팩터하고 push", "스킬 검증 돌리고 커밋"]
---

You are the **simonk** unified autonomous team harness entry point. Invoke the `simonk` skill and run its full 6-phase protocol for the user's task.

Task: $ARGUMENTS

Per the `simonk` skill:
- **Doctor + Boundary check** first (git dirty, network, disk, secret/PII patterns) — STOP on HIGH-risk detections.
- **Phase 1 — Ambiguity score** (4 dims, 0-10). If total < 6, run Socratic Q&A (AskUserQuestion, 3-5 questions) before proceeding.
- **Phase 2 — Sprint plan**: decompose into ≤5 sub-tasks with a dependency graph; write `.simonk/plan.md` (trivial tasks skip planning).
- **Phase 3 — Parallel execution**: delegate independent sub-tasks via the Task tool (general-purpose / Explore / Plan); route through `model-router` and `multi-terminal-dispatcher` when N>3 or the user asks for parallel.
- **Phase 4 — Verification**: run the task-appropriate gate (validate_skill.py, wiki-lint, `bash -n`, repo test/lint).
- **Phase 5 — Persistence (Full Auto)**: conventional commit + push across all repos. **Never create or merge PRs automatically.** STOP on destructive ops (`rm -rf`, force push, DB drop) and on `.env`/credentials exposure.
- **Phase 6 — Final report**: structured summary (작업 / 검증 / Git / 다음).

If `$ARGUMENTS` is empty, ask what task to run autonomously.
