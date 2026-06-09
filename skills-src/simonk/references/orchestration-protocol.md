# simonK Orchestration Protocol — Detail Reference

## Contents

- [Ambiguity Score Calculation](#ambiguity-score-calculation)
- [Sprint Plan Format](#sprint-plan-format)
- [Task Tool Delegation Templates](#task-tool-delegation-templates)
- [Verification Matrix](#verification-matrix)
- [Auto-Push Decision Tree](#auto-push-decision-tree)
- [External Repo Integration](#external-repo-integration)

## Ambiguity Score Calculation

Each dimension scored 0-3 (rare 4+ for excellent clarity). Total = sum / clamped to 0-10.

| Dimension | 0 (bad) | 2 (medium) | 3 (good) |
|---|---|---|---|
| Goal clarity | "improve X", "make better" | "add field Y to schema Z" | "rename foo() to bar() in module M" |
| Scope boundary | "the whole thing" | "files under src/" | "skills-src/<specific-skill>/SKILL.md only" |
| Success criteria | "looks good" | "tests pass" | "validate_skill.py exit 0 + N broken links" |
| Risk awareness | unmentioned | "I think this is safe" | "no public push · no .env touch" |

Score < 6 → invoke deep-interview pattern (3-5 Socratic questions).
Score 6-7 → proceed with caution flag (state assumptions before acting).
Score 8+ → proceed directly.

## Sprint Plan Format

`.simonK/plan.md`:

```markdown
---
sprint-id: 2026-05-23T17:00
user-task: "통합 simonK harness 빌드"
ambiguity-score: 7/10
sub-tasks: 4
parallel-tasks: 3
sequential-tasks: 1
start: 2026-05-23T17:05
---

# Sprint Plan

## Sub-tasks

### [P1] skills-src/simonK/SKILL.md 작성
- agent: general-purpose
- deps: none
- est-time: 5min

### [P2] PowerShell function simonk.ps1
- agent: general-purpose
- deps: none
- est-time: 3min

### [P3] settings.json env var 추가
- agent: Explore + manual edit
- deps: none
- est-time: 2min

### [S4] SimonK-stack CLAUDE.md 갱신 + commit + push
- agent: general-purpose
- deps: P1, P2, P3
- est-time: 5min

## Status

(updated by simonK during execution)
```

## Task Tool Delegation Templates

### General-purpose research

```
Description: <2-5 word summary>
prompt: |
  컨텍스트: <필요한 cwd, env, 관련 파일>
  
  목표: <specific outcome>
  
  방법 (선택사항): <approach hint>
  
  반환 형식:
  - finding 1: <fact>
  - finding 2: <fact>
  - <summary in 1 sentence>
  
  제약: <안전·범위 제한>
subagent_type: general-purpose
```

### Explore (read-only)

```
Description: <2-5 word>
prompt: |
  Find: <pattern or symbol>
  Path scope: <dir>
  Breadth: quick | medium | very thorough
subagent_type: Explore
```

### Plan (architecture)

```
Description: <2-5 word>
prompt: |
  Task to plan: <task>
  Constraints: <list>
  Output: step-by-step plan + critical files + tradeoffs
subagent_type: Plan
```

## Verification Matrix

| Touched | Verify |
|---|---|
| `skills-src/<name>/SKILL.md` | `python .claude/skills/skill-gen-agent/scripts/validate_skill.py skills-src/<name>` |
| `.claude/skills/<name>/SKILL.md` | same |
| `*.sh` in hooks/scripts | `bash -n <file>` |
| `*.json` (settings/config) | `python -c "import json; json.load(open('<file>'))"` |
| `*.yaml` / SKILL frontmatter | `python -c "import yaml; yaml.safe_load(open('<file>').read().split('---')[1])"` |
| Wiki `*.md` (SimonKWiki) | structural lint script (broken wikilinks · index sync · frontmatter check) |
| Anything in SimonKWiki Output/ | manual visual diff |

## Auto-Push Decision Tree

```
After commit:
├─ Branch is main?
│  ├─ Yes
│  │  ├─ Force push needed? → STOP, ask user
│  │  ├─ Multi-collaborator repo? → confirmed only on first push
│  │  └─ Solo repo (SimonKWiki, SimonK-stack)? → push immediately
│  └─ No (feature branch) → push immediately (no risk)
│
└─ Network/auth failure?
   ├─ Retry once (10s wait)
   └─ If retry fails → report only · do not block
```

## External Repo Integration

When user requests features from external repos:

| Request | Action |
|---|---|
| "OMC team mode 써줘" | Suggest user run `/plugin marketplace add Yeachan-Heo/oh-my-claudecode` + `/plugin install oh-my-claudecode` (one-time). Then `/team <N>:<role> <task>` available. |
| "OMO Hashline edit 써줘" | Reference `external/oh-my-openagent/` for impl pattern. Currently no vendoring (OpenCode-specific). |
| "OpenHarness ohmo 게이트웨이" | Reference `external/OpenHarness/`. Phase 6 polish. Currently npm CLI `omc` is available for similar features. |
| "anthropics 공식 skill X 추가" | Cherry-pick from `external/anthropics-skills/skills/<name>/` into SimonK-stack skills-src + run validate_skill.py. |

## Slash Command Disambiguation

If user types `/simonK <task>` inside Claude Code:
- Skip PowerShell wrapper
- Execute simonK protocol directly with task = `<task>`

If user types `simonK <task>` in PowerShell:
- PowerShell function dispatches `claude -p "/simonK <task>"` in `C:\Coding` dir
- Same protocol executes

If no task ("simonK" alone): open interactive Claude Code in `C:\Coding`.
