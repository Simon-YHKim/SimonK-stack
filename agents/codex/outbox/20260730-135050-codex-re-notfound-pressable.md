---
id: 20260730-135050-codex-re-notfound-pressable
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-07-30 13:50:50 KST
---

# Not found 목적지 링크 Pressable 정규화 완료

열린 미응답 Codex order는 없어서 BOARD 기준 Codex lane의 UI anti-slop 작업 하나를 수행했다.

2nd-B 새 worktree branch `codex/pressable-sweep-w-20260730-134750`에서 `src/app/+not-found.tsx`의 네 개 목적지 링크를 수정했다. Pressable에는 touch, accessibility, ripple, hitSlop만 두고 내부 `View`가 시각 레이아웃을 담당하게 분리했다.

2nd-B 로컬 커밋: `0c912bd7` (`fix: normalize not found destination pressables`)
푸시: 수행하지 않음.

검증:
- `npx prettier --check "src/app/+not-found.tsx"` 통과
- `npx eslint "src/app/+not-found.tsx"` 통과
- `git diff --check` 통과
- `npm run type-check` 실패: 기존 dependency type resolution 문제로 `madge`, `react-native-google-mobile-ads`, `@react-native-firebase/analytics` 타입 해석이 막힘

위험 분류: 작은 UI touch-surface 수정이라 MoA 추가 검증 요청 대상 아님.

## Links

- `agents/codex/outbox/preview/20260730-135050-notfound-pressable.html`
