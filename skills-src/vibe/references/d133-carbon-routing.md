# D-133 · /vibe 2.30.0 · Gemini 4 Carbon이 Argon 자리를 맡는다

2026-11-28 KST · Simon 지시 "새 모델을 평가한 뒤에 스킬에 반영, 깃허브 반영, 이 컴퓨터 설치" · 허브 PROTOCOL 35.8 1단(측정 근거).

## 왜 지금인가

- Antigravity 모델 표가 Gemini 4 Argon의 제거를 알린다. 같은 목록에 Gemini 3.8 Flash, GPT-OSS-120b, Claude 4.6이 있고 날짜는 2026-11-30이다. ([Antigravity models](https://antigravity.google/docs/models), 2026-11-28 읽음)
- D-131은 Argon에 네 자리를 줬다. 12월 1일부터 그 단계는 모두 갈 곳이 없어진다.
  - 추론 2차 의견
  - 최종 코드 리뷰
  - 설계 보조
  - 한국어 초안 대체
- 같은 표에 따르면 Gemini 4 Carbon은 유료 Google AI Pro에서도 쓸 수 있다. 이 PC의 agy 1.5.18 목록에도 `gemini-4-carbon-low/medium/high`가 있다.
- 0턴 `/usage`로 보면 Carbon은 Neon·Argon·Hydrogen과 같은 Gemini 공용 주간·5시간 창을 쓴다.

## 배정

| 작업 | D-131 | D-133 |
|---|---|---|
| REASONING_ABSTRACT · CODE_REVIEW_FINAL | Argon high (rank 0) | Carbon high (rank 0) |
| PLAN_ARCHITECTURE | Argon high (rank 1) | Carbon high (rank 1) |
| KOREAN_PROSE 대체 | Argon high | Carbon medium |
| ai-debate Gemini 좌석 | `gemini-4-argon-high` | `gemini-4-carbon-high` |

그대로 둔 것:
- Neon 1순위, Hydrogen 역할, GPT-6.2와 Claude 배정
- D-74 사용량 게이트와 다른 벤더 사실 대조
- 순위표 창 끝 2026-12-01 00:00 KST

`gemini-4-argon` 키는 원장 호환용으로만 남는다.

## 근거

- **같은 과제 실측**
  - 과제는 6개이고 정답은 기계로 채점했다: 라인 밸런싱, 조합 세기, 명세 모순 4개, Python 결함 4개, TypeScript 결함 3개, 한국어 공지 사실 13개.
  - 실행기와 같은 `agy --print` argv로 18회 보냈다. Carbon과 Argon은 high, Neon은 high이고 한국어는 Carbon·Neon 모두 medium이다.
  - 세 모델 모두 27/27이었다.
  - Carbon은 합계 1,143초, 출력 95,357토큰이었다. Argon은 511초·40,720토큰, Neon은 492초·52,885토큰이다.
  - 18회에 Gemini 주간 사용량이 17.8%에서 24.3%가 됐다.
  - transcript의 `model` 값은 요청한 슬러그와 같다.
- **공개 지표**
  - Artificial Analysis 지수: Neon xhigh 62, Carbon high 60, Argon 51
  - Arena 텍스트(11-22): Carbon 1위
  - Google은 Enterprise Orchestrator의 planner로 Carbon High를 쓴다.
- **사용자 후기**: DC AI활용 갤러리, HN, X를 보았다.
  - 긍정: 설계·근본원인 분석 5/0/0, 코드 리뷰 3/2/2, 연구 질문 3/0/1
  - 부정: 속도 0/2/9, 과잉 검증·범위 이탈 2/1/5
  - 그래서 구현·UI·한국어 1순위에는 넣지 않았다.

## 한계

- 과제가 쉬워 세 모델이 모두 만점이다. 품질 우위는 이번 측정이 아니라 공개 지표와 후기에서 나왔다.
- Carbon은 같은 일에 약 2.2배 오래 걸린다. ai-debate 호출 기본 600초 안에는 들어왔지만(최장 465초) 긴 증거에서는 시간 초과가 날 수 있다.
- Reddit은 403이었다. X 장문은 280자에서 잘려 일부는 검색 요약으로만 확인했다.
