---
name: mobile-attribution-integrator
description: "Use when the user wants to wire mobile install attribution—triggers \"설치 어트리뷰션\", \"SKAdNetwork\", \"ATT 프롬프트\", \"UA 추적\", \"앱 광고 측정\", \"deferred deep link\", \"install referrer\", \"MMP 연동\", \"install attribution\", \"app ad measurement\", \"/mobile-attribution-integrator\". Produces a mobile attribution wiring plan: MMP SDK pick (Branch/AppsFlyer free tier) → SKAdNetwork conversion-value map → iOS ATT pre-prompt → Apple AdServices + Android Install Referrer → deferred deep-link install→first-open join → channel-attributable first_open event. NOT web/page tracking—that is tag-manager-integrator."
allowed-tools: Read, Write, Edit, Bash, WebSearch, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# mobile-attribution-integrator

모바일 **앱 설치(install) 어트리뷰션** 을 배선하는 skill. "이 설치가 어느 광고·채널에서 왔나" 를 프라이버시 프레임워크(SKAdNetwork/AdAttributionKit·ATT) 안에서 측정한다. RN/Expo·네이티브 모두 적용.

## tag-manager-integrator 와 혼동 금지

| | mobile-attribution-integrator (이 skill) | tag-manager-integrator |
|---|---|---|
| 대상 | **네이티브 앱 설치**(iOS/Android) | **웹 페이지** 이벤트 |
| 측정 단위 | install → first_open, 채널 귀속 | page_view, click, conversion |
| 프레임워크 | SKAdNetwork/AAK, ATT, Install Referrer, AdServices | GTM/gtag, Meta Pixel, 쿠키 |
| 식별자 | IDFA(ATT 동의 시), GAID, 디바이스 핑거프린트 금지 | 쿠키·webId |

"앱 설치 추적"·"SKAdNetwork"·"ATT" → 이 skill. "GTM"·"전환 태그"·"웹 픽셀" → tag-manager-integrator. 광고를 **집행**(기획)하는 건 paid-ads-campaign, 딥링크 라우팅 자체는 deeplink-integrator, 동의 UI 는 consent-manager 로 핸드오프.

## 발동 조건

- "설치 어트리뷰션 붙여줘", "어느 광고로 설치됐는지 보고 싶어"
- "SKAdNetwork 설정", "ATT 프롬프트", "UA 추적", "앱 광고 측정"
- paid-ads-campaign 에서 "전환 추적 핸드오프" 가 모바일 앱일 때 체인

## 사전 질문 (먼저 확정)

`AskUserQuestion` 으로 다음을 묻고 진행한다. 가정 금지.

1. 플랫폼: iOS 전용 / Android 전용 / 둘 다
2. 런타임: Expo(managed/dev-client) / bare RN / 네이티브
3. 광고 채널: Meta / Google(UAC) / TikTok / Apple Search Ads / 유기적만
4. 예상 월 비유기적 설치 수 (MMP 무료 티어 판단용)
5. deferred deep link 필요 여부 (설치 후 특정 화면·프로모코드로 진입)

## 1. MMP SDK 선택 (무료 티어 우선)

MMP(Mobile Measurement Partner)는 채널별 postback·딥링크·SKAN 맵을 한 곳에서 통합한다. 직접 SKAN 만 다루면 채널마다 따로 배선해야 하므로, 초기엔 MMP 무료 티어가 비용·공수 모두 유리하다.

| MMP | 무료 티어 (2026 기준, 변동 가능) | 강점 | 비고 |
|---|---|---|---|
| **Branch** | deep linking + 기본 attribution 무료 | deferred deep link 1급, 링크 생성 무제한 | 딥링크 중심이면 기본값 |
| **AppsFlyer** | "Zero" 플랜: 생애 비유기적 설치 12k 미만 / 첫 12개월 전환 12k | 채널 커버리지·부정설치 방지 광범위 | 성장 후 전환당 과금($0.07~) — 볼륨 늘면 비쌈 |
| **Adjust** | 무료 attribution 티어(월 ~1.5k attribution) | 투명한 정액 요금, 구독 앱 강점 | 엔터프라이즈는 custom |
| **직접(SKAN+Referrer)** | $0 | 의존성 0, $0/mo 제약 부합 | 채널별 수동 배선, deferred DL 직접 구현 |

원칙: **무료 티어 한도 안에서 시작**하고, 한도·전환당 과금이 free-tier 약속($0/mo)을 깨는지 반드시 확인. 딥링크가 핵심이면 Branch, 채널 다변화·부정설치 우려가 크면 AppsFlyer Zero, 의존성 0 을 원하면 직접 배선.

설치 전 최신 SDK 버전·요금·SKAN 호환을 `WebSearch` 로 재확인(요금/한도는 자주 바뀜). 시크릿(MMP dev key)은 env 로만 — 하드코딩 금지.

```
EXPO_PUBLIC_MMP_PROVIDER=branch        # branch | appsflyer | adjust | none
BRANCH_KEY=...            # native config / EAS secret, 코드 하드코딩 금지
APPSFLYER_DEV_KEY=...
```

## 2. SKAdNetwork / AdAttributionKit conversion-value 맵 (iOS)

iOS 는 IDFA 동의가 없어도 SKAdNetwork(SKAN) 으로 **익명·집계** 어트리뷰션을 받는다. SKAN 4 는 postback 을 3개 윈도우로 받는다: **0–2일 / 3–7일 / 8–35일**. AdAttributionKit(AAK, iOS 17.4+/18+)는 SKAN 후속 프레임워크로 재참여·웹→앱까지 확장 — 신규 앱은 SKAN 호환 맵을 먼저 세우고 AAK 로 점진 확장.

conversion value 종류:
- **fine** (0–63, 6비트): 설치량 충분할 때. 행동·매출 구간을 직접 인코딩.
- **coarse** (low/medium/high): 설치량 적은 캠페인의 프라이버시 임계 충족용.

설계 원칙: CV 는 "설치 직후 N시간 내 가치"를 1개 숫자로 압축한다. 비즈니스 마일스톤을 우선순위로 매핑(예: 가입 > 첫 핵심행동 > 결제). `templates/skan-conversion-map.json` 에서 시작.

```jsonc
// fine value 예시 (0-63) — 가치 오름차순
0  = install only
1  = first_open
2  = onboarding_complete
5  = aha_moment_reached      // 핵심 가치 경험 (aha-moment-optimizer 연동)
10 = signup_completed
20 = subscription_trial
40 = purchase
```

`Info.plist` 에 채널별 `SKAdNetworkItems`(네트워크 ID) 등록 필수 — MMP·채널 문서의 최신 ID 목록을 그대로 반영(임의 추정 금지). Expo 는 `app.json` 의 `ios.infoPlist` 또는 config plugin 으로 주입.

## 3. iOS ATT 프롬프트 (사전 설득 우선)

ATT(App Tracking Transparency) 동의가 있어야 IDFA 기반 결정론적 매칭이 가능하다. 동의 없어도 SKAN 은 동작하므로 **ATT 거부 = 측정 0 이 아니다**. 시스템 프롬프트는 1회뿐 → 거부율을 낮추려면 **사전 설득 화면(pre-prompt)** 으로 가치를 먼저 설명하고, 사용자가 "허용" 의향을 보일 때만 시스템 다이얼로그를 띄운다.

| 단계 | 화면 | 규칙 |
|---|---|---|
| 1 | pre-prompt (앱 자체 UI) | 측정 가치 1줄 + "다음" 1개 CTA. 강요·다크패턴 금지 |
| 2 | 시스템 ATT 다이얼로그 | pre-prompt 통과 후에만. `Info.plist` `NSUserTrackingUsageDescription` 필수 |
| 3 | 분기 | 허용 → IDFA 사용 / 거부 → SKAN·AdServices 로 폴백 |

문구는 정직하게(과장·"꼭 허용하세요" 강요 금지). 표현은 제품 어휘 정책 준수 — clinical/과장 용어 금지. 동의 상태·시각은 audit 로 남긴다. 동의 UI 전반은 consent-manager 와 정렬. `templates/att-pre-prompt.tsx` 참고.

## 4. 채널 신호 수집: Apple AdServices + Android Install Referrer

MMP 없이 직접 배선하거나 MMP 신호를 보강할 때 사용하는 1st-party 소스.

| 플랫폼 | 소스 | 무엇을 주나 | 비고 |
|---|---|---|---|
| iOS | **Apple AdServices** (AAAttribution) | Apple Search Ads 캠페인 토큰 → attribution API 로 캠페인·키워드 | ASA 집행 시. 토큰은 설치 직후 단기 유효 |
| iOS | SKAdNetwork postback | 채널·CV(집계) | 위 2절 |
| Android | **Google Play Install Referrer** | `install_referrer` 문자열(utm_* 포함), 클릭→설치 시각 | Play Console 라이브러리, 설치 후 1회 조회 |
| Android | Google Ads gclid / Meta referrer | 채널별 referrer 파라미터 | MMP 가 보통 파싱 |

Google Play Install Referrer는 첫 실행 후 한 번 조회하고 연결을 종료한다([공식 라이브러리 안내](https://developer.android.com/google/play/installreferrer/library)). 수집한 문자열은 외부 입력으로 취급해 `scripts/parse-install-referrer.ts`의 순수 함수 `parseInstallReferrer`로 정규화한다. 이 함수는 SDK 호출·로그·딥링크 라우팅을 하지 않고, 알 수 없는 소스를 `channel=null`, `matchedBy=none`으로 남긴다. 반환값의 `verified=false`는 referrer 문구만으로 광고 집행·결제 전환이 증명되지 않음을 뜻한다. 핑거프린팅(IP+UA 확률적 매칭)은 기본 비활성.

## 5. deferred deep-link: install → first_open 조인

deferred deep link = 앱 미설치 사용자가 광고/링크를 누르면 → 스토어 설치 → **첫 실행 시** 원래 의도한 화면·컨텍스트(프로모코드·초대·콘텐츠)로 보내는 흐름. 어트리뷰션과 같은 조인 키를 공유한다.

```
[광고 클릭]
   │  click_id + deep_link_data 저장 (MMP 서버 또는 1st-party)
   ▼
[스토어 → 설치 → first_open]
   │  iOS: AdServices token / SKAN  ·  Android: Install Referrer
   ▼
[조인]  click ↔ first_open  (MMP 매칭 or referrer utm 매칭)
   ▼
[라우팅]  deep_link_data → 화면 이동   (deeplink-integrator 핸드오프)
   +
[이벤트]  first_open { channel, campaign, deeplink, matched_by }
```

조인 키 우선순위: ① 검증된 MMP 결정론적 매칭 → ② Install Referrer 신호(Android) → ③ AdServices 토큰(iOS ASA). SKAN/AdAttributionKit postback은 사용자·기기 식별자를 제공하지 않는 집계 측정이므로 개별 `first_open`에 조인하지 않고 별도 캠페인 집계로 다룬다([Apple 공식 개요](https://developer.apple.com/documentation/adattributionkit)). 라우팅 자체(URL→화면 스택)는 deeplink-integrator 로 넘긴다.

## 6. 채널 귀속 first_open 이벤트 (최종 산출)

모든 신호를 합쳐 **채널이 귀속된 first_open** 한 건을 만들고, 이후 분석으로 흘려보낸다. 스키마를 analytics/tag-manager 의 이벤트 택소노미와 일치시킨다.

```jsonc
// first_open 이벤트 표준 스키마
{
  "event": "first_open",
  "platform": "ios" | "android",
  "channel": "meta" | "google" | "tiktok" | "apple_search_ads" | "organic" | null,
  "campaign": "conv_app_2606",          // utm_campaign 정규화
  "matched_by": "mmp" | "install_referrer" | "adservices" | "none",
  "deferred_deeplink": "app://invite/AB12" | null,
  "att_status": "authorized" | "denied" | "not_determined",
  "skan_cv": 1,                          // iOS conversion value (있으면)
  "ts": "ISO8601"
}
```

핸드오프: 이 이벤트를 analytics-integrator(택소노미·퍼널) / tag-manager-integrator(서버사이드 전환) 로 보내 Acquisition 단계를 채운다. 개별 설치에 조인할 근거가 없으면 `matched_by=none`, `channel=null`로 기록한다. 확인되지 않은 설치를 `organic`으로 간주하거나 SKAN 집계 결과를 특정 사용자에게 붙이지 않는다. 기존 스키마의 `skan_aggregate` 값은 호환용으로만 남아 있으며 새 개별 이벤트에서 사용하지 않는다.

## 검증 체크리스트

- [ ] 플랫폼·런타임·채널·예상 설치량 사전 확인(AskUserQuestion) 완료
- [ ] MMP 무료 티어 한도 확인 — free-tier 약속($0/mo) 위반 없음
- [ ] MMP dev key·토큰 전부 env/EAS secret (코드 하드코딩 0)
- [ ] iOS `Info.plist`: `SKAdNetworkItems`(채널 ID 최신) + `NSUserTrackingUsageDescription` 존재
- [ ] ATT 사전 설득 화면 → 시스템 프롬프트 순서, 강요/다크패턴 없음
- [ ] ATT 거부 시 SKAN/AdServices 폴백 경로 동작 (측정 0 아님)
- [ ] Android Install Referrer 1회 조회 + utm 파싱 정규화
- [ ] referrer 알 수 없음·중복·비정상 입력은 귀속 실패로 기록; 클릭 ID 원문을 로그에 남기지 않음
- [ ] deferred deep link 라우팅은 deeplink-integrator 로 핸드오프
- [ ] first_open 이벤트 스키마가 analytics 택소노미와 일치
- [ ] 미매칭 설치는 `channel=null`, `matched_by=none`; SKAN/AAK는 집계로만 보고
- [ ] 핑거프린팅 비활성 (프라이버시·정책)

## Related Skills

- `tag-manager-integrator` — (혼동 주의) 웹 페이지 이벤트·전환 태그. 이 skill 은 앱 설치 어트리뷰션
- `paid-ads-campaign` — 광고 집행(기획). 전환 추적 핸드오프가 모바일이면 이 skill 로 체인
- `deeplink-integrator` — 딥링크 URL→화면 라우팅. deferred DL 라우팅 부분 핸드오프
- `consent-manager` — ATT/개인정보 동의 UI·기록 정렬
- `analytics-integrator` — first_open 택소노미·퍼널 연동
- `aha-moment-optimizer` — SKAN conversion value 에 매핑할 핵심 가치 마일스톤 정의

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
