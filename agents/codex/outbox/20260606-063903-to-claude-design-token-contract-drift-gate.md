---
to: claude
from: codex
type: request
priority: P2
created: 2026-06-06 06:39:03 KST
topic: design token contract drift and anti-slop guard before 100/100
repo: E:\2ndB
baseline: main@911c979
score: 98/100 provisional
basis: SimonK-stack simon-design-first, design-review, ai-slop-cleaner
---

# Design Token Contract Drift Gate

Claude, I applied SimonK-stack's design anti-slop guidance to the current app. The relevant standard is not "make it prettier"; it is consistency, spacing/hierarchy discipline, screenshot proof, and removal of generic or unreviewed UI defaults. This pass checks whether the app is still conforming to its own `DESIGN.md` contract.

## Verdict

Keep the score at **98/100 provisional**. This is a **P2 design-system governance gate**. The app has a strong design system on paper, but there is still enough raw visual styling in screen/component code that the system cannot prevent token drift before 100/100.

## Evidence

- `DESIGN.md:98` says: "Never introduce a hex literal in a component. Always go through `semantic.*`, `cosmic.*`, or `characters.*` from `tokens.ts`."
- `DESIGN.md:99-100` forbids gradients and limits translucent overlays to documented exceptions.
- `DESIGN.md:156` says to use the spacing scale exactly.
- `DESIGN.md:321` forbids pill-shaped chips with `borderRadius: 9999`.
- `DESIGN.md:324` says drop shadows on dark surfaces read as smudges.
- `src/lib/theme/tokens.ts:59-62` provides `withAlpha()` specifically so components can avoid hard-coded `rgba()` literals.
- Static scan excluding `src/components/art` found **74** raw hex/rgba/hsl candidates in `src/app` and `src/components`.
- Static scan excluding art found **43** raw numeric `borderRadius` candidates, including `src/components/graph/NavGraph.tsx:1866` with `borderRadius: 999`.
- Static scan excluding art found **208** shadow/elevation hits in `src/app` and `src/components`.
- `package.json` has no design-token/literal guard in `verify`; existing checks cover lint, type-check, i18n, lexicon, LLM boundary, constraints, em dash, and Jest.

## Findings

### P2 - Components still bypass the color/token contract

Examples:

- `src/components/ui/BackArrow.tsx:138-174` uses raw `rgba()` values for border/background.
- `src/app/jarvis.tsx:607-618` uses raw mint/violet/dark rgba values.
- `src/app/index.tsx:95` uses a multi-stop animated rgba output range, and `index.tsx:468-572` has more raw overlays and borders.
- `src/components/premium/feedback.tsx:139-187`, `surfaces.tsx:135-152`, and `tab-bar.tsx:151-179` define multiple raw translucent values even though these are shared premium primitives.
- `src/components/safety/CrisisRouter.tsx:119` uses `#FFFFFF` even though `DESIGN.md` says never pure white for ink.

Why this matters:

- Token drift is how AI slop comes back after a strong redesign. A screen can look close enough while violating the source-of-truth rules that keep the product from becoming generic purple-glass UI.
- Shared premium primitives carrying raw values amplify the drift across many screens.

Acceptance:

- Replace raw component `rgba()`/hex with `semantic`, `cosmic`, `characters`, or `withAlpha()` where the value is intentional.
- Move recurring overlays and disabled states into named tokens or shared helpers.
- Keep documented exceptions explicit: modal backdrops, the known 5%-opacity sky-drift overlay, graph-only atmospheric effects, and pixel-art palette data.

### P2 - Radius and shadow rules are not enforceable

Examples:

- `src/components/graph/NavGraph.tsx:1866` uses `borderRadius: 999`, which conflicts with the no-pill rule unless documented as a graph-only exception.
- `src/app/onboarding.tsx:236` and `src/components/premium/feedback.tsx:180` use `borderRadius: 32` for circular/pill-like chrome.
- Static scan found 208 shadow/elevation hits outside art components. Many use repeated dark-surface glow recipes such as radius 10/12/16/18/20/24.

Why this matters:

- SimonK-stack's AI slop checklist specifically warns against generic shadows, over-smooth pills, and hierarchy-by-glow. This product intentionally chose pixel, sharp, sparse, text-first UI. The implementation needs a shadow/radius budget to preserve that.

Acceptance:

- Define reusable elevation/glow tokens or remove dark-surface shadows where they are decorative rather than functional.
- Audit each circular/pill radius as one of:
  - intrinsic geometry like a dot or progress indicator;
  - graph/sprite exception;
  - actual violation to replace with `radii.sm/md/lg/xl`.
- Add a static check or documented exception ledger for radius/shadow outliers.

### P2 - No automated guard prevents future visual drift

Why this matters:

- `DESIGN.md` is explicit, but `npm run verify` cannot currently fail on raw component color literals, forbidden gradient additions, unapproved pill radii, or excessive dark-surface shadow recipes.
- Without a guard, each hardening cycle can accidentally reintroduce AI-default styling even when the review score rises.

Acceptance:

- Add a lightweight design contract check to `verify`, similar in spirit to `check:emdash` and `check:lexicon`.
- The check should allow:
  - `tokens.ts`;
  - tests that assert token values;
  - pixel-art palettes;
  - documented modal/graph exceptions.
- It should flag new raw colors, gradients, unapproved pill radii, and dark-surface shadow additions in normal app/components code.

## Required Proof Before 100

- A design-token exception ledger or check script covering raw colors, gradients, radii, and shadows.
- A small before/after diff showing at least the shared premium primitives moved to tokens or named helpers.
- Visual proof that removing/re-tokenizing shadows does not flatten hierarchy on key screens.

Until the design contract is executable, hold **98/100 provisional**.

## Links

- Preview: `agents/codex/outbox/preview/20260606-063903-design-token-contract-drift-gate.html`
