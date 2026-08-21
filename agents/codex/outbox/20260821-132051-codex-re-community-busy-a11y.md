---
id: 20260821-132051-codex-re-community-busy-a11y
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-08-21 13:20:51 KST
---

# 2nd-B 커뮤니티 busy 접근성 보강

이번 Codex 자율 폴 사이클에서 새로 처리할 열린 Codex/all 요청은 없었습니다. Codex 레인에 맞춰 2nd-B 커뮤니티 화면의 진행 상태 접근성 누락 한 건을 수정했습니다.

- worktree: `C:\2ndB\.worktrees\codex-qa-20260821-131736`
- branch: `codex/qa-cycle-20260821-131736`
- base: `origin/main fafb9e0b`
- app commit: `f8c43f8d55980f597e39ce050e9ce4935731af28`
- 변경: 커뮤니티 생성, 1:1 초대, 방 초대, 방 나가기, 메시지 보내기 `MdButton`에 `loading={busy}`를 연결했습니다.
- 테스트: `src/lib/community/__tests__/community-screen-busy-a11y.test.ts`를 추가해 busy 접근성 배선을 회귀 방지합니다.
- push: 하지 않았습니다.

## Verification

- `npm test -- --runTestsByPath src/lib/community/__tests__/community-screen-busy-a11y.test.ts --runInBand` 통과
- `npx prettier --check src/app/community.tsx "src/app/community/[room].tsx" src/lib/community/__tests__/community-screen-busy-a11y.test.ts` 통과
- `npx eslint src/app/community.tsx "src/app/community/[room].tsx" src/lib/community/__tests__/community-screen-busy-a11y.test.ts` 통과
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

## Links

- HTML report: `agents/codex/outbox/preview/20260821-132051-community-busy-a11y.html`
