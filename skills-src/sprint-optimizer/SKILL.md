---
name: sprint-optimizer
description: "Use when the user wants to run sprint planning with multiple options—triggers "스프린트 모드", "3가지 방안", "케이스 비교", "best case 추천", "반복 고도화", "sprint mode", "compare options", "iterate on best case". Produces 3-case analysis (Conservative/Balanced/Aggressive), recommends Best case, and offers iterative refinement loop with user-agreed depth of iteration."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# sprint-optimizer

스프린트 모드: 3 case 도출 → Best 추천 → 반복 고도화.

## 발동 조건

- "스프린트 모드로 해줘", "3가지 방안 비교", "best case 추천"
- "반복해서 고도화하자", "케이스 비교 분석"

## Workflow

### 1. 3 Case 도출

모든 의사결정에 대해 3가지 접근을 동시 생성:

| Case | 성격 | 리스크 | 보상 |
|---|---|---|---|
| **Conservative** | 검증된 방법, 최소 변경 | 낮음 | 낮음-중간 |
| **Balanced** | 적정 혁신 + 안정성 | 중간 | 중간-높음 |
| **Aggressive** | 최대 혁신, 실험적 | 높음 | 매우 높음 |

### 2. Best Case 추천

평가 기준 (가중치 사용자 조정 가능):
- **Impact** (40%): 목표 달성 기여도
- **Feasibility** (30%): 현재 리소스로 실행 가능성
- **Speed** (20%): 구현 속도
- **Risk** (10%): 실패 시 복구 비용

### 3. 반복 고도화 (사용자 합의 필수)

```
Claude: "Best case를 선택하셨습니다. 
        반복 고도화를 진행할까요?
        - 깊이: 1회 (빠른 개선) / 3회 (중간) / 5회+ (심층)
        - 각 회차에서 피드백을 반영합니다."

사용자: "3회로 하자"

반복 1: 초안 → 피드백 수렴 → 개선
반복 2: 개선안 → 엣지 케이스 보완 → 정교화
반복 3: 정교화 → 최종 검증 → 확정
```

**핵심**: 반복 깊이는 반드시 사용자와 합의. 무한 루프 방지.

### 4. 산출물

매 스프린트마다:
```markdown
# Sprint Report — <주제>

## 3 Cases
| | Conservative | Balanced | Aggressive |
|---|---|---|---|
| 설명 | ... | ... | ... |
| 예상 결과 | ... | ... | ... |
| 소요 시간 | ... | ... | ... |
| 리스크 | ... | ... | ... |

## Recommendation: [Balanced]
이유: ...

## 반복 고도화 로그
- Round 1: ...
- Round 2: ...
```

## Related Skills

- `pmf-analyzer` — PMF 달성을 위한 스프린트
- `aarrr-growth-planner` — 그로스 실험 스프린트
- `aha-moment-optimizer` — A/B 실험 스프린트
- `karpathy-guidelines` — 원칙 4 (Goal-Driven) 적용
