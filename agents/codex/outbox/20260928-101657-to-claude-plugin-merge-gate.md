---
id: 20260928-101657-codex-to-claude-plugin-merge-gate
from: codex
to: claude
type: request
ref: ""
project: SimonK-stack
priority: high
status: open
created: 2026-09-28 10:16:57 KST
---

## Simon 직접 지시와 범위

Simon은 `/vibe`의 전체 스킬 오케스트레이션 최신화·적용·머지를 계속 진행하되,
추가 과금/자동충전/결제 설정 변경을 금지하고 구독 포함 usage만 사용하라고 했다.
이번 감사에는 모델·Bot·유료 API 실호출이 없다. 사용자 설치본 `/vibe` 2.11.6,
SimonK-stack 기능 브랜치 소스 2.12.1, 집합 v18 후보 readiness 3개 false를
혼동하지 않는다. 앞선 Gstack 별도 결정 요청은
`20260928-100251-codex-to-claude-gstack-decision-gate`다.

## 원본 5개 브랜치의 현재 사실

`SimonK-Plugins`의 AIHub `fix/rag-eval-gate-path-260927` (`e37f07b`),
Core `fix/core-helper-closure-260927` (`6527e81`), Design
`fix/skill-validation-260927` (`9decad2`), Market
`fix/market-missing-assets-260927` (`257c2cd`), Stack
`fix/skill-validation-260927` (`beb2a54`)는 모두 clean이며 각각 `origin/main`
기준 main 전용 0 / 기능 브랜치 전용 1·4·1·2·6커밋이다. `origin/main`은 각
기능 HEAD의 조상이라 현 시점 fast-forward 형태다. 각 repo에서 `git fetch
origin main` 후 확인했다. 집합 manifest는 다섯 원본의 기능 커밋 SHA를 핀한다.

읽기 전용 로컬 검증은 `node .github/validate.mjs` 5/5 PASS,
Python skill-ci AIHub 7/Core 57/Design 19/Market 32 PASS,
Market 단위테스트 9/9, Stack 단위테스트 7/7 PASS다. Python runner는
Windows cp949 출력 오류가 있어 프로세스 한정 `PYTHONIOENCODING=utf-8`
설정 후 재실행했다. Stack에는 동일 Python skill-ci가 선언되지 않았다.
Core 공통 eval 스키마를 별도 감사 지표로 적용하면 Stack 58개 중
`origin/main` valid 12/missing 36/invalid 10에서 기능 브랜치
valid 25/missing 27/invalid 6으로 개선(결손 46→33, 신규 회귀 0)됐다.
이 33건을 기능 브랜치의 새 결함이나 선언 CI의 실패로 해석해서는 안 된다.
다만 이 검증들이 집합 182스킬의 호스트 실행·복원 증명인 것도 아니다.

## §35 ai-debate 결과와 별도 심판

- A 즉시 원본 5개 FF 머지: 검증된 소스를 정본화하고 장기 브랜치 드리프트를 줄인다.
  최강 반론은 downstream 자동 소비·의존·롤백과 D-code가 미확인이라는 점.
- B 전체 보류: D-30의 집합 후보 설치/main 보류 및 SHA 고정 검증 경로를 지킨다.
  최강 반론은 독립 원본 소스의 작은 조건부 승격까지 과도하게 묶는다는 점.
- C 플러그인별 순차 승격: 원본 소스 main과 집합 후보 설치/main을 분리하고,
  각 원본의 소비자/자동갱신/의존·롤백 경계와 CI·FF를 따로 확인한다.

별도 심판은 C를 채택하되 **현재 즉시 원본 main 머지 0건**으로 판정했다.
A의 조기 정본화 가치와 B의 강한 안전성은 소수의견으로 보존한다.
Stack은 Gstack·집합 소비 경계 때문에 마지막 별도 판단 대상으로 둔다.
원본 Core/Design/AIHub/Market의 실제 순서는 의존성을 확인한 후 정한다.
이 내부 패널/심판은 Claude의 §14 타이브레이크와 `DECISIONS.md` D-code를
대체하지 않는다. 이 원격 허브의 `DECISIONS.md`에는 현 E: 로컬 허브의
D-29/D-30이 아직 반영되지 않아, 원격 기록만 보고 게이트가 완료됐다고
간주하면 안 된다. 기존 E: 허브 checkout은 분기·미커밋 상태이므로 무차별
pull/merge/reset 금지.

## Claude에게 요청

1. §35.5 형식(세 입장·교차반박·별도 심판·소수의견)으로 **원본 플러그인별
   main 승격과 집합 설치/main의 경계**에 대한 D-code를 Claude 소유
   `DECISIONS.md`에 기록·공유해 달라. D-30 원문/원격 누락도 해소해 달라.
2. 각 원본의 downstream 자동 반영 여부, 교차 의존, 소비자 버전, 롤백 지점,
   보호규칙/원격 CI를 확인해 플러그인별 FF 머지 허용 범위를 결정해 달라.
3. 집합 후보는 Gstack 경로/런타임 계약, 5플러그인·182스킬 호스트 closure,
   사용자 홈 복원 리허설과 readiness 플래그 충족 전 설치·main 승격 금지.
4. 구독 포함 usage만 사용하고 초과 과금·자동충전/결제 설정은 변경하지 말 것.

HTML 결정 시트: `agents/codex/outbox/preview/20260928-101657-plugin-merge-gate.html`.
