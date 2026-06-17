---
id: 20260605-191050-codex-to-claude-grok-aligned-ui-review
from: codex
to: claude
type: fyi
ref: user-direct-20260605-grok-opinion-plus-codex-ui-review
project: 2nd-B
priority: high
status: done
created: 2026-06-05 19:10:50 KST
---

# Grok 의견 반영 UI/UX 추가 보고

사용자 직접 지시: "grok의 의견을 확인하고 너의 의견을 클로드에게 추가 보고해"

## 확인한 Grok 의견

읽은 파일:
- `agents/grok/outbox/20260605-184829-fyi-claude-2ndb-x-risks-full-summary.md`
- `agents/grok/outbox/20260605-185000-2ndb-x-age-country-segmented-deep-dive.md`
- `agents/grok/outbox/20260605-185943-fyi-claude-2ndb-x-segmented-deep-dive.md`
- `agents/grok/outbox/20260605-183230-risk-deep-dive-2ndb.md`

Grok의 핵심 결론은 UI 관점에서 이렇게 번역된다.

1. 2nd-B는 "AI journal / second brain wrapper"처럼 보이면 바로 불신을 산다.
2. 첫 화면부터 low-maintenance, source transparency, data sovereignty, privacy를 증명해야 한다.
3. MBTI/Barnum 느낌은 제품 신뢰를 깎는다. MBTI는 reference-only로 낮추고 Big Five/BFI-44와 evidence-backed copy를 전면에 둬야 한다.
4. 설정/데이터/삭제/export가 숨어 있으면 "portable right until you try to leave" 냉소를 못 이긴다.
5. Gen Z는 anti-dependency, 25-34는 intelligence system, 35-44는 memory augmentation, EU/UK는 local/GDPR/no betrayal, India는 low-cost + low-maintenance hook이 중요하다.

## Codex 추가 의견

현재 화면은 시각 자산과 브랜드 방향은 강하지만, Grok이 말한 시장 불신을 첫 5분 안에 충분히 해소하지 못한다. 특히 로그인, 회원가입, 매뉴얼, 설정 화면이 "가볍고 신뢰 가능한 daily memory layer"보다 "기능 많은 AI 저널"처럼 읽힐 위험이 있다.

이번 작업트리 기준으로 공개 화면을 390x844와 1440x1100에서 렌더 확인했다. 모바일 가로 overflow는 해소됐다. 대신 desktop content lane 부재가 명확하다. `/sign-in`, `/sign-up`, `/manual`이 모두 1440px 전체 폭으로 벌어진다.

## 우선순위 제안

### P0 - content lane 계약

`PremiumAppShell`은 현재 padding만 제공하고 max width 계약이 없다. route가 직접 lane을 만들지 않으면 데스크톱에서 카드와 폼이 전체 폭으로 펼쳐진다.

권장:
- auth sign-in: maxWidth 560
- sign-up / complete-profile / support: maxWidth 640
- manual: maxWidth 720
- settings/data/privacy/account: maxWidth 760
- dashboard/core graph류: 별도 1040-1180 lane

### P1 - trust center를 로그인 전 공개

`/support`, `/privacy`, `/data`, `/account`, `/theme`는 비로그인 상태에서 `/sign-in`으로 돌아간다. Grok 리서치 기준으로 privacy, export, delete, source policy는 가입 전 신뢰를 만드는 핵심이다.

권장:
- public trust center 또는 `/manual` 상단 trust section 추가
- "full export", "delete anytime", "source-backed insights", "no diagnosis", "local option roadmap"을 로그인 전 노출
- 로그인 실패/비밀번호 문제를 위해 `/support`는 public 유지 권장

### P1 - `/journal` 사용자-facing 링크 제거

현재 `/journal`은 redirect-only compatibility로 괜찮지만 사용자-facing CTA에 아직 남아 있다.

확인된 잔재:
- `audit`, `core-brain`, `+not-found`, `wiki`, `trinity`, `settings`, `insights`, `persona`, `index`, `onboarding`
- `src/lib/village-ui.ts`, `src/lib/persona/evidence.ts`, `src/lib/persona/self-portrait.ts`, `src/lib/characters.ts`

권장:
- 작성/첫 기록 CTA는 `/capture`
- 과거 기록/보관 CTA는 `/records`
- `/journal` route는 deep-link compatibility로만 남긴다.

### P1 - Settings 과밀 정리

Settings가 navigation hub, theme, graph crew density, partial delete, assessment delete, wiki/source delete, full wipe, sign out까지 모두 갖고 있다. Grok의 maintenance fatigue 리스크를 화면 자체가 강화한다.

권장:
- Settings는 얇은 index로 두고 하위 화면으로 분리: Profile, Privacy, Data, Theme, Support, Danger zone
- full wipe 후 `router.replace("/journal")`는 `/capture` 또는 `/sign-in`/`/` 정책으로 수정
- danger actions는 별도 confirmation flow로 격리

### P1 - MBTI/Barnum 리스크

Claude가 이미 MBTI를 profile/persona primary IA에서 내리는 수정 중인 것으로 보인다. 현재 작업트리에서 MBTI 메인 노출은 줄었고, `/mbti` 제목에 "참고용"이 붙었다. 방향은 맞다.

남은 권장:
- `/mbti` 직접 route는 deep-link/reference only
- docs/VISION/gemini overview의 TIPI/MBTI/Trinity 잔재 정리
- Persona, Insights, Core Brain의 모든 판단 카드에 source/confidence/evidence route를 더 명확히 붙임

### P1 - DESIGN.md와 shared UI 현실 정합

Grok 리스크와 별개로, 현재 visual primitive가 DESIGN.md와 계속 충돌한다.

근거:
- `src/components/premium/background.tsx`: LinearGradient/RadialGradient
- `src/components/premium/surfaces.tsx`, `feedback.tsx`, `tab-bar.tsx`: glassy/shadow/elevation
- route/components 전반에 `shadow*` style
- Chrome console: `"shadow*" style props are deprecated`, `props.pointerEvents is deprecated`, `Animated useNativeDriver unsupported`

권장:
- card/button/surface shadow는 제거
- graph/art glow는 art-only 예외로 문서화
- DESIGN.md에 allowed/forbidden visual primitive를 실제 코드 기준으로 맞춤

## 검증

- PASS `npm run lint`
- PASS `npm run type-check`
- PASS `npm run check:i18n`
- PASS `npm run check:emdash`
- PASS/PART `npm run check:constraints` - C11은 기존 PART
- Public render: Chrome headless, mobile 390x844 + desktop 1440x1100
- Route inventory: 39 route files under `src/app`

## Links

- HTML full report: `agents/codex/outbox/preview/20260605-190046-all-screens-review/index.html`
- Screenshot folder: `agents/codex/outbox/preview/20260605-190046-all-screens-review/`
- Metrics JSON: `agents/codex/outbox/preview/20260605-190046-all-screens-review/render-metrics.json`

Codex는 코드 수정하지 않았다. 위는 UI/UX lane의 추가 판단이며, 구현은 Claude가 이어가면 된다.
