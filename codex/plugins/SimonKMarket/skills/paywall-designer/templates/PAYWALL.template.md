# Paywall Design — <서비스명>

> 작성: paywall-designer · 상류: MONETIZATION.md · 하류: payment-integrator
> 모든 수치는 측정으로 검증할 것. 가설은 "(가설)"로 표기.

## 1. 컨텍스트

- 플랫폼: <모바일 IAP / 웹 / 둘 다>
- 티어·가격점: <Free / Pro ₩9,900월·₩7,900월(연) / ...>  (출처: MONETIZATION.md)
- Aha 순간: <유저가 가치를 처음 체감하는 행동>
- 현재 측정 수단: <GA4 / PostHog / 없음 → 5장에서 셋업>

## 2. 트리거 규칙 · 타이밍

| ID | 트리거 유형 | 발동 시점 | wall 유형 | surface |
|----|------------|----------|----------|---------|
| T1 | Aha-gated  | <예: 첫 결과 생성 직후> | soft | 바텀시트 |
| T2 | Limit-reached | <무료 N회 소진> | hard | 전체화면 |
| T3 | Feature-gated | <유료 탭 진입> | hard | 전체화면 |

빈도 상한: 세션당 <1>회, 일 <N>회. 닫기(X) 항상 허용.

## 3. 가치 프레이밍 카피 (기본안)

- Headline(결과 1개): "<...>"
- Subcopy(근거 1줄): "<...>"
- CTA: "<예: 7일 무료로 시작>"
- Secondary: "<나중에>"

변형 세트는 `paywall-copy-variants.md` 참조.

## 4. 가격 레이아웃 (앵커링·디코이)

| 순서 | 플랜 | 표시가 | 청구 | 배지 | 비고 |
|------|------|-------|------|------|------|
| 1(위) | Pro 연간 | ₩7,900/월 | 연 ₩94,800 | 추천·기본선택 | anchor·기본값 |
| 2 | Pro 월간 | ₩9,900/월 | 월 청구 | — | 디코이(연간 유리해 보이게) |

- 실제 청구 금액·주기 명확 표기(기만 금지).
- 트라이얼: <카드 선등록 / 미등록>, 길이 <7일>, 종료 <1~2>일 전 고지.

## 5. 측정 이벤트

`scripts/gen-paywall-events.mjs` 산출 스키마를 analytics-integrator 이벤트 분류에 병합.

| 이벤트 | 시점 | 속성 |
|--------|------|------|
| paywall_trigger | 조건 충족 | trigger_type, surface, tier_context |
| paywall_view | 노출 | variant, plan_default, entry_point |
| paywall_plan_select | 플랜 탭 | plan_id, billing_period |
| paywall_cta_tap | 결제 탭 | plan_id, variant |
| paywall_dismiss | 닫기 | dwell_ms, reason |
| purchase_success | 결제 완료 | plan_id, amount, trial (payment-integrator) |

추적 지표: View→Purchase, Trigger→View 노출률, dwell, 트라이얼 전환율, 환불율.

## 6. A/B 백로그 (한 번에 한 변수)

| 우선 | 실험 | 변수 | 북극성 | 코호트 |
|------|------|------|--------|--------|
| 1 | 가격점 ₩9,900 vs ₩12,900 | price | ARPU | 신규만, sticky |
| 2 | 트리거 T1 vs T2 | timing | View→Purchase | 신규만 |
| 3 | 손실 vs 이득 카피 | copy | 전환율 | 신규만 |

WTP 리서치: Van Westendorp PSM <예정/완료>, Gabor-Granger <예정>.

## 7. 미해결·리스크

- <예: 모바일 IAP 가격은 스토어 가격 티어에 종속 → 임의 가격점 불가>
- <예: 기존 유저 가격 변경 금지(신규 코호트만)>
