---
id: 20260814-151858-codex-re-record-detail-busy-a11y
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-08-14 15:18:58 KST
---

# 레코드 상세 액션 접근성 상태 보강

열린 신규 Codex/all 요청은 없어서 lane 작업으로 2nd-B 레코드 상세 화면의 접근성 상태 결함 하나를 처리했습니다.

- worktree: `C:\2ndB\.worktrees\codex-qa-20260814-151712-min`
- branch: `codex/qa-cycle-20260814-151712-record-detail-a11y`
- app commit: `ea7b9ba4`
- push: 하지 않음
- 변경: source promote 버튼에 `busy: promoting`, 삭제 아이콘 버튼에 `disabled/busy` 접근성 상태 추가
- 회귀 가드: `scripts/check-constraints.ts`에 `RecordDetailActionA11yState` 추가

## Verification

- PASS `npm run check:constraints`
- PASS `npx jest src/screens/deepspace/__tests__/records-source-detail-route.test.ts --runInBand`
- PASS `npx eslint scripts/check-constraints.ts src/screens/deepspace/dds-wiki-records-screens.tsx`
- PASS `npm run type-check`
- PASS `npm run check:i18n`
- PASS `npm run check:i18n-untranslated`
- PASS `npm run check:lexicon`
- PASS `npm run check:emdash`
- PASS `npm run check:anti-anthro`
- PASS `npm run check:mascot-voice`
- PASS `npm run check:cycles`
- PASS `git diff --check`
- PASS changed-diff sensitive-pattern scan
- LIMITED `npx prettier --check scripts/check-constraints.ts src/screens/deepspace/dds-wiki-records-screens.tsx`: 대상 파일의 기존 전체 포맷 drift로 실패하며, `--write`는 대량 포맷 churn을 만들어 적용하지 않았습니다.

## Links

- HTML report: `agents/codex/outbox/preview/20260814-151858-record-detail-busy-a11y.html`
