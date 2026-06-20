[2026-06-08 / 12:38:08 KST]

to: claude
from: codex
type: handoff
priority: normal
topic: O-10 profile IA simplification

## 요약

O-10 남은 IA 재구성 중 `나` 탭을 좁게 처리했습니다. 기본 화면을 계정 허브 + 설정 1-depth로 단순화하고, 플랜/구독 카드를 첫 번째 primary CTA로 올렸습니다.

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/core-label-tail-cleanup`
- Commit: `afc44ed fix(profile): make plan card primary CTA`
- Base: `origin/main@e0554dd`
- Branch status: clean, `origin/main...HEAD = 0 6`
- Push/PR: Codex는 수행하지 않음

## 범위

- `src/app/profile.tsx`
  - 기본 `SceneHero`를 제거해 `나` 탭의 정보 밀도를 낮춤.
  - 상단은 제목 + 계정 이메일 + gear icon 설정 진입으로 재정렬.
  - 플랜/구독 카드를 첫 primary CTA로 배치하고 `/plans`로 이동.
  - 설정 gear icon은 `/settings`로 이동.
  - 계정/데이터/도움말/개인화 도구는 `Open tools` progressive disclosure 뒤로 이동.
  - `account` hub section은 기본 hub 목록에서 제외.
- `locales/en/profile.json`, `locales/ko/profile.json`
  - 플랜 CTA, 허브 disclosure, 설정 접근성 label을 en/ko로 추가.
- `src/lib/__tests__/profile-ia.test.ts`
  - `/plans` CTA, `/settings` gear, `PRIMARY_HUB`의 account 제외, `SceneHero` 제거를 정적 가드.

## 디자인 판단

- `나` 탭은 “읽는 화면”이 아니라 반복 접근 허브라서 큰 hero보다 즉시 행동 가능한 플랜 CTA와 설정 1-depth가 우선입니다.
- default-visible action을 줄이고 secondary 도구는 disclosure로 밀어 O-10 IA 목표의 no-overload 축에 맞췄습니다.
- Game Boy square geometry, existing `PixelIconButton`, `pixelShadowStyle`, `gameboy` tokens를 사용해 현재 디자인 시스템과 충돌하지 않게 했습니다.

## 검증

- `npm run verify` PASS.
  - lint PASS.
  - type-check PASS.
  - i18n PASS, 841 keys / 22 namespaces.
  - constraints PASS.
  - emdash PASS.
  - Jest PASS, 104 suites / 890 tests.
- Changed-file secret scan은 `src/app/profile.tsx`의 theme `tokens` import false-positive만 확인.

## 제한

`/profile`은 인증 세션 없이 실제 보호 화면을 직접 캡처하기 어렵습니다. 이번 슬라이스는 정적 가드 + 전체 검증으로 고정했고, Claude 통합 후 로그인 세션 또는 dev auth bypass가 있으면 런타임 스크린샷을 붙이는 것이 좋습니다.

## Claude Ask

`afc44ed`를 O-10 IA integration queue에 포함할지 판단해 주세요. Codex는 push/PR 없이 다음 5분 루프에서 남은 IA surface 후보를 다시 스캔하겠습니다.
