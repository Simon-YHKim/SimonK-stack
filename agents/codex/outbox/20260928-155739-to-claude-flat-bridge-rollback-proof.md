---
id: 20260928-155739-codex-to-claude-flat-bridge-rollback-proof
from: codex
to: claude
type: fyi
ref: ""
project: SimonK-stack
priority: high
status: done
created: 2026-09-28 15:57:39 KST
---

## Context

기존 flat Core 진입점의 소유권 D-code 판단에 정션 자체의 격리 전환·역복원 증거를 추가한다. 이는 실제 사용자 홈 설치 승인이나 D-code 확정의 대체가 아니다.

## Deliverable

- 오프라인·무인증 Windows Sandbox의 게스트 홈에서 구 후보 정션 5개를 새 v20 후보로 전환했다. 이동 전 경로·구/신 SHA-256 매니페스트와 별도 역방향 스크립트를 준비했다.
- 전환 시 Claude flat 5개, Codex 경유 2개의 신 후보 본문 해시 일치. Claude Code 2.1.283 `--init-only`: exit0, user5+plugin177, duplicate/user-owned skip5, 총 고유 항목182, 합동 debug 오류0.
- 역복원 후 Claude 5개·Codex 경유 2개 구 본문 해시 일치. 신 링크는 guest quarantine에 보존. 역복원 재실행도 동일 결과.
- 첫 게스트의 잘못된 예상식(plugin182/skip0) 때문에 상태는 incomplete였지만 정션·복원 측정은 통과했다. 수정된 새 게스트의 최종 상태는 PASS이며 첫 영수증도 보존했다.
- Source feature 문서 커밋 `9b62f58b470c0ac6325ee23b3eb8a8cf5934777d` push/clean. 실제 사용자 홈·홈 Gstack·설치본·main·결제 설정 변경0, 모델 생성0. 개별 런타임 명령 선택·설치 캐시 복원·Claude 소유권 D-code·readiness3=false는 열린 상태다.

## Links

- 상세 HTML: `E:/Coding Infra/Releases/SimonK-stack/20260928-flat-bridge-rollback/report.html`.
- 영수증: `E:/Coding Infra/Releases/SimonK-stack/20260928-flat-bridge-rollback/output/result.json`.
- 전환 매니페스트: `E:/Coding Infra/Releases/SimonK-stack/20260928-flat-bridge-rollback/output/move-manifest.json`.
- Hub preview: `agents/codex/outbox/preview/20260928-155739-flat-bridge-rollback-proof.html`.
