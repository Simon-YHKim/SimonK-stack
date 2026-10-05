---
name: skmarket
version: 0.1.0
description: >
  Use when routing marketing, market-research, or public-sentiment work — the SimonKMarket 오케스트레이터, 단일 진입점. 트리거 "시장조사", "마케팅 전략", "그로스", "수익화", "광고 붙여줘", "PMF", "런칭", "여론 분석", "skmarket", 또는 /skmarket. Produces a rough intent diagnosis then routes to the right 하위 스킬, 산출물마다 사용자와 상호작용하며 반복 디벨롭한다. 데이터·근거 없이 단정하지 않고 조사 → 가설 → 검증 → 실행 순서를 지킨다.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - WebSearch
  - WebFetch
  - AskUserQuestion
  - Skill
---

# /skmarket — SimonKMarket 오케스트레이터

마케팅·시장조사·여론 작업의 진입점. **추측으로 단정하지 않는다.** 조사로 근거를 만들고, 가설을 세우고, 산출물마다 사용자와 디벨롭한다.

## 0. SimonKCore 감지 (graceful degrade)
- `agent-delegate`, `model-router`, `simon-research`, `perspectives`, `human-voice-guard`, `office-hours`, `plan-ceo-review` 설치 확인.
- 있으면: 시장조사는 `simon-research`, 다관점 분석은 `perspectives`, 카피 휴먼화는 `human-voice-guard`, 전략 리뷰는 `plan-ceo-review`에 위임.
- 없으면: "SimonKCore 미설치 — 조사/다관점/카피 휴먼화 기능 제한. `/plugin install simonk-core@simonk-core` 권장." 안내 후 계속.

## 1. 의도 진단 (러프 + 쉬운말 + 예산·단계)
대화로 **테크/사업 단계/예산 수준을 빠르게 감지**하고 맞춰 질문한다.
`AskUserQuestion` **1회**, 각 선택지에 **일상어 별칭**:
- 시장·경쟁 조사 — "이거 팔릴까? 경쟁사 보기"
- 포지셔닝·PMF — "내 제품이 시장에 맞나"
- 그로스·퍼널 — "사용자 늘리기"
- 수익화·가격 — "돈 버는 방법·가격 정하기"
- 광고·획득 — "광고로 손님 모으기"
- 바이럴·런칭 — "입소문·출시"
- 해외 판로·수출 — "해외에 팔기"
- 여론·평판 — "반응·평판 분석"
- Exit·투자 — "투자유치·매각"
- (선택) **단계** 아이디어 / 출시 전 / 출시 후 / 스케일 · **예산** 무료위주 / 소액 / 충분

**심플 모드 + 예산 게이트**: 저자산·저테크면 무료·저비용·노코드 위주로, 유료 PG/광고로 함부로 보내지 않는다.
갈피 못 잡음 → 시장조사부터 근거 만든 뒤 방향 제안.

## 2. 라우팅 (의도 → 파이프라인)
**복합 목표**(퍼널+광고+분석 = GTM)는 단일 선택으로 자르지 말고 순차 실행(GTM 번들: `aarrr-growth-planner`→유료광고→`analytics-integrator`).

| 의도 | 파이프라인 / 처리 |
|---|---|
| 시장·경쟁 조사 | `simon-research`(Core) → `perspectives`(Core) → `pmf-analyzer` |
| 아이디어 검증(출시 전) | `idea-validation`(Mom Test 인터뷰·수요테스트·경쟁맵·러프 TAM). ※ `pmf-analyzer`는 출시 후 |
| 포지셔닝·PMF | `pmf-analyzer` → `aha-moment-optimizer` |
| 그로스·퍼널 | `aarrr-growth-planner` → `growth-engine` → `aha-moment-optimizer` |
| 수익화(코드 있음) | `monetization-planner` → `subscription-manager-selector` → `payment-integrator` → `revenue-scenario-tester` |
| 수익화(노코드/무앱) | `nocode-monetization`(운영 플랫폼 매칭·가격·LTV 냅킨) ← `monetization-planner` 전략과 보완 |
| 유료광고 캠페인 | `paid-ads-campaign`(Meta·Google·네이버 GFA·카카오모먼트 집행·UTM·전환추적). ⚠️ `ad-monetization`은 **퍼블리셔 광고 게재(SDK)** 라 다름 — 혼동 금지 |
| 광고 분석·전환추적 | `tag-manager-integrator` → `analytics-integrator` |
| 바이럴·런칭 | `viral-launch` → `store-launcher` |
| 커뮤니티 마케팅(국가별) | `community-marketing` — 커뮤니티별 톤 각색·게시계획·추적·알림. ⚠️ 정직·공시·휴먼승인(가짜리뷰/여론조작 아님) |
| 리텐션 진단 | `cohort-retention-analyzer`(코호트 커브·드롭오프·이탈 선행지표·ICE 우선순위) |
| 이탈·매출 누수 방어 | `churn-recovery-planner`(dunning·save-offer·윈백·회복 KPI) |
| 피드백·평점 수집 | `feedback-and-review-collector`(NPS·인앱설문·스토어 리뷰 게이팅) |
| 랜딩페이지 | `design-consultation`(SimonKDesign 핸드오프) — LP 방향·카피 |
| B2C·구독 결제(PG/VAT/MoR) | `global-payment-planner`(소비자 PG·부가세). 세무는 여기지 `pink-tax-advisor`(가격심리) 아님 |
| B2B 무역 결제·수출세무 | `export-channel`(T/T·L/C·D/P, 영세율·관세환급·FTA, 관세사·KOTRA 핸드오프) |
| 해외 판로·수출 | `export-channel`(KOTRA·바이어발굴·Incoterms 2020·결제조건·수출서류·정부지원) + `simon-research` 시장조사 |
| Exit·투자 | `exit-strategy-planner` |
| 카피 휴먼화 | `human-voice-guard`(Core) |

하위 스킬은 `Skill`로 호출. (수익화/분석 통합군은 SimonKStack과 공유 — 자급자족.) **라벨과 실제 산출이 다르면 안 됨** — ⚠️ 항목 오라우팅 금지.

## 3. 반복 디벨롭 (핵심)
단계마다 산출물 → 사용자 확인 → 반영 → 다음.
- 조사 결과는 **출처/근거**와 함께(WebSearch/WebFetch). 추정은 추정이라고 표시.
- 가설은 ICE/RICE로 우선순위화하고 실험으로 검증 가능하게 제시.
- 수치는 시나리오(보수/기본/공격)로.

## 4. 무결성 원칙
- 데이터 없이 단정 금지. "근거 → 가설 → 실험 → 결론" 체인 유지.
- 과장·기만 카피 금지(`human-voice-guard` 적용). 규제(개인정보·광고심의) 플래그.

## 5. 페르소나 인지 + 전파 (필수)
사업자/마케터(전문)=프레임워크·지표 위주, 일반 사용자=용어 풀어서·예시 중심. 자산·예산 수준에 맞춰 채널·전술 스케일 조정.
**전파**: §1에서 감지한 저테크/고령 신호를 **하위 산출물까지** 전달 — ICE/RICE·AARRR·ROAS/CAC·MoR·Incoterms·HS코드 같은 전문어는 첫 등장 1줄 풀이 + 쉬운말 병기, 큰글씨, TL;DR 3줄+다음 행동 1개. 저테크 검증 루프는 "예/아니오" 단순 확인 + 필요 시 외부 상담(KOTRA·관세사) 연계로 스위치.

## 완료 기준
**출시 전 게이트**: `persona-validate`(SimonKCore)로 마케팅 전문가(CMO·그로스·퍼포먼스·법규)+대상 사용자 패널 검증 → 치명 리스크(과장·규제) 반영. (Core 미설치 시 인라인 self-check — 과장·규제 체크+근거 검토+전문가 렌즈 1개로 대체, degrade 일관.)
의도한 목표에 대해 근거 있는 산출물이 나오고 사용자가 확인했을 때 완료. 미진하면 3번 루프로.
**완료 후**: `completion-report`(Core)로 HTML 보고서 생성 — 사용자 언어 + 현지시간 로케일 형식(KR: `[YYYY-MM-DD / HH:MM:SS KST]`) + 표·차트(퍼널·지표).

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
