---
name: payment-integrator
description: "Use when the user asks to implement payment or subscription—triggers \"결제 붙여줘\", \"구독 시스템 만들어줘\", \"Stripe 연동\", \"PortOne 세팅\", \"인앱결제\", \"implement payments\", \"add subscription\", \"billing system\". Produces payment integration code (Stripe/PortOne/RevenueCat), webhook handlers, subscription state machine, receipt verification, and sandbox test suite. Covers card, 간편결제, in-app purchase, and crypto payments."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# payment-integrator

결제/구독 시스템을 실제 코드로 구현하는 skill.

## 발동 조건

- "결제 붙여줘", "구독 시스템 만들어줘", "Stripe 연동"
- "인앱결제 추가", "PortOne 세팅", "RevenueCat 연동"
- monetization-planner 실행 후 자동 체인

## Provider 선택 Decision Tree

```
플랫폼?
├─ 모바일 앱 (iOS/Android)
│   ├─ 구독 → RevenueCat (Apple IAP + Google Play Billing 통합)
│   └─ 일회성 → 네이티브 IAP SDK
├─ 웹 (글로벌)
│   └─ Stripe (카드 + 구독 + 인보이스)
├─ 웹 (한국 타겟)
│   ├─ 간편결제 필요 → PortOne (Toss/Kakao/Naver 통합)
│   └─ 카드만 → Stripe Korea
└─ 1인 개발 (세금 귀찮)
    └─ Paddle 또는 Lemon Squeezy (MoR)
```

## 구현 단계

### 1. 스키마 설계

```sql
-- 구독 상태 머신
CREATE TYPE subscription_status AS ENUM (
  'trialing', 'active', 'past_due', 'canceled', 'paused', 'expired'
);

CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  plan_id TEXT NOT NULL,
  status subscription_status NOT NULL DEFAULT 'trialing',
  provider TEXT NOT NULL, -- stripe | portone | revenuecat
  provider_subscription_id TEXT,
  current_period_start TIMESTAMPTZ,
  current_period_end TIMESTAMPTZ,
  cancel_at_period_end BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  subscription_id UUID REFERENCES subscriptions(id),
  amount INTEGER NOT NULL, -- cents
  currency TEXT NOT NULL DEFAULT 'krw',
  status TEXT NOT NULL, -- succeeded | failed | refunded | disputed
  provider_payment_id TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

### 2. Webhook 핸들러

필수 이벤트:
- `payment_intent.succeeded` / `charge.failed`
- `customer.subscription.created` / `updated` / `deleted`
- `invoice.payment_failed` (dunning)
- `charge.dispute.created`

원칙:
- 반드시 **서명 검증** (HMAC)
- 반드시 **멱등성** (Idempotency-Key로 중복 처리 방지)
- Raw body로 서명 계산 (파싱 전)

### 3. 구독 상태 머신

```
trialing ──[trial_end]──→ active
active ──[payment_failed]──→ past_due
past_due ──[retry_success]──→ active
past_due ──[max_retries]──→ canceled
active ──[user_cancel]──→ active (cancel_at_period_end=true) ──[period_end]──→ canceled
canceled ──[resubscribe]──→ active
```

### 4. 한국 특이사항

- 자동갱신 사전 고지 (갱신 7일 전 이메일/SMS 의무)
- 현금영수증/세금계산서 발행 로직
- 전자상거래법 7일 청약철회 (디지털 콘텐츠 예외 조건 명시)
- PG사별 정산 주기 차이 (D+2 ~ D+7)

### 5. Sandbox 테스트

- Stripe: `4242424242424242` (성공), `4000000000000002` (거절)
- PortOne: 테스트 모드 PG 설정
- RevenueCat: Sandbox receipt

## 검증 체크리스트

- [ ] Webhook 서명 검증 구현
- [ ] 멱등성 처리 (같은 이벤트 2번 와도 안전)
- [ ] 구독 상태 머신 전이 테스트
- [ ] 환불 로직 (전액/부분)
- [ ] Dunning (결제 실패 시 재시도 로직)
- [ ] 한국 법규: 자동갱신 고지, 청약철회
- [ ] revenue-scenario-tester 통과

## Related Skills

- `monetization-planner` — 어떤 모델을 구현할지 결정
- `paid-api-guard` — 결제 보안 6층 방어 (기존 skill과 연계)
- `auth-builder` — 유료 tier에 따른 권한 분리
- `revenue-scenario-tester` — Payment Agent + Subscription Agent 검증
- `subscription-manager-selector` — 구독 결제·관리 도구 (Lemon Squeezy / RevenueCat / Adapty) 선택

