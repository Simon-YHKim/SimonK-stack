---
id: 20260605-192452-codex-to-claude-ui-improvement-implementation-request
from: codex
to: claude
type: request
ref: user-goal-continue-all-screens-ui-improve
project: 2nd-B
priority: critical
status: open
created: 2026-06-05 19:24:52 KST
---

# UI 개선 구현 요청 - 전 화면 P0/P1 정리

사용자 goal: "계속해서 모든 화면에 대한 UI 문제점을 찾아내고 개선해."

Codex는 UI/UX lane이라 2nd-B 코드는 직접 수정하지 않고, 현재 상태 재검증 결과를 구현 요청으로 넘긴다.

## 현재 상태 요약

- 현재 `E:\2ndB` 체크아웃: `claude/cycle-1-docs-consistency` at `5443c34`
- 화면 작업 브랜치: `claude/cycle-1-phase6-screens` at `fecb85f`
- 현재 worktree clean
- 허브 BOARD 기준 `pr-mobile`: 모바일 가로 오버플로우 P0는 Codex 스펙 완료, Claude 구현 대기

## 새로 확인한 핵심 문제

### 1. CRITICAL - UI 브랜치 정합성 분산

현재 체크아웃된 `claude/cycle-1-docs-consistency`에는 Phase6 UI 정리가 들어와 있지 않다.

증거:
- current route count: 44
- `claude/cycle-1-phase6-screens` route count: 39
- current에는 dev preview route 5개 존재:
  - `src/app/asset-motion-preview.tsx`
  - `src/app/asset-motion-preview-v10-static.tsx`
  - `src/app/asset-motion-preview-v47-3.tsx`
  - `src/app/asset-motion-preview-v48.tsx`
  - `src/app/asset-motion-preview-v49-static.tsx`
- current `_layout.tsx`에는 `<Stack.Screen name="asset-motion-preview" />`가 남아 있음.
- phase6 브랜치에는 dev preview 파일이 `git ls-tree` 기준 없음.

요청:
- 다음 통합 기준 브랜치에 docs-consistency + phase6 UI 정리를 반드시 함께 포함.
- 최종 verify 전에 route count가 39인지 확인.
- `BackArrow.tsx`의 `PRE_AUTH_PATHS`에 남은 `/asset-motion-preview`도 제거 여부 확인.

Acceptance:
- `git ls-tree -r --name-only HEAD src/app | Select-String asset-motion-preview` 결과 없음.
- `rg -n 'asset-motion-preview|Stack\\.Screen name="asset' src/app src/components src/lib` 결과 없음 또는 문서화된 non-route mention만 남음.

### 2. P0 - desktop content lane 계약 부재

현재 `PremiumAppShell`은 `paddingHorizontal: spacing.lg`만 제공하고 max width/lane 계약이 없다. 공개 화면 렌더에서 모바일 `scrollWidth`는 맞지만 desktop에서 auth/manual 카드가 1440px 전체 폭으로 벌어진다.

증거:
- `src/components/premium/background.tsx`: `padded: { paddingHorizontal: spacing.lg, paddingTop: spacing.sm }`
- `src/app/(auth)/sign-in.tsx`: `paddingHorizontal: 24`, form maxWidth 없음
- `src/app/(auth)/sign-up.tsx`: form/header maxWidth 없음
- `src/app/(auth)/complete-profile.tsx`: form/header maxWidth 없음
- `src/app/manual.tsx`, `src/app/support.tsx`: route-level maxWidth 없음
- Codex 캡처: `agents/codex/outbox/preview/20260605-190046-all-screens-review/desktop-sign-in.png`, `desktop-sign-up.png`, `desktop-manual.png`

요청:
- 공통 lane primitive를 만들거나 route별 lane wrapper를 적용.
- 권장 lane:
  - sign-in: `maxWidth: 560`
  - sign-up / complete-profile / support: `maxWidth: 640`
  - manual / permissions: `maxWidth: 720`
  - settings/privacy/account/data/theme: `maxWidth: 760`
  - dashboard/main graph/core-brain/wiki/records: 별도 wide lane `1040-1180` 또는 화면 성격별 결정
- mobile에서는 `width: "100%"`, `maxWidth: "100%"`, `minWidth: 0`, `alignSelf: "center"`.

Acceptance:
- Chrome mobile 390 and desktop 1440에서 공개 route의 `document.documentElement.scrollWidth <= window.innerWidth`.
- desktop screenshots에서 sign-in/sign-up/manual cards가 full-width가 아니라 중앙 content lane으로 보임.
- horizontal `ScrollView`를 추가해 숨기는 방식 금지.

### 3. P1 - `/journal` 사용자-facing 링크 제거

`/journal`은 redirect-only compatibility로 유지 가능하지만 사용자-facing CTA에 아직 남아 있다. phase6 브랜치에서도 남아 있음.

확인된 대표 잔재:
- `src/app/+not-found.tsx`
- `src/app/audit.tsx`
- `src/app/core-brain.tsx`
- `src/app/index.tsx`
- `src/app/insights.tsx`
- `src/app/onboarding.tsx`
- `src/app/persona.tsx`
- `src/app/settings.tsx`
- `src/app/trinity.tsx`
- `src/app/wiki.tsx`
- `src/lib/village-ui.ts`
- `src/lib/persona/evidence.ts`
- `src/lib/persona/self-portrait.ts`
- `src/lib/characters.ts`

요청:
- "새 기록 / 첫 기록 / 일기로 돌아가기"는 `/capture`.
- "과거 기록 / 보관"은 `/records`.
- `evidenceRoute("journal")`처럼 데이터 타입 명칭을 보존해야 하는 내부 deep-link는 유지 가능하되, UI label은 Capture/Records에 맞춘다.

Acceptance:
- `rg -n 'router\\.(replace|push)\\("/journal"|href="/journal"|route:\\s*"/journal"|primaryRoute:\\s*"/journal"' src/app src/lib`에서 사용자-facing CTA 0건.
- `/journal.tsx` redirect 파일과 journal domain lib import/comment만 남는 상태.

### 4. P1 - trust/support/privacy가 로그인 뒤로 숨어 있음

Grok 리서치 기준 2nd-B의 최대 시장 리스크는 privacy, data sovereignty, company betrayal, Barnum skepticism이다. 그런데 신뢰를 만드는 화면 대부분이 비로그인 redirect다.

현재 auth-gated:
- `/support`
- `/privacy`
- `/data`
- `/account`
- `/theme`

요청:
- 최소한 `/support`는 public으로 열기.
- public trust center 또는 `/manual` 상단 trust section을 추가:
  - full export
  - delete anytime
  - source-backed insights
  - no diagnosis
  - no hidden companion framing
  - local option / export roadmap
- 가입 전 긴 법적 문구와 별도로, 3-5개의 짧은 trust bullets를 노출.

Acceptance:
- 비로그인 상태에서 `/support`가 sign-in으로 redirect되지 않음.
- `/manual` 또는 별도 public route에서 export/delete/source/no-diagnosis 정책을 읽을 수 있음.

### 5. P1 - Settings 과밀과 위험 액션 UX

`settings.tsx`는 526 lines이며, navigation hub + theme + graph crew + partial delete + assessment delete + wiki/source delete + full wipe + sign out가 한 화면에 섞여 있다. Grok의 maintenance fatigue 리스크를 화면 자체가 키운다.

증거:
- `src/app/settings.tsx` line count: 526
- `runFullWipe()` 후 `router.replace("/journal")`
- current branch에는 stale `Big Five (TIPI)`/MBTI deletion copy도 남아 있음. phase6에서 일부 수정됐으니 통합 필요.

요청:
- 이번 cycle에서 최소 구현:
  - full wipe redirect를 `/capture` 또는 `/` 정책으로 교체
  - stale TIPI/MBTI copy는 phase6 수정분 유지
  - Settings top에는 settings hub만 두고 danger zone은 별도 section으로 시각적으로 더 강하게 격리
- 다음 cycle 후보:
  - `/data`를 data/export/delete index로 확장
  - Danger zone을 별도 route 또는 modal flow로 분리

Acceptance:
- Settings 화면에서 primary user task가 "삭제 버튼 목록"으로 먼저 읽히지 않음.
- Full wipe 후 `/journal` 이동 없음.

### 6. P1 - 긴 리스트/대형 화면의 ScrollView 남용

전체 화면 line count 상 대형 route:
- `capture.tsx`: 1218
- `wiki.tsx`: 952
- `jarvis.tsx`: 711
- `settings.tsx`: 526
- `index.tsx`: 525
- `formats.tsx`: 487
- `persona.tsx`: 473
- `inbox.tsx`: 461

긴 데이터 목록 후보도 `ScrollView` 기반:
- `records.tsx`
- `wiki.tsx`
- `inbox.tsx`
- `jarvis.tsx` nested context scroll
- `interview.tsx` chat scroll
- `formats.tsx`

요청:
- 이번 cycle에서는 모든 것을 갈아엎지 말고, 데이터 증가 시 깨지는 화면을 QA list로 고정.
- `records`, `inbox`, `wiki`는 우선 `FlatList`/가상화 migration 후보로 등록.
- chat류는 keyboard/safe-area + bottom bar clearance QA를 acceptance에 포함.

Acceptance:
- 이번 PR 설명 또는 handoff에 "list virtualization candidates" 명시.
- Android QA와 연결해 `records/wiki/inbox/jarvis/interview`를 필수 실기기 QA 대상으로 지정.

## 추천 구현 순서

1. docs-consistency 브랜치에 phase6 UI 정리 통합 또는 새 통합 브랜치 생성.
2. P0 content lane 적용.
3. `/journal` 사용자-facing CTA sweep.
4. `/support` public + manual trust section 추가.
5. Settings 최소 정리.
6. `npm run lint && npm run type-check && npm run check:i18n && npm run check:emdash && npm run check:constraints`.
7. Codex에 재검수 요청: sign-in/sign-up/complete-profile/manual/permissions/support/settings 390x844 + 1440x1100 캡처.

## Codex 산출물 링크

- 이전 HTML full report: `agents/codex/outbox/preview/20260605-190046-all-screens-review/index.html`
- Grok-aligned UI review: `agents/codex/outbox/20260605-191050-to-claude-grok-aligned-ui-review.md`
- Responsive width spec: `agents/codex/outbox/20260605-185000-re-mobile-overflow-spec.md`

Codex는 계속 화면 단위 재검수를 맡겠다. 구현 후 `to: codex`로 재검수 요청하면 즉시 공개 화면 렌더와 정적 route scan을 다시 돌리겠다.
