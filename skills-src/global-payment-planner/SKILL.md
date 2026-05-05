---
name: global-payment-planner
description: "Use when the user needs to handle payments across multiple countries—triggers "글로벌 결제", "해외 결제", "국가별 규제", "다국가 결제", "cross-border payment", "international billing", "payment compliance", "multi-currency". Produces country-specific payment regulation summary, optimal PG combination per region, tax/VAT handling strategy, currency conversion approach, and compliance checklist per jurisdiction."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# global-payment-planner

국가별 결제 규제 + 최적 PG 조합 + 세금/환율 처리.

## 발동 조건

- "글로벌 결제 어떻게 해", "해외 결제 붙여줘", "국가별 규제 확인"
- "다국가 결제 시스템", "cross-border payment"
- payment-integrator에서 글로벌 요구사항 감지 시

## 주요 국가별 규제

| 국가/지역 | 필수 결제수단 | 세금 | 주요 규제 |
|---|---|---|---|
| **한국** | 카드, 간편결제 (Kakao/Naver/Toss) | VAT 10% | 전자상거래법, 자동갱신 고지 |
| **미국** | 카드, ACH, Apple/Google Pay | Sales Tax (주별) | PCI-DSS, CCPA |
| **EU** | 카드, SEPA, iDEAL(NL), Bancontact(BE) | VAT 19-27% | PSD2/SCA, GDPR |
| **일본** | 카드, 편의점 결제, PayPay | 소비세 10% | 자금결제법 |
| **동남아** | GrabPay, GCash, OVO | 국가별 상이 | 현지 PG 필수 |
| **중국** | Alipay, WeChat Pay | VAT 6-13% | ICP 라이선스, 데이터 현지화 |

## 최적 PG 조합

```
글로벌 기본: Stripe (190+ 국가)
  + 한국 보강: PortOne (Toss/Kakao/Naver)
  + 동남아 보강: Xendit 또는 PayMongo
  + MoR (세금 자동): Paddle 또는 Lemon Squeezy

1인 개발자 최소 구성:
  Paddle (MoR) — 전 세계 세금 자동 처리, 단일 API
```

## 환율/통화 처리 전략

| 전략 | 장점 | 단점 |
|---|---|---|
| **단일 통화 (USD)** | 단순 | 환율 부담 고객에게 |
| **현지 통화 표시** | UX 좋음 | 환율 변동 리스크 |
| **MoR 위임** | 모든 것 자동 | 수수료 높음 (5-10%) |

## VAT/세금 자동화

- **Paddle/Lemon Squeezy**: MoR로 세금 완전 위임
- **Stripe Tax**: 자동 세율 계산 (별도 신고 필요)
- **수동**: 국가별 세율 테이블 + 인보이스 생성

## Related Skills

- `payment-integrator` — 선택된 PG 실제 구현
- `pink-tax-advisor` — 지역별 PPP 가격 차등
- `revenue-scenario-tester` — KR-Compliance Agent 활용
