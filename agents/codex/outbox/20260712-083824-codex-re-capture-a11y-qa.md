---
id: 20260712-083824-codex-re-capture-a11y-qa
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-07-12 08:38:24 KST
---

# 캡처 접근성 검토

`claude/feat-capture-a11y` 브랜치(`34aaa66a`, 기준 `origin/main` `90a1a42b`)를 Codex UI/접근성 레인에서 검토했습니다.

## 판정

머지 전 수정 권고입니다. `DeepSpaceViews.tsx`의 비활성 저장 버튼에 추가된 `accessibilityHint={!canSave && !saving ? f("saveHint") : undefined}`는 모든 캡처 모드에 적용되지만, 새 번역 문구는 글 모드의 “무엇을” 입력만 가리킵니다.

예: 링크, 사진, 음성, 할 일 모드에서 저장 버튼이 비활성일 때도 한국어 힌트가 “무엇을 칸을 채우면 담기가 켜져요.”로 읽힙니다. 실제 해제 조건은 각 모드의 URL, 캡션, 음성 메모, 할 일 입력이므로 스크린리더 사용자에게 잘못된 조작 안내가 됩니다.

권장 수정은 `saveHint`를 모드 중립 문구로 바꾸는 것입니다. 예: “내용을 추가하면 담기를 저장할 수 있어요.” 더 세밀하게 하려면 모드별 힌트 키를 분기해야 합니다.

## 확인

- `MdButton`은 `...rest`로 `accessibilityHint`를 `Pressable`에 전달합니다.
- 저장 성공과 저장 실패의 `AccessibilityInfo.announceForAccessibility(...)` 추가는 방향이 맞습니다.
- `npx tsc --noEmit --pretty false`: 통과
- `npm run check:i18n`: 통과
- `npm run check:lexicon`: 통과
- `npm test -- --runInBand src/components/m3/__tests__/m3-primitives.test.ts src/components/deep-space/__tests__/deep-space-style.test.ts src/components/deep-space/__tests__/deep-space-canon-no-legacy.test.ts`: 3개 스위트, 24개 테스트 통과
- `npm test -- --runInBand src/lib/capture/__tests__/fourw.test.ts src/lib/records/__tests__/create-advisor-gate.test.ts`: 2개 스위트, 13개 테스트 통과

## Links

- HTML 보고서: `agents/codex/outbox/preview/20260712-083824-capture-a11y-qa.html`
