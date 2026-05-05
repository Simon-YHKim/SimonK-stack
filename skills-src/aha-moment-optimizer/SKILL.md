---
name: aha-moment-optimizer
description: "Use when the user wants to find or optimize their product Aha Moment—triggers "아하 모먼트 찾아줘", "핵심 가치 경험 포인트", "온보딩 최적화", "TTFV 줄이기", "activation 개선", "find aha moment", "optimize onboarding", "time to value". Produces Aha Moment hypothesis generation, experiment design (A/B test plan), data verification framework, and iterative improvement cycle (hypothesis→experiment→data→refine)."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# aha-moment-optimizer

아하 모먼트를 발굴하고 최적화하는 skill. 가설→실험→데이터 사이클.

## 발동 조건

- "아하 모먼트 찾아줘", "온보딩 최적화", "활성화 개선"
- "TTFV 줄이자", "유저가 가치를 느끼는 순간이 뭘까"
- aarrr-growth-planner의 Activation 단계 심화 시

## 아하 모먼트란?

유저가 "이 서비스 진짜 좋다!" 하고 느끼는 **최초의 순간**.

유명 사례:
- Facebook: 10일 내 7명 친구 추가
- Slack: 2000개 메시지 교환
- Dropbox: 1개 파일을 1개 폴더에 저장
- Twitter: 30명 팔로우

## Workflow: 가설→실험→데이터→개선

### Phase 1: 가설 생성

1. **행동 데이터 분석**: 유지 유저 vs 이탈 유저의 초기 행동 차이
2. **유저 인터뷰**: "언제 이 서비스가 좋다고 느꼈나요?"
3. **경쟁자 분석**: 경쟁 서비스의 온보딩 첫 화면

가설 형식:
> "유저가 가입 후 [N일] 이내에 [특정 행동]을 [M회] 하면,
> D30 retention이 [X%] 이상일 것이다."

### Phase 2: 실험 설계

```
실험명: Aha-001
가설: "가입 후 24시간 내 프로젝트 1개 생성 시 D7 retention 2배"
변형:
  A (Control): 기존 온보딩
  B (Treatment): 가입 직후 프로젝트 생성 강제 유도
지표: D7 Retention, Activation Rate
표본: 최소 500/variant
기간: 14일
```

### Phase 3: 데이터 확인

분석 프레임워크:
1. **Correlation**: 아하 행동 vs Retention 상관계수
2. **Causation**: A/B 테스트로 인과관계 검증
3. **Threshold**: 최적 횟수/기간 임계값 탐색

### Phase 4: 개선 (반복)

```
결과에 따라:
├─ 가설 맞음 → 온보딩에 해당 행동 유도 강화
├─ 가설 틀림 → 새 가설 생성 (Phase 1로)
└─ 부분적 → 변수 조정 후 재실험
```

## TTFV (Time to First Value) 최적화

| 최적화 방향 | 방법 |
|---|---|
| 단계 줄이기 | 가입 5단계 → 2단계 |
| 기본값 제공 | 빈 화면 대신 샘플 데이터 |
| 진행률 표시 | "3단계 중 2단계 완료" |
| 즉시 보상 | 첫 행동 후 즉각적 피드백 |
| 스킵 허용 | 나중에 하기 옵션 |

## 산출물

`docs/growth/aha-moment-<date>.md`:
- 현재 가설 (순위별)
- 실험 백로그
- 실험 결과 기록
- 최적화된 온보딩 플로우 제안

## Related Skills

- `aarrr-growth-planner` — Activation 단계 전략
- `pmf-analyzer` — Retention 개선이 PMF에 미치는 영향
- `analytics-integrator` — 코호트 분석 세팅
- `sprint-optimizer` — 실험 스프린트 실행
