---
name: monetization-planner
description: "Use when the user asks to design a revenue model, pricing strategy, or tier structure—triggers \"수익 모델 설계\", \"가격 정하자\", \"무료/유료 나누자\", \"pricing strategy\", \"freemium vs subscription\", \"how to monetize\". Produces MONETIZATION.md with model selection (freemium/subscription/usage/hybrid), tier structure (Free/Pro/Team/Enterprise), free-vs-paid boundary decisions, and Korea-specific considerations (구독 피로, 간편결제 선호, 전자상거래법)."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# monetization-planner

서비스의 수익 모델과 가격 구조를 설계하는 skill.

## 발동 조건

- "수익 모델 설계해줘", "가격 정하자", "무료/유료 어떻게 나눌까"
- "pricing strategy", "freemium design", "how to monetize this"
- app-dev-orchestrator 단계에서 호출

## Workflow

### 1. 서비스 진단

인터뷰 질문:
- **타겟**: B2C / B2B / B2B2C?
- **시장**: 글로벌 / 한국 / 양쪽?
- **유저 볼륨**: 100명대 / 1만명대 / 100만명대?
- **핵심 가치**: 시간 절약 / 데이터 접근 / 협업 / 엔터테인먼트?
- **경쟁**: 경쟁자 가격대?
- **리소스**: 1인 개발 / 팀?

### 2. 모델 선택 Decision Tree

```
유저가 반복 사용?
├─ YES: 매일/매주 사용
│   ├─ 가치가 누적됨 (데이터, 히스토리) → 구독 (Subscription)
│   └─ 가치가 일회성 (도구) → Freemium + 용량 제한
├─ NO: 가끔 사용
│   ├─ 사용 빈도 예측 가능 → 크레딧/종량제
│   └─ 예측 불가 → 일회성 구매 + 업그레이드 팩
└─ 플랫폼 (양면 시장)
    └─ 마켓플레이스 수수료 모델
```

### 3. Tier 구조 설계

**표준 4-tier 템플릿**:

| Tier | 목적 | 가격 원칙 |
|---|---|---|
| Free | 획득 (Acquisition) | 핵심 가치 경험 가능, 성장 제한 |
| Pro | 전환 (Conversion) | 개인 파워유저의 모든 필요 충족 |
| Team | 확장 (Expansion) | 협업 + 관리 기능 |
| Enterprise | 수확 (Harvest) | 보안 + SLA + 커스터마이징 |

**무료↔유료 경계 축** (복수 선택):
- 용량 / 횟수 / 기능 / 인원 / 지원 / 브랜딩 / 속도 / API / 보존기간

### 4. 한국 시장 보정

- 구독 피로 → Lifetime deal 또는 연간 할인 강조
- 간편결제 선호 → Kakao Pay / Naver Pay 필수
- 가격 심리 → ₩9,900 (만원 미만), ₩29,000 (3만원 미만)
- 법규 → 전자상거래법 7일 환불, 자동갱신 사전고지

### 5. 산출물

`MONETIZATION.md` 생성:
```markdown
# Monetization Strategy

## Model: <선택된 모델>
## Tiers
| Tier | Price | Includes | Limit |
## Free-Paid Boundary
## Korea Adjustments
## Metrics to Track (MRR, Churn, LTV, CAC)
## Related: payment-integrator, analytics-integrator
```

## 검증 체크리스트

- [ ] 경쟁자 대비 가격 합리성
- [ ] 무료 tier가 충분히 매력적 (바이럴 가능)
- [ ] 유료 전환 동기가 명확 (무료 제한이 "짜증"이 아닌 "아쉬움")
- [ ] 한국 법규 준수 (자동갱신 고지, 환불 정책)
- [ ] 기술적 구현 가능성 (payment-integrator와 체인)

## Related Skills

- `payment-integrator` — 결정된 모델을 실제 구현
- `auth-builder` — 유료 tier의 권한 분리 구현
- `analytics-integrator` — 전환율/이탈률 추적 세팅
- `revenue-scenario-tester` — 과금 시나리오 통합 테스트


## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
