# O-8 Design Audit Plan (4-AI Workflow)

# O-8 통합 FIX PLAN — 2nd-B 4-Screen Synthesis

Grounded in the four audits (capture · secondb · index · profile/settings/account). SSOT note carried forward: DESIGN.md supersedes generic O-8 on **font (NeoDunggeunmo pixel, not Pretendard/Inter)** and **type scale**. ⚠️ The audits disagree on the low end of the scale (capture cites `11/13/...`, index/me-profile cite `12/14/...` from `tokens.ts:234`) — confirm against `E:/2ndB/src/lib/theme/tokens.ts` before any size-snapping sweep.

---

## 1. CROSS-CUTTING VIOLATIONS (fix once in a token / shared component)

| # | Pattern | Where it recurs | Fix-once location |
|---|---------|-----------------|-------------------|
| C1 | **Raw hex/rgba literals** instead of `cosmic.*`/`withAlpha()` (DESIGN.md hard rule, CI-checked) | secondb 660,661,671 · index 99-100,601,609-610,693-694,748-749,761-762 · settings 64,762,765,769-770,792 (capture & profile clean) | Substitution to existing tokens; **`index:761` is literally `cosmic.coreGlow` retyped by hand** |
| C2 | **Drop shadows / glows on dark surfaces** ("read as smudges" — explicit never-do) | capture 573,1167-1174,1366-1379 · secondb 664-667 · index 616-619,667-670,697-700,750-753 · profile 191-194 · settings 722-725,740 · account 317-320 | Root cause is shared **`src/components/.../surfaces.tsx`** `PremiumCard glow` prop + `PremiumButton` shadow + per-screen `shadow*`/`elevation` style keys |
| C3 | **Modal/drawer backdrop = raw rgba, wrong value** (spec = `rgba(0,0,0,0.6)`) | secondb 671 `rgba(8,12,24,0.78)` · index 601 `rgba(5,7,15,0.38)` | Define **one `semantic.backdrop` token** in `tokens.ts`, reference everywhere |
| C4 | **Raw `<Pressable>` with static style — no pressed/hover/focus** (spec: 80ms opacity→0.8) | capture 653-734,1034-1051 · secondb 298-555 (all) · index 420-548 (all) · profile 159-168 | Route actions through shared **`Button`** (owns focus/hover/loading/disabled); add pressed-opacity wrapper for chips |
| C5 | **Touch targets <44dp** | capture (tagChip, manageFormatsLink, advisorRow, text links) · secondb 439-462,484-497,536-555,330-353 · profile 198-205 | Shared chip/link component → `minHeight:44`; modal buttons → shared `Button` (guarantees ≥44) |
| C6 | **Pixel face on long KO body/CTA** (typography.ts:28-37 says use `fontFamilies.readable`/Pretendard) | capture 1303-1308 (textarea) · index 658,677,789 · settings 425-427,582-585 · account body | One rule: multi-line KO body + CTA copy → `fontFamilies.readable`; keep pixel for labels/badges |
| C7 | **Off-4px-grid spacing + non-`radii.lg` cards** (cards/modals must be `radii.lg`=12) | capture 574,580,629,996,1000,1029,1316,1362 · secondb 583,610,624,715,681,734-735,658,745 · index 613,637,683,691,747,759 · settings/account padding `md` vs `lg` | Pure substitution to `spacing.*` / `radii.*` |
| C8 | **Info-density: ≥2 graphics + no single primary CTA + persistent `SceneHero`** (standing rule: one message + one graphic) | capture 560-1052 · secondb 263-283 · index 395-570 · profile 32-78,121-174 | Shared **`SceneHero`** should collapse to single-line title once content exists (empty-state-only art); each screen picks ONE `variant="primary"` |
| C9 | **Glyph/dingbat used as icon** (anti-slop: → SVG) | capture 886 `✓`, 1024 `✕` · index 427 `✕` | Needs real SVG assets (see Defer) |
| C10 | **Reduced-motion not gated on every animation** | capture 1056-1058,1381 (+companion pop) · index 211-236 (entry flourish) | Mirror existing `prefersReducedMotion()` pattern already used in `useSkyDrift`/`SceneHero` |
| C11 | **Labels >7 KO chars** | capture advisor 13ch, proposal 8ch · secondb 357 9ch · settings 477/495/509/521/539/553/565 (8-18ch) | Copy rewrite (see Defer) |

---

## 2. PRIORITIZED ATOMIC COMMITS (한 커밋 = 한 범주)

Ordered: highest user-visible impact × lowest risk first.

1. **`fix(color): route all chrome colors through tokens`** — Files: `secondb.tsx` (660,661,671), `index.tsx` (99-100,601,609-610,693-694,761-762), `settings.tsx` (64,762,765,769-770,792); add `semantic.backdrop` to `tokens.ts`. Change: every raw rgba → `withAlpha(cosmic.*)`; `:761`→`cosmic.coreGlow`; both backdrops → new token. Why: breaks the single hardest CI-checked DESIGN rule; pure substitution. Risk: **very low** (values mostly identical, visual-neutral). *(C1, C3)*

2. **`fix(hierarchy): remove drop shadows/glows on dark surfaces`** — Files: shared `surfaces.tsx` (`PremiumCard glow`, `PremiumButton` shadow) + capture 573,1167-1174,1366-1379 · secondb 664-667 · index 616-619,667-670,697-700,750-753 · profile 191-194 · settings 722-725,740 · account 317-320. Change: delete `shadow*`/`elevation`/`glow`; lean on hairline border + spacing + mint fill. Why: explicit never-do, app-wide smudge cleanup. Risk: **low** (visual only; fixing the shared prop cascades). *(C2)*

3. **`fix(a11y): touch targets ≥44dp + input hints`** — Files: capture (tagChip/manageFormatsLink/advisorRow/text links), secondb (439-462,484-497,536-555 + Input hint 502-509), profile (198-205,167). Change: `minHeight:44`/`hitSlop`; bump profile chip text `subtle`→`caption`/`text`; add `accessibilityHint`. Why: WCAG fail on the most-tapped surfaces. Risk: **low-med** (layout reflow on chips). *(C5)*

4. **`fix(states): press/focus via shared Button`** — Files: shared `Button`/`surfaces.tsx` (ensure focus-visible + 80ms opacity-0.8) → then replace hand-rolled Pressables: secondb modal buttons (536-555), capture tossBtn (1034-1051) + mode/track chips, index 420-548, profile chips. Also `disabled={sending}` on secondb mode toggle (329-362). Why: every tappable currently gives zero feedback. Risk: **medium** (behavioral; test loading/disabled paths). *(C4)*

5. **`fix(typography): readable font on long KO body/CTA`** — Files: capture textarea (1303-1308), index (658,677,789), settings (425-427,582-585), account body. Change: `fontFamilies.readable`. Why: pixel face illegible for long-form/small KO per typography.ts note. Risk: **low** (keep pixel for labels). *(C6)*

6. **`fix(spacing): snap to 4px grid + radii.lg on cards`** — Files: capture, secondb, index, settings/account per C7 line lists. Change: literals → `spacing.*`; card/modal/drawer radius → `radii.lg`; resolve type-scale off-values (16/20 → nearest token) **after** confirming the scale. Why: density/grid compliance, pure substitution. Risk: **low**. *(C7)*

7. **`fix(motion): gate reduced-motion + ease-in-out cubic`** — Files: capture (1056-1058,1381,companion pop), index (211-236 entry flourish → `setValue(1)` like `useSkyDrift`), secondb (171-172 cubic; pulse floor 0.4↔1, hold 1 on reduced — 121,178), capture press `scale`→opacity-0.8 only. Why: a11y on every animation + DESIGN motion spec. Risk: **low-med**. *(C10)*

8. **`fix(anti-slop): glyph icons → SVG + kill em dash`** — Files: capture 886/1024, index 427 (also delete redundant top-right ✕ — skip button already dismisses), index 147 em dash. Why: never-do breaches. Risk: **low for em-dash/✕-delete**; SVG swap blocked on assets → see Defer. *(C9)*

9. **`refactor(density): one message + one graphic + one primary CTA`** — Per-screen (highest impact, do last, **needs Simon's IA call** — see Defer): capture 560-1052 collapse to hero+input+저장 (sticky); secondb collapse SceneHero once `turns>0` (263-283) + demote mint links (306-322) + left-align empty (389-392); index reduce graph+ribbon+2 "Touch!" cards to graph+one nudge (479-570), render SecondB once (499/541); profile cut 21→3-4 tasks + one primary CTA, delete nav duplicated with settings (profile 62-77 ↔ settings 342-388). Risk: **high** (product/IA). *(C8)*

10. **`chore(cleanup): dead styles + duplicate components`** — secondb dead `header`/`headerLeft`/`meter` (611-621); settings drop custom `SettingsActionButton` (38-106) → shared `Button`. Risk: low. (Folds naturally as you do #4.)

---

## 3. GRAPHIC vs COPY/TOKEN

- **Pure token/code (no design decision):** C1, C2, C3, C7 — commits 1,2,6. Mechanical.
- **Copy CUT, not more copy** (explanatory text = graphic failed): secondb hero speech multi-sentence (270-282) → one clause; index `coreCardBody` 3-line → 2 (523); capture helper lines (762-764,920-926,1029-1031); settings 3-line body (425-427,582-585). These screens are **text-heavy because the graphic underperforms — reduce text, do NOT add graphic.**
- **Graphic BEHAVIOR change (not new art):** shared `SceneHero` collapse-when-content (C8) — same asset, conditional render.
- **Genuinely needs NEW graphic asset:** the ✓/✕ glyph→SVG swap (C9) is the only place needing a new vector asset; everywhere else the rule is *fewer* graphics, not more. profile/settings are text-list screens whose fix is IA restructure + one primary CTA, **not** decorating with a graphic.

---

## 4. DEFER — needs Simon's decision

- **New SVG icon assets** for check (capture 886) and close (capture 1024, index 427). Asset creation/sourcing — flag for Simon (or reuse existing `react-native-svg` `Path` already imported in capture).
- **Copy rewrites / label shortening** (C11): exact wording for capture "세컨비에게 묻기"/"내 형식 저장", settings noun-only labels, secondb "새 관점으로", and **localizing `"Touch!"` → KO** (index 505,525) — needs Simon's voice.
- **Info-density restructure (commit 9)**: what is each screen's ONE primary action, what moves behind drilldown — product/IA call, especially profile↔settings nav de-duplication (which screen is the hub) and capture's 12-block → which blocks survive default view.
- **Danger button color change**: settings/`surfaces.tsx` render danger as faint-rose+rose; DESIGN spec = solid `zoneRed`+white. App-wide brand-visible change — confirm before sweeping.
- **Type-scale ground truth**: resolve the `11/13` vs `12/14` discrepancy in `tokens.ts:234` before commit 6's size-snap.

---

## 5. SPLIT FOR PARALLEL EXECUTION

**Codex (pure mechanical / token sweeps — isolate on a worktree, low merge risk):**
- Commit 1 (rgba→token + backdrop token)
- Commit 2 (delete `shadow*`/`elevation`/`glow` keys — once the shared `surfaces.tsx` prop signature is fixed by Claude)
- Commit 5 (`fontFamilies.readable` swap)
- Commit 6 (spacing/radii grid snap — **after** Claude confirms the type scale)
- Commit 8 partial (em-dash fix index:147, delete redundant ✕ index:427)

**Claude (integration / shared-component / behavioral / IA):**
- Commit 2 root fix in shared `surfaces.tsx` (`PremiumCard glow`, `PremiumButton`) — must land first so Codex's per-screen shadow deletions don't conflict.
- Commit 3 (a11y touch + Input hints — layout judgment)
- Commit 4 (shared `Button` focus/press states + Pressable→Button migration — touches behavior/loading)
- Commit 7 (reduced-motion gating — animation logic)
- Commit 9 (density/IA restructure — needs Simon checkpoint per §4)
- Commit 10 (dead-style/duplicate-component cleanup)
- SVG asset swap (C9) once assets decided.

**Sequencing constraint:** Claude lands the shared `surfaces.tsx`/`Button` changes (C2 root, C4) **before** Codex runs its per-screen style sweeps, to avoid both editing the same style blocks. Token commit (1) and font commit (5) are independent and can run fully parallel. Per CLAUDE.md §18, isolate the Codex sweep in a `git worktree`; commit small, Conventional-Commits, no `git add -A`.