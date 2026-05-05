---
name: pmf-analyzer
description: "Use when the user wants to analyze or predict Product-Market Fit—triggers "PMF 분석", "제품 시장 적합성", "활성 사용자 예측", "PMF 리포트", "시장성 분석", "product market fit", "analyze PMF", "user projection". Produces 3-case PMF projection (Optimistic/Base/Pessimistic) with active user ratio prediction, Sean Ellis test simulation, retention curve modeling, and optional periodic reporting mode for post-launch tracking."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# pmf-analyzer

PMF(Product-Market Fit) 분석 + 3 case 시나리오 예측 + 주기적 리포팅.

## 발동 조건

- "PMF 분석해줘", "시장성 분석", "활성 사용자 예측"
- "PMF 달성했을까?", "리포트 돌려줘"
- 출시 전 예측 + 출시 후 추적 모두 지원

## PMF 측정 프레임워크

### Sean Ellis Test

> "이 제품을 더 이상 사용할 수 없다면 어떻게 느끼시겠습니까?"
> - 매우 실망 ≥ 40% → PMF 달성

### 정량 지표

| 지표 | PMF 신호 | 비고 |
|---|---|---|
| D30 Retention | >20% (B2C), >40% (B2B) | 가장 중요 |
| NPS | >50 | 추천 의향 |
| DAU/MAU | >20% | 서비스 stickiness |
| Organic Growth | >50% of new users | 유료 광고 없이 성장 |
| Payback Period | <12개월 | CAC 회수 기간 |

## 3 Case 시나리오 생성

### Case 1: Optimistic (상위 25%)
- 경쟁자 대비 차별화 명확
- 초기 바이럴 계수 K > 0.5
- Retention D30 > 30%
- 12개월 내 PMF 달성

### Case 2: Base (중위)
- 시장 평균 성과
- K = 0.2-0.3
- Retention D30 = 15-20%
- 18-24개월 PMF 도달

### Case 3: Pessimistic (하위 25%)
- 차별화 부족, 시장 포화
- K < 0.1
- Retention D30 < 10%
- Pivot 필요 신호

## 활성 사용자 비율 예측 모형

```
Month N 활성 유저 = (신규 유저 × Activation Rate × Retention_N)
                   + (기존 유저 × Retention_monthly)
                   + (추천 유저: 기존 × K-factor)

예시 (Base Case, 월 1000 가입):
M1: 1000 × 0.6 × 0.5 = 300 활성
M3: 300 + 800 신규활성 - 이탈 = ~600 활성
M6: ~1200 활성 (유기적 + 추천)
M12: ~2500 활성 (PMF 접근)
```

## 주기적 리포팅 모드 (#6)

사용자가 원하면 자동 리포트 설정:

```
[주기: 주간/월간]
PMF Dashboard:
- Sean Ellis Score: X% (목표 40%)
- D30 Retention: X%
- DAU/MAU: X%
- NPS: X
- Organic vs Paid ratio: X%
- MoM Growth: X%

Verdict: [PRE-PMF / APPROACHING / PMF ACHIEVED]
Next actions: [3가지 실험 추천]
```

## 산출물

`docs/pmf/pmf-analysis-<date>.md`:
- 3 Case 시나리오 테이블
- 월별 활성 유저 예측 그래프 (텍스트)
- PMF 달성 예상 시점
- 핵심 개선 레버 3가지

## Related Skills

- `aarrr-growth-planner` — AARRR 각 단계 목표
- `aha-moment-optimizer` — Activation 개선
- `analytics-integrator` — 지표 추적 세팅
- `sprint-optimizer` — PMF 달성을 위한 스프린트
