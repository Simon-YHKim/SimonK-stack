---
id: 20260814-080208-codex-re-phone-shell-back-label
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-08-14 08:02:08 KST
---

# PhoneShell 뒤로가기 접근성 라벨 현지화

Codex 자율 폴 사이클에서 새 open 요청은 없었고, BOARD의 codex 레인에 따라 2nd-B UI 접근성 anti-slop 작업을 하나 수행했습니다.

앱 worktree는 `C:\2ndB\.worktrees\codex-qa-20260814-075857`, 브랜치는 `codex/qa-cycle-20260814-075857`입니다. `origin/main 5ba0cdd905ec3e9e2d5aac0fceb17830c556ab09`에서 분기했고, 앱 로컬 커밋은 `5a449f0e5efc5223361c5bbe419bf48018c56736`입니다. 2nd-B push는 하지 않았습니다.

변경은 `src/components/deepspace/shell/PhoneShell.tsx`의 상단 뒤로가기 접근성 라벨을 하드코딩 `"뒤로"`에서 `t("navGraph.drilldown.back")`로 바꾼 것입니다. 회귀 가드로 `src/components/deepspace/shell/__tests__/phone-shell-a11y.test.ts`를 추가했습니다.

검증:

- `npm test -- --runTestsByPath src/components/deepspace/shell/__tests__/phone-shell-a11y.test.ts --runInBand` 통과
- `npx eslint src/components/deepspace/shell/PhoneShell.tsx src/components/deepspace/shell/__tests__/phone-shell-a11y.test.ts` 통과
- `npx prettier --check src/components/deepspace/shell/PhoneShell.tsx src/components/deepspace/shell/__tests__/phone-shell-a11y.test.ts` 통과
- `npm run type-check` 통과
- `npm run check:i18n` 통과
- `npm run check:i18n-untranslated` 통과
- `npm run check:lexicon` 통과
- `npm run check:constraints` exit 0, 기존 `C11 PART` 상태 표시만 있음
- `npm run check:emdash` 통과
- `npm run check:anti-anthro` 통과
- `npm run check:mascot-voice` 통과
- `npm run check:cycles` 통과
- `git diff --check` 통과
- 변경 diff 민감 패턴 스캔은 `theme/tokens` 일반 단어만 잡힌 false positive

## Links

- HTML 보고서: `agents/codex/outbox/preview/20260814-080208-phone-shell-back-label.html`
