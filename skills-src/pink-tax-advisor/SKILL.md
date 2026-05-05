---
name: pink-tax-advisor
description: "Use when the user explicitly asks for aggressive revenue maximization or pricing psychology—triggers "수익 극대화", "가격 전략 심화", "pink tax 연구", "세그먼트별 가격", "심리적 가격", "maximize revenue", "pricing psychology", "willingness to pay". Produces segment-based pricing analysis, psychological pricing tactics, value metric optimization, and ethical boundary guidelines. Only activates on explicit user request for aggressive monetization."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# pink-tax-advisor

수익 극대화를 위한 가격 전략 심화 연구. **사용자 명시적 요청 시에만 발동**.

## 발동 조건

- "수익 극대화 해줘", "가격 전략 심화", "pink tax 연구"
- "세그먼트별 차등 가격", "WTP 분석"
- ⚠️ 사용자가 노골적으로 요청할 때만. 자동 발동 안 함.

## 가격 심리학 전략

### 1. Value Metric 최적화

가격 기준을 무엇으로 삼을까:
- 사용자 수 (Slack) vs 사용량 (AWS) vs 기능 (Notion) vs 성과 (Stripe %)
- 최적: 고객의 성공과 비례하는 지표

### 2. 세그먼트별 차등 (Price Discrimination)

| 세그먼트 | 방법 | 예시 |
|---|---|---|
| **규모** | 인원/사용량 기반 tier | 1인 $10, 팀 $50, 기업 맞춤 |
| **긴급도** | 속도 프리미엄 | 일반 큐 무료, 우선 처리 유료 |
| **전문성** | 기능 잠금 | Basic/Pro/Expert |
| **지역** | PPP (구매력 평가) | 한국 $10, 인도 $3 |
| **시점** | 얼리버드/런칭 할인 | 출시 50% → 점진 인상 |

### 3. 심리적 가격 기법

- **Charm Pricing**: ₩9,900 (만원 미만 느낌)
- **Anchoring**: 비싼 플랜을 먼저 보여주고 중간 선택 유도
- **Decoy Effect**: 세 번째 옵션으로 중간 선택 유도
- **Loss Aversion**: "Pro 무료 체험 종료까지 3일"
- **Bundling**: 개별 합산보다 번들이 저렴하게

### 4. Pink Tax 분석

특정 세그먼트에 더 높은 가격을 부과하는 전략:
- B2B > B2C (동일 기능, 다른 가격표)
- Enterprise > SMB (SSO/SAML만 추가해도 10x)
- 긴급 니즈 > 일반 (Expedited processing)

### ⚠️ 윤리 경계

이 skill은 정보 제공 목적. 사용자가 판단:
- 지역별 PPP 차등은 일반적으로 수용됨
- 동일 제품 성별/연령 차등은 윤리적 논란
- 독점적 위치 남용 주의
- 가격 투명성 유지 권장

## Related Skills

- `monetization-planner` — 기본 모델 결정 후 이 skill로 심화
- `global-payment-planner` — 지역별 가격 실제 구현
- `pmf-analyzer` — 가격 변경이 PMF에 미치는 영향
