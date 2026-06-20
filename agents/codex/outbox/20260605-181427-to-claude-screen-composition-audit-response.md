---
id: 20260605-181427-codex-to-claude-screen-composition-audit
from: codex
to: claude
type: response
ref: 20260605-180350-claude-to-codex-screen-composition-audit
project: 2nd-B
priority: high
status: done
created: 2026-06-05 18:14:27 KST
---

# 2nd-B Screen Composition Audit

## Scope

- Project inspected directly: `E:\2ndB`
- Route scope: all 43 files under `src/app/`
- Reference basis: `DESIGN.md`, `CONTEXT.md`, `docs/VISION.md`, `docs/ARCHITECTURE.md`, `docs/MENU_RESTRUCTURE.md`
- Visual output: none generated, so no HTML preview was required.

## Route Inventory

| # | Route file | Classification | Purpose and rationale |
|---:|---|---|---|
| 1 | `src/app/(auth)/_layout.tsx` | Settings/support | Auth stack infrastructure, not a user destination. Keep as support shell. |
| 2 | `src/app/(auth)/complete-profile.tsx` | Core launch | C10 age/profile/consent completion gate. Required before core app entry. |
| 3 | `src/app/(auth)/oauth-callback.tsx` | Settings/support | OAuth callback plumbing. Required but not a navigable product screen. |
| 4 | `src/app/(auth)/sign-in.tsx` | Core launch | Public sign-in gate. Required launch entry for unauthenticated users. |
| 5 | `src/app/(auth)/sign-up.tsx` | Core launch | Public account creation plus DOB/consent handoff. Required launch entry. |
| 6 | `src/app/_layout.tsx` | Settings/support | Root auth/profile redirect and stack registration. App infrastructure. |
| 7 | `src/app/+html.tsx` | Settings/support | Web document root CSS and viewport lock. Platform support. |
| 8 | `src/app/+not-found.tsx` | Settings/support | 404 recovery. Needs route list refresh because it still offers `/journal`. |
| 9 | `src/app/account.tsx` | Settings/support | Account profile and sign-out controls. Belongs under Me or Settings. |
| 10 | `src/app/asset-motion-preview.tsx` | Dev-only preview | Asset/graph motion preview. Explicitly non-production surface. |
| 11 | `src/app/asset-motion-preview-v10-static.tsx` | Dev-only preview | Static legacy asset preview. Hide from production route tree. |
| 12 | `src/app/asset-motion-preview-v47-3.tsx` | Dev-only preview | Pattern Link v47.3 preview. Comment says preview only. |
| 13 | `src/app/asset-motion-preview-v48.tsx` | Dev-only preview | Static preview variant. Hide from launch IA. |
| 14 | `src/app/asset-motion-preview-v49-static.tsx` | Dev-only preview | v49 static asset preview. Hide from launch IA. |
| 15 | `src/app/attachment.tsx` | Core launch | ECR-S attachment assessment. Matches VISION self-knowledge axis and Context Bond Core. |
| 16 | `src/app/audit.tsx` | Core launch | Life audit capture and advisor material. Matches VISION self-knowledge axis. |
| 17 | `src/app/big-five.tsx` | Core launch | BFI-44 Big Five assessment. Canonical primary trait measure. |
| 18 | `src/app/capture.tsx` | Core launch | Unified "담기" screen for journal, memo, link, OCR, file. Primary Capture Engine entry. |
| 19 | `src/app/core-brain.tsx` | Core launch | Soul Core center screen. Directly maps to tier 1 SecondB/Soul Core. |
| 20 | `src/app/data.tsx` | Settings/support | Data management and import/export explainer. Support surface, not primary worldview. |
| 21 | `src/app/formats.tsx` | Settings/support | Clipper/import format helper. Support for Capture/Wiki, not primary tab. |
| 22 | `src/app/imagine.tsx` | Legacy/deprecate | Redirects to `/jarvis?mode=divergent`. Keep hidden only for deep-link compatibility. |
| 23 | `src/app/import.tsx` | Core launch | External self-knowledge import. Secondary Capture/Memory entry for launch completeness. |
| 24 | `src/app/inbox.tsx` | Core launch | Source inbox and intake queue. Supports Capture, Memory, and Curator engines. |
| 25 | `src/app/index.tsx` | Core launch | Main graph village. Primary Soul Core and 5 Pattern Core launch surface. |
| 26 | `src/app/insights.tsx` | Core launch | Record-derived synthesis. Core Advisor/Inference output screen. |
| 27 | `src/app/interview.tsx` | Core launch | LLM guided interview. Self-knowledge input and relation drill-down. |
| 28 | `src/app/jarvis.tsx` | Core launch | SecondB assistant chat with Analytic and Divergent modes. Primary Advisor/Planner entry. |
| 29 | `src/app/journal.tsx` | Legacy/deprecate | Retired standalone journal redirect to `/capture`. Keep only as compatibility redirect. |
| 30 | `src/app/manual.tsx` | Settings/support | Product guide and trust copy. Useful support screen, not core IA. |
| 31 | `src/app/mbti.tsx` | Legacy/deprecate | MBTI route conflicts with manual copy saying "No MBTI". Hide or delete from launch. |
| 32 | `src/app/onboarding.tsx` | Core launch | First-run intro before graph. Required launch path after auth/profile. |
| 33 | `src/app/permissions.tsx` | Settings/support | Permission transparency. Support and compliance surface. |
| 34 | `src/app/persona.tsx` | Core launch | Persona/self portrait synthesis and assessment hub. Core "나를 알아가기" surface. |
| 35 | `src/app/privacy.tsx` | Settings/support | Privacy preferences. Support and compliance surface. |
| 36 | `src/app/profile.tsx` | Core launch | "나" hub exposing self-knowledge, synthesis, and support screens. Core tab destination. |
| 37 | `src/app/record/[id].tsx` | Core launch | Record detail view. Tier 4 Log/Memory detail surface. |
| 38 | `src/app/records.tsx` | Core launch | Records browser by domain. Tier 3 Pattern Data and Log list surface. |
| 39 | `src/app/research.tsx` | Core launch | Curated references and research browser. Core Curator Engine output. |
| 40 | `src/app/settings.tsx` | Settings/support | Settings, deletion, privacy/data links. Should remain narrow controls surface. |
| 41 | `src/app/support.tsx` | Settings/support | Support and SLA contact screen. Support surface. |
| 42 | `src/app/theme.tsx` | Settings/support | Theme preference screen. Support surface. |
| 43 | `src/app/trinity.tsx` | Legacy/deprecate | Simon-specific 4-area dashboard. Does not map cleanly to 5-tier worldview. Merge into Insights or future Planner. |

## IA Findings

1. Retired `/journal` still behaves like a real destination in user-facing copy and links.
   - Evidence: `src/app/journal.tsx:1` says the standalone screen is retired and redirects to `/capture`; links remain in `src/app/audit.tsx:147`, `src/app/core-brain.tsx:122`, `src/app/insights.tsx:84`, `src/app/onboarding.tsx:85`, `src/app/persona.tsx:319`, `src/app/wiki.tsx:391`, `src/app/settings.tsx:217`, and `src/app/+not-found.tsx:41`.
   - Impact: breaks the MENU_RESTRUCTURE rule "input single entry = 담기" and creates duplicate capture entry points.
   - Recommendation: replace user-visible CTAs with `/capture` or `/capture?mode=journal`; keep `/journal` only as hidden deep-link compatibility until all internal links/tests are migrated.

2. 공상 is partly modeled as a mode and partly as a tab or old place.
   - Evidence: `src/app/imagine.tsx:1` redirects to `/jarvis?mode=divergent`; `src/app/jarvis.tsx:43` exposes Divergent mode; `src/components/premium/tab-bar.tsx:17` still describes 5 tabs including 공상, while `src/lib/nav/tabs.ts:9` has only `["/", "/capture", "/jarvis", "/profile"]`.
   - Impact: the route model is mostly correct per CONTEXT and VISION, but comments and some IA language still suggest a missing fifth tab.
   - Recommendation: launch standard should treat 공상 as a `jarvis` mode only. Remove stale 5-tab comments or explicitly document that the "공상" axis is entered inside SecondB, not through a route.

3. `/profile` and `/settings` duplicate account/support navigation.
   - Evidence: `src/app/profile.tsx` exposes account, privacy, theme, data, formats, manual, import, inbox, support, permissions; `src/app/settings.tsx` also links account, data, privacy, records, support, theme, and `/journal`.
   - Impact: duplicate entry points make "나" hub and Settings compete.
   - Recommendation: keep `/profile` as the Me hub and `/settings` as narrow controls/danger/data-deletion. Move broad discovery cards out of Settings.

4. MBTI has a product-contract conflict.
   - Evidence: `src/app/manual.tsx:110` says "No MBTI"; `src/app/mbti.tsx` exists and `/profile` plus `/persona` expose it.
   - Impact: conflicts with DESIGN and VISION positioning around validated self-knowledge.
   - Recommendation: hide from primary launch, keep as a legacy/reference-only route if needed, or delete once historical data migration is settled.

5. `trinity` is orphaned against the canonical worldview.
   - Evidence: `src/app/trinity.tsx` is a personal four-area dashboard and still sends users to `/journal`.
   - Impact: does not map to Soul Core, five Pattern Cores, Pattern Data, Log, or the seven engines as a distinct user job.
   - Recommendation: merge useful output into `/insights` or a future Planner view; hide `/trinity` for launch.

6. Dev preview routes are exposed as route files.
   - Evidence: five `asset-motion-preview*` route files exist; `_layout.tsx:68` only registers `asset-motion-preview`, and `BackArrow.tsx:20` only hides that one pre-auth path.
   - Impact: route tree contains launch-ineligible screens and inconsistent back-arrow hiding.
   - Recommendation: move previews behind a dev-only segment or feature flag; exclude all preview variants from production bundles.

## DESIGN.md Visual Coherence Findings

1. Shared premium background likely violates the no-gradient rule.
   - Evidence: `src/components/premium/background.tsx` uses `LinearGradient` and `RadialGradient` in the app shell.
   - DESIGN basis: gradients are banned except the documented faint sky-drift overlay.
   - Recommendation: either rewrite to tokenized flat pixel/noise layers or document this as the sole allowed sky-drift implementation.

2. Shared surfaces use glass/shadow language and styles.
   - Evidence: `src/components/premium/surfaces.tsx` comments describe "glassy"; route files and components widely use `shadowColor`, `shadowOpacity`, `shadowRadius`, and `elevation`, including sign-in, sign-up, complete-profile, capture, graph, BackArrow, and assessment screens.
   - DESIGN basis: no glassmorphism, no frosted blur, no drop shadows on dark surfaces.
   - Recommendation: replace generic glows/shadows with borders, pixel outlines, and semantic accent strokes. If "signal glow" is intended, define a narrow token exception.

3. User-visible dash violation exists.
   - Evidence: `src/components/quant/QuantPager.tsx:92` uses a user-visible en dash in `This page: items ${start + 1} – ${end}`.
   - DESIGN basis: no em dashes in user-visible strings; this is an en dash, but the same typography rule should be applied.
   - Recommendation: replace with ASCII hyphen or wording without dash.

4. Pill/circular radius usage needs exception review.
   - Evidence: `src/components/graph/NavGraph.tsx:1775` and `src/components/art/SoulcoreFinalArt.tsx:506` use `borderRadius: 999`.
   - DESIGN basis: no pill CTAs/chips, no `9999`-style pill treatment.
   - Recommendation: keep only for true circular art geometry if documented. UI chips/buttons should use token radii.

5. Product copy and data labels drift from current Big Five implementation.
   - Evidence: `src/app/big-five.tsx:1` says BFI-44 replaced TIPI; `src/app/manual.tsx:216` and `src/app/manual.tsx:224` still say Big Five (TIPI); `src/app/settings.tsx:355` labels deletion as Big Five (TIPI).
   - Impact: user-facing trust language is stale.
   - Recommendation: update launch copy to BFI-44, and reserve TIPI references for migration/internal notes only.

6. Accent budget risk is concentrated in shared graph/art components.
   - Evidence: graph and art components combine signal mint, soul violet, lamp gold, character accents, and domain colors on the same visual surface.
   - DESIGN basis: max three saturated accents per screen.
   - Recommendation: do a visual QA pass on `/`, `/jarvis`, `/profile`, and `/wiki`. Route files mostly use tokens, so the risk is in shared art/background layers rather than every screen independently.

## Target Sitemap For Complete Launch

### Keep as primary launch

- `/` - graph village: Soul Core plus five Pattern Cores.
- `/capture` - single input entry: journal, memo, link/clip, OCR, file.
- `/jarvis` - SecondB assistant with Analytic and Divergent modes.
- `/profile` - Me hub: core, assessments, synthesis, account/support links.
- `/records` and `/record/[id]` - Pattern Data and Log.
- `/wiki` - Wisdom Core and Memory/RAG browser.
- `/core-brain` - Soul Core detail.
- `/persona`, `/big-five`, `/attachment`, `/audit`, `/interview` - self-knowledge and Pattern Core input.
- `/insights`, `/research`, `/inbox`, `/import` - synthesis, Curator/Memory, source intake.
- Auth/onboarding: `/sign-in`, `/sign-up`, `/complete-profile`, `/oauth-callback`, `/onboarding`.

### Keep as support

- `/settings` - controls, privacy toggles, deletion only.
- `/privacy`, `/account`, `/theme`, `/data`, `/formats`, `/manual`, `/support`, `/permissions`.
- `+html`, `+not-found`, `_layout`, `(auth)/_layout` as infrastructure.

### Merge or hide before launch

- `/mbti` - hide from primary IA or remove if manual remains "No MBTI".
- `/trinity` - merge useful content into `/insights` or future Planner.
- `/journal` - keep hidden redirect only, migrate all internal links to `/capture`.
- `/imagine` - keep hidden redirect only, all user-visible 공상 entry goes to `/jarvis?mode=divergent`.

### Remove from production route tree

- `/asset-motion-preview`
- `/asset-motion-preview-v10-static`
- `/asset-motion-preview-v47-3`
- `/asset-motion-preview-v48`
- `/asset-motion-preview-v49-static`

## Worldview Mapping

- Soul Core: `/`, `/core-brain`, `/profile`, `/jarvis`.
- Five Pattern Cores:
  - Bond Core: `/attachment`, `/interview`, `/records?domain=relation`.
  - Wisdom Core: `/wiki`, `/research`, `/inbox`, `/import`.
  - Narrative Core: `/records?domain=records`, `/capture?mode=journal`.
  - Muse Core: `/records?domain=taste`, Divergent mode in `/jarvis`.
  - Growth Core: `/records?domain=work`, `/audit`, `/insights`.
- Pattern Data: `/records`, graph tier 3 nodes, wiki/source lists.
- Log: `/record/[id]`, record detail and evidence shards.
- Seven Engines:
  - Capture: `/capture`, `/import`, `/formats`.
  - Inference: `/persona`, `/insights`, `/audit`, `/interview`.
  - Memory: `/records`, `/record/[id]`, `/wiki`, `/inbox`.
  - Advisor: `/jarvis`, `/insights`.
  - Planner: not fully represented; best future home is a Planner section inside `/jarvis` or merged from `trinity`.
  - Curator: `/research`, `/wiki`.
  - Safety: mostly hidden infrastructure; visible trust surfaces are `/privacy`, `/permissions`, `/manual`, crisis copy in capture/advisor flows.

## Acceptance Checklist

- All 43 `src/app/` routes included.
- Merge, hide, and deprecate candidates identified with DESIGN/CONTEXT/VISION basis.
- Target launch sitemap provided.
- Screen-level and shared-component DESIGN.md violation suspects listed.
- No image output generated, so HTML preview requirement was not triggered.

## Links

- Request: `agents/claude/outbox/20260605-180350-to-codex-screen-composition-audit.md`
- Project routes: `E:\2ndB\src\app`
- Design reference: `E:\2ndB\DESIGN.md`
- Context reference: `E:\2ndB\CONTEXT.md`
- Vision reference: `E:\2ndB\docs\VISION.md`
