---
id: 20260813-192243-codex-re-context-pill-a11y
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-08-13 19:22:43 KST
---

# ContextPill 접근성 라벨 처리

열린 codex 주문은 없었고, stale peer outbox 행은 기존 응답 또는 현 포커스와 맞지 않아 새 UI/anti-slop 작업 1건을 수행했다.

- 2nd-B worktree: `C:\2ndB\.worktrees\codex-qa-20260813-191504`
- 브랜치: `codex/qa-cycle-20260813-191504`
- 기준: `origin/main 5ba0cdd905ec3e9e2d5aac0fceb17830c556ab09`
- 앱 커밋: `12b80762`
- 푸시: 하지 않음

수정:
- `ContextPill` 본문을 `accessible accessibilityRole="text"`로 명시했다.
- 닫기 버튼 라벨을 generic `clearContext`에서 대상 포함 `clearContextFor`로 바꿨다.
- 기존 하드코딩 한국어 접근성 문구를 `common` locale 5종으로 이동했다.
- `context-pill-a11y.test.ts` 소스 스캔 회귀 테스트를 추가했다.
- `PremiumA11yLocaleCopy` constraint 기대값을 새 locale-key 구현에 맞췄다.

검증:
- `npx jest src/lib/__tests__/context-pill-a11y.test.ts --runInBand` 통과
- `npx prettier --check` 변경 파일 통과
- `npx eslint` 변경 파일 통과
- `npm run type-check` 통과
- `npm run check:i18n` 통과
- `npm run check:i18n-untranslated` 통과
- `npm run check:lexicon` 통과
- `git diff --check` 통과
- `npm run check:constraints`: `PremiumA11yLocaleCopy` 통과, 기존 별도 항목 `ArtA11ySemantics` 실패 잔존
- diff 민감정보 패턴 스캔: 실제 secret 없음, constraint 테스트의 일반 단어만 false positive

## Links

- `agents/codex/outbox/preview/20260813-192243-context-pill-a11y.html`
