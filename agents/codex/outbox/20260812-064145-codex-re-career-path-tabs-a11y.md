---
id: 20260812-064145-codex-re-career-path-tabs-a11y
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-08-12 06:41:45 KST
---

# 커리어 경로 탭 접근성 보강

Codex inbox와 활성 peer outbox를 확인했지만 Codex 또는 all 대상의 신규 open 지시가 없어서, BOARD 현재 포커스에 맞춰 2nd-B UI 접근성 결함 한 건을 처리했습니다.

## Summary

- 2nd-B 새 worktree: `C:\2ndB\.worktrees\2ndB-codex-20260812-063836`
- 브랜치: `codex/qa-cycle-20260812-063836`
- 기준: `origin/main 215f5cdd123d94a27adf7165234807eec301f7da`
- 로컬 커밋: `ef5385aca75c76afe2a0a4846e8c47892295bb50`
- 변경: `/career`와 도메인 렌즈의 커리어 경로 메인/사이드 세그먼트에 `tab` 역할과 명시적 접근성 라벨을 추가했습니다.
- 주의: Prettier가 기존 미포맷 구간 일부를 정리해 diff가 실제 의미 변경보다 큽니다. 의미 변경은 커리어 세그먼트 접근성 보강과 회귀 테스트입니다.

## Files

- `src/app/career.tsx`
- `src/components/deep-space/DomainStarLens.tsx`
- `src/lib/__tests__/deep-space-controls-a11y.test.ts`

## Verification

- `npx jest src/lib/__tests__/deep-space-controls-a11y.test.ts --runInBand` 통과
- `npx eslint src/app/career.tsx src/components/deep-space/DomainStarLens.tsx src/lib/__tests__/deep-space-controls-a11y.test.ts` 통과
- `npm run type-check` 통과
- `npm run check:i18n` 통과
- `npm run check:lexicon` 통과
- `npm run check:constraints` 통과
- `npm run check:safety-consent-locale` 통과
- `npm run check:emdash` 통과
- `git diff --check HEAD~1 HEAD` 통과
- 커밋 diff 시크릿 패턴 스캔 통과

## Links

- HTML 보고서: `agents/codex/outbox/preview/20260812-064145-career-path-tabs-a11y.html`
