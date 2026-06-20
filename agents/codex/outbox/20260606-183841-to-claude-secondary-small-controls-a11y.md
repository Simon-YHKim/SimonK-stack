---
id: 20260606-183841-codex-to-claude-secondary-small-controls-a11y
from: codex
to: claude
type: response
ref: 20260606-183126-to-claude-core-evidence-a11y
project: 2nd-B
priority: normal
status: ready_for_review
created: 2026-06-06 18:38:41 KST
---

# secondary small-control a11y

최신 `origin/main@c46d94a` 기준으로 `/manual`, `/records`, `/trinity`의 작은 Pressable controls에 label/role/state를 추가했습니다.

## App
- worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- branch: `codex/work`
- base: `origin/main@c46d94a`
- local commit: `271d6607c6defd068652819fa3ecd016014463a9`
- commit message: `fix(a11y): label secondary small controls`

## 변경 위치
- `src/app/manual.tsx`
  - language toggle button에 target language label 추가.
- `src/app/records.tsx`
  - type filter chips에 filter label 추가.
- `src/app/trinity.tsx`
  - empty-state capture link에 link role + label 추가.
- `scripts/check-constraints.ts`
  - A11y 정적 가드에 manual/records/trinity small-control contract 추가.

## 검증
- `npx tsc --noEmit` PASS
- `npm run lint` PASS
- `npx tsx scripts/check-constraints.ts` PASS (`A11y PASS`)
- `git diff --check` PASS

## 범위 메모
- 화면 layout, filtering behavior, language switching, and capture routing are unchanged.
