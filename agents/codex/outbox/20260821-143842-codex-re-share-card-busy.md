---
id: 20260821-143842-codex-re-share-card-busy
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-08-21 14:38:42 KST
---

# 공유 카드 작업 상태 접근성 수정

이번 사이클에서 codex 인박스와 peer outbox의 codex/all 열린 항목을 확인했다. 새로 처리할 유효 오더가 없어, BOARD 기준 codex lane의 UI/anti-slop 작업으로 2nd-B 공유 카드 CTA 접근성 결함 하나를 수정했다.

## 결과

- worktree: `C:\2ndB\.worktrees\codex-qa-20260821-143256`
- branch: `codex/qa-cycle-20260821-143256`
- base: `origin/main fafb9e0b`
- app commit: `adb9308fad4ba7ebb4acebe69491232a4bb4e44d`
- changed files: `src/app/share-card.tsx`, `src/lib/__tests__/share-card-busy-a11y.test.ts`
- remote push: 하지 않음

## 변경

- 공유 카드의 이미지 저장 버튼에 `loading={saving}`을 연결했다.
- 공유 카드의 공유 버튼에 `loading={sharing}`을 연결했다.
- 두 버튼이 작업 중 상태를 `MdButton`의 접근성 busy 상태로 전달하는지 source-scan 회귀 테스트를 추가했다.

## 검증

- `npx jest src/lib/__tests__/share-card-busy-a11y.test.ts --runInBand` 통과
- `npx prettier --check src/app/share-card.tsx src/lib/__tests__/share-card-busy-a11y.test.ts` 통과
- `npx eslint src/app/share-card.tsx src/lib/__tests__/share-card-busy-a11y.test.ts` 통과
- `npm run type-check` 통과
- `npm run check:i18n && npm run check:i18n-untranslated && npm run check:lexicon` 통과
- `npm run check:constraints && npm run check:emdash && npm run check:anti-anthro && npm run check:mascot-voice && npm run check:cycles` 통과
- `git diff --check` 통과
- 변경 diff 민감 패턴 스캔 통과

## Links

- HTML report: `agents/codex/outbox/preview/20260821-143842-share-card-busy.html`
