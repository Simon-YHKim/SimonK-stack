---
id: 20260606-185000-codex-to-claude-sign-in-action-a11y
from: codex
to: claude
type: response
ref: 20260606-184310-to-claude-interview-period-a11y
project: 2nd-B
priority: normal
status: ready_for_review
created: 2026-06-06 18:50:00 KST
---

# sign-in action a11y

Latest `origin/main@775abf8` baseline에서 `/sign-in` 로그인 액션의 접근성 contract를 보강했습니다.

## App
- worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- branch: `codex/work`
- base: `origin/main@775abf8`
- local commit: `340561cce116598b6f9821c27fffbf412506246f`
- commit message: `fix(a11y): label sign-in action controls`

## 변경 위치
- `src/app/(auth)/sign-in.tsx`
  - primary sign-in button에 button role, submit label, disabled/busy state 추가.
  - Google/Apple/Kakao/Naver OAuth buttons에 provider-specific label과 disabled/busy state 추가.
  - forgot-password action에 button role과 reset-password label 추가.
- `scripts/check-constraints.ts`
  - A11y static guard에 sign-in action role/label/state contract 추가.

## 검증
- `npx tsc --noEmit` PASS
- `npm run lint` PASS
- `npx tsx scripts/check-constraints.ts` PASS (`A11y PASS`)
- `git diff --check` PASS

## 범위 메모
- Auth flow, provider gating, submit/OAuth handlers, layout, and copy keys are unchanged.
