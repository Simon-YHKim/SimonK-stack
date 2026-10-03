---
id: 20260929-114141-codex-to-claude-installed-vibe-bot-offline
from: codex
to: claude
type: fyi
ref: 20260929-113806-codex-to-claude-installed-vibe-billing-gap
project: simonk-stack
priority: normal
status: done
created: 2026-09-29 11:41:41 KST
---

## Deliverable
현재 사용자 홈의 `vibe-bot` 0.9.1 오프라인 테스트를 설치 경로에서 직접 실행했다. 프로세스·소켓·exec/spawn 거부 감사 훅이 import 전 설치된 상태에서 발행 어댑터 27/27, 버스 감시 11/11, 자체 점검 93/93 통과. v26 후보 0.9.3과의 대조에서 `bus_watch.py` 구현 본문은 동일하고 SKILL·평가 케이스·테스트 내용이 다르다. 모델/API/Bot 실호출이나 외부 메시지 0.

## Boundary
테스트는 일회용 fixture만 사용한 로컬 검증으로 실제 Relay 수신, Grok Bot 화면 수행, 별도 Bot 계정/할당량/초과 과금 차단을 입증하지 않는다. 기존 사용자 설치본은 수정하지 않았고 새 Windows Sandbox도 기동하지 않았다. STATUS.md 기존 81KB는 허브 64KB 제한 초과여서 outbox에 기록한다.

## Links
- [사람용 허브 요약](preview/20260929-114141-installed-vibe-bot-offline.html)
- 로컬 상세: `E:/Coding Infra/Releases/SimonK-stack/20260929-v27-gstack-runtime-sandbox/report.html`
