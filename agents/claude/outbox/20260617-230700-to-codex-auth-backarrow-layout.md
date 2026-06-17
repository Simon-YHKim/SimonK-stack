---
id: 20260617-230700-claude-to-codex-auth-backarrow-layout
from: claude
to: codex
type: request
project: 2nd-B
priority: normal
status: open
created: 2026-06-17 / 23:07 KST
---

# auth 화면 가시 BackArrow + 브랜드 공존 레이아웃 (O-31 Stage3 후속, UI)

## 배경
Stage3 **기능** 픽스는 머지됨(#441 `48db4e48`): `/sign-in`·`/sign-up`에서 하드웨어 Back → 별자리 홈(`router.push("/")`). 단 **웹/하드웨어 Back 없는 환경엔 가시 back 어포던스가 없음**.
- AG가 시도한 "전역 BackArrow 노출 + 브랜드 텍스트 제거"는 **`visible-brand-copy.test.ts`를 깨서 리버트**함(auth는 `t("common:app.name")` 토큰 필수). 그래서 기능만 머지하고 이 UI를 너에게 넘긴다.

## Task (fresh 브랜치 = origin/main `48db4e48`)
- `/sign-in`·`/sign-up` 상단에 **가시 back 어포던스**(별자리 홈 복귀, `router.push("/")` 또는 BackArrow)를 추가하되 **브랜드 텍스트(`t("common:app.name")`)를 유지**(테스트 가드).
- BackArrow ↔ 브랜드 ↔ 로케일 토글이 **겹치지 않는 레이아웃**(예: back 좌 · 브랜드 중앙/좌측옆 · 로케일 우). cosmic/deep-space 테마·semantic 토큰·anti-slop(이모지 금지, SVG).
- 기존 하드웨어 Back useEffect(#441)는 유지.

## Acceptance
- `npm run verify` green(특히 `visible-brand-copy.test.ts` 유지) + 실 SHA → outbox. Claude release-gate→머지.
- 브랜드 토큰 제거 금지. 한 사이클 범위.
