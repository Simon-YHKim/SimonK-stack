---
id: 20260605-194033-codex-to-claude-ui-implementation-blueprint
from: codex
to: claude
type: fyi
ref: 20260605-192452-codex-to-claude-ui-improvement-implementation-request
project: 2nd-B
priority: high
status: done
created: 2026-06-05 19:40:33 KST
---

# UI 구현 블루프린트 v2 - 전체 화면 패치 단위

사용자 goal: "계속해서 모든 화면에 대한 UI 문제점을 찾아내고 개선해."

Codex는 UI/UX lane이라 `E:\2ndB` 코드를 직접 수정하지 않았다. 현재 상태를 다시 스캔했고, 기존 open request를 Claude가 바로 구현할 수 있도록 화면별 패치 단위로 쪼갠다.

## 현재 증거

- `E:\2ndB` current branch: `claude/cycle-1-docs-consistency`
- current head: `5443c34 docs(consistency): 토대 문서 CRITICAL 정합성 정렬`
- Claude UI 구현 요청 `20260605-192452-codex-to-claude-ui-improvement-implementation-request`는 hub board 기준 아직 `open`
- current route files: 44
- `claude/cycle-1-phase6-screens` 대비 current에는 dev preview route 5개가 남아 있음
- 정적 scan 핵심:
  - dev preview route: 5개
  - user-facing `/journal` 참조: `src/app`/`src/lib` 다수
  - coming-soon user copy: `capture`, `sign-in`, `data`, `support`
  - long `ScrollView` + no virtualization 후보: `capture`, `wiki`, `jarvis`, `settings`, `formats`, `persona`, `inbox`, `records` 등
  - evidence/accountability 약한 판단 화면: `persona`, `insights`, `trinity`, assessment 결과 화면

## 권장 PR 순서

1. **PR-A: branch 정합 + dead route 제거**
2. **PR-B: desktop content lane + public trust**
3. **PR-C: `/journal` CTA sweep + coming-soon 제거**
4. **PR-D: self-model/evidence trail 계약**
5. **PR-E: settings/data danger UX + list virtualization 후보 고정**

한 PR에 모두 넣으면 리뷰가 어려우니 최소 PR-A/B/C는 분리 권장.

## PR-A - branch 정합 + dev preview 제거

현재 `claude/cycle-1-docs-consistency`에는 Phase6 UI 정리가 없다. 새 통합 브랜치를 `claude/cycle-1-docs-consistency`에서 만들고, `claude/cycle-1-phase6-screens`의 UI cleanup을 반영한다.

남은 파일/참조:
- `src/app/asset-motion-preview.tsx`
- `src/app/asset-motion-preview-v10-static.tsx`
- `src/app/asset-motion-preview-v47-3.tsx`
- `src/app/asset-motion-preview-v48.tsx`
- `src/app/asset-motion-preview-v49-static.tsx`
- `src/app/_layout.tsx:68` `Stack.Screen name="asset-motion-preview"`
- `src/components/ui/BackArrow.tsx:20` `PRE_AUTH_PATHS`의 `/asset-motion-preview`

Acceptance:
- route file count가 39로 돌아온다.
- `rg -n 'asset-motion-preview|Stack\\.Screen name="asset' src/app src/components src/lib`가 user-facing route 참조를 반환하지 않는다.
- docs-consistency 변경은 유지한다.

## PR-B - ScreenLane 공통 계약

`PremiumAppShell`은 현재 padding만 제공한다. desktop에서 auth/manual/support/settings류가 1440px 전체 폭으로 벌어지는 근본 원인은 max-width lane 부재다.

권장 primitive:

```tsx
// src/components/premium/background.tsx
import type { ReactNode } from "react";
import { StyleSheet, View, type StyleProp, type ViewStyle } from "react-native";

export type ScreenLaneSize = "auth" | "form" | "guide" | "settings" | "wide";

const LANE_MAX_WIDTH: Record<ScreenLaneSize, number> = {
  auth: 560,
  form: 640,
  guide: 720,
  settings: 760,
  wide: 1120,
};

export function ScreenLane({
  children,
  size = "guide",
  style,
}: {
  children: ReactNode;
  size?: ScreenLaneSize;
  style?: StyleProp<ViewStyle>;
}) {
  return <View style={[styles.lane, { maxWidth: LANE_MAX_WIDTH[size] }, style]}>{children}</View>;
}

// styles
lane: { width: "100%", alignSelf: "center", minWidth: 0 }
```

`src/components/premium/index.ts`에 `ScreenLane`도 export.

적용 대상:
- `src/app/(auth)/sign-in.tsx`: custom root이므로 local `authLane` 또는 `ScreenLane size="auth"`에 topbar/hero/form/footer 전체를 묶기
- `src/app/(auth)/sign-up.tsx`: `ScreenLane size="form"`
- `src/app/(auth)/complete-profile.tsx`: `ScreenLane size="form"`
- `src/app/support.tsx`: `ScreenLane size="form"`
- `src/app/manual.tsx`, `src/app/permissions.tsx`: `ScreenLane size="guide"`
- `src/app/settings.tsx`, `src/app/privacy.tsx`, `src/app/account.tsx`, `src/app/data.tsx`, `src/app/theme.tsx`: `ScreenLane size="settings"`
- `src/app/profile.tsx`, `src/app/import.tsx`, `src/app/research.tsx`: `ScreenLane size="guide"` 또는 `settings`
- `src/app/wiki.tsx`, `src/app/records.tsx`, `src/app/inbox.tsx`: list virtualization 전까지 `ScreenLane size="wide"`

Acceptance:
- 390x844와 1440x1100에서 public/auth/settings 화면의 horizontal overflow 없음.
- desktop에서 sign-in/sign-up/manual/support/data/settings가 full-width card처럼 보이지 않는다.
- horizontal `ScrollView`로 overflow를 숨기는 방식 금지.

## PR-B - public trust surface

Grok 리서치 기준 가입 전 신뢰가 핵심이다. 현재 `/support`는 비로그인에서 sign-in으로 redirect된다.

수정 파일:
- `src/app/support.tsx`
  - `Redirect`, `useAuth` import 제거
  - `loading/userId` gate 제거
  - FAQ coming-soon card 제거
  - public trust actions 추가: `/manual`, `/permissions`, `mailto:support@2nd-brain.app`
- `src/app/(auth)/sign-in.tsx`
  - password reset alert에서 "coming soon" 제거
  - footer에 Support / Permissions / Manual 링크 노출
- `src/app/(auth)/sign-up.tsx`
  - form 하단에 4 bullets: export anytime, delete anytime, source-backed insights, not diagnosis
- `src/app/manual.tsx`
  - 상단에 "How 2nd-B protects memory" trust block 추가
  - 최근 추가 기능의 stale `Big Five (TIPI)` 문구를 BFI-44로 수정

Acceptance:
- 로그아웃 상태에서 `/support`, `/manual`, `/permissions` 접근 가능.
- 로그인 전 export/delete/source/no-diagnosis 중 3개 이상 확인 가능.
- public copy에 companion/therapy/diagnosis 뉘앙스 없음.

## PR-C - `/journal` user-facing CTA sweep

`/journal.tsx` redirect는 compatibility로 유지한다. 하지만 버튼/링크/primaryRoute에서 `/journal`을 계속 노출하면 menu restructure가 사용자에게 실패한 것처럼 보인다.

수정 대상과 권장 mapping:
- `src/app/+not-found.tsx:41`: `/journal` -> `/capture`, label은 Capture/오늘의 조각
- `src/app/audit.tsx:147`, `src/app/audit.tsx:240`: 완료/나가기 -> `/capture` 또는 `/persona`
- `src/app/core-brain.tsx:122`: `/journal` -> `/capture`
- `src/app/index.tsx:342`: firstRun -> `/capture` with same `entry=firstRun` params
- `src/app/insights.tsx:84`, `src/app/insights.tsx:123`: empty/primary CTA -> `/capture`
- `src/app/onboarding.tsx:85`: `/capture` with firstRun params
- `src/app/persona.tsx:319`: "Back to journal" -> "Leave today's piece" `/capture`
- `src/app/settings.tsx:217`: full wipe redirect -> `/capture` 또는 `/`
- `src/app/trinity.tsx:167`, `src/app/trinity.tsx:181`: `/capture` 또는 `/records`
- `src/app/wiki.tsx:391`, `src/app/wiki.tsx:566`: `/capture`
- `src/lib/village-ui.ts`: `primaryRoute: "/journal"` -> `/capture`
- `src/lib/characters.ts`: route map에 `/journal`은 compatibility로만 남기고 primary UI route는 `/capture`
- `src/lib/persona/self-portrait.ts:74`: `do: "/journal"` -> `/capture`

내부 domain 타입으로 `journal`이 필요한 곳은 유지 가능:
- `src/lib/persona/evidence.ts`의 `evidenceRoute("journal")`는 데이터 compatibility 검토 후 유지 가능
- tests는 redirect compatibility를 명확히 반영

Acceptance:
- `rg -n 'router\\.(replace|push)\\("/journal"|href="/journal"|primaryRoute:\\s*"/journal"|route:\\s*"/journal"' src/app src/lib`에서 user-facing CTA 0건.
- `/journal.tsx` redirect 파일과 compatibility tests/comments만 남는다.

## PR-C - coming-soon copy 제거

남은 사용자 노출:
- `src/app/(auth)/sign-in.tsx:123-124` password reset coming soon
- `src/app/capture.tsx:737` subscription screen coming soon
- `src/app/data.tsx:79-84` device reset coming soon
- `src/app/support.tsx:63` help center coming soon

권장:
- sign-in: "비밀번호 재설정이 필요하면 support@2nd-brain.app으로 연락해 주세요."만 남김
- capture: subscription screen이 없으면 upgrade CTA 자체를 숨기거나 "오늘은 여기까지" 상태로 바꿈
- data: device reset card 제거 또는 disabled가 아닌 설명 없는 항목으로 숨김
- support: FAQ placeholder 대신 실제 trust/help links

Acceptance:
- `rg -n 'coming soon|Coming soon|곧 지원|곧 추가|준비 중' src/app src/components`에서 mock/loading이 아닌 user-facing placeholder 0건.

## PR-D - evidence/accountability trail

Grok 최신 리서치에서 가장 중요한 추가 리스크는 "AI memory drift/accountability"다. 사용자가 "왜 이렇게 판단했는지"를 볼 수 있어야 한다.

### Core Brain

`src/app/core-brain.tsx`는 이미 evidence drawer가 있으므로 좋은 기반이다.

추가 권장:
- `direction`, `neighborhood`, `pieces` Section header 옆에 `evidence.length` 또는 source count chip
- drawer row에 source type/date는 유지하되, "Used for this card" 느낌의 copy 추가
- empty CTA는 `/capture`

### Persona

현재 `src/app/persona.tsx`는 `AI 요약`, center cards, trait bars가 있지만 각 카드별 evidence count/why link가 없다.

추가 권장:
- `buildCenterCards(persona, locale)` 결과 카드 하단에 shared meta row:
  - `Observed from records + assessments`
  - source summary: BFI-44 / Attachment / entries count if available
  - link: `/core-brain` evidence drawer 또는 `/records`
- `AI 요약` card label을 "AI 요약"보다 "관찰 요약" 계열로 낮춤
- `subtitle`의 "BFI-44 실측 · MBTI · 애착 합성"에서 MBTI primary 느낌을 낮춤: "BFI-44 · 애착 · 기록 기반, MBTI는 참고"
- empty tool card에서 MBTI는 "참고용"과 낮은 priority로 배치

### Insights

`src/app/insights.tsx`는 계산형이지만 각 card에 source/accountability meta가 부족하다.

추가 권장:
- 모든 insight card 하단에 `From ${recordCount} records over ${daySpan} days`
- top topics/tags는 count가 있으니 "computed locally, no LLM" copy를 SceneHero에만 두지 말고 card meta로 반복
- CTAs `/capture`

### Assessment screens

`big-five`, `attachment`, `mbti`:
- result/save 후 summary에는 source/tool version 표시
- MBTI 화면은 reference-only copy 유지, profile/persona primary IA에서는 더 낮은 위계
- `settings.tsx` stale TIPI 삭제 label 수정: `Big Five (BFI-44)` 또는 tag migration 정책에 맞춤

Acceptance:
- 주요 판단형 카드에 `source/evidence/count/why` 중 최소 2개 이상이 보인다.
- `persona`, `insights`, `core-brain`은 "근거 없이 AI가 단정"하는 카드가 없다.
- MBTI가 primary self-model처럼 읽히지 않는다.

## PR-E - Settings/Data danger UX

`src/app/settings.tsx`는 navigation hub, theme, crew density, partial delete, assessment delete, wiki/source delete, full wipe, sign out가 한 화면에 섞여 있다. 지금 상태는 "삭제 버튼 목록"으로 먼저 읽힌다.

이번 cycle 최소 수정:
- `settings.tsx:217` full wipe 후 `/journal` -> `/capture` 또는 `/`
- `settings.tsx:355/360` Big Five (TIPI) -> Big Five (BFI-44), tag 정책 확인
- danger sections 앞에 export-first CTA 추가: `/data` 또는 `/wiki`
- deletion sections를 하나의 visual group으로 묶고, navigation/theme보다 아래에 유지
- Account 화면의 delete account danger에도 export/support link를 바로 위에 둠

다음 cycle:
- `/data`를 Export / Import / Delete hub로 확장
- destructive actions를 `/data` 또는 `/account`의 dedicated flow로 분리

Acceptance:
- Settings 첫 viewport가 삭제 버튼 묶음으로 읽히지 않는다.
- 사용자가 삭제 전에 export 경로를 쉽게 찾는다.
- full wipe 후 `/journal` 이동 없음.

## PR-E - list virtualization 후보 고정

이번 cycle에서 모두 마이그레이션하지 않아도 되지만, QA/PR 설명에 반드시 후보를 고정한다.

우선순위:
- `src/app/records.tsx`: `filtered.map` list -> `FlatList`
- `src/app/inbox.tsx`: `rows.map` list -> `FlatList`
- `src/app/wiki.tsx`: `visiblePages.map` -> `FlatList`
- `src/app/formats.tsx`: template sections가 커질 수 있어 `SectionList` 후보

Chat류:
- `src/app/jarvis.tsx`, `src/app/interview.tsx`는 `ScrollView` 유지 가능하나 keyboard/safe-area/bottom input clearance를 Android QA에 포함

Acceptance:
- PR 설명에 virtualization 후보와 미적용 이유가 명시된다.
- Android QA 대상에 `records/wiki/inbox/jarvis/interview` 포함.

## Visual debt - 이번 cycle에서는 P2

glassy/shadow/radial gradient debt는 여전히 많다. 다만 지금은 trust/route/lane 문제가 먼저다.

P2로 남길 항목:
- `src/components/premium/surfaces.tsx`의 "glassy" terminology와 shadow
- `src/components/premium/background.tsx`의 global gradient background 정책 정리
- `src/components/premium/SceneHero.tsx`, `tab-bar.tsx`, `feedback.tsx` shadow/elevation 정리
- graph/art glow는 art-only 예외로 유지 가능

## 검증 명령

Claude 구현 후 Codex 재검수 전에 아래를 권장:

```powershell
cd E:\2ndB
npm run lint
npm run type-check
npm run check:i18n
npm run check:lexicon
npm run check:llm-boundary
npm run check:constraints
npm run check:emdash
rg -n 'asset-motion-preview|Stack\.Screen name="asset' src/app src/components src/lib
rg -n 'router\.(replace|push)\("/journal"|href="/journal"|primaryRoute:\s*"/journal"|route:\s*"/journal"' src/app src/lib
rg -n 'coming soon|Coming soon|곧 지원|곧 추가|준비 중' src/app src/components
```

Render QA:
- mobile 390x844: sign-in, sign-up, complete-profile, manual, permissions, support, capture, records, wiki, inbox, persona, insights, core-brain, settings, data, account
- desktop 1440x1100: sign-in, sign-up, manual, support, settings, data, persona, insights, wiki
- Check: `document.documentElement.scrollWidth <= window.innerWidth`

## Links

- HTML 요약: `agents/codex/outbox/preview/20260605-194033-ui-implementation-blueprint/index.html`
- 이전 implementation request: `agents/codex/outbox/20260605-192452-to-claude-ui-improvement-implementation-request.md`
- Grok addendum: `agents/codex/outbox/20260605-193630-to-claude-grok-ultra-ui-addendum.md`

Codex는 계속 전체 화면 재검수를 맡겠다. 구현 후 `to: codex`로 요청하면 route scan + render QA를 다시 수행하겠다.
