---
name: subscription-manager-selector
description: "Use when the user needs to choose a subscription management platform—triggers "구독 관리 서비스", "RevenueCat vs Stripe", "구독 플랫폼 비교", "subscription management", "billing platform", "which subscription service". Produces comparison of subscription management services (RevenueCat/Stripe Billing/Chargebee/Paddle/Lemon Squeezy), recommendation based on platform and scale, and integration guide for the selected service."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# subscription-manager-selector

구독 관리 서비스를 비교하고 최적을 추천하는 skill.

## 발동 조건

- "구독 관리 서비스 뭐 쓰지", "RevenueCat vs Stripe Billing"
- "구독 플랫폼 비교", "billing platform 추천"
- payment-integrator에서 구독 모델 구현 시 연동

## 서비스 카탈로그

| 서비스 | 플랫폼 | 가격 | 핵심 기능 | 적합 |
|---|---|---|---|---|
| **RevenueCat** | iOS+Android | 매출 $2.5K 이하 무료 → 1% | IAP 통합, 영수증 검증, A/B | 모바일 앱 |
| **Stripe Billing** | 웹 | 0.5-0.8% | 인보이스, 프로레이션, 쿠폰 | 웹 SaaS |
| **Paddle** | 웹 | 5%+50¢ (MoR) | 세금 자동, 글로벌 | 1인 글로벌 SaaS |
| **Lemon Squeezy** | 웹 | 5%+50¢ (MoR) | Paddle 대안, 심플 | 인디 개발자 |
| **Chargebee** | 웹+앱 | $249/월~ | 엔터프라이즈급, 매출 인식 | B2B SaaS |
| **Recurly** | 웹 | $0~매출 기반 | Dunning 최적화 | 미디어/구독 |

## Decision Tree

```
플랫폼?
├─ 모바일 앱 (iOS/Android)
│   └─ RevenueCat (IAP 통합 + 크로스 플랫폼)
├─ 웹 SaaS
│   ├─ 세금 직접 처리 OK → Stripe Billing (가장 유연)
│   ├─ 세금 자동 처리 원함 → Paddle 또는 Lemon Squeezy
│   └─ 엔터프라이즈 → Chargebee
└─ 웹 + 모바일 통합
    ├─ RevenueCat (모바일) + Stripe (웹) 조합
    └─ 또는 Chargebee (통합)
```

## 핵심 비교

| 기능 | RevenueCat | Stripe | Paddle | Lemon Squeezy |
|---|---|---|---|---|
| Apple IAP 통합 | ✅ | ❌ | ❌ | ❌ |
| Google Play 통합 | ✅ | ❌ | ❌ | ❌ |
| MoR (세금 대행) | ❌ | ❌ | ✅ | ✅ |
| 프로레이션 | ❌ | ✅ | ✅ | ✅ |
| Dunning 자동화 | ❌ | ✅ | ✅ | ✅ |
| 커스텀 UI | SDK | 완전 자유 | Checkout 위젯 | Checkout 위젯 |
| 한국 결제 | ❌ (IAP만) | PortOne 필요 | 제한적 | 제한적 |

## Related Skills

- `payment-integrator` — 선택된 서비스 실제 구현
- `monetization-planner` — 구독 모델 설계
- `global-payment-planner` — 글로벌 세금 처리
- `revenue-scenario-tester` — Subscription Agent 검증
