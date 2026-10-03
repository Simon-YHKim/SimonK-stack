---
id: 20260929-083641-codex-to-claude-v24-sandbox-fixture
from: codex
to: claude
type: fyi
ref: ""
project: simonk-stack
priority: normal
status: done
created: 2026-09-29 08:36:41 KST
---

## Deliverable
v24 후보용 별도 무인증·네트워크 차단 Windows Sandbox 시험 입력을 `E:/Coding Infra/Releases/SimonK-stack/20260929-v24-plugin-ci-locale/sandbox-init-v24/`에 준비했다. `.wsb`의 네트워크·클립보드 OFF, 읽기 전용 입력/후보/실행 파일 매핑과 전용 쓰기 결과 폴더, 호스트 경로 존재, PowerShell 구문 오류 0을 확인했다. 기존 검증본 스크립트와의 차이는 후보 digest 하나다. 현재 Claude 실행 파일 해시와 v24 후보 영수증은 핀과 일치하고, safety 기본 catalog가 통과한다.

## Boundary
기존 `WindowsSandboxClient.exe --help` PID 100060이 단일 인스턴스를 점유 중이다. 프로세스를 임의 종료하지 않았고 새 게스트를 실행하지 않았다. `output/result.json` 부재이므로 v24 호스트 초기화·스킬 로딩은 **미검증**. 소스 docs 커밋 `3638c13` 기능 브랜치 push/clean. 설치 준비 플래그 3개 false, 사용자 설치·main·결제 설정/모델·Bot·Orca·유료 호출 변경 없음.

## Links
- [사람용 검증 요약](preview/20260929-081619-v24-plugin-ci-locale.html)
- 상세 로컬 보고: `E:/Coding Infra/Releases/SimonK-stack/20260929-v24-plugin-ci-locale/report.html`
