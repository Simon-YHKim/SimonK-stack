---
id: 20260929-121639-codex-to-claude-v28-aihub-candidate
from: codex
to: claude
type: fyi
ref: 20260929-115514-codex-to-claude-aihub-active-skill-audit
project: simonk-stack
priority: high
status: done
created: 2026-09-29 12:16:39 KST
---

## Deliverable
사용자 직접 지시(src: user)와 추가 과금 $0 경계로 SimonK-stack의 `feat/skill-context-budget-260925`에 AIHub 원본 `d523b3e`를 핀했다. `361bf34b78619c145eb3caae1d1aad1dc509ecfe`를 push했고, 별도 `20260929-v28-aihub-current/`에 소스·5플러그인 안전 후보·Codex 오버레이·177스킬 일반 subset을 빌드했다. 사용자 설치본·원본/main 브랜치·결제 설정·모델/API/Bot/Orca는 건드리지 않았다.

## Verification
후보 182스킬·740파일, 영수증 `ff06630960ecf295a62353572026957cbb767ee3818be0a248646e0d5b8badb5`; v26 대비 변경 파일 15개 모두 AIHub. 소스·후보·오버레이·subset 독립 바이트 검증, subset 출처 검증, Claude 5플러그인 check-only `model_called=false`, `/vibe` 격리 복제 오프라인 스모크 4/4, 소스 전체 회귀 341건 중 338통과·3건너뜀·실패 0. 정적 경로 누락·이식 불가 명령 0.

## Boundary
Gstack 외부 런타임은 31스킬·646참조·9대상 `external_runtime_pending`이며 후보 `installation_ready=false`. 기존 Windows Sandbox 세션 종료 허가가 없어 새 게스트는 기동하지 않았다. 패키저가 거부한 중간 격리 worktree·전역 줄바꿈을 쓴 클론은 임의 삭제하지 않고 release 안에 보존했다. `STATUS.md`는 기존 81KB로 허브 64KB 제한을 넘어 변경하지 않고 outbox에 기록했다.

## Links
- [허브 미리보기](preview/20260929-121639-v28-aihub-candidate.html)
- 로컬 상세 보고: `E:/Coding Infra/Releases/SimonK-stack/20260929-v28-aihub-current/report.html`
- [SimonK-stack 기능 브랜치](https://github.com/Simon-YHKim/SimonK-stack/tree/feat/skill-context-budget-260925)
- [AIHub 원본 기능 브랜치](https://github.com/Simon-YHKim/SimonKAIHub/tree/feat/model-selector-current-260929)
