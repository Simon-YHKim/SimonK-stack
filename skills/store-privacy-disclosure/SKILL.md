---
name: store-privacy-disclosure
description: "스토어 개인정보 공시(Apple App Privacy 라벨 + Google Play Data Safety + ATT 카피)를 데이터플로우 인벤토리에서 자동 생성하는 skill. 트리거 \"App Privacy 라벨\", \"Data Safety\", \"개인정보 공시\", \"ATT 카피\", \"NSUserTrackingUsageDescription\", \"Nutrition Label\", \"data safety 설문\", /store-privacy-disclosure. data-flow-mapper 인벤토리(data-flow.md)를 입력으로 Apple Privacy Nutrition Label과 Google Data Safety 설문을 자동으로 채우고, ATT 프리프롬프트 + NSUserTrackingUsageDescription 카피를 생성한다. 코드에서 관측된 수집과 라벨 선언이 어긋나면(선언↔수집 불일치) 스토어 리젝 사유로 강제 경고한다. 선언이 아니라 인벤토리의 코드 근거를 단일 소스로 삼는다."
allowed-tools: Read, Grep, Write, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# store-privacy-disclosure

`data-flow-mapper`가 만든 데이터플로우 인벤토리(`data-flow.md`)를 입력으로, 스토어 제출에 필요한 개인정보 공시 3종을 자동 생성하는 skill:

1. **Apple App Privacy Nutrition Label** (App Store Connect 입력값)
2. **Google Play Data Safety** 설문 응답
3. **ATT 프리프롬프트 카피 + `NSUserTrackingUsageDescription`** 문자열

특정 앱 전용이 아니라 사용자가 만드는 임의의 RN/Expo·웹 앱에 적용하는 범용 skill이다. 산출물의 모든 항목은 인벤토리의 **코드 근거**에서 파생하며, 선언(기존 처리방침·라벨)과 코드가 다르면 코드가 우선한다.

## 발동 조건

- "App Privacy 라벨 채워줘", "Nutrition Label 만들어줘"
- "Data Safety 설문 채워야 해", "Play Data Safety"
- "개인정보 공시", "ATT 카피", "NSUserTrackingUsageDescription 써줘"
- `store-launcher`의 제출 직전 단계, `data-flow-mapper` 인벤토리 완성 직후 호출

## 입력: data-flow.md (필수 상류)

이 skill은 인벤토리를 **소비**한다. 직접 코드를 라벨로 분류하지 않는다 — 그건 `data-flow-mapper`의 일이다. 인벤토리가 없으면 먼저 `data-flow-mapper`를 돌리도록 안내한다.

읽어들이는 섹션:

| data-flow.md 섹션 | 이 skill이 쓰는 것 |
|---|---|
| §1 인벤토리 표 | 데이터 타입 → Apple 카테고리 / Play 유형, 수집 목적 |
| §2 처리자 맵 | "공유(shared)" 판정, 국외이전, 처리자별 전송 |
| §3 위험 목록 | 선언↔코드 불일치, 플랫폼 분기(ATT) 누락 → 경고로 승계 |
| 헤더 메타 | 대상 지역·아동 대상·출시 플랫폼 → 산출물 범위 결정 |

## 강제 원칙 (절대 약화 금지)

| 원칙 | 규칙 |
|---|---|
| **코드 근거 우선** | 라벨의 모든 항목은 인벤토리에 코드 근거가 있어야 한다. 근거 없는 선언은 라벨에 넣지 않는다. |
| **선언↔수집 불일치 = 리젝** | 코드는 수집하는데 라벨에 빠진 항목, 라벨엔 있는데 코드엔 없는 항목 모두 강제 경고. Apple 5.1.1 / Play Data Safety 부정확 신고의 단골 사유. |
| **추적(Tracking) = ATT 필수** | IDFA/광고ID 수집 또는 제3자 광고·데이터 브로커 공유가 있으면 ATT 프롬프트 + `NSUserTrackingUsageDescription` 없이는 라벨이 성립하지 않는다. |
| **공유는 처리자 맵과 1:1** | Play "shared" / Apple "Linked"는 §2 처리자 맵의 국외 전송과 정확히 맞춘다. 처리자로 나가면 공유다. |

## Apple App Privacy Nutrition Label

App Store Connect는 각 데이터 타입에 대해 3가지를 판정한다.

| 판정 축 | 값 | 의미 |
|---|---|---|
| 수집 카테고리 | Contact Info / Location / Identifiers / Usage Data / Diagnostics / Purchases / Health / User Content / Contacts ... | 인벤토리 데이터 타입을 Apple 카테고리로 매핑 |
| Linked to You | Linked / Not Linked | 사용자 신원(계정·식별자)과 연결되면 Linked |
| Used for Tracking | Tracking / Not Tracking | 제3자 광고·데이터 브로커와 연결·공유되면 Tracking → ATT 필수 |

매핑 참조표는 `templates/apple-google-mapping.md`. 인벤토리 §2에서 처리자(광고/분석 SDK)로 나가는 항목이 Tracking/Linked 판정을 좌우한다.

> Diagnostics(크래시·성능)는 보통 Not Linked·Not Tracking. 단 크래시 SDK가 user_id를 붙이면 Linked로 승격.

## Google Play Data Safety

각 데이터 타입에 대해 5개 질문에 답한다.

| 질문 | 판정 근거 |
|---|---|
| 수집(collected)하는가 | 인벤토리 §1에 해당 데이터가 있으면 예 |
| 공유(shared)하는가 | §2 처리자 맵에서 제3자로 전송되면 예 |
| 전송 중 암호화(in transit) | HTTPS/TLS면 예 (네트워크 콜이 https인지 확인) |
| 삭제 요청 제공 | DSAR/계정 삭제 흐름 존재 여부 |
| 수집 목적 | §1 수집 목적 → App functionality / Analytics / Advertising / Account management ... |

> Play의 "공유"는 처리자(3rd party) 전송을 모두 포함한다. 분석·광고 SDK가 있으면 거의 항상 공유 = 예. SDK가 받는 데이터를 §2와 대조.

## ATT 프리프롬프트 + Usage Description

추적(IDFA/광고ID 수집 또는 광고·브로커 공유)이 있을 때만 생성한다. 없으면 ATT 산출물 자체를 건너뛰고 그 사실을 명시.

1. **프리프롬프트(pre-prompt)** — 시스템 ATT 다이얼로그 직전에 띄우는 자체 설명 화면. 거부 시 시스템 다이얼로그를 띄우지 않아 "Denied 영구화"를 피한다. 가치를 솔직하게, 과장 없이.
2. **`NSUserTrackingUsageDescription`** — `app.json`/`Info.plist`의 한 줄. 무엇을·왜를 구체적으로. 빈 값/포괄 문구는 리젝.
3. 카피는 EN/KO 양쪽 생성(C7 키 패리티 관습). 카피 자체에 PII·시크릿·과장·이모지 금지.

카피 템플릿: `templates/att-copy.md`.

## Workflow

### 1. 입력 확인 (AskUserQuestion)

- `data-flow.md` 경로? (없으면 → `data-flow-mapper` 먼저 실행 안내)
- 출시 플랫폼? (App Store / Play / 둘 다) → 산출물 범위
- 추적/광고 SDK 있나? (인벤토리로 이미 알면 확인만) → ATT 산출물 여부
- 기존 라벨/Data Safety 선언이 있나? → 불일치 대조 대상

### 2. 인벤토리 파싱

`scripts/fill-disclosure.mjs`가 `data-flow.md`의 §1 표·§2 처리자 맵·§3 위험 목록을 결정론적으로 파싱한다. 자동 분류가 아니라 **인벤토리에 이미 적힌 사실의 변환**이다.

```bash
node scripts/fill-disclosure.mjs <path/to/data-flow.md> [--out disclosure.md]
```

출력: 채워진 Apple 라벨 표 + Play Data Safety 표 + ATT 필요 여부 + 불일치 경고를 `disclosure.md`로 생성(또는 stdout). 매핑에 모호한 항목은 `[검토필요]`로 남긴다.

### 3. 선언↔수집 불일치 대조 (필수 출력)

기존 라벨/Data Safety 선언이 있으면 인벤토리와 양방향 대조해 강제 경고:

- **과소 선언** — 코드는 수집/공유하는데 라벨에 없음 → 리젝·신고 위험(중대).
- **과대 선언** — 라벨엔 있는데 코드 근거 없음 → 불필요한 신뢰 저하, 정리 권고.
- **Tracking 누락** — 광고ID/광고 공유가 있는데 ATT/Tracking 미표기 → Apple 즉시 리젝.
- **공유 누락** — 처리자 전송이 있는데 Play "shared=아니오" → Data Safety 부정확.

### 4. ATT 산출물 (추적 있을 때만)

`templates/att-copy.md`로 프리프롬프트 EN/KO + `NSUserTrackingUsageDescription` 한 줄 생성. `app.json`의 `ios.infoPlist.NSUserTrackingUsageDescription` 위치를 안내(직접 수정은 사용자 확인 후).

### 5. 산출물 정리

`templates/disclosure.template.md`에 Apple·Play·ATT·불일치 경고를 채워 최종본을 만든다. 각 행에 인벤토리 코드 근거를 역참조로 남긴다.

## 산출물

1. `disclosure.md` — Apple 라벨 표 + Play Data Safety 표 + ATT 필요 여부 + 불일치 경고.
   템플릿: `templates/disclosure.template.md`.
2. (추적 시) ATT 프리프롬프트 EN/KO + `NSUserTrackingUsageDescription`.
   템플릿: `templates/att-copy.md`.
3. 매핑 참조표: `templates/apple-google-mapping.md`.

## 검증 체크리스트

- [ ] Apple/Play 라벨의 모든 항목이 `data-flow.md`에 코드 근거를 가짐 (근거 없는 선언 0건)
- [ ] 인벤토리엔 있는데 라벨에 빠진 항목 0건 (과소 선언 없음)
- [ ] 라벨엔 있는데 코드 근거 없는 항목이 `[검토필요]`로 플래그됨 (과대 선언 정리)
- [ ] 광고ID 수집·광고/브로커 공유가 있으면 Apple Tracking=예 + ATT + `NSUserTrackingUsageDescription` 존재
- [ ] Play "shared" 판정이 §2 처리자 맵의 제3자 전송과 1:1로 일치
- [ ] 전송 암호화(in transit) 판정이 실제 네트워크 콜(https)과 일치
- [ ] 삭제 요청 제공 여부가 실제 DSAR/계정삭제 흐름과 일치
- [ ] ATT 카피에 PII·시크릿·과장·이모지 없음, EN/KO 패리티 충족
- [ ] 기존 선언과의 불일치가 과소/과대/Tracking/공유로 분류되어 경고에 빠짐없이 포함됨

## Related Skills

- `data-flow-mapper` — 이 skill의 단일 상류 입력(`data-flow.md`)을 생성. 라벨은 그 인벤토리의 변환물이다.
- `consent-manager` — Tracking/광고 항목의 실제 동의 게이트(ATT·카테고리 동의)를 구현. 이 skill은 그 결과를 공시로 선언.
- `store-launcher` — 제출 패키지에 이 공시 산출물(App Privacy 라벨·Data Safety·ATT)을 포함. 5.1.1/Data Safety 리젝 방지 단계와 연결.
