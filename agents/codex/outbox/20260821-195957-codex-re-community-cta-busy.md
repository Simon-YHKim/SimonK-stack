---
id: 20260821-195957-codex-re-community-cta-busy
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-08-21 20:00:07 KST
---

# 커뮤니티 버튼 진행 상태 보강 완료

이번 Codex poll cycle에서 새로 처리할 열린 Codex 오더는 없었습니다. BOARD의 Codex 레인에 맞춰 2nd-B 커뮤니티 화면의 비동기 CTA 접근성 결함 1건을 처리했습니다.

## Result

- 2nd-B worktree: `C:\2ndB\.worktrees\codex-qa-20260821-195034-native-safety-a11y`
- Branch: `codex/qa-cycle-20260821-195034-native-safety-a11y`
- Local app commit: `21ad4a9f`
- Commit message: `fix: expose community cta busy state`
- Push: 하지 않음

## Changes

- `src/app/community.tsx`: 방 생성과 DM 초대 CTA를 `busyAction`으로 분리하고 각 버튼에 `loading`을 연결했습니다.
- `src/app/community/[room].tsx`: 초대 공유, 방 나가기, 메시지 전송 CTA를 `busyAction`으로 분리하고 각 버튼에 `loading`을 연결했습니다.
- `src/lib/community/__tests__/community-cta-busy-a11y.test.ts`: 커뮤니티 CTA별 busy 접근성 회귀 테스트를 추가했습니다.

## Verification

- `npm test -- --runTestsByPath src/lib/community/__tests__/community-cta-busy-a11y.test.ts src/lib/community/__tests__/chat.test.ts --runInBand` 통과
- `npx eslint src/app/community.tsx "src/app/community/[room].tsx" src/lib/community/__tests__/community-cta-busy-a11y.test.ts` 통과
- `npx prettier --check src/app/community.tsx "src/app/community/[room].tsx" src/lib/community/__tests__/community-cta-busy-a11y.test.ts` 통과
- `npm run type-check` 통과
- i18n, untranslated, lexicon, constraints, emdash, LLM boundary, pixel rules, anti-anthro, mascot voice, asset-exts, cycles, OTA runtime 게이트 통과
- `npm run verify` 통과: 493 suites, 4609 tests passed
- `git diff --check` 통과
- 변경 diff 민감 문자열 검사: 실제 시크릿 없음

## Notes

- 전체 lint에는 기존 unused warning 71건이 유지되었습니다.
- 전체 Jest 종료 시 기존 형태의 worker graceful-exit warning이 있었고 테스트 실패는 없었습니다.
- 허브 branch 전환, 2nd-B push, destructive, cost, secrets 작업은 수행하지 않았습니다.

## Links

- HTML report: `C:\Coding Infra\AI Infra\Communication\agents\codex\outbox\preview\20260821-195957-community-cta-busy.html`
