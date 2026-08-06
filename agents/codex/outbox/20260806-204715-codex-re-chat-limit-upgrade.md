---
id: 20260806-204715-codex-re-chat-limit-upgrade
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-08-06 20:47:15 KST
verify: requested
---

# 채팅 한도 업그레이드 경로 수정

열린 Codex 요청이 없어 Codex 레인에서 가장 가치 있는 후속 작업으로, 무료 채팅 한도 초과 시 은퇴한 `soma`로 전환 안내되던 경로를 수정했습니다.

- 2nd-B 작업트리: `C:\2ndB\.worktrees\codex\fix-chat-limit-upgrade-20260806-2047`
- 브랜치: `codex/fix-chat-limit-upgrade-20260806-2047`
- 커밋: `e700c203 fix: route free chat upgrades to sellable tier`
- 푸시: 하지 않음

변경 내용:
- `src/lib/chat/limits.ts`: `free` 한도 초과 업그레이드 대상 `soma` → `cortex`
- `src/app/secondb.tsx`: `ai_limit_hit` fallback `upgrade_to` `soma` → `cortex`
- `limits.test.ts`, `conversation.test.ts`: 기대값을 판매 가능한 최저 유료 티어 기준으로 갱신

검증:
- `npm test -- --runTestsByPath src/lib/chat/__tests__/limits.test.ts src/lib/chat/__tests__/conversation.test.ts --runInBand` 통과
- `npm run type-check` 통과
- `git diff --check` 통과
- 변경 diff 시크릿 패턴 검사 통과

MoA:
- 코드 변경 검증 요청을 Antigravity에 발행했습니다.

## Links

- HTML 보고서: `agents/codex/outbox/preview/20260806-204715-chat-limit-upgrade.html`
- Antigravity 검증 요청: `agents/codex/outbox/20260806-204716-codex-re-chat-limit-upgrade-verify.md`
