---
id: 20260821-130342-codex-re-subscription-busy-a11y
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-08-21 13:03:42 KST
---

# 2nd-B 구독 관리 busy 접근성 보강

이번 Codex 자율 폴 사이클에서 열린 Codex/all 요청은 없었습니다. Codex 레인에 맞춰 2nd-B 구독 관리 화면의 진행 상태 접근성 누락 한 건을 수정했습니다.

- worktree: `C:\2ndB\.worktrees\codex-qa-20260821-125720`
- branch: `codex/qa-cycle-20260821-125720`
- base: `origin/main fafb9e0b`
- app commit: `441957f851f424f46c91b9bca12b78a46d69be68`
- 변경: `src/app/subscription.tsx`의 취소/환불 CTA 네 곳에 `loading={busy}`를 연결해 공유 `MdButton`이 busy 접근성 상태를 노출하도록 했습니다.
- 테스트: `src/lib/billing/__tests__/subscription-ux-terms-and-refund.test.ts`에 소스 스캔 회귀 테스트를 추가했습니다.
- push: 하지 않았습니다.

## Verification

- `npm test -- --runTestsByPath src/lib/billing/__tests__/subscription-ux-terms-and-refund.test.ts --runInBand` 통과
- `npx eslint src/app/subscription.tsx src/lib/billing/__tests__/subscription-ux-terms-and-refund.test.ts` 통과
- `npm run type-check` 통과
- `npm run check:i18n` 통과
- `npm run check:i18n-untranslated` 통과
- `npm run check:lexicon` 통과
- `npm run check:constraints` 통과
- `npm run check:emdash` 통과
- `npm run check:anti-anthro` 통과
- `npm run check:mascot-voice` 통과
- `npm run check:cycles` 통과
- `git diff --check` 통과
- 변경 diff 민감 패턴 검사: 탐지 없음
- `npx prettier --check src/app/subscription.tsx src/lib/billing/__tests__/subscription-ux-terms-and-refund.test.ts`는 기존 파일 포맷 드리프트 때문에 실패했습니다. 대량 포맷 diff를 피하려고 이번 사이클에서는 포맷 전체 정리를 하지 않았습니다.

## Links

- HTML report: `agents/codex/outbox/preview/20260821-130342-subscription-busy-a11y.html`
