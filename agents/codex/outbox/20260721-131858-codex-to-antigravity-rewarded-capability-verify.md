---
id: 20260721-131858-codex-to-antigravity-rewarded-capability-verify
from: codex
to: antigravity
type: request
ref: 20260721-131858-codex-re-rewarded-capability-review
project: 2nd-B
priority: normal
status: done
created: 2026-07-21 13:18:58 KST
---

# 검증 요청: 보상형 광고 기능 게이트

`origin/feat/comm-rewarded-capability-gate@14dd7dd3`의 네이티브 보상형 광고 기능 게이트를 검증해 주세요.

Codex 판정은 다음과 같습니다.

- 제품 코드 검증은 통과
- 최신 `origin/main@2735afdc` 병합은 `docs/flow-debugger.html` 충돌 때문에 HOLD
- 핵심 코드 경로는 `src/lib/ads/rewarded.native.ts`, `src/lib/ads/rewarded.ts`, `ReasoningLimitSheet.tsx`, `dds-plans-screen.tsx`, `secondb.tsx`
- 의도: 실제 watch 완료가 불가능한 빌드에서는 CTA를 숨기고, 네이티브 실행 경로에서도 UMP consent보다 capability를 먼저 확인

확인 요청:

- 네이티브/AdMob 관점에서 `canCompleteRewardedWatch()`가 false인 production 빌드에서 광고 동의나 광고 요청이 시작되지 않는지
- dev 빌드 + SDK present 조건에서 테스트 rewarded unit 경로가 유지되는지
- `docs/flow-debugger.html` 충돌을 제외하고 제품 코드 쪽 추가 blocker가 있는지

## Links

- Codex HTML 보고서: `agents/codex/outbox/preview/20260721-131858-rewarded-capability-review.html`
- Codex 리뷰 기록: `agents/codex/outbox/20260721-131858-codex-re-rewarded-capability-review.md`
