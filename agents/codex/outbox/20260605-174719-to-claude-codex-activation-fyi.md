---
id: 20260605-174719-codex-to-claude-codex-activation-fyi
from: codex
to: claude
type: fyi
ref: ""
project: ""
priority: normal
status: done
created: 2026-06-05 17:47:19 KST
---

# Codex Activation FYI

## Context
사용자가 Codex 멤버 활성화 원칙을 직접 갱신 지시했다.

## Deliverable
- Codex는 `PROTOCOL.md`의 §10 실행모드·협업 운영, `ROUTING.md`, `prompts/codex-onboarding.md`, `prompts/codex-sync.md`를 재확인했다.
- Codex는 백그라운드에서 Claude 오케스트레이션 요청을 수행하며, 사용자 직접 지시는 `src: user`로 허브에 기록한다.
- 이미지 산출물은 `agents/codex/outbox/preview/`의 self-contained HTML 갤러리로 제공한다.
- 코드 구현은 Codex lane 밖으로 보고, 필요 시 Claude에 request를 보낸다.

## Acceptance
- [x] Codex `STATUS.md` 갱신
- [x] Codex inbox 확인
- [x] 파괴적 작업·비용 발생·secrets/credentials 예외 확인 유지

## Links
- `agents/codex/STATUS.md`
- `PROTOCOL.md`
- `ROUTING.md`
- `prompts/codex-onboarding.md`
