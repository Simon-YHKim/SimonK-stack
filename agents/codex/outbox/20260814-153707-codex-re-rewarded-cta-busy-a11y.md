---
id: 20260814-153707-codex-re-rewarded-cta-busy-a11y
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-08-14 15:37:07 KST
---

# 보상형 광고 버튼 접근성 상태 보강

열린 신규 Codex/all 요청은 없어서 lane 작업으로 2nd-B 보상형 광고 시트의 CTA 접근성 결함 하나를 처리했습니다.

- worktree: `C:\2ndB\.worktrees\codex-qa-20260814-153228`
- branch: `codex/qa-cycle-20260814-153228`
- app commit: `f11c371c06326359bd3a2423581ffc5e444b6204`
- push: 하지 않음
- 변경: 광고 시청 CTA가 실행 중일 때 `disabled`와 `accessibilityState.disabled/busy`를 노출하고, 보조 닫기 버튼에 명시적 접근성 label을 추가
- 회귀 가드: `src/lib/ads/__tests__/ssv-wiring.test.ts`에 source-scan 테스트 추가

## Verification

- PASS `npx prettier --check src/components/deepspace/RewardedSheet.tsx src/lib/ads/__tests__/ssv-wiring.test.ts`
- PASS `npm test -- --runTestsByPath src/lib/ads/__tests__/ssv-wiring.test.ts --runInBand`
- PASS `npx eslint src/components/deepspace/RewardedSheet.tsx src/lib/ads/__tests__/ssv-wiring.test.ts`
- PASS `npm run type-check`
- PASS `npm run check:i18n`
- PASS `npm run check:i18n-untranslated`
- PASS `npm run check:lexicon`
- PASS `npm run check:constraints`
- PASS `npm run check:emdash`
- PASS `npm run check:anti-anthro`
- PASS `npm run check:mascot-voice`
- PASS `npm run check:cycles`
- PASS `git diff --check`
- LIMITED changed-diff sensitive-pattern scan: `tokens`라는 테마 모듈 주석을 잡은 false positive만 있었고 실제 시크릿 값은 없었습니다.

## Links

- HTML report: `agents/codex/outbox/preview/20260814-153707-rewarded-cta-busy-a11y.html`
