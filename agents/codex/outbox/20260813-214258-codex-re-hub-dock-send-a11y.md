---
id: 20260813-214258-codex-re-hub-dock-send-a11y
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-08-13 21:43:18 KST
---

# 허브 도크 전송 버튼 접근성 상태 수정

새 actionable open order가 없어 codex 레인의 단일 신규 UI 접근성 작업을 수행했습니다.

- 2nd-B worktree: `C:\2ndB\.worktrees\codex-qa-20260813-214033`
- Branch: `codex/qa-cycle-20260813-214033`
- Base: `origin/main 5ba0cdd905ec3e9e2d5aac0fceb17830c556ab09`
- Local app commit: `31f2ed1488023c97531e7da445d433c39bceb8dc`
- Change: `DeepSpaceHubDockScreen`의 세컨비 입력 전송 버튼에 `sendDisabled` 단일 계산값을 도입해 `disabled`, `accessibilityState.disabled`, 비활성 스타일을 같은 상태로 묶고 source-scan 회귀 테스트를 추가했습니다.
- Push: 하지 않음.

## Verification

- `npm test -- --runTestsByPath src/lib/__tests__/deep-space-controls-a11y.test.ts --runInBand` PASS, 1 suite / 9 tests
- `npx eslint src/screens/deepspace/DeepSpaceHubDockScreen.tsx src/lib/__tests__/deep-space-controls-a11y.test.ts` PASS
- `npm run type-check` PASS
- `npm run check:i18n` PASS
- `npm run check:i18n-untranslated` PASS
- `npm run check:lexicon` PASS
- `npm run check:constraints` PASS. Existing `C11 PART` remains unrelated to this diff.
- `npm run check:emdash` PASS
- `git diff --check` PASS
- diff sensitive-pattern scan: no matches
- `npx prettier --check` on the two touched files FAILS, and the same check on `HEAD` originals also fails; this is pre-existing file-level formatting drift, so I avoided broad formatter churn.

## Self-panel

- 가치: 빈 입력 상태에서 실제로 비활성인 전송 버튼을 보조 기술에도 비활성으로 노출합니다.
- 중복: 최근 `.cycle-sigs`의 기록 CTA, 보상 시트, 배경 작업 도크 라벨 작업과 다른 표면입니다.
- 안전: 스키마, 결제, 시크릿, 배포, 파괴 작업 없음. MoA 고위험 검증 대상이 아닙니다.

## Links

- HTML report: `agents/codex/outbox/preview/20260813-214258-hub-dock-send-a11y.html`
