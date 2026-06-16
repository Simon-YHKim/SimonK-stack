---
name: multi-terminal-dispatcher
description: "Use when the user wants to run multiple tasks in parallel across separate terminal windows/tabs, OR when simonk dispatches a sprint with N independent subtasks. Trigger phrases: '병렬로 진행', '다중 터미널', '병렬 터미널', 'multi-terminal', 'parallel terminals', 'team mode', '모델 자동 배치', 'best model dispatch', '여러 창에서', '동시에 진행'. Calls model-router for per-task LLM assignment (wiki ai-model-benchmarks source of truth), then launches each task in its own terminal (Windows Terminal tab / psmux pane / VS Code task / separate PowerShell window). Produces: (1) per-task model + terminal assignment table, (2) cost estimate (task × model = $X), (3) launched terminal IDs for user observation, (4) merged result report after all terminals complete. Safety: destructive ops single-terminal only, user confirms cost > $5."
version: 0.1.0
---

# multi-terminal-dispatcher — Parallel Terminal Orchestrator

> 사용자 1 대화창 → task 분해 → [[model-router]] 으로 모델 배치 → 다중 터미널 병렬 실행 → 결과 통합. [[../../wiki/concepts/multi-agent-dispatch]] 패턴 구현.

## 0. 운영 컨텍스트

- **호출 시점**: simonk Phase 3 (병렬 위임) OR 사용자 trigger word 감지
- **결정 layer**: `model-router` skill (task type → best LLM)
- **실행 layer**: `scripts/multi-terminal-launch.ps1` (Windows Terminal 기반)
- **환경**: Windows primary (PowerShell + Windows Terminal), macOS/Linux 옵션 (tmux)

## 1. 사용 흐름 (5 단계)

```
Step 1: 사용자 prompt → simonk 또는 직접 호출
Step 2: orchestrator (Claude Opus 4.7) 가 N tasks 로 split + 각 task type 분류
Step 3: model-router 가 각 task → best model (primary + fallback) 매핑
Step 4: launcher script 가 N terminal launch (각 terminal = 1 task + 1 model)
Step 5: 모든 terminal complete 후 orchestrator 가 결과 merge → 사용자 보고
```

## 2. Task → Terminal 배치 매트릭스

| Task type | 권장 환경 | 명령 패턴 |
|---|---|---|
| CODE_NEW / CODE_FIX | Windows Terminal tab (PowerShell) | `wt.exe -w 0 new-tab -p "PowerShell" -d "<repo>" pwsh -c "claude '...prompt...'"` |
| RESEARCH | Windows Terminal tab + Claude Code [1M] | `wt.exe new-tab pwsh -c "claude --model claude-opus-4-7[1m]"` |
| COMPUTER_USE | 별도 PowerShell window (UI 동작) | `Start-Process pwsh -ArgumentList "-c", "..."` |
| DESIGN_UI | VS Code task (preview 동반) | `code --task design-task-N` |
| BULK_LIGHT | background job (no UI) | `Start-Job -ScriptBlock {...}` |

## 3. Launcher 옵션 (환경별)

### 3.1 Windows Terminal (Windows primary)

```powershell
# 3 task 병렬, 각 다른 tab
wt.exe -w 0 new-tab -p "PowerShell" -d "$repo" --title "Task1-Sonnet" pwsh -NoExit -c "claude --model claude-sonnet-4-6 'task1 prompt'"
wt.exe -w 0 new-tab -p "PowerShell" -d "$repo" --title "Task2-Opus" pwsh -NoExit -c "claude --model claude-opus-4-7 'task2 prompt'"
wt.exe -w 0 new-tab -p "PowerShell" -d "$repo" --title "Task3-Haiku" pwsh -NoExit -c "claude --model claude-haiku-4-5-20251001 'task3 prompt'"
```

### 3.2 psmux (Windows tmux, `winget install psmux`)

```bash
psmux new-session -d -s simonk-dispatch
psmux split-window -h
psmux send-keys "claude --model claude-opus-4-7 'task1'" Enter
psmux split-window -v
psmux send-keys "claude --model claude-sonnet-4-6 'task2'" Enter
```

### 3.3 Claude Code worktree (git worktree per task)

```bash
# simon-worktree skill 활용
git worktree add ../task1-branch
git worktree add ../task2-branch
# 각 worktree 에서 별도 Claude Code session 실행
```

### 3.4 VS Code tasks.json

```json
{
  "version": "2.0.0",
  "tasks": [
    { "label": "task1", "type": "shell", "command": "claude --model claude-sonnet-4-6 'task1'" },
    { "label": "task2", "type": "shell", "command": "claude --model claude-opus-4-7 'task2'" },
    { "label": "all", "dependsOn": ["task1", "task2"], "dependsOrder": "parallel" }
  ]
}
```

### 3.5 Background PowerShell Job (no visual)

```powershell
$jobs = @()
$jobs += Start-Job -Name "task1-sonnet" -ScriptBlock { claude --model claude-sonnet-4-6 "task1" }
$jobs += Start-Job -Name "task2-opus" -ScriptBlock { claude --model claude-opus-4-7 "task2" }
$jobs | Wait-Job | Receive-Job
```

## 4. LLM 의 컴퓨터 제어 통합

IDE / AI 채팅이 computer-use 도구 제공 시 적극 활용:
- **Claude in Chrome** (MCP `mcp__Claude_in_Chrome__*`) — 브라우저 자동화 task 직접 dispatch
- **Windows-MCP** (`mcp__Windows-MCP__*`) — 데스크탑 앱 제어 task
- **computer-use** (Claude Code default tool 일부) — terminal launch 자체를 자동
- **Cursor multi-pane** — IDE 내장 분할, dispatcher 가 pane 명령

이 도구들이 가용한 환경 → terminal launch 자체를 LLM 이 직접 (사용자 수동 작업 X).
가용하지 않은 환경 → Bash tool 로 PowerShell command 실행 (현재 default).

## 5. 안전 가드 (필수)

1. **각 terminal 가시화** — 작업 silent 실행 X, 사용자가 모든 terminal 화면 볼 수 있음
2. **파괴적 작업 단일 terminal** — `rm -rf`, force push, DB drop 등은 dispatch X, 단일 main terminal 에서만 + 명시 확인
3. **Cost estimate 사전** — 각 task 의 추정 비용 = (input_tokens × $price_in + output_tokens × $price_out). Total > $5 → 사용자 confirm.
4. **결과 모순 표시** — 같은 input 다른 모델 → 결과 다를 시 사용자에게 "Model A 답: X / Model B 답: Y" 명시
5. **터미널 좀비 방지** — 모든 task 완료 또는 사용자 abort 시 `wt.exe` window close 옵션

## 6. simonk 통합 예시

simonk Phase 2 (Sprint plan) 에서 4 task split → multi-terminal-dispatcher 호출:

```
[orchestrator (Opus 4.7)]
  Sprint v25 = 4 parallel tasks:
    T1: CODE_NEW (구현) → Claude Sonnet 4.6 → Terminal-1 (wt tab)
    T2: RESEARCH (조사) → Claude Opus 4.7 [1M] → Terminal-2 (wt tab)
    T3: BULK_LIGHT (대량 정리) → Gemini 3.5 Flash → Terminal-3 (background job)
    T4: COMPUTER_USE (브라우저 자동) → GPT-5.4 → Terminal-4 (separate PowerShell)

  Cost estimate: ~$2.30 total (input 200K + output 80K avg)
  Launch? [Y/n]
```

## 7. 출력 형식

### 7.1 Dispatch plan (사용자에게 보여줌)

```
| Task ID | Type | Model | Terminal | 추정 비용 |
|---|---|---|---|---|
| T1 | CODE_NEW | Sonnet 4.6 | wt-tab-1 | $0.85 |
| T2 | RESEARCH | Opus 4.7 [1M] | wt-tab-2 | $1.20 |
| T3 | BULK_LIGHT | Gemini 3.5 Flash | bg-job-1 | $0.05 |
| **Total** | | | 3 terminals | **$2.10** |
```

### 7.2 결과 merge (완료 후)

```markdown
## Sprint v25 결과 — multi-terminal dispatch

### T1 (CODE_NEW, Sonnet 4.6)
- ✅ 완료 (Terminal-1, 4분 32초)
- Output: <요약>

### T2 (RESEARCH, Opus 4.7 [1M])
- ✅ 완료 (Terminal-2, 7분 12초)
- Output: <요약>

### T3 (BULK_LIGHT, Gemini 3.5 Flash)
- ✅ 완료 (bg-job-1, 1분 8초)
- Output: <요약>

총 cost: $2.18 (estimate 대비 +3.8%)
```

## 8. 관련 자산

- **Decision layer**: [[../model-router]] — task → model 매핑
- **Wiki source of truth**: `wiki/concepts/ai-model-benchmarks.md` + `wiki/concepts/multi-agent-dispatch.md` (SimonKWiki PRIVATE)
- **Launcher**: `scripts/multi-terminal-launch.ps1`
- **simonk 통합**: Phase 3 위임 시 자동 호출
- **External vendor reference**:
  - OMC (`external/oh-my-claudecode/`) — Team Mode 19 agents, parallel dispatch 패턴
  - OMO (`external/oh-my-openagent/`) — 6M lines TypeScript model-agnostic harness
  - OpenHarness (`external/OpenHarness/`) — multi-agent coordination infrastructure

## 9. Roadmap

- ✅ **v0.1** (2026-05-25, 현재): Windows Terminal launcher + PowerShell job + 매뉴얼 cost estimate + price table (11 모델) + safety guard
- 📋 **v0.2** (next sprint): psmux auto-setup script + cost estimate 정확도 향상 (anthropic-tokenizer-py 통합) + result merge 자동화 (각 terminal stdout collect → orchestrator markdown report)
- 📋 **v0.3**: Claude in Chrome / Windows-MCP 자동 통합 (computer-use). LLM 이 terminal launch 자체를 click + type 으로 (Bash 우회)
- 📋 **v0.4**: VS Code tasks.json 자동 생성 (`.vscode/tasks.json` 안 dispatch task) + Cursor multi-pane wiring (Cursor Composer API 또는 keybinding)
- 📋 **v0.5**: model 간 결과 모순 자동 detection (LLM diff) + 사용자 1줄 보고
- 📋 **v1.0**: 결과 자동 merge + 모순 detection + 사용자 가이드 + 통합 cost tracker (월별 누적)
- 📋 **v1.1**: Antigravity CLI launcher 옵션 추가 (Gemini CLI deprecation 후, Background orchestration native 활용)

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
