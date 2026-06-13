# 스토어 개인정보 공시 — <앱 이름>

> 이 문서는 `data-flow.md`(data-flow-mapper 인벤토리)에서 파생된 스토어 제출용 공시다.
> App Store Connect의 App Privacy 라벨, Google Play Data Safety 설문에 그대로 입력한다.
> 모든 항목은 인벤토리의 코드 근거를 가져야 한다. 근거 없는 선언은 넣지 않는다.

- 작성일: YYYY-MM-DD
- 입력 인벤토리: `data-flow.md` (스캔 커밋 `<git sha>`)
- 출시 플랫폼: <App Store / Play / 둘 다>
- 추적(ATT) 필요: <예 / 아니오>

## 1. Apple App Privacy Nutrition Label

App Store Connect → App Privacy 에 입력. 각 행: 카테고리 / Linked to You / Used for Tracking.

| 데이터 타입 | Apple 카테고리 | Linked to You | Used for Tracking | 코드 근거 |
|---|---|---|---|---|
| 이메일 | Contact Info | Linked | Not Tracking | `src/lib/auth` |
| 광고ID(IDFA) | Identifiers | Linked | Tracking | `AdMob init` |
| 크래시·진단 | Diagnostics | Not Linked | Not Tracking | `Crashlytics init` |
| <...> | | | | |

> IDFA 수집 또는 광고/브로커 공유 = Tracking → §3 ATT 필수. Diagnostics에 user_id가 붙으면 Linked로 승격.

## 2. Google Play Data Safety

Play Console → Data safety 에 입력. 각 데이터 타입에 5개 질문.

| 데이터 타입 | Play 유형 | 수집 | 공유 | 전송 암호화 | 삭제요청 | 수집 목적 | 코드 근거 |
|---|---|---|---|---|---|---|---|
| 이메일 | Personal info | 예 | 아니오 | 예(TLS) | 예 | Account management | `src/lib/auth` |
| 사용 이벤트 | App activity | 예 | 예(GA4) | 예(TLS) | 아니오 | Analytics | `App.tsx init` |
| <...> | | | | | | | |

> "공유"는 §2 처리자 맵의 제3자 전송과 1:1로 일치해야 한다. 분석·광고 SDK가 있으면 거의 항상 공유=예.

## 3. ATT (App Tracking Transparency)

- 추적 필요: <예 / 아니오> (광고ID 수집 또는 광고/브로커 공유 시 예)
- 프리프롬프트 카피: `att-copy.md` 참조 (EN/KO)
- `NSUserTrackingUsageDescription`: <한 줄 카피 — 빈 값/포괄 문구 금지>
- `app.json` 위치: `ios.infoPlist.NSUserTrackingUsageDescription`

추적이 없으면 이 섹션 전체를 "추적 없음 — ATT 미적용"으로 남기고 ATT 산출물을 추가하지 않는다.

## 4. 불일치 / 검토 경고 (필수)

각 항목: 무엇 / 어디 / 분류 / 조치.

### 과소 선언 (코드 수집 O, 라벨 X) — 리젝 위험(중대)
- [ ] <코드는 수집/공유하나 라벨에 없는 항목 — 데이터 타입 / 코드 근거>

### 과대 선언 (라벨 O, 코드 근거 X) — 정리 권고
- [ ] <라벨에 있으나 인벤토리 근거 없는 항목 — 데이터 타입>

### Tracking 누락 — Apple 즉시 리젝
- [ ] <광고ID/광고 공유가 있으나 ATT/Tracking 미표기 — 항목>

### 공유 누락 — Data Safety 부정확
- [ ] <처리자 전송이 있으나 Play "shared=아니오" — 항목 / 처리자>

### 매핑 미결 (`[검토필요]`)
- [ ] <자동 매핑되지 않아 사람이 카테고리/유형 지정 필요한 항목>
