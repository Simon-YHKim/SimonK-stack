---
id: 20260814-113109-codex-re-hub-dock-screen-a11y
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-08-14 11:31:09 KST
---

# 딥스페이스 허브 독 화면 접근성 라벨 지역화

이번 사이클에서 codex inbox와 peer outbox의 codex/all open 후보를 확인했고, 새 actionable 요청은 없었습니다. 그래서 codex 레인의 단일 작업으로 2nd-B UI 접근성 결함 하나를 처리했습니다.

2nd-B 별도 worktree `C:\2ndB\.worktrees\codex-qa-20260814-112715`, 브랜치 `codex/qa-cycle-20260814-112715`에서 `src/screens/deepspace/DeepSpaceHubDockScreen.tsx`의 한국어 고정 접근성 라벨을 `deepspace` locale 키로 옮겼습니다. `en/ko/es/pt/id` locale에 `hubDockScreen` 키를 추가했고, `src/lib/__tests__/deep-space-hub-dock-screen-a11y.test.ts`로 한국어 하드코딩 라벨 재유입을 막았습니다.

앱 로컬 커밋은 `94ce596ae3cc237cee7b3941b72a7fa4823cfb26`입니다. 2nd-B 원격에는 푸시하지 않았습니다.

검증:
- `npx jest src/lib/__tests__/deep-space-hub-dock-screen-a11y.test.ts --runInBand`
- `npx prettier --check` 대상 파일
- `npx eslint` 대상 파일
- `npm run type-check`
- `npm run check:i18n`
- `npm run check:i18n-untranslated`
- `npm run check:emdash`
- `npm run check:lexicon`
- `npm run check:constraints`
- `npm run check:cycles`
- 변경 diff 민감 패턴 스캔: `@/theme/tokens` false positive만 확인

주의: 대상 화면 파일은 기존 포맷 편차가 커서 Prettier 적용 후 `src/screens/deepspace/DeepSpaceHubDockScreen.tsx` diff가 크게 보입니다. 기능 변경 범위는 접근성 라벨 지역화와 회귀 테스트입니다.

## Links

- HTML 보고서: `agents/codex/outbox/preview/20260814-113109-hub-dock-screen-a11y.html`
