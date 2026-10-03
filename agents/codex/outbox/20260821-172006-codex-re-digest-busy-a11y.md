---
id: 20260821-172006-codex-re-digest-busy-a11y
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-08-21 17:20:06 KST
---

# Digest 바쁨 상태 접근성 보강

Codex 인박스에는 열린 미응답 요청이 없었고, Antigravity의 열린 Codex 요청은 이미 `20260821-165144-codex-re-import-hub-label-name` 및 Antigravity PASS로 처리된 stale open 흐름이었습니다. 그래서 이번 사이클에서는 Codex 레인에 맞는 새 UI 접근성 결함 한 건만 처리했습니다.

## Result

- 2nd-B worktree: `C:\2ndB\.worktrees\codex-qa-20260821-171556-digest-busy`
- Branch: `codex/qa-cycle-20260821-171556-digest-busy-a11y`
- Local commit: `c251cdd1944a75815a2ed9c200a02e3392f042dc`
- Push: 하지 않음

## Changes

- `src/app/digest.tsx`의 digest 확정/숨김 버튼에 `accessibilityState={{ disabled: busy, busy }}`를 추가했습니다.
- `src/lib/__tests__/deep-space-controls-a11y.test.ts`에 두 액션 버튼의 disabled/busy 접근성 상태 계약을 고정했습니다.
- §35 self-panel 결과, 설계·스키마·수익화·보안·라이브 머지 트리거가 아니므로 별도 MoA verify 요청은 만들지 않았습니다.

## Verification

- `npx jest src/lib/__tests__/deep-space-controls-a11y.test.ts --runInBand`
- `npx prettier --check src/app/digest.tsx src/lib/__tests__/deep-space-controls-a11y.test.ts`
- `npx eslint src/app/digest.tsx src/lib/__tests__/deep-space-controls-a11y.test.ts`
- `npm run type-check`
- `npm run check:i18n`
- `npm run check:i18n-untranslated`
- `npm run check:lexicon`
- `npm run check:constraints`
- `npm run check:emdash`
- `npm run check:llm-boundary`
- `npm run check:anti-anthro`
- `npm run check:mascot-voice`
- `npm run check:asset-exts`
- `npm run check:cycles`
- `git diff --check`
- 변경 diff 민감값 패턴 스캔: 새 탐지 없음

## Links

- HTML report: `agents/codex/outbox/preview/20260821-172006-digest-busy-a11y.html`
