---
name: data-flow-mapper
description: "개인정보(PII) 데이터플로우 인벤토리와 합법근거 맵을 만드는 skill. 트리거 \"개인정보 흐름 정리\", \"PII 맵\", \"데이터 인벤토리\", \"수집 항목 정리\", \"privacy 라벨 준비\", \"국외이전 점검\", \"data inventory\", \"privacy label\", /data-flow-mapper. 코드를 스캔(SDK init·네트워크 콜·DB 컬럼·env 키)해서 데이터타입×목적×법적근거×처리자×저장지역×보존기간 표를 산출하고, 동의 없는 수집·국외이전 같은 위험을 플래그한다. 이 인벤토리는 Apple Privacy Nutrition Label·Google Data Safety·개인정보처리방침·DSAR 응답의 단일 상류 소스다."
allowed-tools: Read, Grep, Glob, Write, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# data-flow-mapper

앱이 실제로 수집·전송·저장하는 개인정보를 코드에서 역으로 식별해, 하나의 데이터플로우 인벤토리로 만드는 skill. 이 인벤토리 한 장이 store 개인정보 라벨, 개인정보처리방침, DSAR(정보주체 요청) 응답, 보존정책의 단일 소스가 된다.

특정 앱 전용이 아니라 사용자가 만드는 임의의 앱에 적용하는 범용 skill이다. 산출물은 사실(코드에서 관측된 것)과 추정(목적·법적근거)을 분리해서 표기한다.

## 발동 조건

- "개인정보 흐름 정리해줘", "PII 맵 만들어줘", "데이터 인벤토리"
- "수집 항목 정리", "privacy 라벨 준비", "Data Safety 폼 채워야 해"
- "국외이전 점검", "어디로 데이터 나가는지 봐줘"
- consent-manager / store-launcher / 개인정보처리방침 작성 전 상류 단계로 호출

## 왜 코드에서 역으로 추출하나

개인정보처리방침과 store 라벨은 보통 "선언"으로 작성되어 실제 코드와 어긋난다. 라벨에 없는 SDK가 데이터를 빼가거나, 방침에 적힌 항목을 실제로는 안 쓰는 일이 흔하다. 규제 위반·스토어 반려·심사 탈락의 단골 원인이다. 그래서 이 skill은 선언이 아니라 **코드에서 관측된 사실**을 1차 소스로 삼는다.

## 산출물

1. `data-flow.md` — 인벤토리 표 (아래 6열) + 위험 목록 + 다운스트림 매핑.
   템플릿: `templates/data-flow.template.md`.
2. (선택) `templates/dsar-checklist.md` — 정보주체 요청 응답 절차.
3. (선택) `templates/privacy-label-map.md` — Apple/Google 라벨 카테고리 매핑.

인벤토리 핵심 표 6열:

| 데이터 타입 | 수집 목적 | 법적 근거 | 처리자(3rd party) | 저장 지역 | 보존 기간 |
|---|---|---|---|---|---|

## Workflow

### 1. 스코프 확인 (AskUserQuestion)

스캔 전 다음을 확인한다. 답이 없으면 보수적(가장 넓은 규제) 기본값으로 진행하고 표에 `[가정]`으로 표기.

- 대상 사용자 지역? (한국만 / EU 포함 / US 포함 / 글로벌) → 적용 규제 결정
- 아동 대상인가? (만 14세 미만 / 13세 미만) → 보호자 동의·COPPA 트리거
- 모바일 스토어 출시? (App Store / Play / 둘 다 / 웹만) → 라벨 산출물 결정

### 2. 코드 스캔 (Grep / Glob)

수집 지점을 5개 표면에서 역추적한다. 스크립트 `scripts/scan-pii.sh`가 1차 패스를 자동화한다.

| 표면 | 스캔 대상 | 단서 |
|---|---|---|
| SDK init | analytics·ad·crash·map·push SDK 초기화 | 자동수집(IDFA/AAID, IP, 디바이스ID) 발생 |
| 네트워크 콜 | `fetch`/`axios`/`XMLHttpRequest`/도메인 | 어떤 데이터가 어느 호스트로 나가나 |
| DB 컬럼 | 스키마·migration·model | email/phone/name/birth/location 등 저장 PII |
| env 키 | `.env*`·`app.json`·`eas.json` | 어떤 외부 처리자에 키를 붙였나 (= 처리자 단서) |
| 권한 선언 | iOS `Info.plist`·Android `manifest`·`app.json` | 카메라/위치/연락처/마이크 = 잠재 PII 소스 |

스캔으로 잡히는 흔한 PII 패턴(범용):

```
email, e-mail, 이메일        phone, mobile, 전화, 휴대폰
name, fullname, 이름          birth, dob, 생년월일, age, 나이
address, 주소, postal, zip    location, lat, lng, gps, geo, 위치
device_id, idfa, aaid, gaid   ip, ip_address, user_agent
photo, image, avatar          contacts, 연락처
ssn, 주민, passport, 여권     card, payment, iban, 결제
health, 건강, biometric       precise_location
```

### 3. 처리자(3rd party) 식별

env 키와 SDK import에서 데이터가 흘러가는 외부 처리자를 뽑고, 각각의 데이터 처리 위치(국내/국외)를 표기한다. 흔한 처리자와 기본 저장 지역:

| 처리자 | 받는 데이터(대표) | 기본 리전 | 국외이전 |
|---|---|---|---|
| Google Analytics / GA4 | 디바이스ID, IP, 이벤트 | US | 예 |
| Firebase / Crashlytics | 디바이스ID, 크래시, IP | US | 예 |
| AdMob / Meta Ads SDK | 광고ID, IP | US | 예 |
| Sentry | IP, 에러, user_id | US/EU 선택 | 리전따라 |
| Supabase / 기타 호스팅 DB | 저장한 모든 PII | 프로젝트 리전 | 리전따라 |
| 결제(Stripe/PG) | 카드·청구정보 | US/국내 | PG따라 |
| 푸시(FCM/APNs) | 디바이스 토큰 | US | 예 |

> 저장 리전·국외이전 여부는 실제 SDK 설정·계약(DPA)으로 확정해야 한다. 표에는 코드 근거가 없는 항목을 `[확인필요]`로 남긴다.

### 4. 법적 근거 매핑

각 데이터 타입에 법적 근거를 1개 이상 매핑한다. 근거가 불명확하면 위험으로 플래그.

| 법적 근거 | 한국(PIPA) | EU(GDPR Art.6) | 쓰는 경우 |
|---|---|---|---|
| 동의 | §15①1, §22 | consent (a) | 마케팅, 선택 수집, 민감정보 |
| 계약 이행 | §15①4 | contract (b) | 서비스 제공에 필수 |
| 법적 의무 | §15①2 | legal obligation (c) | 전자상거래법 보존 등 |
| 정당한 이익 | (제한적) | legitimate interest (f) | 보안·사기방지 (한국은 좁게) |

민감정보(건강·생체·사상·정밀위치·만14세미만)는 별도 강화 동의가 필요하다 — 별도 플래그.

### 5. 위험 플래그 (필수 출력)

스캔 결과에서 다음을 위험 목록으로 강제 출력한다. 베스트프랙티스 4종 강제:

- **동의 게이트 누락** — 수집은 있는데 동의 흐름이 코드에 없음. classifier/consent 체크 없이 PII가 흐르는 경로.
- **fail-open 위반** — 동의/분류 호출이 실패할 때 수집이 차단(fail-closed)되어야 하는데 통과하는 코드. 동의 미확인 시 기본은 "수집 안 함".
- **감사로그 누락** — PII 접근·전송·삭제에 감사로그 INSERT가 없는 경로 (DSAR·사고대응 시 추적 불가).
- **플랫폼 분기 누락** — iOS ATT(IDFA) / Android 권한 / 웹 쿠키 동의를 플랫폼별로 분기하지 않고 한 경로로 처리.
- **국외이전 미고지** — 국외 처리자(대개 US)로 데이터가 나가는데 처리방침/동의에 국외이전 고지가 없음.
- **선언 ↔ 코드 불일치** — 기존 처리방침/라벨에 있는데 코드엔 없거나, 코드엔 있는데 라벨에 없음.

### 6. 다운스트림 산출물 매핑

인벤토리를 4개 소비처에 연결한다(이 skill은 상류, 실제 작성은 다른 skill/문서가 함).

| 소비처 | 인벤토리에서 가져오는 것 |
|---|---|
| Apple Privacy Nutrition Label | 데이터 타입 → Apple 카테고리, "Linked to You" 여부, 추적용 여부 |
| Google Play Data Safety | 데이터 타입 → 수집/공유 구분, 암호화, 삭제요청 가능 여부 |
| 개인정보처리방침 | 6열 표 전체 (항목·목적·근거·처리자·보유기간·국외이전) |
| DSAR 응답 | 데이터 위치 맵 → 열람·정정·삭제·이동 대상 테이블/처리자 |

## scan-pii.sh 사용

```bash
bash scripts/scan-pii.sh <project-root>
# 기본 project-root: 현재 디렉터리
```

PII 키워드·SDK·env·권한 선언을 한 번에 grep해서 후보 목록을 stderr로 출력한다. 결과를 사람이 검토해 `data-flow.md` 표로 정리한다. 자동 분류가 아니라 **후보 수집 지점 인덱스**다.

## 검증 체크리스트

- [ ] 6열 표의 모든 행에 법적 근거가 1개 이상 매핑됨
- [ ] 모든 외부 처리자가 식별되고 저장 리전이 표기됨 (없으면 `[확인필요]`)
- [ ] 국외이전 데이터가 전부 플래그되고 고지 여부 확인됨
- [ ] 민감정보·아동 데이터가 별도 강화 동의로 분리됨
- [ ] 동의 게이트·fail-open·감사로그·플랫폼 분기 위반이 위험 목록에 빠짐없이 들어감
- [ ] 기존 처리방침/라벨과의 불일치 항목이 명시됨
- [ ] 사실(코드 근거)과 가정(`[가정]`/`[확인필요]`)이 표에서 구분됨

## Related Skills

- `consent-manager` — 이 인벤토리의 "동의 필요" 항목을 실제 동의 흐름으로 구현
- `analytics-ad-wiring` — analytics/ad SDK 수집 항목의 실제 배선 (이 skill이 그 수집을 인벤토리화)
- `auth-builder` — 인증이 저장하는 PII(email/phone/CI·DI) 컬럼 식별 연동
- `security-checklist` — PII 접근 경로의 RLS·IDOR·감사로그 감사
