# Scenario Matrix — Exhaustive Test Case Generation

## Contents

1. [7개 시나리오 카테고리 상세](#7개-시나리오-카테고리-상세)
2. [매트릭스 템플릿](#매트릭스-템플릿)
3. [도메인별 예시](#도메인별-예시)
4. [우선순위 결정](#우선순위-결정)
5. [테스트 레벨 매핑](#테스트-레벨-매핑)

---

## 7개 시나리오 카테고리 상세

### 1. Happy Path

정상 흐름. 사용자가 의도한 대로 모든 것이 작동.

질문:
- 가장 흔한 성공 케이스는?
- 비즈니스가 기대하는 표준 동작은?

### 2. Sad Path

기대된 실패. 사용자 실수, 비즈니스 규칙 위반, 외부 시스템 실패.

질문:
- 입력이 invalid면? (포맷, 범위)
- 외부 API가 실패하면? (timeout, 5xx, rate limit)
- 비즈니스 규칙 위반은? (잔액 부족, 재고 없음, 권한 없음)

### 3. Bad Path

악의적 입력. 보안 관점.

질문:
- SQL injection?
- XSS?
- Command injection?
- Path traversal?
- 음수 금액, 0, MAX_INT 초과?
- 매우 긴 문자열, 특수 문자, unicode/emoji?
- 빈 값, null, undefined?

### 4. Race Condition

동시성. 여러 요청이 같은 자원을 만질 때.

질문:
- 같은 사용자가 동시에 두 요청을 보내면?
- 두 사용자가 같은 자원을 동시에 수정하면?
- Optimistic lock 충돌은?
- Idempotency key 중복은?
- DB transaction의 격리 수준?

### 5. Boundary

경계값. off-by-one, 최소/최대, 시간 경계.

질문:
- 0, 1, MAX, MAX+1, MIN, MIN-1?
- 빈 배열, 1개 요소, 1000개 요소?
- 시간 경계: 자정, 월말, 윤년 2/29?
- 문자열: 빈 문자, 1자, 최대 길이, 최대+1자?
- 만료 직전 1초, 직후 1초?

### 6. Permission

권한 분기. 누가 무엇을 할 수 있는가.

질문:
- 비로그인 사용자?
- 일반 사용자가 admin endpoint 접근?
- 다른 사용자의 자원 접근 (IDOR)?
- 만료된 토큰?
- 권한 강등 직후?

### 7. State Transition

상태 머신. 잘못된 전이 차단, 올바른 전이 허용.

질문:
- 모든 상태를 그래프로 그렸나?
- 각 전이의 trigger와 condition?
- 불가능한 전이 (`paid → cart`)는 차단되나?
- 동시 전이 시도는?
- 중간 실패 시 rollback은?

---

## 매트릭스 템플릿

### 입력 × 상태 × 권한

```
                 | Anon | User | Admin |
-----------------|------|------|-------|
Empty input      |  ?   |  ?   |   ?   |
Valid input      |  ?   |  ?   |   ?   |
Invalid format   |  ?   |  ?   |   ?   |
SQL injection    |  ?   |  ?   |   ?   |
Max length       |  ?   |  ?   |   ?   |
```

각 셀에 기대 동작 작성 → 21개 시나리오. 우선순위로 cull.

### State × Action

```
              | submit | cancel | refund | timeout |
--------------|--------|--------|--------|---------|
cart          |   ?    |   ?    |   X    |    -    |
checkout      |   ?    |   ?    |   X    |    ?    |
paid          |   X    |   X    |   ?    |    -    |
refunded      |   X    |   X    |   X    |    -    |
```

`X` = 불가능, `?` = 시나리오 작성, `-` = 해당 없음

---

## 도메인별 예시

### 결제 플로우

| 카테고리 | 시나리오 |
|---|---|
| Happy | 카드 결제 성공 → confirmation 페이지 |
| Sad | 잔액 부족 → 사용자에게 친절한 에러 메시지 |
| Bad | 음수 금액, 0원, MAX_INT 초과, 카드번호 SQL injection |
| Race | 같은 idempotency key로 두 번 호출 → 한 번만 처리 |
| Boundary | 카드 만료일 D-1, 최소 결제 금액, 최대 결제 금액 |
| Permission | 비로그인 결제 시도, 다른 사용자 카드로 결제 시도 |
| State | cart → checkout → payment → confirmation 정상 전이, paid → cart 차단 |

### 인증 플로우

| 카테고리 | 시나리오 |
|---|---|
| Happy | 이메일/비밀번호 로그인 성공 |
| Sad | 비밀번호 틀림 → 5회 후 lockout |
| Bad | SQL injection in email field, brute force, password length 1자/10000자 |
| Race | 동시 로그인 시도, 토큰 갱신 race |
| Boundary | 토큰 만료 직전 1초, 직후 1초 |
| Permission | 만료된 토큰, 위조 토큰, 다른 사용자 토큰 |
| State | logged-out → logged-in → expired → renewed |

### 파일 업로드

| 카테고리 | 시나리오 |
|---|---|
| Happy | 정상 이미지 업로드 |
| Sad | 네트워크 끊김 → resume 가능? |
| Bad | 실행 파일 업로드, 거대 파일 (DoS), 0 byte 파일, path traversal in filename |
| Race | 같은 파일 두 번 업로드, 업로드 중 다른 요청 |
| Boundary | 파일 크기 한도 직전/직후, 파일명 최대 길이 |
| Permission | 비로그인 업로드, 용량 한도 초과 사용자 |
| State | uploading → done, uploading → cancelled |

---

## 우선순위 결정

### Tier 1 (Critical — 반드시 작성)

- 모든 Happy path
- 비즈니스 critical Sad path (결제 실패, 인증 실패)
- 보안 Bad path (injection, IDOR)
- 주요 State transition

### Tier 2 (Important — 가능한 한 작성)

- 모든 Boundary
- Permission 분기
- 일반 Race condition

### Tier 3 (Nice-to-have — 시간 있을 때)

- 희귀 Race condition
- Edge of edge cases

---

## 테스트 레벨 매핑

| 시나리오 | 적절한 레벨 |
|---|---|
| 단일 함수 입출력 | Unit |
| 모듈 간 상호작용 | Integration |
| 사용자 시나리오 (form 작성 → 제출 → 결과 확인) | E2E |
| 동시성 (Race) | Integration (DB 포함) |
| 권한 (Permission) | Integration (auth middleware 포함) |
| 보안 (Bad path) | E2E + 별도 보안 테스트 (security-checklist 참조) |

### Pyramid

```
       /\
      /E2\         적은 수, 비싼 비용, 가장 가치 있는 시나리오
     /----\
    /Integ.\       중간 수, 모듈 간 계약 검증
   /--------\
  /  Unit    \     많은 수, 빠름, 경계값/edge case 망라
 /------------\
```

E2E는 핵심 user journey 5-10개. Integration은 모듈별 happy + critical sad. Unit은 모든 edge case.

---

## Output 템플릿

scenario-test 작성 시:

```typescript
describe('Payment Checkout Flow', () => {
  describe('Happy paths', () => {
    test('successful card payment redirects to confirmation', () => {})
  })

  describe('Sad paths', () => {
    test('insufficient funds shows user-friendly error', () => {})
    test('expired card prompts re-entry', () => {})
  })

  describe('Bad paths (security)', () => {
    test('rejects negative amount', () => {})
    test('rejects amount exceeding MAX_INT', () => {})
    test('sanitizes card number against SQL injection', () => {})
  })

  describe('Race conditions', () => {
    test('idempotency key prevents duplicate charges', () => {})
  })

  describe('Boundary conditions', () => {
    test('accepts minimum payment amount (1원)', () => {})
    test('rejects payment 1ms after card expiration', () => {})
  })

  describe('Permissions', () => {
    test('blocks non-logged-in user', () => {})
    test('blocks payment with another user\\'s card', () => {})
  })

  describe('State transitions', () => {
    test('allows cart -> checkout -> paid', () => {})
    test('blocks paid -> cart transition', () => {})
  })
})
```
