---
name: cohort-retention-analyzer
description: "Use when the user wants to diagnose retention / cohorts / churn—triggers \"리텐션 분석\", \"코호트\", \"이탈 지점\", \"리텐션 커브\", \"왜 빠져나가지\", \"가입 코호트\", \"행동 코호트\", \"RFM 세그먼트\", \"retention curve\", \"cohort analysis\", \"churn drivers\", \"where do users drop\". Produces signup/behavioral cohort retention curves (n-day vs unbounded vs bracket), funnel drop-off, RFM segments, and leading churn indicators from PostHog or SQL. Includes a SQL cohort-aggregation template and a stdlib-only Python calculator (no deps). Outputs the next experiments prioritized by ICE. Distinguishes vanity retention (cumulative) from true retention, and flags survivorship bias."
allowed-tools: Read, Write, Bash, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# cohort-retention-analyzer

리텐션을 **진단**하는 skill. "유저가 빠져나간다"는 막연한 느낌을, 어느 코호트가 / 며칠째에 / 어떤 행동을 안 해서 빠지는지 숫자로 분해한다. 가입·행동 코호트 리텐션 커브, 퍼널 드롭오프, RFM 세그먼트, 이탈 선행지표를 산출하고, 다음 실험을 ICE 로 우선순위화한다.

이 skill 은 **측정·진단 전용**이다. 캠페인 설계는 `lifecycle-campaign-designer`, 실험 판정은 `experiment-analyzer` 로 넘긴다.

## 발동 조건

- "리텐션이 떨어진다", "유저가 어디서 빠지지?", "이탈 지점 찾아줘"
- "코호트별로 비교해줘", "6월 가입자가 더 잘 남나?"
- "RFM 세그먼트 나눠줘", "충성 유저 vs 휴면 유저 구분"
- PostHog Retention/Funnel 화면, 또는 events 테이블 SQL 결과를 붙여넣고 해석 요청할 때
- `pmf-analyzer` 가 PMF 신호로 리텐션을 보라고 했을 때의 실제 측정 단계

## 시작 전 4가지 확정 (불명확하면 AskUserQuestion)

| 질문 | 왜 필요한가 | 기본값 |
|---|---|---|
| 코호트 기준 | 가입일(signup) vs 첫 행동(behavioral)? | signup |
| 리텐션 정의 | n-day / unbounded / bracket 중? (아래 표) | bracket |
| Return 이벤트 | "살아있다"의 정의 = 어떤 이벤트? | app_open / session_start |
| 기간 단위 | day / week / month? | 제품 사용주기에 맞춰 |

> 단위 선택 규칙: 일일 사용 제품(메신저·뉴스) = day, 주간(생산성·툴) = week, 월간 이상(여행·B2B) = month. 단위를 잘못 잡으면 멀쩡한 제품도 "리텐션 박살" 로 보인다.

---

## 핵심: 리텐션 정의 3종 (혼동 금지)

같은 데이터도 정의에 따라 숫자가 완전히 달라진다. 보고할 때 **반드시 어느 정의인지 명시**한다.

| 정의 | 계산 | "Day 7 리텐션" 의미 | 쓸 때 |
|---|---|---|---|
| **N-day (classic)** | Day N **당일**에 돌아온 유저 비율 | 7일째 그날 접속 | 일일 습관 제품. 가장 빡빡함 |
| **Unbounded (rolling)** | Day N **또는 그 이후** 접속 비율 | 7일째 또는 이후 한 번이라도 | 저빈도 제품. N-day 가 너무 가혹할 때 |
| **Bracket (range)** | Day N 이 속한 구간(예: 5–7일)에 접속 | 5~7일 사이 한 번이라도 | 대부분의 SaaS·앱 기본. 노이즈 적음 |

- **vanity 함정**: "누적(cumulative) 리텐션" = 가입 후 한 번이라도 돌아온 비율. 시간이 갈수록 떨어지지 않고 올라가기만 한다 → 리텐션처럼 보이지만 아님. 보고 금지.
- bracket 을 기본 권장한다. n-day 는 저빈도 제품에서 0에 수렴해 오해를 부른다.

---

## 4가지 산출물

### A. 코호트 리텐션 커브

코호트(가입 주차 등) × 경과 기간의 삼각행렬(triangle). 행=코호트, 열=경과 N.

- **세로(같은 N, 코호트별)**: 신규 코호트가 과거 코호트보다 나아지나? = 제품 개선이 먹히나
- **가로(같은 코호트, N 증가)**: 어디서 급락하나? = 이탈 절벽 위치
- **평탄화 지점(retention floor)**: 커브가 수평이 되는 구간 = 진짜 충성 코어. 이 floor 가 0보다 확실히 높아야 PMF 신호 (`pmf-analyzer` 와 연결).

읽는 법: 첫 1~2 기간(Day 1, Week 1)의 급락은 대부분 **온보딩/활성화** 문제, 이후 완만한 하락은 **습관/가치 전달** 문제. 둘은 다른 처방을 받는다.

### B. 퍼널 드롭오프

가입 → 핵심행동(activation) → 반복사용 → 결제 등 단계별 통과율. 최대 이탈 단계(bottleneck) 1곳을 지목한다.

- 단계 정의는 제품마다 다르므로 사용자에게 확인.
- "활성화(activation) = aha moment 도달 이벤트" 를 퍼널 한가운데 둔다 (`aha-moment-optimizer` 와 연결).
- 리텐션 커브의 초기 급락 ↔ 퍼널 activation 단계 드롭은 보통 같은 원인이다. 교차 확인.

### C. RFM 세그먼트

활동 기준 유저 분류. Recency(최근성)·Frequency(빈도)·Monetary(금액 — 없으면 R·F만).

| 세그먼트 | 조건(대략) | 처방(다음 skill) |
|---|---|---|
| Champions | R 높음·F 높음 | 리퍼럴 요청 (`referral-program-builder`) |
| Loyal | F 높음·R 중 | 업셀·구독 (`subscription-manager-selector`) |
| At-risk | R 낮음(최근 뜸함)·과거 F 높음 | 윈백 캠페인 (`lifecycle-campaign-designer`) |
| Hibernating | R 매우 낮음·F 낮음 | 재활성 1회 시도 후 손절 |
| New | 가입 직후 | 온보딩 (`onboarding-flow-builder`) |

분위수(quantile) 기반으로 R·F 를 각각 1~5점화 → 점수 조합으로 세그먼트 배정. 절대 임계값 하드코딩 금지(제품마다 다름).

### D. 이탈 선행지표 (leading churn indicators)

이탈은 어느 날 갑자기가 아니라 **선행 신호**가 있다. 이탈 유저 vs 잔존 유저의 가입 후 첫 N기간 행동을 비교해, 잔존과 가장 강하게 연관된 행동(activation lever)을 찾는다.

- 예: "첫 주에 친구 3명 추가한 유저는 W4 리텐션 2.4배" → 추가 3명을 onboarding 목표로.
- 상관 ≠ 인과. 선행지표는 **실험 가설**이지 결론이 아니다 → `experiment-analyzer` 로 검증.
- 흔한 lever: 핵심행동 빈도, 소셜 연결 수, 데이터 입력량, 알림 허용 여부.

---

## 데이터 입력 2경로

### 경로 1 — SQL (events 테이블 직접)

`scripts/cohort_retention.sql` 는 표준 events 스키마(`user_id`, `event`, `event_time`)를 가정한 코호트 집계 템플릿. Postgres/Supabase·BigQuery 양쪽 주석 포함. 플레이스홀더만 바꿔 실행:

```sql
-- 바꿀 것: {{RETURN_EVENT}}, {{PERIOD}} (day|week|month),
--          {{COHORT_EVENT}} (signup 이벤트), {{LOOKBACK}}
```

결과(코호트, period_number, cohort_size, retained)를 CSV/TSV 로 받아 경로 2 의 계산기에 넣는다.

### 경로 2 — PostHog / 붙여넣기

PostHog Retention insight(JSON 또는 표) 또는 임의 코호트 표를 표준 CSV 로 환원:

```
cohort,period_number,cohort_size,retained
2026-05-W1,0,1200,1200
2026-05-W1,1,1200,540
2026-05-W1,2,1200,360
...
```

이 CSV 를 계산기에 넣으면 정의별(n-day/bracket) 비율, 코호트 비교, retention floor 추정을 출력한다.

---

## 계산기 (stdlib 전용, 외부 의존성 없음)

```bash
# 코호트 CSV → 리텐션 커브 + floor + 코호트 간 비교
python scripts/retention_calc.py curve --input cohorts.csv

# RFM: user_id, recency_days, frequency, monetary CSV → 세그먼트 배정
python scripts/retention_calc.py rfm --input users.csv

# 선행지표: retained 플래그 + 행동 카운트 CSV → 잔존 상관 lever 랭킹
python scripts/retention_calc.py drivers --input behavior.csv
```

각 서브커맨드는 `--help` 로 정확한 컬럼 스펙을 출력한다. 결정론적 계산만 한다(난수·LLM 호출 없음).

---

## Workflow

1. 4가지 확정 (코호트 기준 / 리텐션 정의 / return 이벤트 / 기간 단위). 불명확하면 `AskUserQuestion`.
2. 데이터 경로 선택 (SQL 템플릿 실행 or PostHog 붙여넣기 → 표준 CSV).
3. `scripts/retention_calc.py curve` 로 커브·floor·코호트 비교.
4. 필요 시 `rfm`, `drivers` 추가 실행.
5. 함정 체크리스트 대조 (아래) → 경고 부착.
6. `templates/retention-report.md` 로 리포트 생성, 다음 실험을 ICE 로 우선순위화.

---

## 함정 (자동 경고)

| 함정 | 증상 | 대응 |
|---|---|---|
| **정의 혼동** | n-day·unbounded·cumulative 를 섞어 비교 | 한 리포트엔 한 정의. 항상 라벨 명시 |
| **누적 리텐션** | 커브가 우상향 | vanity. 진짜 리텐션은 비증가. 폐기 |
| **미성숙 코호트** | 최근 코호트의 Day 30 칸이 비었거나 작음 | 경과기간 미달 칸은 비교 제외(survivorship/right-censoring) |
| **코호트 크기 과소** | cohort_size < 100 | 비율 노이즈 큼. 주차 묶기 또는 신뢰구간 병기 |
| **생존 편향** | 살아남은 유저만 보고 "다 만족" 결론 | 이탈 유저 행동도 함께 봐야 lever 가 보임 |
| **계절·요일 효과** | 특정 코호트만 튐 | 최소 4 코호트 이상으로 추세 확인 |
| **상관=인과 착각** | 선행지표를 곧장 KPI 목표로 박음 | lever 는 가설. `experiment-analyzer` 로 검증 후 채택 |

미성숙 코호트는 삼각행렬에서 자동으로 NA 처리하고 비교에서 뺀다.

---

## 산출물

`docs/retention/<날짜>-retention-report.md` — `templates/retention-report.md` 기반:
- 정의·단위·return 이벤트 명시
- 코호트 리텐션 커브(삼각행렬) + floor 추정
- 퍼널 드롭오프 + bottleneck 1곳
- RFM 세그먼트 분포
- 이탈 선행지표 랭킹(상관, 가설 라벨)
- 다음 실험 백로그 (ICE 우선순위)

## 정직성 원칙

- 어느 리텐션 정의인지 항상 명시한다. 정의 안 밝힌 숫자는 무의미.
- 미성숙·소형 코호트는 "아직 모른다"로 표기 — 억지 추세 그리지 않는다.
- 선행지표는 "상관·가설"로만 보고하고, 인과로 단정하지 않는다.
- 리텐션 floor 가 0으로 수렴하면 좋게 포장하지 않는다 (PMF 미달 신호).

## Related Skills

- `analytics-integrator` — 이벤트·전환 추적, PostHog 세팅 (이 skill 의 데이터 소스)
- `lifecycle-campaign-designer` — 진단된 이탈 지점·세그먼트별 재참여 캠페인 설계
- `experiment-analyzer` — 선행지표 lever 를 실험으로 검증·판정
- `pmf-analyzer` — retention floor 를 PMF 신호로 해석
- `aha-moment-optimizer` — 퍼널 activation 단계 개선

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
