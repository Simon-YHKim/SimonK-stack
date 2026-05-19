---
name: growth-engine
description: "Use when the user asks to set up marketing tools, growth infrastructure, or user engagement systems—triggers \"마케팅 도구 세팅\", \"푸시 알림 구현\", \"이메일 시스템\", \"A/B 테스트\", \"어트리뷰션\", \"setup growth tools\", \"add push notifications\", \"email marketing\", \"feature flags\". Produces growth stack setup (email via Resend/SendGrid, push via OneSignal/FCM, attribution via Branch, A/B via GrowthBook/PostHog), lifecycle email sequences, and retention automation."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# growth-engine

마케팅/그로스 도구를 통합 세팅하는 skill.

## 발동 조건

- "마케팅 도구 세팅해줘", "푸시 알림 구현", "이메일 시스템 만들어줘"
- "A/B 테스트 세팅", "어트리뷰션 추적", "피처 플래그"
- app-dev-orchestrator 후반 단계에서 호출

## 그로스 스택 구성

| 채널 | 추천 | 대안 |
|---|---|---|
| **트랜잭션 이메일** | Resend | SendGrid, AWS SES |
| **마케팅 이메일** | Customer.io | Brevo, Mailchimp |
| **푸시 알림** | OneSignal | FCM 직접, Expo Push |
| **딥링크/어트리뷰션** | Branch | AppsFlyer, Adjust |
| **피처 플래그** | GrowthBook | LaunchDarkly, PostHog |
| **A/B 테스트** | PostHog / GrowthBook | Optimizely |
| **인앱 메시지** | Intercom | Drift, Chatwoot (OSS) |

## 라이프사이클 이메일 시퀀스

```
가입 직후 (D0):
  → 환영 이메일 + 핵심 기능 1개 안내

D1 (미활성):
  → "어제 시작하셨죠? 이것부터 해보세요"

D3 (활성):
  → 고급 기능 소개

D7 (미복귀):
  → "돌아오세요" + 한정 혜택

D14 (미전환):
  → Pro 무료 체험 제안

구독 취소 (D0):
  → 이유 설문 + 윈백 쿠폰

결제 실패 (D1/D3/D7):
  → Dunning 이메일 시퀀스
```

## A/B 테스트 프레임워크

1. **가설**: "X를 Y로 바꾸면 Z 지표가 N% 개선될 것"
2. **최소 표본**: MDE 기반 계산 (보통 1000+ per variant)
3. **기간**: 최소 1 full week (요일 효과)
4. **의사결정**: p < 0.05 + 실질적 유의미성

## 피처 플래그 패턴

```typescript
if (featureFlag('new_pricing_page')) {
  return <NewPricingPage />;
}
return <OldPricingPage />;
```

용도: 점진적 롤아웃, A/B, kill switch, 베타 프리뷰

## 검증 체크리스트

- [ ] 이메일 발송 + 수신 확인 (스팸 폴더 아님)
- [ ] 푸시 알림 수신 (iOS + Android)
- [ ] 딥링크 클릭 → 앱 내 정확한 화면 이동
- [ ] 피처 플래그 on/off 즉시 반영
- [ ] A/B 테스트: 균등 분배 + 이벤트 기록
- [ ] Unsubscribe 동작 (CAN-SPAM, 한국 광고법)

## Related Skills

- `analytics-integrator` — 이벤트 기반 세그멘트 연동
- `monetization-planner` — 전환율 최적화 목표 정의
- `revenue-scenario-tester` — 전체 흐름 검증

