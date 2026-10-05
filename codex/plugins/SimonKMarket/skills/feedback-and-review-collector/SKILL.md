---
name: feedback-and-review-collector
description: "Use when the user wants to collect in-app feedback / ratings / store reviews—triggers \"NPS\", \"인앱 설문\", \"앱 평점 유도\", \"리뷰 요청\", \"CSAT\", \"별점 유도\", \"마이크로 설문\", \"피드백 위젯\", \"store review prompt\", \"in-app survey\", \"rating prompt\", \"NPS 위젯\". Produces NPS/CSAT/CES micro-survey widgets, satisfaction-gated StoreKit / Play In-App Review prompts (fire only after a positive signal, frequency-capped, route detractors to a private feedback channel instead of the store), and turns qualitative signals into prioritized improvement hypotheses. Includes a stdlib-only score calculator (NPS/CSAT/CES + verbatim theming) and a deterministic review-prompt eligibility engine. Distinguishes measuring sentiment from begging for 5 stars, and never games store ratings."
allowed-tools: Read, Write, Edit, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# feedback-and-review-collector

인앱 피드백·평점을 **올바르게** 수집하는 skill. 두 가지를 분리해서 다룬다: (1) 제품 개선용 정량·정성 신호 수집(NPS·CSAT·CES 마이크로설문), (2) 스토어 평점 유도(StoreKit / Play In-App Review). 핵심 원칙은 **만족한 유저에게만, 만족 직후에, 횟수 제한을 두고** 스토어 리뷰를 요청하고, 불만 유저는 스토어가 아니라 **비공개 피드백 채널**로 보내는 것이다.

이 skill 은 **수집·게이팅 설계 전용**이다. 수집한 신호의 코호트 분석은 `cohort-retention-analyzer`, 활성화 가치 순간은 `aha-moment-optimizer`, 스토어 등록·메타데이터는 `store-launcher` 로 넘긴다.

## 발동 조건

- "NPS 넣어줘", "인앱 설문 만들어줘", "CSAT 측정하자"
- "앱 평점 유도하고 싶어", "리뷰 요청 팝업", "별점 유도 어떻게 하지"
- "유저 피드백 받는 위젯", "마이크로 설문"
- `aha-moment-optimizer` 가 가치 순간을 찾은 뒤 그 직후 만족 신호를 수집할 때
- `cohort-retention-analyzer` 가 이탈 선행지표로 만족도를 보라고 했을 때

## 시작 전 4가지 확정 (불명확하면 AskUserQuestion)

| 질문 | 왜 필요한가 | 기본값 |
|---|---|---|
| 측정 지표 | NPS / CSAT / CES 중 무엇? (아래 표) | 제품 단계로 결정 |
| 만족 시그널 | 무엇을 "만족했다"의 트리거로 볼지 (가치 행동 완료·연속 사용·긍정 응답) | aha 행동 N회 완료 |
| 플랫폼 | iOS(StoreKit) / Android(Play) / 웹 중 어디? | RN/Expo → iOS+Android 양쪽 |
| 불만 유저 행선지 | 스토어 대신 어디로 보낼지 (인앱 폼·이메일·인터컴) | 인앱 피드백 폼 |

> 단계 규칙: 초기 PMF 탐색 = NPS(애착·추천의향), 특정 경험 직후 = CSAT(만족), 마찰 진단 = CES(수고). 한 화면에 두 지표를 섞지 않는다.

---

## 핵심: 측정 지표 3종 (혼동 금지)

같은 "만족도"라도 무엇을 묻느냐에 따라 다른 행동을 처방한다. 한 설문에는 한 지표만 쓰고, 보고 시 어느 지표인지 명시한다.

| 지표 | 질문 | 척도 | 계산 | 쓸 때 |
|---|---|---|---|---|
| **NPS** | "이 앱을 친구에게 추천할 가능성?" | 0–10 | %(9–10 Promoter) − %(0–6 Detractor) | 전반적 애착·관계 강도. 분기 추적 |
| **CSAT** | "방금 경험에 얼마나 만족?" | 1–5 (또는 1–7) | %(상위 box: 4–5) | 특정 경험 직후. 거래·지원 완료 시 |
| **CES** | "원하는 걸 처리하기 얼마나 쉬웠나?" | 1–7 (1=매우 어려움) | 평균 또는 %(쉬움: 5–7) | 마찰·온보딩·기능 사용성 진단 |

- **NPS 함정**: NPS 는 −100 ~ +100 범위라 "점수"이지 백분율이 아니다. 표본 < 100 이면 신뢰구간이 ±10 을 넘으니 추세로만 본다.
- **상위 box 규칙**: CSAT 은 평균 내지 말고 상위 box 비율을 본다(평균은 분포를 숨긴다).
- **응답 편향**: 인앱 설문은 활성·만족 유저가 과대표집된다(생존 편향). 이탈 유저 표본을 별도로 봐야 진짜 그림이 나온다.

---

## 핵심: 리뷰 프롬프트 게이팅 (이 skill 의 심장)

스토어 평점은 함부로 띄우면 (a) 별점을 깎이고 (b) OS 가 프롬프트를 throttle 해버린다. 따라서 **게이트를 통과한 유저에게만** 네이티브 리뷰 시트를 호출한다.

### 게이트 4조건 (AND — 모두 충족해야 호출)

| 조건 | 규칙 | 이유 |
|---|---|---|
| **만족 시그널** | 직전에 긍정 신호 발생 (CSAT≥4, NPS≥9, 또는 가치 행동 완료) | 불만 유저를 스토어로 보내면 안 됨 |
| **체류·숙성** | 설치 후 N일 + 세션 M회 이상 | 앱을 충분히 겪은 유저만 |
| **빈도 캡** | 마지막 요청 후 최소 P일, 버전당 1회, 연 K회 이하 | OS 한도 + 피로 방지 |
| **부정 직후 아님** | 최근 크래시·에러·결제 실패·환불 없음 | 최악의 타이밍 회피 |

### 분기 처리 (불만 유저는 절대 스토어로 보내지 않음)

```
만족 시그널?
├─ YES  → 게이트 통과 시 네이티브 리뷰 시트 (StoreKit / Play In-App Review)
└─ NO   → 인앱 피드백 폼 (불만 사유 수집) → 스토어 노출 안 함
```

이 분기가 **본질**이다. 만족한 유저는 스토어로, 불만 유저는 비공개 채널로. 만족 여부를 묻지 않고 무조건 별점 시트를 띄우는 것은 평점 도박이다.

### 네이티브 API 의 현실 (반드시 고지)

| 플랫폼 | API | 통제할 수 없는 것 |
|---|---|---|
| iOS | `SKStoreReviewController.requestReview` / `requestReview(in:)` | iOS 가 자체 throttle(연 ~3회). 시트가 **안 뜰 수도** 있다. 버튼 텍스트·노출 보장 없음 |
| Android | Play In-App Review (`ReviewManager`) | Play 가 quota 로 throttle. 표시 보장 없음. 흐름 완료 콜백 ≠ 리뷰 작성됨 |
| Expo | `expo-store-review` (`StoreReview.requestReview()`) | 위 두 OS 동작을 래핑. `isAvailableAsync()` 선확인 필수 |
| 웹 | 네이티브 시트 없음 | 자체 별점 위젯 → 긍정 시 외부 리뷰 링크 유도 |

> 결정적 함정: 네이티브 시트는 **호출해도 안 뜰 수 있고**, 떴는지/작성했는지 **알 수 없다**. 따라서 "리뷰 요청 시도" 만 로깅하고, 리뷰 시트 뒤에 "고마워요" 화면을 강제로 띄우거나 보상을 주면 **스토어 정책 위반**이다.

---

## 금지 사항 (스토어 정책 — CI 가 아니라 정책으로 강제됨)

- 별점을 조건으로 보상·잠금해제·콘텐츠 제공 (Apple App Store Review 1.1, Google Play 정책 위반)
- "5점 주세요" 처럼 특정 점수 유도. 중립적으로 평가만 요청
- 리뷰 시트를 앱 진입·종료마다 도배
- 불만 응답자를 스토어로 깔때기질
- 가짜·인센티브 리뷰, 리뷰 대량 요청 캠페인
- 네이티브 시트 위에 자체 모달을 덮어 작성을 강제하는 척

---

## 산출물 4종

### A. 마이크로설문 위젯 사양

한 화면 = 한 질문 원칙. 카피·척도·트리거를 `templates/microsurvey-copy.md` 의 EN↔KO 쌍으로 제공. 위젯은 바텀시트(모달 도배 금지), 1탭 응답, "나중에/닫기" 항상 노출.

### B. 리뷰 프롬프트 게이팅 설정

`templates/review-prompt-config.json` — 4조건 임계값(N일·M세션·P일 쿨다운·K회/년), 만족 시그널 정의, 불만 분기 행선지. 이 설정을 `scripts/review_gate.py` 가 그대로 읽어 결정론적으로 판정한다.

### C. 점수 리포트

응답 CSV → NPS/CSAT/CES 점수, 추세, 표본·신뢰구간 경고. `scripts/feedback_calc.py`.

### D. 정성 신호 → 개선 가설

verbatim(자유응답)을 키워드로 테마 클러스터링 → 빈도·감성으로 랭킹 → "이 마찰을 없애면 CSAT +X" 형태의 **가설**로 변환. 가설은 결론이 아니므로 `experiment-analyzer` 로 넘긴다.

---

## 데이터 입력

표준 응답 CSV (지표별 컬럼):

```
# NPS
respondent_id,score,verbatim,segment
u001,9,추천 의향 높음,paid
u002,5,UI 가 복잡해요,free

# CSAT (score 1-5) / CES (score 1-7) 도 동일 포맷, score 범위만 다름
```

---

## 계산기 & 게이트 엔진 (stdlib 전용, 외부 의존성 없음)

```bash
# NPS 점수 + Promoter/Passive/Detractor 분포 + 표본 경고
python scripts/feedback_calc.py nps --input nps.csv

# CSAT 상위 box 비율 (척도 자동 감지 1-5/1-7)
python scripts/feedback_calc.py csat --input csat.csv --scale 5

# CES 평균 + 쉬움 비율
python scripts/feedback_calc.py ces --input ces.csv

# verbatim 테마 클러스터링 (키워드 빈도 + 감성 단어 매칭, 결정론적)
python scripts/feedback_calc.py themes --input nps.csv

# 리뷰 프롬프트 게이트 판정 (유저 상태 JSON + 설정 JSON → 호출/대기/피드백폼)
python scripts/review_gate.py --user user_state.json --config templates/review-prompt-config.json
```

각 서브커맨드는 `--help` 로 컬럼 스펙을 출력한다. 난수·네트워크·LLM 호출 없이 닫힌식 계산만 한다. 게이트 엔진은 동일 입력 → 동일 판정(결정론)이다.

---

## Workflow

1. 4가지 확정 (지표 / 만족 시그널 / 플랫폼 / 불만 행선지). 불명확하면 `AskUserQuestion`.
2. 마이크로설문 위젯 사양 작성 (`templates/microsurvey-copy.md` 기반, EN↔KO 쌍, 바텀시트·1탭·닫기).
3. 리뷰 게이팅 설정 작성 (`templates/review-prompt-config.json`), 만족 분기 + 불만 폼 행선지 명시.
4. `scripts/review_gate.py` 로 대표 유저 상태들에 대해 판정을 dry-run, 게이트가 의도대로 막는지 확인.
5. 응답 수집 후 `scripts/feedback_calc.py` 로 점수·테마 산출, 함정 체크리스트 대조.
6. verbatim 테마 → 개선 가설로 변환, ICE 우선순위, `experiment-analyzer` 로 검증 인계.

---

## 함정 (자동 경고)

| 함정 | 증상 | 대응 |
|---|---|---|
| **무조건 별점 시트** | 진입/종료마다 리뷰 요청 | 만족 게이트 통과 시 1회만. OS throttle 로 어차피 무력 |
| **불만 유저 스토어行** | NPS 낮은 유저에게도 별점 시트 | 만족 분기 필수. 불만은 비공개 폼으로 |
| **보상 미끼** | "5점 주면 코인 지급" | 정책 위반. 즉시 제거 |
| **CSAT 평균 보고** | "평균 4.1점" | 평균은 분포 은폐. 상위 box 비율로 보고 |
| **표본 과소 NPS** | n<100 인데 "NPS 32!" | 신뢰구간 ±10 초과. 추세로만 |
| **생존 편향** | 활성 유저만 응답 → "다 만족" | 이탈 유저 표본 별도 수집 |
| **시트 결과 가정** | "리뷰 시트 떴으니 작성됨" | 떴는지/작성됐는지 알 수 없음. "시도"만 로깅 |
| **피로 무시** | 같은 유저에게 매주 설문 | 응답자별 쿨다운, 응답 후 장기 침묵 |

---

## 정직성 원칙

- 어느 지표(NPS/CSAT/CES)인지 항상 명시한다. 라벨 없는 점수는 무의미.
- 표본·생존 편향을 숨기지 않는다. 만족 유저 과대표집을 보고에 적는다.
- 네이티브 리뷰 시트는 "호출 시도"까지만 사실이다. 노출·작성은 추정으로도 단정하지 않는다.
- 정성 신호는 "가설"로만 보고하고 인과로 단정하지 않는다 → `experiment-analyzer` 로 검증.
- 평점을 올리기 위한 어떤 도박·미끼·강제도 설계하지 않는다. 측정과 구걸을 혼동하지 않는다.

## 비밀·환경값

- 인터컴·이메일·웹훅 토큰 등 피드백 채널 자격증명은 코드에 하드코딩 금지. `EXPO_PUBLIC_` 접두사가 붙지 않은 서버 환경변수로 관리하고, 클라이언트엔 공개 가능한 값만 노출한다.

## Related Skills

- `store-launcher` — 스토어 등록·메타데이터·심사 (리뷰 시트의 무대)
- `aha-moment-optimizer` — 가치 순간 = 만족 시그널 트리거의 근거
- `cohort-retention-analyzer` — 수집한 만족도를 코호트·이탈 선행지표로 분석
- `experiment-analyzer` — 정성 가설을 실험으로 검증
- `analytics-integrator` — 설문 노출·응답·리뷰 시도 이벤트 추적

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
