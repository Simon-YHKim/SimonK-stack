---
name: paywall-designer
description: "Use when the user wants to design or optimize a paywall, upgrade prompt, or conversion moment—triggers \"페이월 설계\", \"업그레이드 유도\", \"결제 전환 올리기\", \"가격 실험\", \"트라이얼 붙여줘\", \"design a paywall\", \"upgrade prompt\", \"improve conversion\", \"price experiment\". Produces paywall trigger rules + timing, value-framing copy, soft/hard wall choice, trial·anchoring·decoy price layout, conversion measurement hooks, and a price-point A/B + WTP research plan. Fills the gap between monetization-planner (what to charge) and payment-integrator (how to charge)."
allowed-tools: Read, Write, Edit, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# paywall-designer

무료 유저가 "결제하겠다"고 결심하는 그 순간(페이월·업그레이드 프롬프트)을 설계·최적화하는 skill.

**경계**: `monetization-planner`(무엇을 얼마에 팔지) → **paywall-designer**(언제·어떻게 결제를 유도할지) → `payment-integrator`(실제 결제 구현). 가운데를 메운다. 모델/티어가 아직 없으면 먼저 `monetization-planner`로 돌아간다.

## 발동 조건

- "페이월 만들어줘", "업그레이드 유도 화면", "결제 전환 올리고 싶어"
- "트라이얼 붙이자", "가격 실험하자", "디코이 가격", "앵커링"
- `monetization-planner` 실행 후 티어·가격이 정해졌을 때 체인

## 시작 전 입력 확인

`AskUserQuestion`으로 빠르게 확정(이미 `MONETIZATION.md`가 있으면 Read 후 생략):

- **티어·가격**: Free/Pro 가격점이 정해졌나? (없으면 monetization-planner 선행)
- **플랫폼**: 모바일 앱(IAP) / 웹 / 둘 다? — 스토어 정책·복귀 동선이 달라짐
- **핵심 가치 순간(aha)**: 유저가 "이거 좋다"를 처음 느끼는 행동은? (페이월 타이밍의 기준점)
- **현재 측정 수단**: analytics 이벤트가 이미 깔려 있나? (없으면 5단계에서 최소 셋업)

## Workflow

### 1. 트리거 규칙 · 타이밍

페이월은 "보여주는 시점"이 카피보다 전환에 더 크게 작용한다. 가치를 느낀 직후에 띄운다.

| 트리거 유형 | 발동 시점 | 적합한 경우 |
|---|---|---|
| Aha-gated | 핵심 가치를 1회 경험한 직후 | 가치 체감이 빠른 도구·생성형 |
| Limit-reached | 무료 한도(횟수/용량/일수) 소진 시 | 반복 사용·누적형 |
| Feature-gated | 유료 전용 기능 탭 시 | 기능 차별이 뚜렷할 때 |
| Time-based | 가입 N일차 / 트라이얼 종료 임박 | 습관 형성 후 전환 |
| Contextual peak | 막 성과를 낸 직후(저장·완성·공유) | 만족도 최고점 활용 |

원칙:
- **첫 세션 즉시 하드월 금지** — 가치 체감 전 결제 요구는 이탈만 키운다(측정으로 확인).
- 한 세션에 페이월 1회. 반복 노출은 빈도 상한(예: 세션당 1, 일 N회)으로 제한.
- 닫기(X)는 항상 즉시 가능 — 강제 닫힘 차단은 스토어 리젝·신뢰 손상 위험.

### 2. 가치 프레이밍 카피

기능이 아니라 **유저가 얻는 결과**를 말한다. 기능 나열 → 결과 번역.

| 약한 카피(기능) | 강한 카피(결과) |
|---|---|
| "무제한 저장" | "다시는 지울지 고민하지 않기" |
| "고급 분석" | "어디에 시간을 쓰는지 한눈에" |
| "광고 제거" | "방해 없이 끝까지 집중" |

체크:
- Headline = 1개 결과(One message 규칙). 서브카피 1줄로 근거.
- 손실 회피(잃을 것) > 이득(얻을 것)이 보통 더 강함 — 단, 과장·공포 마케팅 금지, 측정으로 검증.
- 임상·치료 어휘 금지(프로젝트 lexicon 준수). 신뢰 훼손 카피("지금 안 하면 손해") 지양.
- 사회적 증거는 **검증 가능한 수치만**(consent 받은 후기·실제 사용자 수). 허위 카운트다운 금지.

### 3. Soft wall vs Hard wall

| 구분 | Soft wall | Hard wall |
|---|---|---|
| 동작 | 닫고 계속 사용 가능 | 결제/로그인 전 차단 |
| 전환 | 낮음 | 높음(단 이탈도 높음) |
| 적합 | 초기·획득 단계, 가치 미체감 | 가치 명확·한도 소진·핵심 기능 |
| 리스크 | 무료로 충분히 새면 전환 0 | 너무 이르면 이탈·악평 |

전략: **점진적 경화**. 초반 soft → 한도 도달/aha 이후 hard. 동일 유저에게 단계적으로 강도를 올린다. 어느 시점이 최적인지는 코호트별 전환·이탈로 측정.

### 4. 트라이얼 · 앵커링 · 디코이 가격 배치

**트라이얼**
- 카드 선등록 vs 미등록: 등록형은 전환율↑·환불 클레임↑, 미등록형은 가입↑·전환율↓. 둘 다 측정 후 선택.
- 트라이얼 종료 사전 고지 필수(앱 스토어 정책·한국 자동갱신 고지). 종료 1~2일 전 알림.
- "리버스 트라이얼": 온보딩 동안 Pro 기능을 잠깐 열어 체험시키고, 이후 Free로 강등하며 업그레이드 제시.

**앵커링 · 디코이(가격 표시 순서)**
- 비싼 플랜을 **먼저/위에** 배치해 기준점(anchor)을 높인다.
- 연간 플랜을 기본 선택으로, 월 환산가를 병기("₩9,900/월, 연 결제 시 ₩7,900/월").
- 디코이: 월간을 일부러 비싸게 두어 연간이 "합리적"으로 보이게(3-옵션 비대칭 우위). 단 기만적 가격 금지 — 실제 청구 금액·주기 명확 표기.
- 가격 끝수: monetization-planner의 ₩9,900/₩29,000 심리가 그대로 적용.

**레이아웃 권장(모바일 1화면)**
- 상단: 가치 결과 1줄(헤드라인). 중앙: 플랜 카드(연간 강조·배지). 하단: 단일 CTA + 작은 "나중에".
- One message + one graphic 규칙: 비교표는 펼치기(progressive disclosure)로 숨긴다.

### 5. 전환 측정 훅

추측 금지 — 모든 페이월은 측정 가능해야 한다. `analytics-integrator`로 셋업된 이벤트 분류에 아래를 추가한다.

| 이벤트 | 시점 | 주요 속성 |
|---|---|---|
| `paywall_trigger` | 트리거 조건 충족 | `trigger_type`, `surface`, `tier_context` |
| `paywall_view` | 페이월 노출 | `variant`, `plan_default`, `entry_point` |
| `paywall_plan_select` | 플랜 탭 | `plan_id`, `billing_period` |
| `paywall_cta_tap` | 결제 버튼 탭 | `plan_id`, `variant` |
| `paywall_dismiss` | 닫기 | `dwell_ms`, `reason?` |
| `purchase_success` | 결제 완료 | `plan_id`, `amount`, `trial` (payment-integrator 발생) |

핵심 지표:
- **View→Purchase 전환율**(페이월 노출 대비 결제), trigger_type별·variant별 분해.
- **Trigger→View** 노출률(트리거됐는데 안 보인 누수).
- Dwell time, dismiss 사유, 트라이얼 시작→전환율, 환불율.
- 시크릿 하드코딩 금지 — analytics 키는 env. PII는 이벤트 속성에 넣지 않는다(동의·법규).

### 6. 가격점 A/B · WTP 리서치

**A/B 설계**(실행·해석은 `aha-moment-optimizer`/`revenue-scenario-tester`와 연계)
- 한 번에 한 변수만(가격점 / 카피 / 트리거 타이밍 / 트라이얼 길이 중 하나).
- **북극성 = 유저당 매출(ARPU) 또는 전환율 × 가격**, 단순 전환율 아님(가격 내리면 전환↑이지만 매출↓일 수 있음).
- 충분 표본·기간 확보 전 조기 종료 금지. 가격 실험은 신규 유저 코호트에만(기존 유저 가격 변경은 신뢰·법적 이슈).
- 신규 유저에게만 노출되도록 코호트 분리, 동일 유저는 같은 variant 고정(sticky).

**WTP(지불의사) 리서치**
- Van Westendorp PSM 4문항: 너무 비쌈 / 비싸지만 고려 / 싸다 / 너무 싸서 의심.
- Gabor-Granger: 가격점별 구매 의향으로 수요곡선·최적가 추정.
- 정성 보강: 이탈 유저 인터뷰 "얼마면 결제했나". 가설은 반드시 실측 A/B로 확인.

## 산출물

대화로 설계를 확정한 뒤, 사용자가 원하면 아래를 생성:

- `PAYWALL.md` — 트리거 규칙·카피·wall 유형·가격 레이아웃·측정 이벤트·A/B 백로그. `templates/PAYWALL.template.md` 사용.
- 페이월 카피 변형 세트 — `templates/paywall-copy-variants.md`.
- 측정 이벤트 명세 — `scripts/gen-paywall-events.mjs`로 이벤트 스키마(JSON) 생성, analytics-integrator에 전달.

## 검증 체크리스트

- [ ] 트리거가 aha 또는 한도 도달 직후(첫 세션 즉시 하드월 아님)
- [ ] 닫기(X) 항상 가능, 페이월 노출 빈도 상한 설정
- [ ] 카피가 기능이 아닌 결과 중심, 1 헤드라인 = 1 메시지
- [ ] 기만적 카운트다운·허위 사회적 증거·공포 마케팅 없음
- [ ] 트라이얼·자동갱신 사전 고지(스토어 정책 + 한국 법규)
- [ ] 디코이/앵커링이 실제 청구액·주기를 왜곡하지 않음
- [ ] 전 단계 측정 이벤트 정의(추측 아닌 데이터로 검증 가능)
- [ ] A/B 북극성이 매출/ARPU(전환율 단독 아님), 한 번에 한 변수
- [ ] 가격 실험은 신규 코호트만, 시크릿은 env

## Related Skills

- `monetization-planner` — 모델·티어·가격점 선행 결정(상류 경계)
- `payment-integrator` — 확정된 페이월의 결제·트라이얼·구독 구현(하류 경계)
- `aha-moment-optimizer` — 트리거 타이밍의 기준점(aha)·A/B 실험 프레임
- `analytics-integrator` — 측정 이벤트·퍼널 셋업
- `revenue-scenario-tester` — 트라이얼/전환/환불 시나리오 통합 검증
- `aarrr-growth-planner` — Revenue 단계 전체 맥락
- `paid-ads-campaign` — 유입 광고와 페이월 메시지 일관성(랜딩→페이월 약속 일치)

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
