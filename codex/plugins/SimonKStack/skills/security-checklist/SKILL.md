---
name: security-checklist
description: "Use when auditing web app security—\"RLS 확인\", \"구독 상태 변조 방지\", \"rate limit 점검\", \"예산 한도\", \"check RLS policies\", or \"API cost cap\". Check RLS/grants, privileged fields/webhooks, user/IP limits, and provider/app/user spending controls. Produces an evidence-labeled checklist and regression test plan without paid calls or production changes."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.0.1
author: simon
---

# Security Checklist

RLS, 구독 상태, Rate Limit, 예산 한도 4개 영역의 적대적 감사. 요청이 특정 영역이면 그 영역을 먼저 심층 점검하고, 나머지는 적용 여부와 미확인 위험만 짧게 보고한다. 기본은 코드·설정의 읽기 전용 검토와 무료 로컬 테스트다. 운영 DB 변경, 결제 설정 변경, 실제 결제·유료 API 호출, 외부 메시지 전송은 이 스킬이 승인하지 않는다.

## When to use

- 새 기능 개발 후 배포 전
- 정기 보안 점검 (월 1회 권장)
- `/cso` 실행 전 사전 감사로
- 사용자가 "보안 점검", "RLS 확인", "rate limit 넣어줘", "비용 폭탄 방지" 등 요청

## Workflow

### A. RLS 시나리오 감사 (Supabase/Postgres)

#### 체크리스트
- [ ] 노출된 스키마의 테이블에서 RLS 활성화(`pg_class.relrowsecurity`)와 `anon`/`authenticated` GRANT를 각각 확인한다. 소유자 접근도 RLS 대상이어야 할 때만 `FORCE ROW LEVEL SECURITY`를 검토한다. `BYPASSRLS` 역할에는 FORCE도 적용되지 않는다.
- [ ] `pg_policies`의 정책 존재만으로 RLS 활성화나 안전성을 판정하지 않는다. 읽기 전용 목록 예시(스키마·테이블·권한 맥락에서 해석):
  ```sql
  SELECT n.nspname AS schema_name, c.relname AS table_name,
         c.relrowsecurity AS rls_enabled, c.relforcerowsecurity AS force_owner_rls,
         count(p.oid) AS policy_count
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
  LEFT JOIN pg_policy p ON p.polrelid = c.oid
  WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
  GROUP BY n.nspname, c.relname, c.relrowsecurity, c.relforcerowsecurity;
  ```
- [ ] Supabase secret/legacy `service_role` 키는 서버 전용. `BYPASSRLS`이므로 클라이언트 번들에 금지한다. 클라이언트는 publishable/legacy `anon` 키와 적절한 RLS·GRANT를 사용한다.
- [ ] 노출된 뷰와 `SECURITY DEFINER` 함수의 소유자 권한·EXECUTE GRANT·search_path를 별도 감사한다. 함수는 안전한 `search_path`(예: 빈 경로와 스키마 완전 지정)를 사용한다.

#### 적대적 테스트 5종

1. **Cross-user SELECT/UPDATE**: A의 토큰으로 B 행을 읽거나 수정 → 접근 거부 또는 0행/0건이어야 한다. 허용된 공유 관계는 정책대로 별도 시험한다.
2. **Anon role 접근**: 인증 없이 민감 테이블 접근 → 권한 거부 또는 0행이어야 한다.
3. **권한 상승 UPDATE**: 자신의 `role`/`is_admin` 변경 → 거부 또는 변경 0건; 행 소유권 정책만으로 열 변경을 막을 수 없다.
4. **JWT 위조·만료**: 유효하지 않은 서명·만료 토큰을 API 계층에서 거부하는지 확인한다. 로그아웃만으로 이미 발급된 JWT가 즉시 폐기된다고 가정하지 않는다.
5. **RLS 상태 스캔**: 위 쿼리에서 `rls_enabled=false`인 노출 테이블을 검토한다. 정책 0개는 RLS 활성 시 기본 거부이지 곧바로 데이터 누출은 아니다.

#### 회귀 테스트 TDD

실제 스키마에 맞춰 `scripts/rls-adversarial-tests.sql`의 읽기 전용 검토 항목과 권한별 회귀 테스트를 작성한다. 프로젝트가 Supabase CLI를 쓰면 `supabase/tests/`의 pgTAP와 `supabase test db`를 우선 검토한다. 운영 DB에 변형 쿼리를 실행하지 않는다.

---

### B. 구독 상태 변경 취약점

#### 원칙
클라이언트는 **절대** 민감 필드를 직접 수정할 수 없다. 서버의 신뢰된 경로(검증된 결제 웹훅, 권한을 확인한 관리자 작업 등)에서만 변경한다.

#### 보호할 민감 필드 예시 (실제 스키마에서 식별)
```
subscription_tier, plan, is_premium, credits, role, is_admin,
trial_ends_at, subscription_status, stripe_customer_id
```

#### 체크리스트
- [ ] RLS `WITH CHECK`는 행 조건이다. 민감 열은 별도 서버 전용 테이블 또는 클라이언트 역할의 열별 UPDATE 권한 제한으로 보호한다. 서버도 인증·인가를 재검사한다.
- [ ] 웹훅 엔드포인트는 공급자·이벤트 유형별 실제 계약을 확인한다:
  - Stripe는 원본 body·`Stripe-Signature`·엔드포인트 비밀로 서명과 타임스탬프를 검증한다.
  - TossPayments의 `tosspayments-webhook-signature`는 지원 이벤트 유형에만 존재한다. 모든 결제 이벤트가 서명된다고 가정하지 말고 공식 문서의 유형별 검증 경로를 확인한다.
  - 검증 후 공급자 이벤트 ID 또는 안정적인 비즈니스 키로 중복 처리 방지. 전송마다 바뀔 수 있는 전송 ID만으로 중복 결제 효과를 막는다고 가정하지 않는다. 원자적 처리 상태를 기록하고 비즈니스 작업 성공 뒤 완료 표시한다. 요청의 `Idempotency-Key`가 모든 웹훅에 있다고 가정하지 않는다.
- [ ] `audit_log` 테이블: `{id, who, when, from_value, to_value, source, ip}` — 민감 필드 변경 시 자동 기록
- [ ] 공급자 웹훅의 서명·재전송 방식, 실시간 상태 조회 필요성은 해당 이벤트 공식 문서로 확인한다.

#### 적대적 테스트

1. **Direct PATCH**: `PATCH /api/users/me {subscription_tier: 'pro'}` → 권한 거부 또는 값 불변 확인
2. **GraphQL mutation**: `updateUser(input: {role: admin})` → 권한 거부 또는 값 불변 확인
3. **서명 조작**: 서명을 제공하는 이벤트의 잘못된 서명 → 처리 거부 확인
4. **중복 웹훅**: 동일 공급자 이벤트 ID 재전송 → 비즈니스 효과 1회만 확인
5. **재전송**: 공급자별 유효기간/재전송 정책에 맞는 검증 확인. 모든 공급자에 5분을 강제하지 않는다.

#### 관련 Gstack 호출
전체 인프라 감사가 필요하면 `/cso daily` 또는 `/cso comprehensive`를 별도로 제안한다.

---

### C. 이중 Rate Limit

#### 원칙
`user_id` 와 `ip` 2중 키를 **동시에** 적용. 어느 한 쪽만 막으면 우회 가능.

#### 계층
1. **Edge (Cloudflare / Vercel)**: IP 기반. DDoS·봇 1차 차단. WAF Rules + Rate Limiting Rules
2. **App (Fastify/Next API)**: user_id 기반. 로그인 사용자 한도. `@fastify/rate-limit` + Redis / Upstash
3. **Provider**: OpenAI / Anthropic / Stripe 자체 한도 (사후 관찰용)

#### 티어별 차등 예시 (제품 요구·트래픽 기준으로 결정)
```
anon      → 분당 10 req
STANDARD  → 분당 60, 일일 1000
PRIME     → 분당 300, 일일 10000
```

#### 엔드포인트별 한도 예시 (고정 보안 기준 아님)
- **로그인/회원가입/비번재설정**: IP·계정별 시도 제한과 악용 방어를 검토. 예: 분당 5, 필요하면 CAPTCHA
- **LLM 호출**: user 당 분당 N + 일일 상한 (티어별)
- **파일 업로드**: 시간 당 MB 한도 (예: STANDARD 100MB/h)
- **검색 API**: user 당 분당 30
- **웹훅 엔드포인트**: 공급자 재시도·버스트를 수용하도록 별도 제한하고, IP 제한을 서명 검증의 대체로 삼지 않는다.

#### 응답 포맷 예시 (헤더와 상태는 실제 API 계약에 맞춤)
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
비용 폭탄 방지는 공급자 제한·앱 호출 전 예산 게이트·사용자별 할당량으로 분리한다. 알림/soft budget을 hard cap으로 표기하지 않는다. 공급자 설정을 볼 수 없으면 **미확인**으로 남긴다.

#### Layer 1. Provider
- **OpenAI**: 프로젝트 월 spend limit은 공식 문서상 soft threshold이며 API를 자동 차단하지 않는다. 조직/계정 제한도 현 계약·설정에서 별도 확인한다.
- **Anthropic**: Console의 현재 workspace 제한 및 초과 처리 방식은 계정 설정·공식 문서로 확인한다.
- **GCP/AWS**: Budget alert 자체는 정지 장치가 아니다. 자동 차단은 별도 검증된 제어가 있어야만 주장한다.
- **결제 공급자**: 결제 처리·환불·분쟁 제한과 알림은 LLM API 예산과 별개로 현재 계정 계약을 확인한다.

#### Layer 2. App
호출 전 원자적 예약·거부와 실제 비용 사후 정산을 구현한다. Redis 카운터는 집계의 한 구성요소다:
```
key: cost:openai:2026-04:total
key: cost:openai:2026-04-12:total
```
임계치(예: 월 예산 80%)에서 경고, 하드 차단선에서 신규 호출 거부를 별도 설정한다. 이메일/Slack 전송은 운영 승인 후 수행한다.

#### Layer 3. User
`user_quotas` 테이블:
```sql
user_id | credits_remaining | period_start | period_end | tier
```
소진 시 제품 API 계약에 맞는 오류와 재설정 시각을 응답한다. `402`를 모든 quota 실패의 표준으로 가정하지 않는다.

#### Circuit Breaker
장애·타임아웃 급증에는 circuit breaker를 검토한다. 이것만으로 비용 상한을 보장하지 않는다:
- 라이브러리: `opossum` (Node), `pybreaker` (Python)
- 예시 설정: error threshold 50%, reset 60s, half-open 1 req (실측에 맞게 조정)

---

## Checklist (종합)

실행 시 다음을 모두 체크:

- [ ] A. RLS 상태·GRANT·정책과 적대적 권한별 테스트 증거 확인
- [ ] A. 프로젝트의 RLS 회귀 테스트 CI 통합
- [ ] B. 실제 민감 필드의 클라이언트 UPDATE 차단 확인
- [ ] B. 공급자·이벤트별 서명/진위·중복·재전송 처리 확인
- [ ] B. `audit_log` 테이블 생성 + 민감 필드 트리거
- [ ] C. Edge + App 이중 레이어 활성화
- [ ] C. 로그인 IP·계정별 rate limit 구현
- [ ] C. 티어별 차등 한도 구현
- [ ] D. 공급자 설정의 hard/soft 구분과 관측 증거 기록
- [ ] D. 앱의 호출 전 원자적 비용 예약·거부 및 사후 정산 검증
- [ ] D. 사용자 quota 소진 응답과 우회 시험
- [ ] D. 장애 circuit breaker와 비용 게이트를 각각 검증

감사 종료 시 각 항목을 **통과/실패/미확인/비적용**으로 보고하고, 실행하지 않은 실험은 통과로 세지 않는다. `/cso` 확장은 필요할 때 별도 제안한다.

---

## Anti-patterns

- ❌ 정책이 있다는 이유만으로 RLS가 켜졌거나 안전하다고 단정
- ❌ 행 소유권 `WITH CHECK`만으로 `role` 같은 민감 열 UPDATE가 막힌다고 단정
- ❌ 클라이언트에서 `supabase.from('users').update({role: 'admin'})` 차단 없이 허용
- ❌ Stripe 웹훅 서명 검증 skip 또는 TossPayments 모든 이벤트에 서명이 있다고 가정
- ❌ IP rate limit 만 적용 (로그인 사용자 우회 가능)
- ❌ 알림성 예산을 공급자 hard cap으로 간주하고 LLM API를 프로덕션 오픈
- ❌ `service_role` 키를 프론트엔드 번들에 포함
- ❌ 적대적 테스트 없이 "구현했으니 안전"

---

## Related skills

- `authz-designer` — 권한 모델 설계 (B 구독 상태와 짝)
- `paid-api-guard` — 유료 API 6층 방어 (C/D 강화)
- `/cso` — Gstack 전체 인프라 보안 감사
- `/codex challenge` — 적대적 리뷰
- `simon-tdd` — 회귀 테스트 작성

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
