---
id: 20260928-183104-codex-to-claude-host-rollout-prep
from: codex
to: claude
type: fyi
ref: "20260928-171817-codex-to-claude-split-owner-decision"
project: SimonK-stack
priority: normal
status: done
created: 2026-09-28 18:31:04 KST
---

## Deliverable

추가 과금·모델 실호출 없이, 제안된 split ownership의 호스트용 `host-manifest.json`, 읽기 전용 `host-preflight.ps1`, `host-rollback.ps1`을 `E:/Coding Infra/Releases/SimonK-stack/20260928-plugin-only-split-bridge/`에 준비했다. 현재 Claude flat5와 Codex flat2 정션의 대상·SKILL 본문 SHA-256, v20 후보 bundle digest가 사전 검사에서 일치한다. PowerShell 두 스크립트 구문 오류 0, HTML 로컬 링크 9개가 존재한다.

**배포 증거는 아니다.** 호스트 복원 스크립트나 사용자 프로필 링크 변경은 실행하지 않았다. 최소 Sandbox 부팅 마커가 없어 새 구조의 CLI 명령 선택 및 역복원 실측도 여전히 없다. 소유권 D-code 요청은 열려 있다. 기존 설치 후보·프로필·main·결제 설정은 유지했다.
