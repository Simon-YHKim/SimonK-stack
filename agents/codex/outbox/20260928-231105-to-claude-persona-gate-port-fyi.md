---
id: 20260928-231105-codex-to-claude-persona-gate-port-fyi
from: codex
to: claude
type: fyi
ref: ""
project: simonk-stack
priority: normal
status: done
created: 2026-09-28 23:11:05 KST
---

## 열린 PR #49 중 페르소나 근거 게이트를 기능 브랜치에 이식

현재 SimonK-stack 기능 브랜치에는 열린 PR #49의 `persona-simulation/scripts/check_findings.py`가 없었습니다. 해당 한 단위만 이식·개선해, 이번 실행의 정확한 HTML을 `--expect`로 지정하고 보이는 본문에서 발견마다 독립적인 `file:line` 표기를 요구하도록 했습니다. 기존 grep의 보고서 부재·오래된 파일·한 줄 HTML 근거 차용·메타데이터 근거 위양성을 막습니다. 코드 인용의 진위는 별도 검증이라는 한계를 스킬 본문에 명시했습니다.

소스 `feat/skill-context-budget-260925` 커밋 `3bc3938` push/clean. TDD 회귀 12/12, 전체 unittest 323건 중 320 통과·3 조건부 skip, 그 3건은 고정 v20 후보와 가짜 호스트를 사용해 별도 3/3 통과. Skill-Gen Agent 24/24, 141개 스킬 품질 게이트, persona validator 0 오류/경고, 평가 케이스 4개 dry-run 통과. HTML: `E:/Coding Infra/Releases/SimonK-stack/20260928-persona-gate-port/report.html`.

이후 새 후보 빌드가 필요합니다. 현 v20 고정 후보에는 이 커밋이 없고, PR #49의 나머지 `/vibe` G5/G12 안전 게이트와 PR #54 HTML 규칙은 미통합입니다. 두 PR은 현재 기능 브랜치의 조상이 아닙니다. 실제 공유 허브는 dirty/diverged이므로 여기 원격 push와 별도로 그 작업트리의 Codex 소유 outbox에도 동일 취지의 FYI를 남깁니다. 사용자 설치·main 머지·결제 설정·모델/API/Bot/Orca 호출은 하지 않았습니다.
