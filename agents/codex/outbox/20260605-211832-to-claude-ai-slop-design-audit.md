---
id: 20260605-211832-codex-to-claude-ai-slop-design-audit
from: codex
to: claude
type: request
project: 2nd-B
priority: high
status: open
created: 2026-06-05 21:18:32 KST
src: user
refs:
  - agents/codex/outbox/20260605-211135-to-claude-screen-by-screen-ui-defect-matrix.md
  - agents/codex/outbox/20260605-210640-to-claude-ui-release-backlog-and-gates.md
  - agents/codex/outbox/20260605-210053-to-claude-grok-opinion-release-gate-addendum.md
  - E:\SimonK-stack\skills-src\simon-design-first\SKILL.md
  - E:\SimonK-stack\skills-src\simon-design-first\references\design-chapters.md
  - E:\SimonK-stack\skills-src\design-review\SKILL.md
  - E:\SimonK-stack\skills-src\design-review\references\detail.md
---

# 2nd-B AI Slop Design Audit

사용자 지시: "AI Slop 방지해서 디자인을 검수하자. SimonKstack에 디자인 관련 스킬이 있으니 참고해. 물론 이걸 무조껀 따를 필요는 없어. Slop만 없으면 돼."

Codex는 `E:\2ndB` 코드를 직접 수정하지 않았다. SimonK-stack 디자인 스킬은 엄격한 처방이 아니라 slop 감지 기준으로만 참고했다. 2nd-B는 일반 웹 landing이 아니라 앱 UI이며, 홈 graph/intro/art 계열만 brand world 예외로 분리하는 것이 맞다.

## Verdict

2nd-B는 흔한 AI slop인 기본 Inter look, 순수 검정/회색 단색, 이모지 장식, generic 3-column marketing grid는 비교적 잘 피하고 있다. 그러나 현재 위험은 "고유함 부족"이 아니라 "장식 시스템의 누수"다.

핵심 slop drift:

- 컬러 좌측 보더 카드가 settings/data/support/account/profile/capture/wiki까지 반복된다.
- reusable premium surfaces가 glass/glow/left accent를 기본 언어처럼 만든다.
- root `DESIGN.md`의 Cosmic Pixel Graph 규칙과 `docs/DESIGN_TOKENS.md`의 Phytoncide Option C 규칙이 충돌한다.
- pixel font가 장문/설명/CTA까지 새어 나갈 수 있다.
- app/components 레벨에서 hardcoded rgba/hex가 계속 늘어나 token discipline을 깨고 있다.

Baseline score:

- Design identity: 7/10. 고유한 pixel graph 세계관은 분명하다.
- AI slop risk: 5/10 overall. Utility/settings/data/support 화면만 보면 7/10 위험이다.
- Confidence: static audit 기준. 렌더 QA가 열리면 스크린샷 기준으로 재채점 필요.

## Reference Filter

SimonK-stack에서 참고한 기준:

- 불필요한 decoration 제거.
- 색은 의미 체계로 제한하고 accent budget을 지킨다.
- reference 없이 무난한 "AI dashboard"를 발명하지 않는다.
- 앱 UI는 calm surface hierarchy, dense but readable, one primary workspace, one accent를 우선한다.
- AI slop blacklist: purple/indigo gradient background, colored left-border cards everywhere, glassmorphism overuse, icons in colored circles, centered everything, uniform bubbly radius, generic copy.

2nd-B에는 그대로 적용하면 안 되는 예외가 있다:

- graph/world/art/loader의 cosmic violet/mint glow는 제품 정체성의 일부다.
- 단, 그 예외가 settings/data/account/support 같은 utility 화면으로 넘어오면 바로 slop이다.

## Findings For Claude

### Critical: Design source of truth conflict

Evidence:

- `E:\2ndB\DESIGN.md`는 Cosmic Pixel Graph Village, no glass, no gradients, no pills, no pure black, no card-within-card를 현재 SoT로 선언한다.
- `E:\2ndB\docs\DESIGN_TOKENS.md`는 Phytoncide Option C로 남아 있어 다른 agent가 전혀 다른 제품을 만들 수 있다.

Request:

- `docs/DESIGN_TOKENS.md`를 current cosmic token doc으로 갱신하거나 superseded 문서로 명시 이동.
- root `DESIGN.md`에서 현재 token doc을 링크한다.
- Claude 구현 전 이 충돌을 먼저 제거해야 한다.

Acceptance:

- 디자인 문서 두 개를 읽어도 같은 색, 폰트, radius, surface hierarchy가 나온다.
- Phytoncide/Option C 계열 표현이 production design instruction으로 남지 않는다.

### High: Colored left-border card overuse

Evidence examples:

- `src/app/settings.tsx` has multiple sections with `borderLeftWidth: 4`.
- `src/app/data.tsx`, `support.tsx`, `account.tsx`, `profile.tsx`, `theme.tsx` repeat the same colored left-border card pattern.
- `src/app/capture.tsx` and `wiki.tsx` also use left borders in workflow surfaces.
- `src/components/premium/surfaces.tsx` centralizes left-border accent behavior.
- Root `DESIGN.md` reserves left border for a yellow rephrase hint, not generic sections.

Request:

- Reserve colored left borders for safety/warning/rephrase/danger evidence states only.
- Convert utility screens to plain rows, unframed sections, or 1px quiet panels.
- Do not replace every left border with another decorative gimmick.

Acceptance:

- Settings/data/support/account/profile no longer read as repeated colored-border card stacks.
- Each utility screen has one clear accent at most.
- Warnings/destructive states remain visibly distinct.

### High: Glass/glow is leaking out of brand world

Evidence examples:

- `src/components/premium/background.tsx` uses gradient and radial glow primitives.
- `src/components/premium/surfaces.tsx` describes "Glassy dark panels with glowing borders".
- `src/components/premium/feedback.tsx` uses glowing/orb language.
- `src/components/ui/InlineLoader.tsx` uses radial violet glow and a glowing pixel orb.

Request:

- Split primitives by intent:
  - `GraphWorldPanel`: allowed for graph, intro, art, loader/world moments.
  - `AppPanel` or `AppSection`: default app UI, no glow, no glass, no left accent, no shadow.
- Audit all imports from `premium/surfaces` in utility/workflow screens.

Acceptance:

- Graph/detail/art can feel cosmic.
- Settings/data/account/support/import/export/delete flows feel quiet, direct, and trustworthy.
- A screen with content hidden cannot look like a generic purple-glass AI dashboard.

### High: Route visual modes must be explicit

Current risk:

- The product has a strong world metaphor, but every route should not inherit the same visual intensity.

Request:

- Extend the shared route metadata requested earlier with a visual mode:
  - `world`: home graph, village, art/loader, selected onboarding/intro.
  - `workflow`: capture, inbox, wiki, records, import.
  - `utility`: settings, data, account, support, privacy, theme.
  - `auth`: sign-in, sign-up, complete-profile.
- Shell/background/surface choices should consume that mode.

Acceptance:

- Utility/auth screens cannot accidentally import graph-world decorations.
- Workflow screens can use product identity, but content hierarchy wins over decoration.

### Medium: Pixel font overuse can become legibility slop

Evidence:

- `src/theme/typography.ts` says long Korean paragraphs and CTAs should use Pretendard/system.
- `fontFamilies.sans` currently maps to `PIXEL`.
- `src/components/ui/Text.tsx` uses `fontFamilies.sans` by default.

Request:

- Make `Text` body/subtle/paragraph variants default to `fontFamilies.readable`.
- Keep pixel font for headings, nav labels, short badges, graph labels, and brand identity moments.
- Audit long Korean descriptions in auth/public/settings/data/persona flows.

Acceptance:

- Long copy remains readable on small mobile.
- Pixel typography still signals the product, but does not force every sentence to be an asset label.

### Medium: Token bypass and hardcoded color drift

Evidence:

- Static scan found roughly 114 `rgba(` or hex hits across `src/app` and `src/components`.
- Some are pixel-art data or graph internals, but component-level hardcoded values remain in premium feedback/surfaces/graph bits/NavGraph and app html.

Request:

- Move app-level surface/text/border/feedback colors to semantic tokens.
- Keep allowlisted literal colors only for pixel art data, SVG internals, and graph rendering math.
- Add a lightweight `rg` gate or comment allowlist so new hardcoded colors do not creep back in.

Acceptance:

- Token exceptions are deliberate and searchable.
- App screens cannot drift into new purple/mint variants without design review.

### Medium: Pill/circular chrome audit

Evidence:

- Root `DESIGN.md` says never `borderRadius: 9999` and no pill chrome.
- Static scan still finds high radii such as `borderRadius: 999` and `borderRadius: 32` in graph/art/onboarding/feedback contexts.

Request:

- Keep circular radius only for graph nodes, avatar-like objects, and asset art.
- Chips/status controls in app screens should use existing small/medium radius tokens.
- Onboarding CTA radius should be audited against `DESIGN.md`.

Acceptance:

- Utility and workflow screens do not look like bubbly SaaS templates.
- Circular forms have an explicit metaphor.

### Medium: Empty/loading/error states should not become decoration

Request:

- Keep cosmic loaders for global loading/graph-world transitions only.
- Empty states in inbox/wiki/records/settings should be evidence/action driven: what happened, what the user can do, what data is missing.
- Avoid orb-only, glow-only, or icon-circle-only empty states.

Acceptance:

- Empty states are useful without relying on decorative glow.

### Medium: Copy slop guard

Request:

- Avoid generic or overclaiming copy such as "AI that learns you", "understands your soul", "scores your personality", "therapy/diagnosis/companion" unless supported and legally reviewed.
- Prefer concrete copy: exportable records, source-backed insight, user-owned capture, trusted outside view, delete controls.
- Keep Grok/Codex outside-view framing: no public rating/score/peer-evaluation framing.

Acceptance:

- Public/auth/capture/persona/settings copy gives verification rights, not mystique.

## Suggested Implementation Order

1. Resolve design SoT conflict.
2. Add visual mode to route metadata.
3. Split `GraphWorldPanel` from quiet `AppPanel`/`AppSection`.
4. Replace repeated left-border utility cards.
5. Fix readable font defaults for body copy.
6. Add color/radius/glow allowlist checks.
7. Run screenshot QA by mode: auth, workflow, self-model, utility, graph-world.

## Verification Commands

Suggested checks after implementation:

```powershell
cd E:\2ndB
rg -n 'borderLeftWidth|borderLeftColor' src\app src\components
rg -n -i 'glassy|glass|glow|shadowOpacity|RadialGradient|LinearGradient|orb' src\app src\components
rg -n '#[0-9A-Fa-f]{3,8}|rgba\(' src\app src\components
rg -n 'borderRadius:\s*(9999|999|32)' src\app src\components
rg -n 'fontFamilies\.(sans|pixel)' src\app src\components
rg -n -i 'score|rating|peer evaluation|anonymous honest feedback|therapy|diagnosis|companion' src\app src\components src\lib
npm run type-check
npm run check:lexicon
```

Expected result is not zero hits. Expected result is that remaining hits are explainable by allowlist:

- graph/world/art rendering
- modal backdrop
- pixel-art literal palette
- global loader
- warning/danger evidence states

## Links

- HTML preview: `agents/codex/outbox/preview/20260605-211832-ai-slop-design-audit/index.html`
- Screen-by-screen matrix: `agents/codex/outbox/20260605-211135-to-claude-screen-by-screen-ui-defect-matrix.md`
- UI release gates: `agents/codex/outbox/20260605-210640-to-claude-ui-release-backlog-and-gates.md`

Codex did not modify `E:\2ndB` code.
