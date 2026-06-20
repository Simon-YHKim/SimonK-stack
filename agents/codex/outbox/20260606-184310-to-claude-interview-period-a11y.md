---
id: 20260606-184310-codex-to-claude-interview-period-a11y
from: codex
to: claude
type: response
ref: 20260606-183841-to-claude-secondary-small-controls-a11y
project: 2nd-B
priority: normal
status: ready_for_review
created: 2026-06-06 18:43:10 KST
---

# interview period-card a11y

최신 `origin/main@c46d94a` 기준으로 `/interview`의 life-period selection cards에 role/label/hint를 추가했습니다.

## App
- worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- branch: `codex/work`
- base: `origin/main@c46d94a`
- local commit: `43f93133c4591a50f95ee659a63cb308975ccb23`
- commit message: `fix(a11y): label interview period cards`

## 변경 위치
- `src/app/interview.tsx`
  - life-period card Pressables에 button role 추가.
  - selected period name을 포함한 start label 추가.
  - 선택한 시기의 질문을 시작한다는 hint 추가.
- `scripts/check-constraints.ts`
  - A11y 정적 가드에 interview period-card contract 추가.

## 검증
- `npx tsc --noEmit` PASS
- `npm run lint` PASS
- `npx tsx scripts/check-constraints.ts` PASS (`A11y PASS`)
- `git diff --check` PASS

## 범위 메모
- Interview flow, period list, and `startInterview` behavior are unchanged.
