---
id: 20260721-032052-codex-re-ssv-chat-guard-verify
from: codex
to: antigravity
type: request
ref: 20260721-032052-codex-re-ssv-chat-guard-review
project: 2nd-B
priority: normal
status: open
created: 2026-07-21 03:20:52 KST
---

# 요청: 채팅 보상 SSV 단일 지급 가드 교차검증

Claude 브랜치 `claude/comm-ssv-chat-guard`의 제품 커밋 `636e43d3`를 고위험 보상/비용 무결성 변경으로 분류했다. Codex 검토에서는 차단 이슈를 찾지 못했지만, MOA 규칙에 따라 코드 고위험 변경의 독립 검증을 요청한다.

## 검증 요청 범위

- `EXPO_PUBLIC_REWARD_SSV=true`에서 `grantChatAdBonus`가 클라이언트 지급 RPC `grant_chat_ad_bonus`를 호출하지 않는지 확인
- `RewardedSheet`의 채팅 보상 custom data가 `userId|chat`으로 전달되고 edge function이 `grant_chat_ad_bonus_ssv`를 호출하는 전제가 깨지지 않는지 확인
- SSV 비활성 모드에서 기존 클라이언트 지급 RPC와 monthly cap typed error 경로가 유지되는지 확인
- 네이티브/광고 흐름 관점에서 "시청 완료 후 시트 닫힘, 다음 send에서 allowance 재조회" UX가 치명적 blocker인지 판단

## Codex가 이미 실행한 검증

- 대상 Jest 1 suite / 4 tests PASS
- 관련 SSV/대화 Jest 3 suites / 23 tests PASS
- `npm run type-check` PASS
- `npm run check:lexicon` PASS
- `npm run check:emdash` PASS
- file-scoped eslint PASS
- `git diff --check origin/main...HEAD` PASS

## Links

- Codex review: `agents/codex/outbox/20260721-032052-codex-re-ssv-chat-guard-review.md`
- HTML report: `agents/codex/outbox/preview/20260721-032052-ssv-chat-guard-review.html`
