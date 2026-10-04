---
name: minor-consent-compliance
description: "Use when the user asks to implement minor or guardian consent, an age-gated consent path, or verifiable parental consent—triggers \"미성년 동의\", \"보호자 동의\", \"연령 게이트 동의\", \"under 14\", \"under-14 동의\", \"COPPA 동의\", \"PIPA 22조의2\", \"verifiable parental consent\", \"보호자 검증\", and /minor-consent-compliance. Produces the guardian-consent route (email double opt-in + PASS-guardian / card verification), an age-tiered versioned consent ledger keyed to the minor's user record, and a COPPA / PIPA §22-2 audit export. The age gate and blocking live in auth-builder; this skill owns the guardian verification path and the audit trail."
allowed-tools: Read, Write, Edit, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# minor-consent-compliance

미성년(만 14세 미만 KO / 13세 미만 US) 가입 시 **검증 가능한 보호자 동의(verifiable parental consent)** 경로와 연령tier·버전드 consent 원장, COPPA/PIPA §22-2 감사 export 를 실제 코드로 구현하는 skill. 임의의 앱(웹/RN)에 적용하는 범용 스킬이다.

## 발동 조건

- "미성년 동의", "보호자 동의", "under 14", "연령 게이트 동의"
- "검증 가능한 보호자 동의", "verifiable parental consent", "보호자 검증"
- "COPPA 동의", "PIPA 22조의2", "아동 개인정보 동의"
- auth-builder 가 연령 게이트에서 미성년을 판별한 뒤 보호자 동의 경로가 필요할 때 핸드오프 수신

## 역할 경계 (중복 금지)

이 skill 은 **보호자 동의를 받는 경로**와 **그 증적 원장**만 소유한다. 차단·게이트·트래커 게이팅은 형제 skill 이 한다.

| 책임 | 담당 skill | 비고 |
|---|---|---|
| 연령 입력 + 미성년 판별 + 가입/기능 **차단** | `auth-builder` | 미성년이면 본인 가입 미완료 상태로 보류 |
| 트래커(GA4/AdMob 등) **카테고리 게이팅** | `consent-manager` | 미성년 확정 시 advertising/맞춤형 analytics 영구 OFF |
| **보호자 검증 동의 수집 + 증적 원장 + 감사 export** | **이 skill** | auth-builder 가 보류한 계정을 활성화하는 유일한 경로 |

> 차단을 여기서 다시 구현하지 않는다. auth-builder 가 미성년을 보류 상태로 넘기면, 이 skill 이 보호자 동의를 검증·기록한 뒤에만 활성화 신호를 돌려준다.

## 강제 베스트프랙티스 (절대 약화 금지)

| 원칙 | 규칙 |
|---|---|
| **본인 동의 무효** | 미성년 본인 클릭으로는 가입/비필수 데이터 처리 **활성화 불가**. 활성화는 검증된 보호자 동의 row 가 있을 때만. |
| **검증 가능성** | 보호자 동의는 "검증 가능"해야 한다 — 이메일 단일 클릭만으로는 부족. double opt-in + 본인확인(PASS-guardian/카드)로 보강. |
| **fail-closed** | 보호자 동의 상태 불명/조회 실패 시 미성년 계정은 **비활성**. 모르면 막는다. |
| **append-only 증적** | 모든 동의 요청·검증·승인·거부·철회를 원장에 INSERT. UPDATE/DELETE 금지(트리거 차단). |
| **데이터 최소화** | 보호자 식별정보는 검증에 필요한 최소만 수집·해시 저장. 원문 PII 장기보관 금지. |
| **시크릿** | PASS/SMS/결제 검증 키는 env 로만. 코드·원장에 평문 금지. `EXPO_PUBLIC_*` 같은 클라이언트 노출 prefix 에 비밀키 두지 않기. |

## 연령 tier (versioned)

연령 임계값과 동의 정책은 법 개정으로 바뀐다 → **정책 버전**과 함께 박제한다. 판별 자체는 auth-builder, 여기서는 tier 별 요구 동의를 정의한다.

| tier | 연령(KO 기준) | 가입 | 요구 동의 | 비필수 데이터 처리 |
|---|---|---|---|---|
| `under_14` | 만 14세 미만 | 보호자 동의 **필수**(§22-2) | 검증된 보호자 동의 | 보호자 동의 범위 내에서만 |
| `minor_14_17` | 만 14–17세 | 본인 동의 가능(자기동의 minor) | 본인 동의 | advertising 기본 OFF 권장 |
| `adult` | 만 18세 이상 | 본인 동의 | 본인 동의 | 일반 |

> US COPPA 는 13세 미만이 `under_14` 에 해당(임계값만 13). tier 매핑은 `templates/age-tier-policy.json` 에서 지역별로 분리.

## 보호자 검증 동의 경로 (verifiable parental consent)

검증 강도는 "수집·이용하는 데이터 민감도"에 비례시킨다. 두 단계 조합이 기본.

| 단계 | 방법 | 검증 강도 | 비고 |
|---|---|---|---|
| 1단계(필수) | 보호자 이메일 **double opt-in** | 낮음 | 미성년이 입력한 보호자 이메일로 토큰 링크 발송 → 클릭 시 1차 확인 |
| 2단계(보강) | **PASS-guardian**(통신사 본인확인, 성인) | 높음 | 보호자가 성인임을 확인. KO 표준. CI/DI 는 해시만 보관 |
| 2단계 대안 | **카드 소액 인증**(0원/소액 승인 후 취소) | 높음 | 성인 결제수단 보유 확인. COPPA 인정 방식 |
| 2단계 대안 | 서명 동의서 업로드 + 사람 검토 | 중간 | 오프라인 폴백. SLA 내 검토 |

규칙:
- 1단계만으로는 비필수 데이터 처리 활성화 **불가**. 민감 데이터/광고가 있으면 2단계까지 통과해야 함.
- 검증 토큰은 단기 만료(예: 72h) + 1회용. 만료/재사용 시 거부 row INSERT.
- 보호자 본인확인 결과(CI/DI, 카드 BIN)는 **해시/마스킹**만 원장에 기록. 원문 비보관.

## 동의 원장 (minor 전용, append-only)

`consent-manager` 의 트래커-카테고리 원장과 **별개**로, 미성년/보호자 동의 생애주기를 기록하는 전용 원장을 둔다. 같은 행에 정책버전·tier·검증수단·actor 를 박제.

- `templates/minor-consent-ledger.sql` — append-only(트리거로 UPDATE/DELETE 차단), 상태 전이 = 새 row.
- 상태: `requested` → `email_confirmed` → `verified` → `granted` | `denied` | `expired` | `revoked`.
- 각 row: `policy_version`, `age_tier`, `region`, `actor`(`minor`|`guardian`|`system`), `verification_method`, `verification_ref_hash`, `scope`(동의 범위 JSON), `created_at`.
- `granted` 가 최신 상태일 때만 계정 활성. `revoked`/`expired` 면 즉시 비활성 + consent-manager 에 OFF 전파.

## COPPA / PIPA §22-2 감사 export

규제기관·감사 대비. 원장 rows 를 받아 **결정론적**으로 감사 리포트를 만든다(스크립트는 입력만 보고 같은 출력 — 외부호출/랜덤 없음).

- `scripts/export-consent-audit.mjs` — 원장 JSON(배열)을 stdin/파일로 받아 subject 별 현재 유효상태 + 미준수 플래그 + 요약을 JSON/Markdown 으로 출력.
- 미준수 플래그(컴플라이언스 위반 후보):
  - `MINOR_GRANTED_WITHOUT_GUARDIAN` — under_14 인데 granted 인데 verified guardian row 없음
  - `WEAK_VERIFICATION_FOR_SENSITIVE` — 민감 scope 인데 1단계(email)만으로 granted
  - `STALE_POLICY_VERSION` — 현재 정책버전보다 낮은 버전으로 granted (재동의 필요)
  - `EXPIRED_STILL_ACTIVE` — expired/revoked 인데 활성 취급
  - `MUTATION_DETECTED` — 같은 동의건에 시간 역행/UPDATE 흔적

## Workflow

### 1. 진단 (AskUserQuestion)
- 플랫폼? (웹 / RN / 둘 다) — 저장소·검증 SDK 분기
- 대상 지역? (KO / US / 둘 다) — 연령 임계값(14 vs 13) 결정
- 수집 데이터 민감도? (기본 프로필만 / 위치·연락처·결제 등 민감 포함) — 2단계 검증 강제 여부
- 보호자 검증 수단? (이메일만 가능 / PASS 연동 / 카드 인증 가능)
- auth-builder 연령 게이트가 이미 있나? (있으면 핸드오프 계약만, 없으면 먼저 auth-builder 권유)

### 2. 정책 박제
- `templates/age-tier-policy.json` 을 지역·임계값·정책버전으로 채운다. 정책버전은 날짜 문자열(예: `2026-06-01`).

### 3. 원장 설치
- `templates/minor-consent-ledger.sql` 적용. append-only 트리거 동작 확인.

### 4. 보호자 동의 경로 구현
- `templates/guardian-consent-flow.ts` 의 상태머신을 연결: 보호자 이메일 입력 → 토큰 발송 → 확인 → (민감 시) 2단계 검증 → granted/denied row INSERT.
- 토큰 발송/검증 비밀키는 env. 클라이언트에 비밀키 노출 금지.

### 5. auth-builder 핸드오프 계약
- auth-builder 가 미성년 보류 계정을 넘김(`user_id` + `age_tier`).
- 이 skill 이 `granted` row 를 만들면 활성화 신호를 돌려줌. 그 전엔 계정 비활성 유지(fail-closed).
- consent-manager 에는 미성년 확정 신호 전파 → advertising/맞춤형 analytics OFF.

### 6. 철회·만료·감사
- 보호자 철회 진입점 상시 노출. 철회 시 `revoked` row INSERT + 계정 비활성 + consent OFF 전파.
- 토큰/동의 만료 시 `expired` row.
- 감사 시 `scripts/export-consent-audit.mjs` 로 export → 미준수 플래그 0 확인.

## 검증 체크리스트

- [ ] 미성년 본인 클릭만으로는 계정 활성/비필수 처리 불가 (fail-closed)
- [ ] 보호자 이메일 double opt-in 동작 (토큰 1회용·만료)
- [ ] 민감 데이터 시 2단계(PASS/카드) 통과 전까지 granted 불가
- [ ] 보호자 본인확인 결과는 해시/마스킹만 저장 (원문 PII 비보관)
- [ ] 원장 UPDATE/DELETE 차단 (트리거 동작)
- [ ] 상태 전이마다 새 row INSERT (requested→…→granted/denied/revoked)
- [ ] 정책버전 상향 시 STALE 플래그 + 재동의 트리거
- [ ] export 스크립트가 같은 입력에 같은 출력 (결정론) + 미준수 플래그 정확
- [ ] 비밀키 env 만 사용, EXPO_PUBLIC_* 등 클라이언트 prefix 에 비밀키 없음
- [ ] auth-builder/consent-manager 핸드오프 신호 정상

## Related Skills

- `consent-manager` — 트래커 카테고리 게이팅 원장(별개). 미성년 확정 시 advertising/analytics OFF 전파 수신
- `auth-builder` — 연령 게이트·미성년 판별·계정 차단(상류). 보호자 동의 후 활성화 신호 반환
- `data-flow-mapper` — 미성년에게서 수집되는 데이터가 어떤 scope/민감도인지 매핑 (2단계 검증 강제 판단 근거)
