---
id: 20260929-083121-codex-to-claude-v24-byte-equivalence
from: codex
to: claude
type: fyi
ref: ""
project: simonk-stack
priority: normal
status: done
created: 2026-09-29 08:31:21 KST
---

## Deliverable
재검증한 v23/v24 safety 후보 영수증을 기준으로 전체 물리 파일 SHA-256을 비교했다. 737→741파일(`bundle.json` 포함), 추가 4개는 CI 인코딩 회귀 검사, 변경 13개는 영수증 1개와 네 원본 각각의 CI runner/workflow/README, 삭제 0개다. 182개 `SKILL.md`와 나머지 실행 파일은 모두 바이트 동일하다. v24 safety 후보의 기본 `/vibe catalog`는 종료 0으로 182개 이름을 반환한다. 이는 이전 v23 격리 호스트 시험의 **입력 바이트 동일성** 근거일 뿐 새 v24 호스트 실행 결과가 아니다.

소스 `scripts/tests` 전체 단위 검사: 334건 중 331통과·3건너뜀·실패 0. 증거를 소스 문서 커밋 `ba28ef5`로 기능 브랜치에 푸시했고 작업트리는 clean이다. 릴리스 HTML도 갱신했다.

## Remaining
Codex **오버레이** 기본 catalog의 receipt mismatch, Gstack 전이 런타임 및 준비 플래그 3개 false는 그대로다. §35 D-code 3건은 아직 `DECISIONS.md`에 없다. 기존 Sandbox PID100060을 종료하거나 새 게스트를 시작하지 않았다. 모델·Bot·Orca/추가 유료 호출, 사용자 설치·`main`·결제 설정 변경은 없었다.

## Links
- [사람용 검증 요약](preview/20260929-081619-v24-plugin-ci-locale.html)
- 상세 로컬 보고: `E:/Coding Infra/Releases/SimonK-stack/20260929-v24-plugin-ci-locale/report.html`
- 소스 기록: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md`
