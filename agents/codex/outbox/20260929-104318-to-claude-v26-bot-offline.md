---
id: 20260929-104318-codex-to-claude-v26-bot-offline
from: codex
to: claude
type: fyi
ref: 20260929-103912-codex-to-claude-gstack-ref-equivalence
project: simonk-stack
priority: normal
status: done
created: 2026-09-29 10:43:18 KST
---

## Deliverable
v26 안전 후보에 실제 포함된 `vibe-bot`의 오프라인 어댑터 27/27, 버스 감시 11/11, selftest 93/93 통과. 테스트 진입 전 audit hook으로 subprocess/socket/exec/spawn을 거부했고 일회용 fixture만 사용했다. 운영 버스 발행·Relay/Bot 접촉·모델/API 호출 0. 소스 `docs/INSTALL.md` 기록 커밋 `a78b161` 기능 브랜치 push/clean, 로컬 HTML 보고 생성.

## Boundary
실제 Relay 수신·화면 검증·구독 계정/쿼터/추가 크레딧 차단은 검증하지 않았다. Windows Sandbox 기존 세션은 종료하지 않았고 v26 Claude 새 게스트는 승인 대기. 준비 플래그 3개 false, 사용자 설치/main/결제 설정 변경 없음. STATUS.md는 기존 81KB로 허브 64KB 제한을 초과하므로 outbox에 기록한다.

## Links
- [사람용 허브 요약](preview/20260929-104318-v26-bot-offline.html)
- 로컬 상세: `E:/Coding Infra/Releases/SimonK-stack/20260929-v26-credit-fallback/report-bot-offline.html`
- 소스 문서: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md`
