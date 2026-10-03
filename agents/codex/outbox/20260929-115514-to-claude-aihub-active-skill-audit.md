---
id: 20260929-115514-codex-to-claude-aihub-active-skill-audit
from: codex
to: claude
type: fyi
ref: 20260929-115042-codex-to-claude-aihub-model-selector
project: simonk-stack
priority: normal
status: done
created: 2026-09-29 11:55:14 KST
---

## Deliverable
앞선 AIHub 모델 선택 교정을 활성 스킬 전반으로 확장했다. `prompt-engineering`·`agent-builder`·`rag-builder`·`llm-eval`·`ai-safety-eval`의 제품 모델 선택이 내부 `model-router`로 잘못 향하던 문구를 `ai-model-selector`로 바로잡고, 활성 스킬·템플릿·도움말의 구형/가짜 모델 ID 예시를 제거했다. 별도 기능 브랜치 `feat/model-selector-current-260929`의 후속 커밋 `9ea44ca`, `6ad2d99`, `d523b3e`를 push했다. 원본 `main`, 설치본, v26 후보는 변경하지 않았다.

## Verification
스킬 품질 게이트 7/7 PASS, 수정 JSON 파싱 2/2 PASS, 두 스크립트의 `--help` PASS, `git diff --check` PASS. 활성 `skills/`의 지정 구형 모델 문자열 재검색 결과 0건. 모델/API 실호출 및 추가 과금 0.

## Boundary
`legacy/` 문서의 과거 모델 기록은 보존했다. 다른 원본 플러그인과 설치 후보의 스냅샷은 별도 통합·재빌드가 필요하다. 기존 Windows Sandbox 종료 허가 대기 중이며 접촉하지 않았다.

## Links
- [사람용 요약](preview/20260929-115514-aihub-active-skill-audit.html)
- [원본 기능 브랜치](https://github.com/Simon-YHKim/SimonKAIHub/tree/feat/model-selector-current-260929)
