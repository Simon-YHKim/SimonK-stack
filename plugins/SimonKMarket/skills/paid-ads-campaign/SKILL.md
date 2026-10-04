---
name: paid-ads-campaign
description: "Use when the user wants to plan or run a paid ad campaign as the advertiser—triggers \"광고 돌리고 싶어\", \"메타 광고\", \"구글 광고 세팅\", \"퍼포먼스 마케팅\", \"네이버 광고\", \"카카오 광고\", \"리타겟팅\", \"ROAS 개선\", \"run ads\", \"performance marketing\", \"/paid-ads-campaign\". Produces a campaign plan: objective (인지/전환/리타겟) → audience design → channel/budget split (Meta/Google/Naver/Kakao) → creative brief → UTM + conversion tracking handoff → measurement (ROAS/CAC/CTR) → optimization loop. Knowledge skill, no backend. NOT for serving ads in your own app—that is ad-monetization."
allowed-tools: Read, WebSearch, WebFetch, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# paid-ads-campaign

광고주 입장에서 **돈을 내고 집행하는** 유료광고 캠페인을 기획·집행하는 skill.

## ⚠️ ad-monetization 과 혼동 금지

| | paid-ads-campaign (이 skill) | ad-monetization |
|---|---|---|
| 입장 | **광고주** (돈을 낸다) | **퍼블리셔** (돈을 받는다) |
| 하는 일 | Meta/Google/네이버/카카오에 광고 집행 | 내 앱/사이트에 광고 SDK 게재 |
| 목표 | 유저 획득·전환 (CAC↓, ROAS↑) | 광고 수익 (eCPM↑) |
| 발동 | "광고 돌리고 싶어" | "광고 붙여줘" |

"광고 붙여줘"·"AdMob 연동" 이면 ad-monetization 으로 보낸다. 이 skill 은 "광고 **돌리고** 싶어"·"메타 광고 세팅"·"퍼포먼스 마케팅" 이다.

## 발동 조건

- "광고 돌리고 싶어", "메타 광고 세팅", "구글 광고", "네이버/카카오 광고"
- "퍼포먼스 마케팅", "리타겟팅 캠페인", "ROAS 개선해줘"
- monetization-planner / growth-engine 에서 "유료 획득 채널" 선택 시 체인

## 예산 게이트 (먼저 확인)

집행 전 `AskUserQuestion` 으로 월 광고 예산을 묻는다. 예산이 작으면 유료 집행을 권하지 않는다.

| 월 예산 | 권고 |
|---|---|
| ~30만원 미만 | **유료 집행 보류.** 유기적 채널(콘텐츠·커뮤니티·SEO) + 소액 A/B 테스트만. growth-engine 으로 핸드오프 |
| 30만~100만원 | 단일 채널 집중 (보통 Meta), 소액 테스트로 CAC 검증 후 확장 |
| 100만~500만원 | 2채널 (Meta + Google/네이버), 리타겟팅 추가 |
| 500만원+ | 풀퍼널 (인지+전환+리타겟), 채널 3개+, 크리에이티브 다변화 |

소액 테스트 원칙: 채널·오디언스·크리에이티브 중 **한 번에 하나만** 바꾸며 검증. 통계적으로 의미 있는 결론 전까지 예산 확대 금지.

## Workflow

### 1. 목표 정의 (퍼널 단계)

| 목표 | 퍼널 | 최적화 지표 | 입찰 방식 |
|---|---|---|---|
| **인지 (Awareness)** | 상단 | CPM, 도달, 노출 빈도 | 노출 최적화 |
| **고려 (Consideration)** | 중단 | CTR, CPC, 영상 조회, 트래픽 | 클릭/참여 최적화 |
| **전환 (Conversion)** | 하단 | CPA, ROAS, 가입·구매 | 전환 최적화 (픽셀 필수) |
| **리타겟 (Retargeting)** | 재방문 | ROAS, 장바구니 회수율 | 전환 최적화 (모수 필요) |

한 캠페인은 하나의 목표만. 인지와 전환을 한 캠페인에 섞지 않는다. 신규 서비스는 전환 모수가 부족하므로 트래픽/참여로 모수를 먼저 쌓고 전환으로 전환.

### 2. 타깃·오디언스 설계

- **핵심(Core)**: 인구·관심사·행동 기반. 처음엔 너무 좁히지 말 것 (Meta Advantage+ 등 알고리즘에 학습 여지)
- **맞춤(Custom)**: 사이트 방문자·고객 리스트·앱 이벤트 → 리타겟용
- **유사(Lookalike/유사타깃)**: 우수 고객 시드(구매자·고LTV) 기반 1~3% 확장
- **제외(Exclusion)**: 기존 전환자·직원·구매 완료자 제외로 낭비 차단

오디언스는 캠페인 목표와 매칭: 인지=Core 넓게, 전환=Custom/Lookalike, 리타겟=Custom(방문/장바구니).

### 3. 채널·예산 배분

| 채널 | 강점 | 적합 목표 | 최소 권장 예산(월) | 비고 |
|---|---|---|---|---|
| **Meta** (FB/IG) | 정교한 타깃·유사타깃, 비주얼·릴스 | 전환·리타겟·인지 | 30만원~ | B2C 기본값, 크리에이티브 의존도 높음 |
| **Google Search** | 구매 의도(키워드) 직격 | 전환(하단) | 50만원~ | 의도 명확, CPC 경쟁 비쌈 |
| **Google PMax/Display/YouTube** | 도달·리타겟·영상 | 인지·리타겟 | 30만원~ | GDN 리타겟 저렴, PMax는 모수 필요 |
| **네이버 GFA** (성과형 디스플레이) | 국내 도달, 스마트채널·피드 지면 | 인지·전환 | 50만원~ | 국내 타깃, 네이버 생태계(쇼핑·플레이스) 연계 |
| **네이버 검색광고** (파워링크) | 국내 검색 의도 1위 | 전환(하단) | 30만원~ | 키워드 입찰, 국내 구매 의도 최강 |
| **카카오모먼트** | 카톡·다음 지면, 톡채널 친구 모수 | 인지·전환·리타겟 | 50만원~ | 국내 도달 광범위, 톡채널 연계 시 강력 |

배분 원칙: 의도가 명확한 하단(검색)부터 채우고 → 잉여 예산을 상·중단(디스플레이/소셜)으로. 국내 타깃이면 네이버·카카오 비중↑, 글로벌·비주얼 제품이면 Meta↑.

### 4. 크리에이티브 브리프

채널·목표별 소재 3~5종을 같은 메시지·다른 앵글로 준비 (A/B 모수 확보).

```
[크리에이티브 브리프]
- 캠페인 목표: (전환 / 가입)
- 핵심 메시지(1줄): 사용자가 얻는 변화. 기능 나열 금지
- 타깃 페르소나: 누가 / 어떤 불편 / 왜 지금
- 앵글(소재별): ① 문제제기 ② 사회적증거 ③ 비포애프터 ④ 혜택직격
- 포맷: Meta=릴스/단일이미지/캐러셀 · 검색=확장텍스트 · GFA/카카오=이미지+카피
- CTA: 하나만 (지금 시작 / 무료 체험)
- 랜딩: 광고 메시지와 일치하는 페이지(메시지 매치)
- 금지: 과장·의료/효능 단정·미승인 클레임 (각 채널 정책)
```

AI 슬롭 방지: 이모지 떡칠·과장 문구·기능 나열형 카피 금지. 하나의 메시지 + 하나의 CTA.

### 5. UTM + 전환추적 (핸드오프)

광고 클릭이 어느 캠페인·소재에서 왔는지 추적하려면 UTM 표준화 + 픽셀/전환 태그 설치가 필수다. **구현은 다음 skill 로 핸드오프**한다 (이 skill 은 지식·설계만):

- **tag-manager-integrator** → GTM/gtag, Meta Pixel·Google Ads 전환 태그·CAPI 설치
- **analytics-integrator** → 이벤트 택소노미·퍼널·동의(개인정보보호법/GDPR) 연동

UTM 규칙 (소문자·일관성):

```
utm_source   = meta | google | naver | kakao
utm_medium   = cpc | display | social | retargeting
utm_campaign = {목표}_{제품}_{연월}   예: conv_2ndb_2606
utm_content  = {소재식별}             예: angle_socialproof_v2
utm_term     = {키워드}               (검색광고만)
```

전환 추적 체크: 픽셀/태그 발화 확인 → 전환 이벤트 매핑 → (가능하면) 서버사이드 CAPI 로 iOS ATT·쿠키 소실 보완 → 동의 전 미수집.

### 6. 측정 지표

| 지표 | 공식 | 의미 |
|---|---|---|
| **CTR** | 클릭 / 노출 | 소재·타깃 매력도 (낮으면 크리에이티브 교체) |
| **CPC** | 비용 / 클릭 | 트래픽 단가 |
| **CPA / CAC** | 비용 / 전환 | 고객 1명 획득 비용 |
| **ROAS** | 광고매출 / 광고비 | 광고 효율 (보통 손익분기 >100%, 목표 250%+) |
| **CVR** | 전환 / 클릭 | 랜딩·오퍼 설득력 |
| **빈도(Frequency)** | 노출 / 도달 | 3 초과 시 피로 → 소재 교체 |

핵심 가드레일: **CAC < LTV** (보통 LTV/CAC ≥ 3). 이 비율이 안 나오면 채널을 늘리지 말고 전환율·객단가·리텐션부터 손본다 (pmf-analyzer / aha-moment-optimizer 핸드오프).

### 7. 최적화 루프 (주간)

```
관찰(지표 수집) → 진단(병목 단계 식별) → 가설(한 변수) → 실험(소액) → 판정 → 확장 or 중단
```

- 학습 기간 존중: Meta/Google 알고리즘 학습 중 잦은 수정 금지 (보통 전환 50건/주 전까지)
- 병목별 처방: CTR↓ → 크리에이티브 / CVR↓ → 랜딩·오퍼 / CPM↑ → 타깃·경쟁 / ROAS↓ → 입찰·제외·LTV
- 끄는 기준 명시: 손익분기 ROAS 미달이 N일 지속 시 중단. 감으로 끌지 않는다
- 승자 소재는 예산 증액(한 번에 20~30%), 패자는 끄고 새 앵글 투입

## 검증 체크리스트

- [ ] 캠페인당 단일 목표 (인지/전환 미혼합)
- [ ] 예산 게이트 통과 (저예산이면 유기적·소액 테스트 우선)
- [ ] 픽셀/전환 태그 설치 확인 (tag-manager-integrator 핸드오프 완료)
- [ ] UTM 규칙 일관 적용 (소문자, source/medium/campaign)
- [ ] 소재 3~5종 + 명확한 단일 CTA + 메시지-랜딩 일치
- [ ] 제외 오디언스 설정 (기존 전환자 낭비 차단)
- [ ] CAC < LTV 가드레일 + 중단 기준 사전 정의
- [ ] 각 채널 광고 정책 준수 (과장·금지업종·개인화 동의)

## Related Skills

- `ad-monetization` — (혼동 주의) 내 앱에 광고 게재 = 퍼블리셔 측, 정반대 방향
- `tag-manager-integrator` — 픽셀·전환 태그·UTM 구현 핸드오프
- `analytics-integrator` — 이벤트 택소노미·퍼널·동의 연동
- `growth-engine` — 어트리뷰션·A/B·유기적 채널
- `aarrr-growth-planner` — Acquisition 단계에서 유료 채널 위치 잡기
- `monetization-planner` / `revenue-scenario-tester` — LTV·단가 가정 검증

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
