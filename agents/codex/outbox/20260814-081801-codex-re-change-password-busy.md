---
id: 20260814-081801-codex-re-change-password-busy
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-08-14T08:18:09+09:00
---

# 비밀번호 변경 제출 상태 접근성 보강

열린 codex 주문이 없어 이번 한 주기는 2nd-B UI 접근성 레인에서 새 결함 하나를 처리했습니다.

- 기준: `origin/main 5ba0cdd905ec3e9e2d5aac0fceb17830c556ab09`
- worktree: `C:\2ndB\.worktrees\codex-qa-20260814-081518`
- branch: `codex/qa-cycle-20260814-081518`
- local app commit: `b81671e76c011462b33434fbd05808e5f26123d8`
- push: 하지 않음

## 변경

- `src/app/change-password.tsx`: 비밀번호 변경 제출 버튼에 `loading={form.submitting}`을 연결해 제출 중 상태가 shared `PremiumButton`의 `accessibilityState.busy`로 전달되게 했습니다.
- `src/lib/__tests__/change-password-a11y.test.ts`: 제출 문구, `loading`, `disabled` 연결을 고정하는 source-scan guard를 추가했습니다.

## 검증

- `npm test -- --runTestsByPath src/lib/__tests__/change-password-a11y.test.ts --runInBand`
- `npx prettier --check src/app/change-password.tsx src/lib/__tests__/change-password-a11y.test.ts`
- `npx eslint src/app/change-password.tsx src/lib/__tests__/change-password-a11y.test.ts`
- `npm run type-check`
- `npm run check:i18n`
- `npm run check:i18n-untranslated`
- `npm run check:lexicon`
- `npm run check:constraints`
- `npm run check:emdash`
- `npm run check:anti-anthro`
- `npm run check:mascot-voice`
- `npm run check:cycles`
- `git diff --check`
- 변경 diff 민감값 패턴 스캔

## Links

- HTML report: `agents/codex/outbox/preview/20260814-081801-change-password-busy.html`
