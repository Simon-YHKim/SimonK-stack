---
name: revenue-scenario-tester
description: "Use when the user asks to test monetization flows end-to-end, verify payment/subscription/ad scenarios, or run revenue system integration tests—triggers \"수익화 테스트\", \"결제 시나리오 검증\", \"구독 테스트 돌려줘\", \"광고 동작 확인\", \"test payments\", \"verify subscription flow\", \"revenue QA\", \"billing test\". Produces comprehensive scenario testing via 7 specialized agents (Payment/Subscription/Ad/Analytics/Store/Security/KR-Compliance) running 80+ scenarios across Happy/Sad/Bad/Race/Boundary/Permission/State categories. Generates revenue-test-report with PASS/FAIL per scenario and auto-fix loop for failures."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch, Agent
version: 1.0.0
author: simon-stack
---

# revenue-scenario-tester

수익화 전체 흐름을 7개 전문 에이전트로 통합 테스트하는 skill.

> 결제 한 번 실패하면 유저를 잃는다. 구독 상태 머신에 빈틈이 있으면 매출이 새어나간다.
> 이 skill은 "돈이 관련된 모든 경로"를 적대적으로 검증한다.

## 발동 조건

- "수익화 테스트 돌려줘", "결제 시나리오 검증"
- "구독 플로우 테스트", "광고 동작 확인"
- `payment-integrator`, `ad-monetization` 구현 후 자동 체인
- `dev-orchestrator` 단계 4 (Scenario Planning) 에서 수익화 관련 시 호출

## 7개 전문 에이전트

### Agent 1: Payment Agent

결제 흐름의 모든 성공/실패 경로 검증.

**시나리오 매트릭스 (20+ 시나리오)**:

| 카테고리 | 시나리오 |
|---|---|
| **Happy** | 카드 결제 성공, 간편결제 성공, 해외 카드 성공 |
| **Sad** | 잔액 부족, 카드 만료, 한도 초과, 3DS 실패 |
| **Bad** | 네트워크 타임아웃 중 결제, 이중 결제 시도, webhook 지연 |
| **Race** | 동시 결제 요청, 결제 중 페이지 새로고침 |
| **Boundary** | 최소 금액 (₩100), 최대 금액, 통화 변환 |
| **Permission** | 비로그인 결제 시도, 정지된 계정 결제 |
| **State** | 환불 → 재결제, 분쟁(dispute) 처리, 부분환불 |

**검증 방법**:
- Stripe 테스트 카드 번호 활용
- PortOne sandbox 모드
- Webhook mock server로 이벤트 시뮬레이션

---

### Agent 2: Subscription Agent

구독 상태 머신의 모든 전이(transition) 검증.

**시나리오 매트릭스 (15+ 시나리오)**:

| 카테고리 | 시나리오 |
|---|---|
| **Happy** | 가입→활성, 업그레이드, 다운그레이드 |
| **Sad** | Trial 만료 미결제, 갱신 실패 (dunning), 카드 교체 |
| **Bad** | 취소 후 즉시 재가입, 동시 플랜 변경, webhook 순서 역전 |
| **Race** | 갱신일에 취소 요청, 업그레이드 중 결제 실패 |
| **Boundary** | 무료→유료 경계, trial 0일, 쿠폰 100% 할인 |
| **Permission** | 만료된 구독으로 프리미엄 기능 접근 |
| **State** | canceled→resubscribe, past_due→active 복원, 일시정지→재개 |

**상태 머신 검증**:
```
모든 가능한 전이 조합을 테스트:
trialing → active ✓
trialing → canceled ✓
active → past_due ✓
active → canceled (immediate) ✓
active → canceled (at_period_end) ✓
past_due → active (retry success) ✓
past_due → canceled (max retries) ✓
canceled → active (resubscribe) ✓
paused → active (resume) ✓
```

---

### Agent 3: Ad Agent

광고 표시 + 수익 추적 검증.

**시나리오 매트릭스 (10+ 시나리오)**:

| 카테고리 | 시나리오 |
|---|---|
| **Happy** | 배너 표시, 인터스티셜 표시, 보상형 완료+보상 |
| **Sad** | 광고 로드 실패 (no fill), 네트워크 오프라인 |
| **Bad** | AdBlock 활성, 정책 위반 광고 콘텐츠 |
| **Boundary** | 빈도 제한 (60초 이내 재표시 차단), 세션 내 최대 횟수 |
| **Permission** | 유료 유저에게 광고 미표시, 미동의 시 비개인화 |
| **State** | Pro 구독 취소 → 광고 다시 표시, 광고 제거 IAP 후 복원 |

---

### Agent 4: Analytics Agent

이벤트 발화 + 데이터 정합성 검증.

**시나리오 매트릭스 (12+ 시나리오)**:

| 카테고리 | 시나리오 |
|---|---|
| **Happy** | 핵심 이벤트 전부 발화, identify 연결, 퍼널 완료 |
| **Sad** | 네트워크 오프라인 시 이벤트 큐잉, 스크립트 로드 실패 |
| **Bad** | 이벤트 중복 발화, 속성 타입 불일치, PII 유출 |
| **Boundary** | 이벤트 속성 null/undefined, 초장문 값, 특수문자 |
| **Permission** | 동의 미획득 시 추적 비활성, GDPR 삭제 요청 처리 |
| **State** | 로그아웃→재로그인 시 identify 연속성, 익명→가입 전환 매핑 |

---

### Agent 5: Store Agent

스토어 정책 준수 + 메타데이터 검증.

**시나리오 매트릭스 (8+ 시나리오)**:

| 카테고리 | 시나리오 |
|---|---|
| **Policy** | 4.2 최소 기능, 외부 결제 유도 금지, 콘텐츠 등급 정확성 |
| **Metadata** | 설명 키워드 스터핑 없음, 스크린샷 규격, 아이콘 규격 |
| **Privacy** | Data Safety 정확성, ATT 구현, 개인정보처리방침 URL 유효 |
| **Technical** | Target API 최신, 64-bit 빌드, 크래시율 <1% |

---

### Agent 6: Security Agent

수익화 보안 적대적 테스트.

**시나리오 매트릭스 (10+ 시나리오)**:

| 카테고리 | 시나리오 |
|---|---|
| **Webhook 변조** | 서명 없는 webhook, 재생 공격, 금액 변조 |
| **가격 조작** | 클라이언트 금액 변조, 쿠폰 코드 brute-force |
| **구독 상태 변조** | JWT 내 plan 필드 변조, 만료된 토큰으로 프리미엄 접근 |
| **크레딧 남용** | 무료 trial 반복 생성 (이메일 변경), 레퍼럴 자기참조 |
| **API 남용** | rate limit 없는 엔드포인트, 대량 환불 요청 |
| **IDOR** | 타인 구독 정보 조회, 타인 결제 수단 사용 |

---

### Agent 7: KR-Compliance Agent

한국 법규 준수 검증.

**시나리오 매트릭스 (8+ 시나리오)**:

| 법규 | 검증 항목 |
|---|---|
| **전자상거래법** | 7일 청약철회 가능 여부, 디지털 콘텐츠 예외 고지 |
| **자동갱신** | 갱신 7일 전 고지 이메일/SMS 발송 확인 |
| **현금영수증** | 현금 결제 시 자동 발행, 조회 API |
| **세금계산서** | B2B 거래 시 발행 로직 |
| **개인정보보호법** | 수집 동의, 제3자 제공 동의, 파기 |
| **청소년보호** | 연령 확인 (19세 미만 결제 제한) |
| **표시광고법** | 가격 표시 정확성, 할인율 계산 기준 |
| **통신판매업** | 사업자 정보 표시 (상호, 대표, 주소, 전화) |

---

## 실행 구조

```
revenue-scenario-tester 발동
  │
  ├─ 1. 프로젝트 스캔
  │     grep으로 어떤 결제/광고/분석이 구현돼 있는지 감지
  │     (stripe|portone|revenuecat|admob|adsense|ga4|posthog)
  │
  ├─ 2. 해당 Agent만 활성화
  │     Stripe 있으면 → Payment + Subscription + Security Agent ON
  │     AdMob 있으면 → Ad Agent ON
  │     GA4 있으면 → Analytics Agent ON
  │     스토어 배포면 → Store Agent ON
  │     한국 서비스면 → KR-Compliance Agent ON
  │
  ├─ 3. 시나리오 매트릭스 생성
  │     각 Agent가 7카테고리 × 해당 시나리오 = 80+ 총 시나리오
  │
  ├─ 4. 에이전트 병렬 실행 (agent-delegate Fan-out)
  │     ├─ Payment Agent → sandbox 테스트 20개
  │     ├─ Subscription Agent → 상태 머신 15개
  │     ├─ Security Agent → 적대적 10개
  │     ├─ Ad Agent → 광고 동작 10개
  │     ├─ Analytics Agent → 이벤트 12개
  │     ├─ Store Agent → 정책 8개
  │     └─ KR-Compliance Agent → 법규 8개
  │
  ├─ 5. 결과 통합
  │     revenue-test-report-<date>.md
  │     ├─ Summary: N/M passed, K critical failures
  │     ├─ Per-Agent breakdown
  │     └─ Failure details + suggested fix
  │
  └─ 6. Auto-fix 루프 (선택)
        FAIL 항목에 대해 simon-tdd RED→GREEN 사이클
        → 수정 → 재테스트 → PASS까지 반복
```

## 리포트 형식

```markdown
# Revenue Scenario Test Report — 2026-05-04

## Summary
- Total scenarios: 83
- Passed: 76 ✅
- Failed: 5 ❌
- Skipped: 2 ⏭️ (not applicable)

## Critical Failures (must fix before launch)
| # | Agent | Scenario | Expected | Actual |
|---|---|---|---|---|
| 1 | Security | Webhook without signature | reject | accepted ❌ |
| 2 | KR-Compliance | Auto-renewal notice | 7d before | not sent ❌ |

## Warnings (should fix)
...

## Per-Agent Results
### Payment Agent: 18/20 ✅
### Subscription Agent: 14/15 ✅
...
```

## 사용 예시

```
나: "결제 시나리오 테스트 돌려줘"

Claude: [revenue-scenario-tester 발동]
  프로젝트 스캔: Stripe + PostHog + AdSense 감지
  → Payment Agent (20), Subscription Agent (15), Analytics Agent (12),
    Ad Agent (10), Security Agent (10), KR-Compliance Agent (8) 활성화
  → 75 시나리오 실행
  → revenue-test-report-2026-05-04.md 생성
  → Critical: 2건 (webhook 서명 미검증, 자동갱신 고지 누락)
  → Auto-fix 진행할까요?
```

## Related Skills

- `payment-integrator` — 결제 구현 (이 skill이 검증)
- `ad-monetization` — 광고 구현 (이 skill이 검증)
- `analytics-integrator` — 분석 구현 (이 skill이 검증)
- `paid-api-guard` — 보안 체크리스트 (Security Agent와 연계)
- `security-checklist` — RLS/IDOR (Security Agent가 확장)
- `agent-delegate` — Fan-out 병렬 실행 패턴
- `simon-tdd` — Auto-fix 시 RED→GREEN 사이클
- `test-gen` — 7카테고리 시나리오 매트릭스 (이 skill이 수익화 전용으로 확장)
