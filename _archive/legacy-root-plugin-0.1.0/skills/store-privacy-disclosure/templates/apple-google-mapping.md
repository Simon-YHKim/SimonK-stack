# Apple / Google 매핑 참조표

> `data-flow.md` §1 인벤토리의 각 데이터 타입을 스토어 공시 카테고리로 변환하는 참조표.
> `fill-disclosure.mjs`의 분류 규칙과 동일한 매핑을 사람이 읽을 수 있게 펼친 것이다.
> 코드에서 관측된 수집만 반영한다 — 선언과 코드가 다르면 코드가 우선.

## Apple App Privacy Nutrition Label

3축 판정: (1) 카테고리, (2) Linked to You, (3) Used for Tracking.

| 인벤토리 데이터 타입 | Apple 카테고리 | Linked | Tracking |
|---|---|---|---|
| 이메일·이름·전화·연락처 정보 | Contact Info | Linked | 광고 공유 시 Tracking |
| 위치(정밀) | Location (Precise) | Linked | 광고 공유 시 Tracking |
| 위치(대략) | Location (Coarse) | Linked | 광고 공유 시 Tracking |
| 광고ID / IDFA | Identifiers | Linked | **Tracking** (항상) |
| 디바이스ID / 푸시 토큰 | Identifiers | Linked | 광고 공유 시 Tracking |
| 사용 이벤트 / 분석 | Usage Data | Linked | 광고 SDK면 Tracking |
| 크래시 · 진단 · 성능 | Diagnostics | Not Linked* | Not Tracking |
| 결제 · 구매 | Purchases | Linked | Not Tracking |
| 사진 · 영상 · 미디어 | User Content | Linked | Not Tracking |
| 건강 · 생체 | Health & Fitness | Linked | Not Tracking |
| 주민/여권 등 식별번호 | Sensitive Info | Linked | Not Tracking |

\* 크래시 SDK가 user_id를 첨부하면 Diagnostics라도 Linked로 승격.

> **Tracking 판정 = ATT 필수.** 광고 식별자 수집 또는 §2 처리자 맵에서 광고/브로커로 데이터가 나가면 Tracking. `att-copy.md`로 프리프롬프트 + `NSUserTrackingUsageDescription` 생성.

## Google Play Data Safety

각 데이터 타입에 5개 질문: 수집 / 공유 / 전송 암호화 / 삭제요청 제공 / 목적.

| 인벤토리 데이터 타입 | Play 유형 | 공유 판정 | 목적 |
|---|---|---|---|
| 이메일 · 이름 · 전화 | Personal info | 처리자 전송 시 공유 | Account management |
| 위치(정밀/대략) | Location (Precise/Approximate) | 광고 SDK면 공유 | App functionality |
| 광고ID(AAID) | Device or other IDs | 광고 시 공유 | Advertising or marketing |
| 디바이스ID / 토큰 | Device or other IDs | 처리자 전송 시 공유 | App functionality |
| 사용 이벤트 | App activity | 분석 SDK 공유 | Analytics |
| 크래시 · 성능 | App info and performance | Crashlytics 공유 | App functionality |
| 결제 | Financial info | PG 공유 | App functionality |
| 사진 · 파일 | Photos and videos / Files | 보통 미공유 | App functionality |
| 건강 | Health and fitness | 강화 고지 | App functionality |

> Play "공유(shared)" = 제3자(처리자)에게 전송되는 모든 경우. `data-flow.md` §2 처리자 맵과 1:1로 맞춘다. 전송 암호화는 네트워크 콜이 https/TLS인지로, 삭제요청 제공은 DSAR/계정삭제 흐름 존재로 확정.

## 모호 / 미매핑 처리

규칙에 걸리지 않는 데이터 타입은 자동 분류하지 않고 `[검토필요]`로 남긴다. 법적·심사 산출물에서 자동 추정을 신뢰하지 않는다 — 사람이 카테고리/유형을 확정한다.

## 검증

- [ ] 모든 공시 항목이 `data-flow.md`에 코드 근거를 가짐
- [ ] 인벤토리엔 있는데 공시에 빠진 항목 없음 (과소 선언 없음)
- [ ] Tracking/공유 판정이 §2 처리자 맵의 광고·분석 SDK 실제 전송과 일치
- [ ] `[검토필요]` 항목이 사람에 의해 모두 확정됨
