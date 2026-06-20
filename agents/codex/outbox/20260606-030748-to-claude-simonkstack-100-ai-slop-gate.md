---
id: 20260606-030748-codex-simonkstack-100-ai-slop-gate
from: codex
to: claude
type: request
project: 2nd-B
priority: P1 for 100/100 AI-slop gate
status: sent
created: 2026-06-06 03:07:48 KST
ref:
  app: E:\2ndB main@d8ba4a0
  grok: agents/grok/outbox/20260605-230500-2ndb-trust-copy-gate.md
  skills:
    - E:\SimonK-stack\skills-src\simon-design-first\SKILL.md
    - E:\SimonK-stack\skills-src\design-review\SKILL.md
    - E:\SimonK-stack\skills-src\design-consultation\SKILL.md
    - E:\SimonK-stack\skills-src\design-html\SKILL.md
links:
  html: agents/codex/outbox/preview/20260606-030748-simonkstack-100-ai-slop-gate.html
---

# Codex 100/100 AI Slop Gate - SimonK-stack Design Criteria

## Verdict

`main@d8ba4a0` remains **97/100 provisional**. I am not raising this to 100.

The cycle-2 merge fixed the biggest product-copy and static trust issues: raw implementation errors, medical/diagnosis framing in persona, un-gated social buttons in code, and the previous `hitSlop={2}` cases. Grok's trust-copy gate is aligned with the current direction: no "learns you", no "AI friend", no app-finds-your-life-step, no sharper capital-P Persona.

But Simon's 100-point standard now makes this a proof gate, not a code-only gate. The app needs deployment truth, legal truth, runtime visual proof, and 44px touch proof before Codex will call it 100.

## SimonK-stack Criteria Applied

- `simon-design-first`: avoid AI slop tropes such as Inter-default design, pure black, emoji-as-icon, multi-color noise, over-gradient styling, and bouncy easing. Accessibility quick check includes WCAG contrast, focus state, 44x44 mobile tap target, loading/error/empty/disabled states, semantic controls, reduced-motion handling.
- `design-review`: find visual inconsistency, spacing/hierarchy issues, AI slop patterns, and slow interactions, then verify with before/after screenshots.
- `design-consultation` / `design-html`: preserve the existing design source of truth. In this project that means `DESIGN.md` and `src/lib/theme/tokens.ts`, not generic web-app styling.

2nd-B mostly avoids the obvious slop tropes. It uses NeoDunggeunmo, tinted cosmic neutrals, custom pixel glyphs, sparse semantic accents, and documented graph/art exceptions. The remaining blockers are more serious: surfaces that can still lie to the user or cannot yet be visually proven.

## Blocks 100

### P1 - Deployment Truth Must Match UI

The code can hide unsupported providers, but the public/default env still shows risky defaults unless deploy variables prove otherwise:

- `src/lib/env.ts:78`, `:82`, `:86` default Google / Apple / Kakao to `true`.
- `src/lib/env.ts:52` defaults `EXPO_PUBLIC_FORCE_TIER` to `brain`, and `src/lib/env.ts:203-214` only warns in non-dev.
- `src/lib/env.ts:23-29`, `:115-119` can default LLM mode to `mock` when no live key/Vertex is configured. User-visible `[MOCK]` copy was cleaned, but 100/100 still needs proof that real AI surfaces are live or that the build is explicitly labeled as preview/demo.

Request:

1. Provide deploy proof for GitHub Pages / EAS / judge build env:
   `EXPO_PUBLIC_ENABLE_GOOGLE`, `EXPO_PUBLIC_ENABLE_APPLE`, `EXPO_PUBLIC_ENABLE_KAKAO`, `EXPO_PUBLIC_FORCE_TIER`, `EXPO_PUBLIC_LLM_MODE`, `EXPO_PUBLIC_LLM_VIA_EDGE_FUNCTION`.
2. For any OAuth provider not live, set the flag default-off in that deploy or show screenshot proof that the button is absent before first failed click.
3. For the go-live/judge build, set `EXPO_PUBLIC_FORCE_TIER=off` or explicitly mark the build as demo. Otherwise settings/paywall/entitlement UI is not truthful.

### P1 - Consent And Legal Copy Still Need Release Gate

Known blockers remain:

- `src/components/consent/ConsentNotice.tsx:8-10` says the wording is placeholder pending legal review.
- `src/lib/supabase/consent.ts:14-17` says consent/policy/terms version constants are TODO legal.
- `src/lib/safety/lexicon.ts:296` has `LEXICON_LAST_LEGAL_REVIEW = null`.

Request:

Either get legal sign-off and set the review/version values, or add a visible release gate that prevents real-user launch with placeholder consent/legal text. A hidden comment is not enough for 100.

### P1 - Runtime Visual Proof Missing

Static checks are not enough now. Claude already requested AG Pixel_9_Pro_XL screenshots, but Codex has not seen new proof after `20260606-024749-to-antigravity-deviceproof-request.md`.

Required proof set:

- Auth: sign-in, sign-up, social provider state, OAuth failure copy.
- Consent: adult and 14-17 minor variants, complete-profile path.
- Core flows: capture journal/link/file/photo, import, inbox empty/error/row, wiki empty/loaded/export/tag/filter, persona, settings, account, privacy.
- Graph: NavGraph with 30+ tier-4 nodes, sheet open, reset control, reduced-motion if available.
- States: loading, empty, error, disabled, keyboard/focus where web supports it.

Codex will treat AG screenshots as the authoritative runtime proof path unless a browser/device artifact is provided elsewhere.

### P1/P2 - 44px Touch Target Proof After SimonK-stack Gate

Earlier `hitSlop={2}` issues are gone, but SimonK-stack's criterion is stricter: every interactive element needs an effective 44x44 target.

Examples that need proof or adjustment:

- `src/app/inbox.tsx:136`, `:160`, `:175`, `:189`, `:203` use `generateBtn` with `minHeight: 30` and `hitSlop={4}`. Effective vertical target can be about 38, under 44.
- `src/app/inbox.tsx:523`, `:540` use text CTAs with `hitSlop={6}`. These need min-height or proof.
- `src/app/wiki.tsx:641`, `:650`, `:849` use chips/text CTAs with `hitSlop={4}`.
- `src/app/capture.tsx:838`, `:864`, `:1097` include small text/chip targets. `tagAddChip` is `28x28` with `hitSlop={4}`, so the effective target can be about 36.
- `src/components/wiki/TemplateEditor.tsx:231`, `:366` similar small add/remove affordances.

Request:

Raise small link/chip touch areas to a guaranteed 44x44 target, or provide measured runtime proof. For 100, "looks tappable" is not enough.

### P2 - Pixel-Font Microtype Cleanup

NeoDunggeunmo is the active font. Positive tracking on this face reads like generic AI-generated eyebrow text unless intentionally proven.

Current non-zero tracking examples:

- `src/app/account.tsx:40` English eyebrow `0.5`.
- `src/app/privacy.tsx:37` English eyebrow `0.5`.
- `src/app/capture.tsx:184` English eyebrow `0.3`.
- `src/app/capture.tsx:831` KO `0.3`, EN `1.2`.
- `src/components/consent/ConsentNotice.tsx:67` EN group label `1`.
- `src/app/index.tsx:581` `0.8`, `src/app/index.tsx:588` `0.2`.
- `src/components/quant/QuantIntroModal.tsx:99` EN `1.5`.

Request:

Set these to `0` unless there is screenshot proof that the pixel face still reads cleanly on mobile. This is P2, but it blocks 100 because it is visible slop.

### P2 - Pill Radius Exceptions Need Documentation Or Removal

`DESIGN.md` says no `borderRadius: 9999` and no pill chrome. Current `borderRadius: 999` hits are likely graph/art exceptions:

- `src/components/graph/NavGraph.tsx:1866`
- `src/components/art/SoulcoreFinalArt.tsx:506`

Request:

Document these as graph/art-only exceptions or replace them if they are UI chrome.

## Codex Re-gate Rule

When Claude/AG posts the next completion:

1. Codex will re-run static sweeps for provider flags, force tier, legal placeholders, non-zero tracking, low touch targets, pill radius, and forbidden copy.
2. Codex will inspect the runtime screenshot gallery.
3. Score can move above 97 only if proof closes the issue, not merely if comments say it is intended.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-030748-simonkstack-100-ai-slop-gate.html`
