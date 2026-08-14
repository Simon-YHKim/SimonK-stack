---
id: 20260814-162953-codex-re-premium-graph-a11y
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-08-14 16:29:53 KST
---

# 프리미엄 그래프 접근성 보강 완료

Codex 폴 사이클에서 새 작업 1건을 수행했습니다. 오래된 open 요청 3건은 이미 응답된 항목으로 판정했고, `origin/main` 기준 새 worktree에서 공용 프리미엄 그래프 요소의 접근성 상태 누락을 보강했습니다.

- Worktree: `C:\2ndB\.worktrees\codex-qa-20260814-162717`
- Branch: `codex/qa-cycle-20260814-162717`
- Base: `origin/main 5ba0cdd905ec3e9e2d5aac0fceb17830c556ab09`
- App commit: `eeac771bb5b8dc38da8c98643185d352cd99ac07`
- Files: `src/components/premium/graph-bits.tsx`, `src/components/premium/__tests__/graph-bits-a11y.test.ts`

## Summary

`ReferenceShardCard`와 `GraphNodeChip`이 `disabled={!onPress}` 상태일 때 `accessibilityState.disabled`를 노출하도록 했습니다. `GraphNodeChip`은 기존 active 시각 상태와 맞춰 `accessibilityState.selected`도 함께 전달합니다.

## Verification

- `npx jest src/components/premium/__tests__/graph-bits-a11y.test.ts --runInBand` 통과
- `npx prettier --check src/components/premium/__tests__/graph-bits-a11y.test.ts` 통과
- `npx eslint src/components/premium/graph-bits.tsx src/components/premium/__tests__/graph-bits-a11y.test.ts` 통과
- `npm run type-check` 통과
- `npm run check:i18n` 통과
- `npm run check:i18n-untranslated` 통과
- `npm run check:lexicon` 통과
- `npm run check:constraints` 통과
- `npm run check:emdash` 통과
- `npm run check:anti-anthro` 통과
- `npm run check:mascot-voice` 통과
- `npm run check:cycles` 통과
- `git diff --check` 통과
- changed-diff sensitive-pattern scan: 매칭 없음

Known note: `npx prettier --check src/components/premium/graph-bits.tsx src/components/premium/__tests__/graph-bits-a11y.test.ts`는 기존 `graph-bits.tsx` 파일 전체 포맷 드리프트 때문에 실패했습니다. 새 테스트 파일은 Prettier 통과했고, 대량 포맷 변경은 하지 않았습니다.

## Section 35 Self-Panel

- 찬성: 공용 프리미엄 그래프 구성요소의 비활성 상태가 보조기술에 드러나 여러 화면에서 같은 누락을 줄입니다.
- 반대: `onPress`가 없을 때 역할도 제거되므로 상태 노출 효과가 제한적일 수 있습니다.
- 판정: 기존 접근성 계약을 좁게 보강하는 실행형 수정이며 설계, 스키마, 보안, 외부 사실, 수학 산출물이 아니므로 MoA verify 요청은 만들지 않았습니다.

## Links

- HTML report: `agents/codex/outbox/preview/20260814-162953-premium-graph-a11y.html`
