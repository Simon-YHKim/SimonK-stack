---
name: onboarding-flow-builder
description: >
  Use when designing or implementing an activation onboarding flow that BUILDs the aha moment aha-moment-optimizer FINDs into a real first-run flow. 트리거 "온보딩 만들어", "첫 화면 플로우", "활성화 개선", "first-run 시퀀스", "빈 상태 카피", "권한 사전설득", "TTFV", "build onboarding", "empty state copy", "permission priming", /onboarding-flow-builder. Produces: first-run 시퀀스 정의 → 빈 상태 카피 → N단계 셋업 체크리스트 → 알림/권한 사전설득(priming) → 각 스텝 activation 이벤트 심기 → 드롭오프 측정 설계. building-native-ui(RN/Expo) 위에 활성화 의도를 얹는다.
allowed-tools: Read, Write, Edit, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# onboarding-flow-builder

아하 모먼트를 **first-run 경험으로 구현**하는 skill. FIND은 `aha-moment-optimizer`, BUILD은 여기.

`aha-moment-optimizer`가 "유저가 가입 후 N일 내 X 행동 M회 → retention 상승" 가설을 만들면,
이 skill은 그 X 행동에 **가장 빨리 도달시키는 화면 시퀀스**를 만든다.

## 발동 조건

- "온보딩 만들어", "첫 화면 플로우 짜줘", "활성화 개선해줘"
- "빈 상태 카피 써줘", "셋업 체크리스트 만들어", "권한 요청 사전설득"
- "TTFV 줄이는 화면 흐름", "first-run 시퀀스"
- `aha-moment-optimizer`가 가설/임계값을 확정한 직후 (BUILD 단계 인계)

## 선행 입력 (없으면 먼저 물어본다)

활성화 의도 없이 화면부터 그리지 않는다. 다음 4개를 AskUserQuestion으로 확정한다.

| 입력 | 질문 | 없을 때 |
|---|---|---|
| Aha 행동 | "유저가 처음 가치를 느끼는 단 하나의 행동은?" | `aha-moment-optimizer` 먼저 호출 권고 |
| Aha 임계값 | "몇 회 / 며칠 안에?" | 가설 형식으로 잠정 설정 후 측정으로 검증 |
| 활성화 정의 | "이 유저는 '활성화됨' 이라고 부를 조건은?" | Aha 행동 1회 완료를 기본값 |
| 플랫폼 | "RN/Expo 앱 · 웹 · 둘 다?" | RN/Expo 가정, 웹이면 building-native-ui 대신 web 패턴 |

## Workflow (6단계)

### 1. First-run 시퀀스 정의

화면을 나열하기 전에 **"한 화면 = 한 목적"** 원칙을 적용한다. 각 화면은 Aha 행동에 가까워지는 한 걸음.

원칙:
- 가입과 가치 경험 사이 마찰 최소화. 회원가입은 가능한 뒤로 (value-first → 나중에 계정).
- 화면당 결정은 1개. 입력 필드 3개 넘으면 분할.
- 모든 화면에 "나중에 하기 / 건너뛰기" 출구. 단, Aha 행동 직전 스텝은 출구를 약하게.

산출물: `templates/first-run-sequence.md` 채워서 `docs/growth/onboarding-<date>.md` 로 저장.

### 2. 빈 상태(empty state) 카피

빈 화면은 이탈 지점이다. "데이터 없음" 대신 **다음 행동 1개**를 제시한다.

빈 상태 3요소 (`templates/empty-state-copy.md`):
1. 한 줄 가치 진술 (왜 여기 있어야 하는가)
2. 단일 CTA (Aha 행동으로 직결)
3. (선택) 샘플/시드 데이터로 "완성된 모습" 미리보기

금지: 클리니컬·과장 표현, 이모지 장식, 빈 화면에 설명만 늘어놓기.

### 3. N단계 셋업 체크리스트

활성화까지 남은 일을 가시화한다. 진행률은 동기 부여 장치(목표 그라데이션 효과).

| 패턴 | 적용 |
|---|---|
| 진행률 바 | "3단계 중 2단계 완료" |
| 첫 항목 미리 체크 | 가입=완료 표시로 시작 모멘텀 |
| 항목당 보상 명시 | 완료 시 잠금 해제되는 가치 |
| 3~5개로 제한 | 길면 압도 → 핵심만 |

각 체크 항목은 1번 시퀀스의 화면 또는 Aha 행동에 매핑된다.

### 4. 알림/권한 사전설득 (priming)

OS 권한 다이얼로그를 **바로 띄우지 않는다**. 사전 설득 화면(soft ask)을 먼저.

순서: 가치 맥락 노출 → soft-ask 화면(왜 필요한지 + "허용/나중에") → 사용자가 동의하면 그때 OS 다이얼로그(hard-ask).

이유: OS 권한은 한 번 거부되면 앱 내 재요청 불가(설정 이동 필요). soft-ask로 한 번 거른다.

RN/Expo 구현 지점:
- 알림: `expo-notifications` `requestPermissionsAsync()` 는 soft-ask 통과 후에만 호출.
- 카메라/위치/사진: `expo-camera` / `expo-location` / `expo-image-picker` 동일 패턴.
- soft-ask UI는 일반 화면(bottom sheet 가능). hard-ask는 OS 소관이라 디자인 불가.

타이밍: 권한은 **그 기능을 처음 쓰려는 순간**에 요청(가입 직후 일괄 요청 금지).

### 5. 스텝별 activation 이벤트 심기

각 시퀀스 스텝 진입·완료·이탈에 이벤트를 심는다. 측정 없는 온보딩은 개선 불가.

이벤트 명명은 `analytics-integrator` 규약을 따른다: `object_action` snake_case.

```
onboarding_started        { variant }
onboarding_step_viewed    { step_id, step_index }
onboarding_step_completed { step_id, step_index, duration_ms }
onboarding_step_skipped   { step_id, step_index }
permission_primed         { permission }          # soft-ask 노출
permission_prompt_shown   { permission }          # hard-ask(OS) 노출
permission_granted        { permission }
permission_denied         { permission }
aha_moment_reached        { action, count, t_since_signup_ms }   # 핵심
onboarding_completed      { duration_ms, steps_skipped }
```

`aha_moment_reached` 는 1번에서 정의한 Aha 행동·임계값과 정확히 일치해야 한다(C: 가설 검증 가능성).
이벤트 실제 발화는 `analytics-integrator` 가 세팅한 provider 추상화 레이어를 통해 보낸다.

### 6. 드롭오프 측정 설계

심은 이벤트로 단계별 퍼널을 구성한다. 어느 스텝에서 떨어지는지 = 다음 개선 1순위.

| 측정 | 정의 | 행동 |
|---|---|---|
| Step funnel | viewed → completed 비율(스텝별) | 최저 전환 스텝부터 수정 |
| Skip rate | skipped / viewed | 높으면 그 스텝 가치 불명확 |
| Time-to-Aha | signup → `aha_moment_reached` 중앙값 | TTFV 핵심 지표 |
| Activation rate | aha_moment_reached / onboarding_started | 코호트별 추적 |
| Permission opt-in | granted / primed | soft-ask 카피 효과 |

`scripts/funnel_dropoff.py` 로 이벤트 로그(JSON/CSV)에서 단계별 드롭오프와 Time-to-Aha를 계산한다.
실험 변형(A/B)은 `aha-moment-optimizer`의 실험 백로그에 등재해 가설 사이클로 돌린다.

## 구현 경계

- **building-native-ui** 가 RN/Expo 화면·네비게이션(expo-router)·성능을 만든다. 이 skill은 그 위에 **활성화 의도**(시퀀스 순서, 카피, priming 타이밍, 이벤트)를 얹는다. 화면 컴포넌트 자체를 새로 발명하지 않는다.
- 첫 진입 1회성 플래그는 영속 저장에 둔다(RN: AsyncStorage 또는 서버 user flag). 2MB 한도 주의 — 큰 상태는 서버로.
- 시크릿·API 키는 코드에 두지 않는다. provider 키는 env 로.

## 검증 체크리스트

- [ ] Aha 행동·임계값이 1번 시퀀스와 5번 `aha_moment_reached` 에서 동일하게 정의됨
- [ ] 모든 스텝에 viewed/completed/skipped 이벤트가 발화됨 (dev 로그 확인)
- [ ] 권한은 soft-ask 통과 후에만 OS 다이얼로그 호출 (가입 직후 일괄 요청 없음)
- [ ] 빈 상태마다 단일 CTA 존재 (설명만 있는 빈 화면 없음)
- [ ] 셋업 체크리스트 3~5개, 진행률 표시
- [ ] first-run 1회성 플래그가 영속 저장에 있음 (앱 재시작 후 재노출 안 됨)
- [ ] 드롭오프 퍼널이 구성되고 최저 전환 스텝이 식별됨

## 산출물

- `docs/growth/onboarding-<date>.md` — first-run 시퀀스 + 빈 상태 카피 + 체크리스트 + priming 플랜
- `templates/first-run-sequence.md` — 시퀀스 정의 양식
- `templates/empty-state-copy.md` — 빈 상태 카피 양식
- 코드: 화면별 이벤트 호출 + soft-ask 화면 (building-native-ui 산출물 위에 Edit)

## Related Skills

- `aha-moment-optimizer` — FIND: 어떤 행동을 활성화로 볼지 가설/임계값 (이 skill의 입력)
- `building-native-ui` — RN/Expo 화면·네비게이션 구현 기반 (이 skill이 위에 얹음)
- `analytics-integrator` — 이벤트 provider 세팅·퍼널 대시보드 (5·6단계 연동)
- `aarrr-growth-planner` — Activation 단계 전략 맥락

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
