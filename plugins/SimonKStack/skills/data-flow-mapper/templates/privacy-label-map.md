# Privacy Label 매핑 — Apple / Google

> `data-flow.md` §1 인벤토리의 각 데이터 타입을 스토어 라벨 카테고리로 변환하는 참조표.
> 라벨은 코드에서 관측된 수집만 반영한다 — 선언과 코드가 다르면 코드가 우선.

## Apple Privacy Nutrition Label

App Store Connect 입력 시 3가지를 판정한다: (1) 수집 카테고리, (2) Linked to You(식별자와 연결됨), (3) Used for Tracking(추적·광고).

| 인벤토리 데이터 타입 | Apple 카테고리 | 흔한 판정 |
|---|---|---|
| 이메일·이름·전화 | Contact Info | Linked |
| 위치(정밀/대략) | Location → Precise / Coarse | Linked |
| 디바이스ID / IDFA | Identifiers | Linked + Tracking(광고 시) |
| 사용 이벤트 | Usage Data | 광고 SDK면 Tracking |
| 크래시·진단 | Diagnostics | 보통 Not Linked |
| 결제·구매 | Purchases / Financial Info | Linked |
| 사진·연락처 | User Content / Contacts | Linked |
| 건강·생체 | Health & Fitness / Sensitive Info | Linked |

> IDFA 수집·추적이 있으면 ATT(App Tracking Transparency) 프롬프트 + `NSUserTrackingUsageDescription` 필수. 플랫폼 분기 위험 항목과 교차 확인.

## Google Play Data Safety

각 데이터 타입에 대해: 수집 여부 / 공유 여부 / 전송 암호화 / 삭제요청 제공 / 수집 목적.

| 인벤토리 데이터 타입 | Play 데이터 유형 | 공유 가능성 |
|---|---|---|
| 이메일·이름 | Personal info | 처리자 전송 시 공유 |
| 위치 | Location (Approximate/Precise) | 광고 SDK면 공유 |
| 광고ID(AAID) | Device or other IDs | 광고 시 공유 |
| 사용 이벤트 | App activity | 분석 SDK 공유 |
| 크래시 | App info and performance | Crashlytics 공유 |
| 결제 | Financial info | PG 공유 |
| 사진·파일 | Photos and videos / Files | 보통 미공유 |
| 건강 | Health and fitness | 강화 고지 |

> "공유(shared)"는 제3자(처리자)에게 전송되는 모든 경우를 포함한다 — `data-flow.md` 처리자 맵과 1:1로 맞춘다.

## 검증

- [ ] 라벨의 모든 항목이 `data-flow.md`에 코드 근거를 가짐
- [ ] 인벤토리엔 있는데 라벨에 빠진 항목 없음 (반대도)
- [ ] Tracking/공유 판정이 광고·분석 SDK 실제 사용과 일치
