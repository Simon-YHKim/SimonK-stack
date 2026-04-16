---
name: smart-suggest
description: >-
  Use PROACTIVELY at session start and before any multi-step task to recommend
  the best skill for the user's request — triggers include any ambiguous user
  request, "뭐 쓰면 돼", "어떤 스킬", "which skill", "추천해줘", "자동으로 해줘",
  "auto mode", "알아서 해", "토큰 아끼자", "save tokens". Two modes:
  SUGGEST (recommend skill + explain why, user picks) and AUTO (user grants
  blanket permission, Claude runs the best skill chain without asking).
  Prevents token waste by routing requests to the right skill immediately
  instead of Claude improvising a generic response. Also monitors context
  usage and warns when switching to a lighter approach would save tokens.
allowed-tools: Read, Grep, Glob
version: 1.0.0
author: simon
tags: [meta, routing, token-saving, auto-mode, suggestion]
---

# Smart Suggest

세션마다 사용자의 요청을 분석하여 가장 적합한 SimonK-Stack skill을 즉시 추천합니다.
토큰 낭비를 방지하고, 숙련자에게는 자동 실행 모드를 제공합니다.

## Problem

SimonK-Stack에 skill이 20개 이상 있지만:
- 초보 사용자는 어떤 skill이 있는지 모름
- 잘못된 skill을 쓰면 토큰만 소모하고 결과가 나쁨
- Claude가 skill 없이 즉흥으로 답하면 품질이 떨어짐
- 매번 "이 skill 써라"고 지시하는 것도 비효율적

## Two Modes

### Mode 1: SUGGEST (기본)

사용자의 요청을 분석 → 가장 적합한 1-2개 skill 추천 → 사용자가 선택.

**동작 순서:**
1. 사용자의 요청에서 키워드·의도 추출
2. 설치된 skill의 description과 매칭
3. 상위 1-2개 skill + 선택 이유 제시
4. 사용자가 선택하면 해당 skill 실행

**출력 형식:**
```
추천 skill:
1. /simon-tdd — 새 기능 구현에 TDD 사이클 적용 (가장 적합)
2. /debug — 단순 버그 수정이라면 이쪽

선택하세요 (1/2) 또는 직접 요청:
```

### Mode 2: AUTO (숙련자용)

사용자가 "알아서 해", "auto mode", "자동으로" 라고 하면:
1. **권한 확인**: "모든 skill 자동 실행 권한을 드릴까요?" 1회 확인
2. 승인 후 → 요청마다 최적 skill을 자동 선택·실행
3. skill 전환 시 간단히 알림: `[smart-suggest] → /simon-tdd 실행`

**자동 모드 해제**: "수동으로", "manual mode", "내가 고를게"

## Routing Rules

요청 유형별 skill 매핑:

| 요청 패턴 | 추천 skill |
|-----------|-----------|
| 새 앱/프로젝트 | `app-dev-orchestrator` |
| 기능 구현, 만들어줘 | `simon-tdd` |
| 버그, 에러, 안 돼 | `debug` or `investigate` |
| 리팩토링, 정리 | `refactor` |
| 테스트 작성 | `test-gen` |
| 코드 리뷰 | `review` + `codex-review` |
| 보안 점검 | `security-orchestrator` |
| 디자인, UI | `design-anti-slop` → `design-consultation` |
| 설명해줘, 이해 | `explain` |
| 커밋, 푸시 | `commit` → `/ship` |
| Next.js 최적화 | `nextjs-optimizer` |
| 결제/API 연동 | `paid-api-guard` |
| 권한 설계 | `authz-designer` |
| 또 틀렸어, 반복 | `simon-instincts` |
| 병렬 작업 | `simon-worktree` |
| 위키/ADR | `harness-wiki-setup` |
| 리서치, 조사 | `simon-research` |
| 컨텍스트 위험 | `context-guardian` |
| Stitch 프롬프트 | `stitch-design-flow` |

## Token Saving Features

### 1. Early Routing
skill 없이 Claude가 직접 답변을 구성하면 토큰을 2-3배 소모합니다.
skill이 구조화된 워크플로를 제공하므로 같은 결과를 적은 토큰으로 달성.

### 2. Context Monitoring
매 응답 시 대략적인 컨텍스트 사용량을 추적:
- **50% 미만**: 정상 진행
- **50-70%**: "큰 파일 읽기를 줄이세요" 안내
- **70-80%**: skill 단위로 commit 후 새 세션 권고
- **80%+**: `context-guardian` 자동 트리거

### 3. Batch Recommendations
연관 작업이 여러 개일 때 순서를 한번에 제안:
```
이 작업에 3개 skill이 필요합니다:
1. /simon-research → 리서치 선행
2. /simon-tdd → 구현
3. /review → 리뷰
순서대로 진행할까요?
```

## Session Start Behavior

SimonK-Stack이 설치된 레포에서 세션 시작 시:
1. 설치된 skill 목록 확인 (INDEX.md 또는 skills/ 디렉토리 스캔)
2. 사용자의 첫 메시지 분석
3. SUGGEST 모드로 최적 skill 추천
4. 사용자가 AUTO 모드를 원하면 전환

## Related Skills

- `context-guardian` — 컨텍스트 고갈 방지 (token saving 연계)
- `app-dev-orchestrator` — 대형 작업 시 자동 라우팅 대상
- `simon-instincts` — 과거 실수 기반 skill 추천 보정
