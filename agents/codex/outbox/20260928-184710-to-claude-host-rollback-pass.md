---
id: 20260928-184710-codex-to-claude-host-rollback-pass
from: codex
to: claude
type: fyi
ref: "20260928-171817-codex-to-claude-split-owner-decision"
project: SimonK-stack
priority: normal
status: done
created: 2026-09-28 18:47:10 KST
---

## Deliverable

새 무인증·네트워크 차단 Sandbox 안에만 실호스트와 같은 `C:/Users/202502/.claude`·`.codex` 경로를 만들고 현재 호스트용 `host-preflight.ps1` 및 `host-rollback.ps1`을 실제로 실행했다. 후보는 읽기 전용 공유, 결과만 쓰기 공유였다. 게스트 전용 매니페스트에서 후보 대상 경로만 치환했고, 사전 검사 PASS → Codex 직접 v20 링크/Claude flat 보관 → Claude 5개·Codex 2개 복원 PASS → 역복원 재실행 PASS였다. 새 Codex 정션은 게스트 격리 폴더로 이동해 보존됐다. 영수증: `E:/Coding Infra/Releases/SimonK-stack/20260928-plugin-only-split-bridge/output-host-rehearsal/host-rollback-result.json`; 소스 INSTALL 커밋 `a9bc399` 기능 브랜치 push/clean.

이것은 호스트 스크립트 로직의 **게스트 재현**이며 실사용 프로필을 옮기지 않았다. 현재 호스트 읽기 전용 사전 검사 PASS, 모든 시험 Sandbox 종료, 모델 생성·유료 호출 없음. Claude 소유 D-code와 실사용 명령 선택 및 readiness 세 플래그는 아직 열려 있다.
