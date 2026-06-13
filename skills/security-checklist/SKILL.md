---
name: security-checklist
description: "Use when the user asks for a security audit of a web app—\"RLS 확인\", \"Supabase 보안\", \"rate limit 점검\", \"예산 한도\", \"구독 상태 변조 방지\", \"check RLS policies\", \"rate limiting audit\", \"API cost cap\"—and run adversarial tests across the four pillars: Row Level Security, subscription/role tampering, dual-layer rate limiting (user + IP), and budget caps (provider/app/user). Produces a checklist + 5 adversarial SQL queries per pillar ready for a regression suite."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.0
author: simon
---

# Security Checklist

RLS, 구독 상태, Rate Limit, 예산 한도 4개 영역의 적대적 감사. 각 영역은 체크리스트 + 적대적 테스트 + 회귀 테스트 TDD 템플릿을 제공한다.

## When to use

- 새 기능 개발 후 배포 전
- 정기 보안 점검 (월 1회 권장)
- `/cso` 실행 전 사전 감사로
- 사용자가 "보안 점검", "RLS 확인", "rate limit 넣어줘", "비용 폭탄 방지" 등 요청

## Workflow

### A. RLS 시나리오 감사 (Supabase/Postgres)

#### 체크리스트
- [ ] 모든 사용자 데이터 테이블 `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY`
- [ ] `pg_policies` 뷰로 정책 누락 테이블 스캔:
  ```sql
  SELECT schemaname, tablename FROM pg_tables
  WHERE schemaname = 'public'
    AND tablename NOT IN (SELECT tablename FROM pg_policies);
  ```
- [ ] `service_role` 키는 서버 전용 (Edge Function, API route). 클라이언트 번들에 절대 금지
- [ ] 클라이언트는 `anon` key + RLS 만 사용
- [ ] `SECURITY DEFINER` 함수 사용 시 `search_path` 고정 (`SET search_path = public`)

#### 적대적 테스트 5종

1. **Cross-user SELECT**: A 계정으로 로그인 후 B의 `user_id` 로 SELECT/UPDATE/DELETE → **모두 실패 기대**
2. **Anon role 접근**: JWT 없이 민감 테이블 접근 → **실패 기대**
3. **권한 상승 UPDATE**: `UPDATE users SET role = 'admin' WHERE id = auth.uid()` → **실패 기대**
4. **JWT 위조·만료**: 만료 토큰·위조 서명 → **401 기대**
5. **Policy 누락 스캔**: 위 쿼리로 RLS 없는 테이블 0개 확인

#### 회귀 테스트 TDD

`tests/security/rls.test.ts` 에 위 5종을 Vitest/Jest 로 작성. CI 필수 경로.

---

### B. 구독 상태 변경 취약점

#### 원칙
클라이언트는 **절대** 민감 필드를 수정할 수 없다. 서버 측 웹훅 (Stripe/Toss/Iamport) 만이 유일한 변경 경로.

#### 민감 필드 화이트리스트
```
subscription_tier, plan, is_premium, credits, role, is_admin,
trial_ends_at, subscription_status, stripe_customer_id
```

#### 체크리스트
- [ ] 위 필드들은 RLS `WITH CHECK` 로 클라이언트 UPDATE 에서 제외
- [ ] 웹훅 엔드포인트 3종 세트:
  - HMAC 서명 검증 (Stripe: `stripe-signature` / Toss: `TossPayments-Signature`)
  - `idempotency-key` 저장 + 중복 요청 차단
  - Timestamp 5분 window 검증 (재전송 공격 방지)
- [ ] `audit_log` 테이블: `{id, who, when, from_value, to_value, source, ip}` — 민감 필드 변경 시 자동 기록
- [ ] Stripe/Toss 는 raw body 로 서명 검증 (파싱된 JSON 아님)

#### 적대적 테스트

1. **Direct PATCH**: `PATCH /api/users/me {subscription_tier: 'pro'}` → **403**
2. **GraphQL mutation**: `updateUser(input: {role: admin})` → **403**
3. **웹훅 서명 조작**: 잘못된 signature → **400**
4. **중복 웹훅**: 같은 idempotency-key 2회 → 1회만 처리
5. **타임스탬프 재전송**: 1시간 전 raw body 재전송 → **400**

#### 관련 Gstack 호출
감사 후 `/cso daily` 또는 `/cso comprehensive` 로 전체 인프라 감사 연계.

---

### C. 이중 Rate Limit

#### 원칙
`user_id` 와 `ip` 2중 키를 **동시에** 적용. 어느 한 쪽만 막으면 우회 가능.

#### 계층
1. **Edge (Cloudflare / Vercel)**: IP 기반. DDoS·봇 1차 차단. WAF Rules + Rate Limiting Rules
2. **App (Fastify/Next API)**: user_id 기반. 로그인 사용자 한도. `@fastify/rate-limit` + Redis / Upstash
3. **Provider**: OpenAI / Anthropic / Stripe 자체 한도 (사후 관찰용)

#### 티어별 차등
```
anon      → 분당 10 req
STANDARD  → 분당 60, 일일 1000
PRIME     → 분당 300, 일일 10000
```

#### 엔드포인트별 한도 (권장치)
- **로그인/회원가입/비번재설정**: IP 당 **분당 5**. 5회 초과 시 CAPTCHA
- **LLM 호출**: user 당 분당 N + 일일 상한 (티어별)
- **파일 업로드**: 시간 당 MB 한도 (예: STANDARD 100MB/h)
- **검색 API**: user 당 분당 30
- **웹훅 엔드포인트**: IP 당 분당 100 (가짜 웹훅 공격 완화)

#### 응답 포맷
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1728000000
```

#### 분산 저장소
- Redis (Upstash 권장 — serverless 호환)
- Cloudflare KV / Durable Objects (Workers)
- DynamoDB (AWS)

---

### D. 예산 한도 (3계층)

#### 원칙
비용 폭탄 방지는 **3계층 방어**: Provider hard cap → App soft cap → User quota.

#### Layer 1. Provider
- **OpenAI**: 대시보드에서 organization 월 hard budget 설정. 초과 시 자동 차단
- **Anthropic**: Console에서 workspace spend limit
- **GCP/AWS**: Budget alert + auto-stop 스크립트 (SNS + Lambda)
- **Stripe**: 결제 한도 자체는 없으나, 계좌 잔고 모니터링

#### Layer 2. App
Redis 카운터로 일/월 집계:
```
key: cost:openai:2026-04:total
key: cost:openai:2026-04-12:total
```
임계치 (예: 월 예산 80%) 도달 시 자동 차단 + 이메일/Slack 알림.

#### Layer 3. User
`user_quotas` 테이블:
```sql
user_id | credits_remaining | period_start | period_end | tier
```
소진 시 `HTTP 402 Payment Required` 응답.

#### Circuit Breaker
외부 API 호출은 circuit breaker 로 감쌀 것:
- 라이브러리: `opossum` (Node), `pybreaker` (Python)
- 설정: error threshold 50%, reset 60s, half-open 1 req

---

## Checklist (종합)

실행 시 다음을 모두 체크:

- [ ] A. RLS 5종 테스트 모두 통과, `pg_policies` 스캔 clean
- [ ] A. `tests/security/rls.test.ts` CI 통합
- [ ] B. 민감 필드 9종 클라이언트 UPDATE 차단 확인
- [ ] B. 웹훅 3종 세트 (서명·idempotency·timestamp) 전부 구현
- [ ] B. `audit_log` 테이블 생성 + 민감 필드 트리거
- [ ] C. Edge + App 이중 레이어 활성화
- [ ] C. 로그인 IP rate limit (분당 5) 구현
- [ ] C. 티어별 차등 한도 구현
- [ ] D. Provider hard budget 설정 완료
- [ ] D. Redis 비용 카운터 구현
- [ ] D. user_quotas 테이블 + 402 응답
- [ ] D. Circuit breaker 적용

감사 종료 시 `/cso daily` 또는 `/cso comprehensive` 호출.

---

## Anti-patterns

- ❌ `ENABLE RLS` 만 쓰고 `FORCE RLS` 생략 — 테이블 owner 는 우회 가능
- ❌ 클라이언트에서 `supabase.from('users').update({role: 'admin'})` 차단 없이 허용
- ❌ Stripe 웹훅 서명 검증 skip
- ❌ IP rate limit 만 적용 (로그인 사용자 우회 가능)
- ❌ 예산 한도 없이 LLM API 를 프로덕션 오픈
- ❌ `service_role` 키를 프론트엔드 번들에 포함
- ❌ 적대적 테스트 없이 "구현했으니 안전"

---

## Related skills

- `authz-designer` — 권한 모델 설계 (B 구독 상태와 짝)
- `paid-api-guard` — 유료 API 6층 방어 (C/D 강화)
- `/cso` — Gstack 전체 인프라 보안 감사
- `/codex challenge` — 적대적 리뷰
- `simon-tdd` — 회귀 테스트 작성
