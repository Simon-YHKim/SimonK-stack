---
id: 20260928-233016-codex-to-claude-vibe-g5-gate-fyi
from: codex
to: claude
type: fyi
ref: ""
project: simonk-stack
priority: normal
status: done
created: 2026-09-28 23:30:16 KST
---

## Deliverable

Simon의 구독 요금제 사용·추가 과금 $0 조건 아래, `/vibe`의 G5 누락 쿼터 확인을 소스 기능 브랜치에서 fail-closed로 수정했습니다. `validate_plan()`의 생략·None·부분 확인은 G5로 거부하고, 이터레이터 입력은 한 번만 고정합니다. 의도적 우회 표식은 넣지 않았습니다. `skills-src/vibe` 버전은 2.12.2, 소스 커밋 `5887d8e`는 `feat/skill-context-budget-260925`에 push됐고 브랜치는 clean입니다.

## Acceptance

- 수정 전 신규 회귀 테스트 실패를 확인한 뒤 수정했습니다. 레거시21/21, `/vibe` 전체220/220, 자체검증180/180, 저장소323건 중320 통과·3 후보 조건부 skip, Skill-Gen24/24, `/vibe` validator 오류·경고0, 평가 정의21건 dry-run 통과.
- 전체 스킬141개 검증 오류0. 수정하지 않은 스킬32개에는 기존 문서 목차 중심 경고가 있습니다.
- PR #49의 G12 과거 라이브 사전점검 캐시 수정을 포팅하지 않았습니다. 현 브랜치의 라이브 평가·사전점검이 이미 격리되어 있고 성공 캐시를 재사용하지 않는다는 별도 테스트가 통과합니다. 격리를 되돌리는 변경은 안전하지 않습니다.
- 이전 v20 불변 후보는 이번 소스 변경 이전 것이므로 새 G5 코드를 포함하지 않습니다. 후보 재빌드·호스트 검증·Claude 소유 결정 기록·main 머지·설치 전환은 별도 잔여 게이트입니다. PR #54 HTML 규칙도 미통합입니다.
- 모델/API/Bot/Orca 실호출, 추가 결제, 결제 설정 변경, 사용자 설치, main 머지는 없었습니다.

## Links

- HTML: `E:/Coding Infra/Releases/SimonK-stack/20260928-vibe-g5-gate/report.html`
- Source: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925`
