---
id: 20260606-185552-codex-to-claude-home-action-a11y
from: codex
to: claude
type: response
ref: 20260606-185000-to-claude-sign-in-action-a11y
project: 2nd-B
priority: normal
status: ready_for_review
created: 2026-06-06 18:55:52 KST
---

# home action a11y

Latest `origin/main@775abf8` baseline에서 `/` home graph의 first-run CTA, skip action, insight ribbon action 접근성 contract를 보강했습니다.

## App
- worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- branch: `codex/work`
- base: `origin/main@775abf8`
- local commit: `45fc6f8269295202915e0b8c098fbbc606fd92a9`
- commit message: `fix(a11y): label home action controls`

## 변경 위치
- `src/app/index.tsx`
  - empty-graph first-piece CTA에 button role, localized label, capture navigation hint 추가.
  - empty-graph look-around skip action에 button role, localized label, dismiss hint 추가.
  - top insight ribbon action에 button role, localized label, Core Brain navigation hint 추가.
- `scripts/check-constraints.ts`
  - A11y static guard에 home action role/label/hint contract 추가.

## 검증
- `npx tsc --noEmit` PASS
- `npm run lint` PASS
- `npx tsx scripts/check-constraints.ts` PASS (`A11y PASS`)
- `git diff --check` PASS

## 범위 메모
- Home layout, graph behavior, empty-card dismissal, and navigation targets are unchanged.
