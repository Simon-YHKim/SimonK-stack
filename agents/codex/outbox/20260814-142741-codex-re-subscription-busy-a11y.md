---
id: 20260814-142741-codex-re-subscription-busy-a11y
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-08-14 14:27:48 KST
---

# 구독 관리 진행 상태 접근성 수정

Codex 단일 폴 사이클에서 `tools/board.ps1 -Me codex`와 활성 `agents/*/outbox` frontmatter 스캔을 수행했고, 열린 `to: codex/all` 오더는 없었습니다. 그래서 BOARD 현재 포커스에 맞춰 2nd-B UI/anti-slop 레인에서 한 건만 처리했습니다.

## Result

- Worktree: `C:\2ndB\.worktrees\codex-qa-20260814-142437`
- Branch: `codex/qa-cycle-20260814-142437`
- Base: `origin/main 5ba0cdd9`
- Local commit: `9815ab99 fix: expose subscription self-service busy state`
- Scope: `/subscription` 구독 관리 화면의 취소와 환불 진입 버튼

## Changes

- `src/app/subscription.tsx`: 취소와 환불 진입 `MdButton`에 `loading={busy}`를 추가했습니다.
- `src/lib/__tests__/subscription-self-service-a11y.test.ts`: 두 버튼이 `disabled={busy}`와 `loading={busy}`를 함께 유지하는지 소스 스캔 회귀 테스트를 추가했습니다.

## Verification

- PASS: `npm test -- --runTestsByPath src/lib/__tests__/subscription-self-service-a11y.test.ts --runInBand`
- PASS: `npx eslint src/app/subscription.tsx src/lib/__tests__/subscription-self-service-a11y.test.ts`
- PASS: `npm run type-check`
- PASS: `npm run check:i18n`
- PASS: `npm run check:i18n-untranslated`
- PASS: `npm run check:lexicon`
- PASS: `npm run check:constraints`
- PASS: `npm run check:emdash`
- PASS: `npm run check:anti-anthro`
- PASS: `npm run check:mascot-voice`
- PASS: `npm run check:cycles`
- PASS: `git diff --check`
- PASS: changed-diff sensitive-pattern scan, no matches
- PARTIAL: 새 테스트 파일 Prettier 통과. `src/app/subscription.tsx`는 `HEAD` 원본도 Prettier stdin 검사에서 실패하는 기존 파일 단위 drift가 있어 전체 파일 포맷은 적용하지 않았습니다.

## Section 35 Self-Panel

- 사용자 관점: 결제 관련 작업 중 상태는 중복 탭과 불안을 줄이기 위해 명확히 전달되어야 합니다.
- 접근성 관점: 기존 `MdButton`의 `loading` 계약을 쓰면 `accessibilityState.busy`가 함께 노출됩니다.
- 엔지니어링 관점: 공유 버튼 컴포넌트 변경 없이 화면 호출부만 수정해 영향 범위를 작게 유지했습니다.

## Links

- HTML report: `agents/codex/outbox/preview/20260814-142741-subscription-busy-a11y.html`

## Constraints

- Hub single-writer respected: wrote only under `agents/codex/`.
- 2nd-B push not performed.
- Hub branch checkout/switch not performed.
- No destructive, cost, or secrets actions.
- MOA cross-verify not requested: this is a low-risk UI accessibility state patch, not a high-risk merge diff/schema/security/math/live-fact deliverable.
