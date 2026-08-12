---
id: 20260812-202709-codex-re-career-drilldown-copy
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-08-12 20:27:09 KST
---

# 커리어 더 파고들기 카피 수정

codex inbox에는 actionable open order가 없었고, peer outbox의 codex/all open 항목은 stale 또는 이미 답변된 항목으로 판단했다. 이번 사이클은 2nd-B UI/i18n anti-slop 한 건만 처리했다.

로컬 2nd-B worktree `C:\2ndB\.worktrees\codex-qa-20260812-202119`, branch `codex/qa-cycle-20260812-202119`에서 `/career`의 `Drill Down` 하드코딩 CTA를 locale 기반 `careerDrilldown.submit` 카피로 교체했다. 한국어 제출 카피는 `세컨비와 더 파고들기`로 맞췄고, source-scan 회귀 테스트를 추가했다.

앱 로컬 커밋: `f495cad6 fix: localize career drilldown entry`

검증:

- `npx prettier --check src/app/career.tsx src/app/__tests__/career-copy-audit.test.ts locales/ko/deepspace.json`
- `npx jest src/app/__tests__/career-copy-audit.test.ts --runInBand`
- `npx eslint src/app/career.tsx src/app/__tests__/career-copy-audit.test.ts`
- `npm run type-check`
- `npm run check:i18n`
- `npm run check:lexicon`
- `npm run check:constraints`
- `npm run check:emdash`
- `npm run check:cycles`
- 선택 diff 기준 `git diff --check` 및 민감정보 패턴 스캔

2nd-B push, 허브 브랜치 전환, 파괴적 작업, 비용 발생 작업, 민감정보 작업은 하지 않았다.

## Links

- HTML 보고서: `agents/codex/outbox/preview/20260812-202709-career-drilldown-copy.html`
