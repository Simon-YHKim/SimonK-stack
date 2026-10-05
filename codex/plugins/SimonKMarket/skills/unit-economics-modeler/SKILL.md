---
name: unit-economics-modeler
description: "Use when the user wants to model unit economics, check whether a business pays back per-customer, or pressure-test LTV against CAC—triggers \"단위경제\", \"단위 경제성\", \"LTV CAC\", \"LTV:CAC\", \"페이백\", \"payback 기간\", \"채산성\", \"고객 한 명당 얼마 남아\", \"이 가격이면 남는 장사야\", \"unit economics\", \"contribution margin\", \"is this sustainable\". Produces a UNIT_ECONOMICS.md: cohort LTV (survival curve + expansion revenue) → blended/paid CAC → payback months → LTV:CAC ratio → contribution margin → conservative/base/aggressive sensitivity. Includes napkin calculators (Python + mjs). Enforces the LTV>CAC and payback<12mo guardrails."
allowed-tools: Read, Write, Bash, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# unit-economics-modeler

고객 한 명을 데려와 유지하는 데 드는 돈보다, 그 한 명에게서 버는 돈이 더 큰가.
이 질문에 숫자로 답하는 skill. PMF 후 "이거 남는 장사인가"를 판정한다.

> 단위경제성(unit economics)은 성장 이전의 전제다. LTV < CAC인 채로 성장하면
> 빨리 성장할수록 빨리 망한다. 가속 페달 밟기 전에 이 숫자부터 본다.

## 발동 조건

- "단위경제 따져줘", "LTV CAC 계산", "페이백 얼마야", "이 가격이면 채산성 나와?"
- "고객 한 명당 얼마 남아", "이거 남는 장사야?", "unit economics", "contribution margin"
- `monetization-planner`로 가격/tier를 정한 직후 자동 체인 (가격이 채산성을 만드는지 검증)
- `revenue-scenario-tester` 전 단계 — 시나리오 테스트 전에 모델이 성립하는지 확인

## 핵심 원리: 측정 가능한 것만 모델링한다

추정치는 반드시 **출처**(애널리틱스/결제 데이터/벤치마크)를 명시한다. 근거 없는
낙관은 모델을 거짓말로 만든다. 데이터가 없으면 "가정(assumption)"으로 라벨링하고
보수 시나리오에서 더 박하게 잡는다.

| 입력값 | 1차 출처 | 없을 때 대체 |
|---|---|---|
| 월 이탈률(churn) | 결제/구독 DB 코호트 | 카테고리 벤치마크 + assumption 라벨 |
| ARPU / 객단가 | revenue_events 집계 | 가격표 × 추정 결제율 |
| 확장매출(expansion) | 업그레이드/추가구매 로그 | 0으로 두고 base에서 제외 |
| CAC | 광고비 ÷ 신규고객 (채널별) | 채널 CPC × 전환율 역산 |
| 변동비(COGS) | 결제수수료 + 서버 + 지원 | 매출 대비 % 가정 |

## Workflow

### 0. 입력 수집 (AskUserQuestion)

데이터가 없으면 다음을 질문한다. 하나라도 추정이면 그 항목에 `(assumption)` 표기.

- 비즈니스 모델: 구독 / 종량제 / 단건반복 / 하이브리드?
- 결제 주기: 월 / 연 / 사용량?
- ARPU(고객 1인 월평균 매출)와 출처
- 월 이탈률(또는 연 유지율)과 출처
- 확장매출 비율(기존 고객의 월 매출 증가율, net revenue retention 단서)
- 변동비 구조: 결제수수료 %, 인당 서버/지원비
- CAC: 채널별 광고비 + 신규고객 수 (블렌디드와 페이드 구분)

### 1. 코호트 LTV (생존곡선 + 확장매출)

단순 `ARPU / churn`은 출발점일 뿐이다. 두 가지를 보정한다.

**(a) 생존곡선(survival curve)** — 이탈은 초기에 몰린다. 평탄한 상수 churn 가정은
LTV를 과대평가한다. 코호트별 잔존율 `S(t)`를 쓰거나, 데이터가 없으면 초기 가중
churn(첫 1~3개월 높음)을 적용한다.

**(b) 확장매출(expansion)** — 남은 고객의 객단가가 오르면 LTV가 커진다.
월 확장률 `g`를 잔존 매출에 곱한다 (net dollar retention > 100%이면 LTV가 크게 상승).

```
공식 (월 단위, 마진 반영):
  LTV = Σ_{t=0}^{N}  S(t) · ARPU · (1+g)^t · GM
        S(t) = 잔존율 (생존곡선),  S(0)=1
        g    = 월 확장률 (없으면 0)
        GM   = 매출총이익률 (gross margin, 변동비 제외 후)
        N    = 지평선 (보통 24~36개월; 무한대 금지 — 과대추정 위험)

상수 churn 근사(빠른 추정):
  LTV ≈ (ARPU · GM) / (churn − g)      단, churn > g 필수 (아니면 발산)
```

지평선 `N`을 유한하게 끊는다. 무한 합은 먼 미래 매출을 현재 가치로 과신한다.
정밀 모델은 월 할인율 `r`로 할인: `S(t)·ARPU·(1+g)^t·GM / (1+r)^t`.

### 2. CAC — 블렌디드 vs 페이드

두 숫자는 다르고, 둘 다 봐야 한다.

| 지표 | 정의 | 용도 |
|---|---|---|
| Blended CAC | 전체 마케팅비 ÷ 전체 신규고객 (오가닉 포함) | 회사 전체 효율 |
| Paid CAC | 유료채널 광고비 ÷ 그 채널 신규고객 | 광고 증액 의사결정 |
| Fully-loaded CAC | + 마케팅 인건비·툴비 | 투자자용 진짜 비용 |

```
Blended CAC = 총 S&M 비용 / 신규 고객 수(전체)
Paid CAC    = 채널 광고비 / 채널 귀속 신규 고객 수
```

광고 증액 판단은 **Paid CAC**로, 사업 지속성 판단은 **Blended/Fully-loaded CAC**로.
오가닉이 큰데 Blended만 보면 광고 효율을 착각한다.

### 3. Payback 기간

CAC를 회수하는 데 걸리는 개월 수. 현금흐름의 핵심.

```
Payback(개월) = CAC / (ARPU · GM)        (월 기여이익 기준)
```

확장·이탈을 반영한 정밀 버전은 누적 기여이익이 CAC를 넘는 첫 월을 찾는다
(scripts가 자동 계산). LTV가 좋아도 payback이 길면 현금이 먼저 마른다.

### 4. LTV:CAC 비율

```
LTV:CAC = LTV / CAC
```

| 비율 | 해석 |
|---|---|
| < 1 | 적자 구조. 팔수록 손해. 즉시 중단·재설계 |
| 1~3 | 빠듯함. 마진/이탈 개선 없이 성장하면 위험 |
| ~3 | 통상 건강 기준선 (벤치마크, 절대 법칙 아님) |
| > 5 | 과소투자 신호일 수 있음 — 더 공격적으로 획득 가능 |

3은 업계 통념이지 보편 상수가 아니다. 자본비용·성장단계로 맥락화한다.

### 5. 기여이익 (Contribution Margin)

매출에서 변동비만 뺀, 고객 1명이 회사에 기여하는 돈. 고정비(임대료·기본급)는
제외 — 단위경제성은 "한 명 더"의 한계 채산성을 본다.

```
단위 기여이익 = ARPU − 변동비(결제수수료 + 인당 서버 + 인당 지원 + COGS)
기여 마진율   = 단위 기여이익 / ARPU
```

기여 마진율이 곧 위 공식의 `GM`. 이게 낮으면 LTV 공식 전체가 흔들린다.

### 6. 시나리오 민감도 (보수 / 기본 / 공격)

단일 숫자는 위험하다. 핵심 가정 3개(churn, ARPU/확장, CAC)를 흔든다.

| 가정 | 보수(Conservative) | 기본(Base) | 공격(Aggressive) |
|---|---|---|---|
| 월 churn | base ×1.5 | 측정값 | base ×0.7 |
| 확장률 g | 0 | 측정값 | base ×1.5 |
| CAC | base ×1.3 | 측정값 | base ×0.8 |
| 마진 GM | base −10%p | 측정값 | base 유지 |

세 시나리오 모두에서 LTV:CAC와 payback을 출력. **보수 시나리오에서도 가드레일을
통과**해야 진짜 건강한 모델이다.

## 가드레일 (둘 다 충족해야 통과)

| 가드레일 | 기준 | 미달 시 |
|---|---|---|
| LTV > CAC | LTV:CAC ≥ 1 (목표 ≥ 3) | 가격↑ / 이탈↓ / CAC↓ 중 무엇을 바꿀지 제시 |
| Payback < 12개월 | 누적 기여이익이 12개월 내 CAC 회수 | 현금 소진 경고, 연간결제 선결제 유도 검토 |

가드레일은 **보수 시나리오 기준**으로 판정한다. base만 통과하면 "취약" 판정.

## scripts — napkin 계산기

데이터 없이도 즉시 돌려보는 봉투 뒷면 계산기. 정밀 회계가 아니라 의사결정용 러프 추정.

```bash
# Python (둘 중 편한 것)
python scripts/unit_economics_napkin.py \
  --arpu 9900 --churn 0.08 --expansion 0.01 \
  --cac 18000 --var-cost-rate 0.20 --horizon 36 --discount 0.0

# Node (의존성 0, ESM)
node scripts/unit_economics_napkin.mjs \
  --arpu 9900 --churn 0.08 --expansion 0.01 \
  --cac 18000 --var-cost-rate 0.20 --horizon 36
```

두 스크립트는 동일 로직 — 코호트 LTV(할인 옵션), payback(누적 기여이익이 CAC를
넘는 첫 월), LTV:CAC, 그리고 보수/기본/공격 3시나리오 표를 출력하고 가드레일을 판정한다.
`--help`로 인자 확인.

## 산출물

`templates/UNIT_ECONOMICS.template.md`를 채워 프로젝트 루트(또는 docs/)에
`UNIT_ECONOMICS.md` 생성:

1. 입력 가정표 (값 + 출처 + assumption 라벨)
2. 단위 기여이익 / 마진율
3. 코호트 LTV (생존곡선 + 확장 반영, 지평선 명시)
4. Blended / Paid / Fully-loaded CAC
5. Payback 개월
6. LTV:CAC
7. 보수/기본/공격 민감도 표
8. 가드레일 판정 (PASS/취약/FAIL) + 개선 레버

## 검증 체크리스트

- [ ] 모든 입력값에 출처 또는 `(assumption)` 라벨이 있다
- [ ] LTV 지평선이 유한하다 (무한 합 금지)
- [ ] churn > expansion (상수 근사 시 발산 방지)
- [ ] CAC를 blended/paid로 분리했다
- [ ] GM(기여 마진율)이 LTV 공식에 반영됐다 (매출이 아닌 마진 기준 LTV)
- [ ] 보수 시나리오에서도 LTV:CAC ≥ 1, payback < 12mo
- [ ] 단일 숫자가 아닌 3시나리오 범위로 제시했다

## Related Skills

- `monetization-planner` — 가격/tier 설계 (이 skill이 그 가격의 채산성을 검증)
- `paid-ads-campaign` — Paid CAC의 입력(채널 CPC/전환율)을 만드는 쪽
- `revenue-scenario-tester` — 모델 성립 확인 후 과금 흐름을 통합 테스트
- `aarrr-growth-planner` — Revenue 단계 KPI(LTV/CAC/payback)와 연결
- `pmf-analyzer` — PMF 확인 후 이 skill로 채산성 판정 (순서: PMF → 단위경제 → 성장)

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
