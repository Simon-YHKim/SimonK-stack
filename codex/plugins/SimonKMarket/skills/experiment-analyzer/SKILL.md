---
name: experiment-analyzer
description: "Use when the user wants to plan or judge an experiment / A/B test—triggers \"A/B 분석\", \"유의성\", \"실험 판정\", \"샘플 크기\", \"검정력\", \"MDE 계산\", \"실험 결과 봐줘\", \"ship 해도 돼\", \"analyze experiment\", \"is this significant\", \"sample size\", \"power calculation\". Produces pre-experiment design (sample size / MDE / power), post-experiment readout (significance, confidence interval, segment split, peeking warnings), and a ship/kill/iterate verdict. Eats PostHog / GrowthBook results. Includes Python scripts for power and significance calculation. Flags common traps: underpowered samples, multiple comparisons, peeking."
allowed-tools: Read, Write, Bash, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# experiment-analyzer

실험을 **설계**(사전)하고 **판정**(사후)하는 skill. 직관·눈대중이 아니라 측정값으로 ship/kill 을 결정한다.

## 발동 조건

- 사전: "샘플 크기 얼마나 필요해?", "이 실험 검정력 충분해?", "MDE 계산해줘"
- 사후: "A/B 결과 봐줘", "이거 유의해?", "ship 해도 돼?", "신뢰구간 알려줘"
- PostHog / GrowthBook / Optimizely 결과를 붙여넣고 판정 요청할 때
- growth-engine 의 실험 백로그를 실제로 돌린 뒤 결과 해석 단계

## 두 모드: 사전 vs 사후

먼저 사용자가 어느 단계인지 확인한다. 불명확하면 `AskUserQuestion` 으로 묻는다.

| 모드 | 입력 | 출력 |
|---|---|---|
| **사전 (설계)** | baseline 전환율, 목표 lift(MDE), 일일 트래픽 | 변형당 표본·소요일·검정력 |
| **사후 (판정)** | 변형별 n / 전환수 (또는 평균·분산) | p-value, 신뢰구간, lift, ship/kill |

---

## 모드 A: 사전 설계

목표 — 실험 시작 전에 "이 실험이 의미 있는 결과를 낼 수 있는가"를 확정한다. 표본이 부족하면 결과가 나와도 못 믿는다.

### 입력 4종

| 항목 | 의미 | 기본값 |
|---|---|---|
| Baseline conversion | 현재 전환율 (Control 예상치) | 측정값 필수 |
| MDE | 탐지하고 싶은 최소 lift (상대 %) | 사용자 지정 |
| α (유의수준) | 위양성 허용 | 0.05 |
| Power (1−β) | 위음성 회피 | 0.80 |

> MDE 를 작게 잡을수록 필요한 표본은 제곱으로 늘어난다. "1% 개선을 잡겠다"는 보통 수십만 표본을 요구한다. 현실적 MDE 부터 합의한다.

### 계산

```bash
python scripts/power.py \
  --baseline 0.10 \
  --mde 0.10 \
  --alpha 0.05 \
  --power 0.80 \
  --daily-traffic 2000 \
  --variants 2
```

출력: 변형당 필요 표본, 총 표본, 예상 소요일. 소요일이 2주를 크게 넘으면 MDE 를 키우거나 트래픽을 늘리는 협의로 되돌린다.

### 사전 게이트 (하나라도 막히면 실험 보류)

- [ ] 변형당 표본이 실제 트래픽으로 28일 이내 도달 가능한가
- [ ] 1차 지표(primary metric)가 **하나**로 고정됐는가
- [ ] 중단 규칙(stopping rule) = 사전 정한 표본 도달 시점만. peeking 금지 합의
- [ ] 분석 단위 = 유저 단위(세션 아님), 무작위 배정 확인

---

## 모드 B: 사후 판정

### 입력 정규화 (PostHog / GrowthBook → 표준 형태)

도구별 표현이 달라도 아래 형태로 환원한다.

```
이진 지표 (전환):   variant, n(노출), converted(전환수)
연속 지표 (값):      variant, n, mean, std
```

PostHog 결과 캡처/JSON, GrowthBook readout 을 붙여넣으면 위 표로 추출한다. 노출(n)과 전환(converted)이 안 보이면 사용자에게 그 두 숫자를 직접 요청한다 — 비율(%)만으로는 검정 불가.

### 계산

```bash
# 이진 지표 (2비율 검정 + Wilson 신뢰구간)
python scripts/significance.py binary \
  --control 5000 520 \
  --variant 5000 590

# 연속 지표 (Welch t-검정)
python scripts/significance.py continuous \
  --control 4800 12.4 8.1 \
  --variant 4750 13.9 8.6
```

출력: 절대/상대 lift, p-value, lift 의 95% 신뢰구간, 유의 여부, 그리고 표본이 사전 설계 표본에 못 미치면 underpowered 경고.

### 판정 규칙

| 조건 | 판정 |
|---|---|
| p < α **그리고** CI 하한 > 0 **그리고** 표본 충족 | **SHIP** |
| p < α 이지만 lift 가 실무상 무의미(< 손익분기 MDE) | **NO-SHIP** (통계적 유의 ≠ 사업적 유의) |
| p ≥ α, CI 가 0 포함 | **KILL 또는 ITERATE** (효과 없음/불확실) |
| 표본 미달 | **계속 수집** (지금 판정 금지) |

> guardrail metric (이탈·환불·지연 등)이 악화되면 1차 지표가 이겨도 ship 하지 않는다. 반드시 함께 본다.

---

## 흔한 함정 (자동 경고)

| 함정 | 증상 | 대응 |
|---|---|---|
| **표본 부족** (underpowered) | n 이 설계치 미만인데 결론 냄 | "수집 계속". 작은 표본의 큰 lift 는 대개 noise |
| **Peeking** | 매일 들여다보며 유의 뜨자마자 중단 | α 부풀려짐. 사전 표본 도달까지 판정 보류. 순차검정 쓸 거면 사전 선언 |
| **다중비교** | 변형·세그먼트·지표 여러 개 동시 검정 | 비교 수만큼 위양성↑. Bonferroni(α/k) 또는 1차 지표 1개로 제한 |
| **세그먼트 낚시** | 전체는 무효인데 "여성 25-34만 유의" | 사후 세그먼트는 가설이지 결론 아님. 후속 실험으로 검증 |
| **SRM** (표본비 불일치) | 50/50 배정인데 n 이 5000 vs 4400 | 배정·로깅 버그 의심. χ² 로 점검, 깨졌으면 결과 폐기 |
| **신규성 효과** | 초반 급등 후 수렴 | 최소 1주(가능하면 2주) 돌려 요일효과·신규성 흡수 |

세그먼트 분석은 항상 "탐색(exploratory)"으로 라벨링하고, 1차 판정은 전체(pooled) 결과로만 한다.

---

## Workflow

1. 모드 확인 (사전/사후). 불명확하면 `AskUserQuestion`.
2. 입력 수집·정규화 (PostHog/GrowthBook → 표준 표).
3. 해당 `scripts/*.py` 실행 (외부 의존성 없음, 표준 라이브러리만).
4. 함정 체크리스트 대조 → 경고 부착.
5. `templates/experiment-readout.md` 로 결과 문서 생성.
6. 사후라면 ship/kill/iterate 판정 + 근거(숫자) 명시.

---

## 산출물

`docs/experiments/<exp-id>-readout.md` — `templates/experiment-readout.md` 기반:
- 가설 / 1차 지표 / guardrail
- 설계 표본 vs 실제 표본
- lift, p-value, 신뢰구간
- 함정 점검 결과
- 판정 (SHIP / NO-SHIP / KILL / ITERATE) + 다음 행동

## 정직성 원칙

- 시그널 없이 단정하지 않는다. p-value·CI·표본 수를 항상 명시.
- "통계적 유의"와 "사업적 유의"를 분리해서 보고한다.
- 표본이 부족하면 그냥 "아직 모른다"고 말한다 — 억지 결론 금지.

## Related Skills

- `growth-engine` — 실험 백로그 생성·우선순위(ICE), 실험 인프라
- `analytics-integrator` — 이벤트·전환 추적, PostHog/GrowthBook 세팅
- `paywall-designer` — 가격·페이월 실험의 변형 설계

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
