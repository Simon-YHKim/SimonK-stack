---
id: 20260730-205113-codex-re-hub-dock-glyph-qa
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-07-30 20:51:13 KST
---

# Codex 허브 도크 장식 기호 QA

이번 cycle은 새 UI 발견 패치를 늘리지 않고, 기존 미머지 후보 `1c24d4f3`를 최신 `origin/main` 기준 QA 브랜치에 다시 적용해 검증했습니다.

## 결과

- QA worktree: `C:\2ndB\.worktrees\codex\qa-hub-dock-glyphs-20260730-204821`
- QA branch: `codex/qa-hub-dock-glyphs-20260730-204821`
- 적용 결과 commit: `7e8bc35d`
- 원본 후보 commit: `1c24d4f3`
- 변경 파일: `src/components/deepspace/DeepSpaceHubDock.tsx`, `src/screens/deepspace/DeepSpaceHubDockScreen.tsx`
- push: 하지 않음

## 검증

- `git cherry-pick 1c24d4f3`: 충돌 없이 적용
- 원본 cherry-pick 직후 `npx prettier --check ...`: 실패. 변경 파일 2개 포맷 이탈
- 포맷 보정 후 `git diff --check origin/main..HEAD`: 통과
- 포맷 보정 후 `npx prettier --check src/components/deepspace/DeepSpaceHubDock.tsx src/screens/deepspace/DeepSpaceHubDockScreen.tsx`: 통과
- `npx eslint src/components/deepspace/DeepSpaceHubDock.tsx src/screens/deepspace/DeepSpaceHubDockScreen.tsx`: 통과
- `npm run check:emdash`: 통과
- `npm run check:lexicon`: 통과
- `npm run type-check`: 실패. 기존 `madge`, `react-native-google-mobile-ads`, `@react-native-firebase/analytics` 타입 해석 문제와 `scripts/check-require-cycles.ts` implicit any에서 중단

## 판정

`7e8bc35d`는 최신 `origin/main`에 충돌 없이 적용되고 변경 파일 단위 lint와 카피 가드를 통과했습니다. 다만 Prettier 통과를 위해 `DeepSpaceHubDockScreen.tsx` 전반의 포맷 정리가 함께 들어가 diff가 커졌습니다. Claude 병합 게이트에서는 기능 변경 후보와 포맷 churn을 분리할지 판단하는 것이 좋습니다.

## 35 self-panel

- 찬성: 장식용 이모지 제거 후보가 최신 main에 적용 가능하다는 근거가 생겼고, 파일 단위 검증이 통과했습니다.
- 반대: Prettier 보정 때문에 실제 의미 변경보다 diff가 커져 리뷰 비용이 증가했습니다.
- 대안: Claude가 원본 `1c24d4f3`를 받되, 별도 포맷 커밋으로 분리하거나 화면 파일 전체 포맷 정리를 선행한 뒤 재적용할 수 있습니다.
- 판정: 병합 후보로 유지하되, 바로 머지보다는 포맷 churn 분리 여부를 게이트에서 확인해야 합니다.

## Links

- HTML report: `agents/codex/outbox/preview/20260730-205113-hub-dock-glyph-qa.html`
