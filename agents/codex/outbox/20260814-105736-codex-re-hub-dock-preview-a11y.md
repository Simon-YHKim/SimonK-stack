---
id: 20260814-105736-codex-re-hub-dock-preview-a11y
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-08-14 10:57:36 KST
---

# 허브 독 미리보기 접근성 라벨 지역화

codex 인박스와 peer outbox의 actionable codex/all 요청은 없었습니다. 이번 사이클에서는 2nd-B UI anti-slop 레인에서 한 건만 처리했습니다.

2nd-B 별도 worktree `C:\2ndB\.worktrees\codex-qa-20260814-105309`, 브랜치 `codex/qa-cycle-20260814-105309`에서 `DeepSpaceHubDockScreen`의 미리보기 전용 스크린 리더 라벨을 `deepspace.hubDockPreview` 번역 키로 옮겼습니다. 한국어, 영어, 스페인어, 포르투갈어, 인도네시아어 locale에 같은 키를 추가했고, 하드코딩 한국어 `accessibilityLabel` 재유입을 막는 source-scan guard를 추가했습니다.

앱 로컬 커밋은 `5cce1bb90c7b6811f9bc9bfc84bc50dfd1916632`입니다. 2nd-B 원격 push는 하지 않았습니다.

검증:

- `npx jest src/lib/__tests__/deep-space-shell-a11y.test.ts --runInBand`
- `npm run check:i18n`
- `npm run check:i18n-untranslated`
- `npm run type-check`
- `npx eslint src/screens/deepspace/DeepSpaceHubDockScreen.tsx src/lib/__tests__/deep-space-shell-a11y.test.ts`
- `npm run check:emdash`
- `npm run check:lexicon`
- `npm run check:constraints`
- `npm run check:anti-anthro`
- `npm run check:mascot-voice`
- `npm run check:cycles`
- `git diff --check`
- 변경 diff 민감정보 패턴 스캔. `theme/tokens` 단어만 false positive로 잡혔습니다.

주의:

- `DeepSpaceHubDockScreen.tsx`는 기존 압축 JSX를 Prettier가 펼쳐 diff 줄 수가 큽니다. 의미 변경은 접근성 라벨 번역 키 배선과 회귀 테스트에 한정됩니다.

## Links

- HTML 보고서: `agents/codex/outbox/preview/20260814-105736-hub-dock-preview-a11y.html`
