---
name: paid-api-guard
description: Use when the user integrates or audits paid third-party APIs (Stripe, Toss, Iamport, Twilio, SendGrid, Google/Naver/Kakao Maps)—triggers include "Stripe 연동", "토스 결제", "Twilio SMS", "결제 API 보안", "webhook signature", "idempotency", "prevent API cost explosion", "protect against leaked keys". Produces a 6-layer defense checklist (network boundary, signing/idempotency, abuse detection, payment hardening, key-leak response, observability) plus 5 adversarial tests and an API design review.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.0
author: simon
---

# Paid API Guard

LLM 외 유료 API (결제·SMS·지도·금융·이메일) 에 대한 6층 방어 및 API 설계 리뷰.

## When to use

- Stripe / Toss / Iamport / PayPal 결제 통합 시
- Twilio / NCP SENS / Aligo SMS
- 네이버·카카오·구글 Maps (유료 tier)
- SendGrid / Postmark / Resend 이메일
- 외부 API 키가 프론트엔드 번들에 들어갈 위험
- 사용자가 "API 보안", "결제 연동 안전하게", "비용 폭탄 방지" 요청

## Workflow — 6층 방어

### Layer 1. 네트워크 경계

- 유료 API egress 는 **단일 서브넷** 에서만 (Vercel/Fly 기본 아님 → BFF 계층 도입)
- **브라우저 직접 호출은 피하라** — 항상 BFF (Backend-for-Frontend) 경유. 프론트에서 직접 호출하면 키가 번들에 포함되거나 CORS 우회 공격이 가능해진다
- Cloudflare WAF 로 선차단: 알려진 봇 UA, 국가 제한(서비스 지역 외)
- API 키는 서버 환경변수만 (`process.env.STRIPE_SECRET_KEY`), `NEXT_PUBLIC_*` 절대 금지

### Layer 2. 서명·멱등성

- 클라이언트 → BFF 는 HMAC + nonce + timestamp (5분 window)
- 결제·비용 요청은 `Idempotency-Key` 헤더 필수 (Stripe 표준)
- 웹훅은 **raw body** 로 서명 검증. JSON 파싱 후 재직렬화 금지 (서명 깨짐)
- nonce 는 Redis 에 5분 TTL 저장, 중복 시 거부

```ts
// 예시: Stripe 웹훅 (Next.js App Router)
export async function POST(req: Request) {
  const rawBody = await req.text();
  const sig = req.headers.get('stripe-signature')!;
  try {
    const event = stripe.webhooks.constructEvent(
      rawBody, sig, process.env.STRIPE_WEBHOOK_SECRET!
    );
    // idempotency: event.id 로 중복 체크
    const already = await redis.get(`stripe:evt:${event.id}`);
    if (already) return new Response('ok', { status: 200 });
    await redis.setex(`stripe:evt:${event.id}`, 86400, '1');
    // ... 처리
  } catch { return new Response('bad sig', { status: 400 }); }
}
```

### Layer 3. 남용 탐지

- 사용자별 비용 대시보드 (일·월 누적)
- 이상 패턴 자동 감지:
  - 평소 대비 10배 이상 호출 → 자동 일시정지 + 이메일
  - 신규 계정 24시간 내 결제 시도 3회 이상 → 수동 승인
  - 동일 IP 에서 여러 계정 빠른 결제 → 차단
- Cloudflare Turnstile / hCaptcha (로그인·회원가입·결제)
- 신규 계정 24시간 한도 축소 (정상치 10%)

### Layer 4. 결제 전용

- 시크릿 매니저 별도 네임스페이스 (`stripe/*`, `toss/*`)
- 카드번호 취급 금지: Stripe Elements / Toss SDK 로 tokenize 후 서버에는 token 만
- 환불·취소는 2차 승인 (OTP 또는 관리자 승인)
- **금액 서버 재계산**: 클라이언트가 보낸 amount 는 신뢰하지 말고, 서버가 DB 의 상품 가격 × 수량으로 재계산한다. 프론트 조작 한 번으로 0원 결제가 가능해지는 가장 흔한 실수
  ```ts
  // 금액은 DB 의 상품 가격 × 수량으로 서버가 재계산
  const amount = products[productId].price * quantity;
  stripe.paymentIntents.create({ amount, currency: 'krw' });
  ```

### Layer 5. 키 탈취 대응

- **Canary 키** 배치: 가짜 키 (유효하지 않음) 를 의도적으로 노출 → 사용 감지 시 알림
- `docs/INCIDENT-PLAYBOOK.md` 작성:
  - 탐지 경로 (Stripe 대시보드 알림·CloudWatch·사용자 신고)
  - 1차 대응 (키 즉시 로테이션)
  - 2차 대응 (피해 범위 산정)
  - 3차 대응 (사용자 공지)
- GitHub push protection ON + trufflehog pre-commit
- 90일 키 로테이션 자동화 (캘린더 리마인더 + 스크립트)

### Layer 6. 관측

모든 외부 API 호출 로깅:
```json
{
  "user_id": "uuid",
  "endpoint": "stripe.paymentIntents.create",
  "cost_estimate_krw": 1000,
  "status": "succeeded",
  "latency_ms": 234,
  "idempotency_key": "...",
  "request_id": "..."
}
```
저장소: BigQuery / ClickHouse / Datadog.
주간 `/retro` 에 `external_api_cost` 섹션 추가 → 이상 추세 검출.

---

## 적대적 테스트 5종

1. **프론트 번들 grep**:
   ```bash
   npm run build && grep -rE "(sk_live|pk_live|STRIPE_SECRET|TOSS_SECRET)" .next/static/ dist/
   ```
   → **0건** 기대
2. **BFF 우회 직접 호출**: 브라우저에서 Stripe API 직접 fetch → **네트워크 차단 또는 403**
3. **Idempotency 중복 결제**: 동일 `Idempotency-Key` 10회 → **1회만** 성공
4. **웹훅 서명 조작**: 랜덤 signature → **400**
5. **토큰 탈취 시뮬레이션**: 평소 10배 호출 → **이상 탐지 발동·자동 일시정지**

---

## API 설계 리뷰 (설계 단계에서 사용)

### 프로토콜 선택
| 옵션 | 언제 |
|---|---|
| REST | 캐싱·CDN 친화, 공개 API, 대부분 기본 |
| GraphQL | 복잡한 중첩·페이로드 최적화, 클라이언트 주도 |
| tRPC | 풀스택 TS, 내부 API, 타입 안전 |
| gRPC | 서비스 간 내부 통신, 낮은 지연 |

### 체크리스트
- [ ] **N+1 쿼리** 탐지: GraphQL 은 DataLoader 필수, REST 는 JOIN 프리로드
- [ ] **Cursor 페이지네이션**: offset 금지 (성능·중복 이슈)
- [ ] **ETag + stale-while-revalidate**: 정적 리소스·읽기 전용 데이터
- [ ] **배치 엔드포인트**: N개 ID 를 한 번에 (`POST /users/batch`)
- [ ] **OpenAPI 자동 생성**: 소스 코드 주석 → 스키마. Swagger UI
- [ ] **에러 포맷 통일**: RFC 7807 (`application/problem+json`) 또는 자체 표준
- [ ] **버전 전략**: `/v1`, `/v2` 또는 `Accept: application/vnd.app.v2+json`

---

## Checklist (전체)

- [ ] Layer 1. BFF 계층 분리, 브라우저 직접 호출 0건
- [ ] Layer 1. 프론트 번들 grep 결과 시크릿 0건
- [ ] Layer 2. 웹훅 raw body 서명 검증
- [ ] Layer 2. Idempotency-Key 전 결제 엔드포인트 적용
- [ ] Layer 3. 사용자별 비용 대시보드
- [ ] Layer 3. Turnstile/hCaptcha 적용
- [ ] Layer 4. 금액 서버 재계산
- [ ] Layer 4. 환불 2차 승인
- [ ] Layer 5. `docs/INCIDENT-PLAYBOOK.md` 작성
- [ ] Layer 5. trufflehog + push protection
- [ ] Layer 6. 호출 로깅 + BigQuery/ClickHouse
- [ ] 적대적 테스트 5종 통과
- [ ] API 설계 체크리스트 완료

## Anti-patterns

- ❌ Stripe secret key 를 `NEXT_PUBLIC_STRIPE_SECRET` 로 노출
- ❌ 클라이언트에서 amount 를 서버로 전송하고 그대로 결제
- ❌ 웹훅 JSON.parse 후 서명 검증 (서명 깨짐)
- ❌ Idempotency-Key 없이 결제 API 반복 호출
- ❌ 90일 넘도록 키 로테이션 안 함
- ❌ 사용자별 비용 상한 없이 production 오픈
- ❌ 카드번호를 서버 DB 에 저장 (PCI DSS 위반)

## Related skills

- `security-checklist` — C(RateLimit), D(예산) 섹션 교차
- `authz-designer` — 결제 엔드포인트 인가
- `/cso comprehensive` — 전체 인프라 감사
- `simon-tdd` — 적대적 테스트 작성
