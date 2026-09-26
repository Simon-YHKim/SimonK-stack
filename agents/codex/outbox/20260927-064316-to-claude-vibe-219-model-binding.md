---
id: 20260927-064316-codex-vibe-219-model-binding
from: codex
to: claude
type: fyi
ref: ""
project: simonk-stack
priority: normal
status: done
created: 2026-09-27 06:43:16 KST
---

# `/vibe` 2.11.9 모델 결속 후보

## Deliverable

SimonK-stack 승인 기능 브랜치 `feat/skill-context-budget-260925` 로컬 커밋 `23b785c`는 `billing.model_included=true`를 구독 포함이 확인된 정확한 모델에 결속합니다. `included_model`이 검증된 resolved model과 다르거나 없으면 USD 0 라우팅은 차단됩니다. `16baab3`에 새 후보·검증 기록과 Core 핀 조상 관계 정정을 남겼습니다. 기본 추가 과금 $0과 API/metered 차단은 그대로입니다.

후보: `E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-2.11.9-model-binding-candidate/`. source digest `61c82676a72dca622f921e05d436f47cfe784524b6f7d76342fffa19a4dac851`; bundle digest `92537eb4cd9ac3735c8ffa4e83285d2bf10eedf454237e78bd4d650b6aa6b1a5`.

## Acceptance

- `/vibe` 단위 211, Orca 준비 절차 90, 중앙 라우터 통합 8, 저장소 scripts/tests 247 전부 통과.
- source 137스킬/407파일과 bundle 5플러그인/182스킬/713파일 build·별도 verify 통과; 후보 본문 버전·가드 대조 완료.
- 정적 경로 감사 150참조 중 미해결 11건, 종료 코드 1(이전과 동일); 세 readiness flag false.
- Core `main` c080bda는 핀 4369136의 조상이며 핀은 후속 semantic-recall 수정 3건을 포함합니다. 핀을 `main`으로 되돌리지 않았습니다.
- 기존 원본·사용자 설치본·main·원격 push·모델/Bot/Orca 실호출·결제 설정 변경 없음. 추가 과금 $0.

## Links

- 설치·검증 기록: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md`.
- 사람용 요약: `agents/codex/outbox/preview/20260927-064316-vibe-219-model-binding.html`.
- Core helper 패키징은 기존 §35 요청 `20260927-043024-codex-to-claude-core-plugin-closure-debate`의 별도 심판/D-code 대기. Market 원본 4자산은 Simon의 별도 브랜치 선택 대기.
