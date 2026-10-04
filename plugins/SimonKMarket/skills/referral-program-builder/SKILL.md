---
name: referral-program-builder
description: "Use when the user asks to build a referral/invite program—triggers \"추천 프로그램\", \"초대코드\", \"리퍼럴\", \"친구 초대 보상\", \"양면 보상\", \"refer a friend\", \"build a referral program\", \"invite code\", \"referral rewards\", or /referral-program-builder. Produces referrals + reward-ledger schema, invite-code generation, deferred deep-link attribution (deeplink-integrator 연계), two-sided reward design, abuse guards (self-referral·multi-account·self-click), and K-factor measurement events."
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# referral-program-builder

양면(two-sided) 추천 프로그램을 실제 스키마 + 로직으로 구현하는 skill.
초대코드 발급 → deferred deep-link 어트리뷰션 → 양면 보상 → 어뷰징 가드 → K-factor 측정까지 한 번에 잡는다.

## 발동 조건

- "추천 프로그램", "초대코드 만들어줘", "리퍼럴 붙여줘", "친구 초대 보상"
- "양면 보상 설계", "refer a friend", "invite code", "referral rewards"
- `viral-launch` 실행 후 추천 루프를 코드로 내릴 때 자동 체인

## 먼저 확정할 4가지 (AskUserQuestion)

코드를 쓰기 전에 아래를 사용자에게 확인한다. 답에 따라 스키마/보상 로직이 갈린다.

| 질문 | 옵션 예시 | 영향 |
|---|---|---|
| 보상 방식 | 양면(추천인+피추천인) / 추천인만 / 단계형(tiered) | 원장 행 생성 규칙 |
| 보상 종류 | 크레딧·포인트 / 현금성 / 무료 기간 / 외부 기프트 | 정산·세무·환불 처리 |
| 적립 트리거 | 가입 즉시 / 첫 결제 / 특정 행동(activation) | qualifying event 정의 |
| 플랫폼 | 앱(딥링크) / 웹(링크) / 둘 다 | 어트리뷰션 경로 |

"알아서 해"면 기본값: **양면 + 크레딧 + 첫 activation 트리거 + 앱·웹 공용**.

## 구현 단계

### 1. 스키마 설계

핵심은 **referrals(관계·상태)** 와 **reward_ledger(불변 원장)** 를 분리하는 것.
보상은 절대 referrals 행에 금액을 직접 쓰지 않고 append-only 원장으로 적립한다(재계산·감사 가능).

전체 DDL: `templates/referral-schema.sql`. 요약:

- `referral_codes` — 사용자당 발급 코드(소유자, 코드 문자열, 활성 여부). 코드는 추측 불가하게 생성(아래 2).
- `referrals` — (referrer_id, referred_id, code, status, attributed_via). status 상태 머신은 3 참조. `(referred_id)` UNIQUE — 한 명은 한 번만 피추천.
- `reward_ledger` — append-only. (user_id, referral_id, role, kind, amount, currency, state, idempotency_key). 지급/회수 모두 행 추가로 표현(회수는 음수 또는 reversal 행).
- `referral_events` — K-factor·퍼널 측정용 raw 이벤트(아래 5).

### 2. 초대코드 + deferred deep-link 어트리뷰션

코드 생성 원칙:
- **추측 불가**: crypto random 8~10자, 혼동 문자 제외(0/O, 1/l/I). 순차 ID 금지.
- 사용자당 1개 안정 코드(재방문 시 동일). 캠페인용 일회성 코드는 별도 발급.

어트리뷰션 경로 (앱):
1. 초대 링크 = 유니버설/앱 링크 + `?ref=CODE` (단축은 deeplink-integrator/단축링크 도구).
2. 미설치 사용자 → 스토어 경유 → **deferred deep-link**로 설치 후 첫 실행에서 `ref` 복원.
3. 첫 실행에서 `claimReferral(code)` 호출 → referrals 행 생성(status=`pending`).

정확한 K-factor 측정이 필요하면 서버가 수신자별 추측 불가 `invite_id`를 발급해 `invite_shared`와 성공한 `referral_signed_up`의 `props.invite_id`에 동일하게 기록한다. 코드 문자열만으로 여러 공유와 한 가입을 정확히 연결할 수 없다. 수신자가 불특정인 소셜 공유는 발송 초대 수로 단정하지 않는다. 클라이언트가 보낸 `invite_id`는 코드·추천인과 서버에서 다시 대조한다.

> deferred deep-link 의 fingerprint/클립보드 복원, iOS/Android 분기, 단축링크 발급은 `deeplink-integrator` skill 에 위임한다. 이 skill 은 복원된 `code` 를 받아 attribution 만 처리한다.

웹은 단순: 쿠키/localStorage 에 `ref` 저장 후 가입 시 전송.

### 3. 양면 보상 설계 + 상태 머신

```
referrals.status:
pending ──[자격 이벤트 발생]──→ qualified ──[보상 지급]──→ rewarded
pending ──[어뷰징 가드 차단]──→ rejected
qualified ──[환불·취소 등 회수 사유]──→ clawed_back
```

보상 지급 규칙(의사코드 전체: `templates/reward-logic.pseudo`):
- `qualified` 진입은 **qualifying event** 1회만(가입 또는 첫 결제/activation — 1에서 확정한 값).
- 지급 시 추천인·피추천인 각각 reward_ledger 행 1개씩(role=`referrer`/`referred`).
- 모든 적립은 `idempotency_key = referral_id + role + reward_rule_version` 로 멱등 처리. 같은 자격 이벤트가 두 번 와도 중복 적립 금지.
- 한도: 추천인당 누적 보상 cap, 기간당 cap(예: 월 N건). cap 초과분은 적립 보류(`capped`).

### 4. 어뷰징 가드 (지급 전 필수 통과)

지급 직전 아래를 모두 검사한다. 하나라도 걸리면 status=`rejected`, 사유 기록.

| 가드 | 차단 대상 | 신호 |
|---|---|---|
| self-referral | 본인이 본인 코드 사용 | referrer_id == referred_id, 동일 이메일/전화 정규화 일치 |
| 다중계정 | 한 사람이 여러 계정 | 디바이스 ID, 결제수단 fingerprint, 가입 IP 군집 |
| 셀프클릭/봇 | 사람 행동 없는 클릭 적립 | 클릭→설치→activation 시간 간격, 동일 IP 클릭 폭주 |
| 자격 미달 | 자격 이벤트 위장 | 결제 직후 즉시 환불, activation 행동 결여 |
| 코드 무차별 | 코드 추측 시도 | 동일 IP의 실패 claim 횟수 rate-limit |

원칙:
- **지급은 항상 자격 이벤트 + 가드 통과 후**. 가입 즉시 현금성 보상 지급 금지(환불 어뷰징 표면).
- 회수 가능 설계: 보상 후 환불·취소되면 `clawed_back` 원장 reversal 행으로 회수.
- 가드 판정은 측정 신호 기반으로만(단정 금지). 임계값은 config 로 빼고 로그로 검증.

상세 규칙·정규화 로직: `templates/reward-logic.pseudo`.

### 5. K-factor 측정 이벤트

K-factor = (사용자당 평균 보낸 초대 수) × (초대 → 가입 전환율).
이걸 계산하려면 아래 이벤트를 `referral_events` 에 적재한다.

| 이벤트 | 발생 시점 | K-factor 기여 |
|---|---|---|
| `invite_shared` | 사용자가 초대 링크 공유/발송 | 분자: 보낸 초대 수 |
| `invite_clicked` | 피추천인이 링크 클릭 | 클릭 전환 퍼널 |
| `invite_installed` | (앱) deferred deep-link 설치 | 설치 전환 |
| `referral_signed_up` | 피추천인 가입 완료 | 분자: 전환 수 |
| `referral_qualified` | 자격 이벤트 충족 | 실보상 전환 |
| `reward_granted` | 양면 보상 지급 | 비용/ROI |

측정 스니펫(SQL): `templates/k-factor-queries.sql` — 초대 ID가 확인된 경우의 30일 K-factor·가입 소요시간. ID가 없으면 K-factor는 0이 아니라 **미정**이다. 추천 코호트 LTV는 이 이벤트 테이블에 매출이 없으므로 실제 매출·변동비 원천을 매핑한 뒤에만 계산한다.

검증 보조 스크립트: `bash scripts/check-referral-integrity.sh` — self-referral 누수, 멱등키 중복, 원장 역할·상태 불일치를 읽기 전용으로 스캔. `PGHOST`, `PGDATABASE`, `PGUSER`와 libpq 인증을 **실행 환경에만** 제공하고 인자에 비밀번호를 넣지 않는다. 운영 DB 조회는 대상·권한을 확인한 뒤에만 실행한다. 스크립트의 0건 결과는 이 네 검사만의 결과이며 어뷰징 전반의 무결성 인증이 아니다.

## 검증 체크리스트

- [ ] referrals `(referred_id)` UNIQUE — 한 명 한 번만 피추천
- [ ] reward_ledger append-only + `idempotency_key` UNIQUE
- [ ] 코드가 추측 불가(crypto random, 순차 ID 아님)
- [ ] deferred deep-link 복원 → claim → attribution 경로 동작
- [ ] 양면 보상이 자격 이벤트 1회에만 지급(중복 적립 없음)
- [ ] 4종 어뷰징 가드 모두 지급 전 검사
- [ ] 환불·취소 시 clawed_back 회수 동작
- [ ] K-factor 이벤트 적재 + 수신자별 `invite_id` 연결률 확인; ID/매출 원천 없으면 미정 표기
- [ ] 보상 금액/한도/임계값이 코드에 하드코딩 아님(config)
- [ ] 시크릿·PG 키 env 처리

## Related Skills

- `deeplink-integrator` — deferred deep-link 복원·단축링크·iOS/Android 분기(어트리뷰션 경로 위임)
- `viral-launch` — 추천 루프 전략·바이럴 캠페인 설계(이 skill은 그 구현체)
- `payment-integrator` — 현금성·크레딧 보상의 정산/환불/세무 처리 연계
- `analytics-integrator` — referral_events 를 GA4/PostHog 이벤트 분류와 정렬
- `aarrr-growth-planner` — Referral 단계 KPI·실험 백로그

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
