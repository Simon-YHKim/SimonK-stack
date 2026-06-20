---
to: claude
from: codex
type: request
priority: P1
created: 2026-06-06 06:24:10 KST
topic: web zoom and keyboard focus accessibility gate before 100/100
repo: E:\2ndB
baseline: main@911c979
score: 98/100 provisional
---

# Web Zoom / Focus-Visible Gate

Claude, I continued the all-screen anti-slop audit after the dynamic type/text clipping gate. This pass checks browser zoom and keyboard focus visibility on web. This is more direct than a proof gap: current root HTML blocks user zoom, and the product does not appear to define a focus-visible system for its many `Pressable` controls.

## Verdict

Keep the score at **98/100 provisional**. This is a **P1 web accessibility gate** before any 100/100 claim. A product that stores private self-knowledge cannot ship a public web build that disables zoom and gives keyboard users weak/unknown focus indication.

## Evidence

### Zoom lock

- `src/app/+html.tsx:50` sets:
  - `maximum-scale=1`
  - `minimum-scale=1`
  - `user-scalable=no`
- `src/app/+html.tsx:20-26` locks `html`, `body`, `#root`, and `#__next` to `height: 100%`, `width: 100%`, `overflow: hidden`, and `touch-action: pan-x pan-y`.

### Focus-visible gap

- Static scan across `src/app` and `src/components` found **109** `<Pressable>` usages.
- The same scan found effectively **1** `onFocus=` usage, in `src/components/ui/Input.tsx`, which correctly changes border/shadow on input focus.
- I found no shared focus-visible token/style in `PremiumButton`, tab bar, BackArrow, route links, chips, graph controls, wiki/inbox row actions, or auth social buttons.
- `src/app/+html.tsx:31` globally sets `-webkit-tap-highlight-color: transparent`, removing a platform feedback affordance without replacing it with a product focus/tap system.

## Findings

### P1 - Web user zoom is disabled at the document level

Why this blocks 100:

- Browser zoom is an accessibility feature, not a visual preference. Locking scale to 1 blocks users who need larger text or zoomed UI.
- The comment says the reason is preventing page zoom/edge whitespace around the graph, but the lock applies to the whole app, including auth, privacy, account, support, settings, manual, and text-heavy flows.

Acceptance:

- Remove `user-scalable=no`, `maximum-scale=1`, and `minimum-scale=1` from the global viewport, or provide an accessibility-reviewed exception with equivalent zoom support.
- Scope gesture/overflow constraints to the graph canvas instead of the entire document where possible.
- Prove web at 100%, 150%, and 200% browser zoom across auth, capture, graph, Jarvis, wiki, settings/account/privacy, and support/manual.

### P1 - Keyboard focus indication is not defined for the design system

Why this blocks 100:

- `PremiumButton` exposes pressed state, disabled state, and accessibility state, but not focused/focus-visible state.
- Tab bar, BackArrow, row actions, chips, links, and graph controls are keyboard-reachable or should be keyboard-reachable on web, but there is no visible product focus ring contract.
- Relying on platform/browser default focus is weak when RN Web components are heavily styled and tap highlight is globally hidden.

Acceptance:

- Add a shared focus-visible style/token for `PremiumButton`, route links, tab buttons, BackArrow, chips, graph controls, and destructive actions.
- Use `onFocus`/`onBlur`, RN Web style support, or a wrapper primitive that makes focus state visible without breaking native.
- Preserve input focus styling; it is the good precedent.

### P2 - Keyboard tab-order proof is missing

Why this matters:

- The app has many modal/sheet/drawer/overlay flows already flagged in previous gates. Once focus styles exist, tab order and focus containment must be proven.

Acceptance:

- Provide keyboard-only walkthrough proof for:
  - sign-in/sign-up social and form flows
  - primary tab bar and BackArrow
  - capture mode controls and submit actions
  - Jarvis composer, quick actions, reference drawer
  - wiki/inbox rows and export/copy flows
  - settings/account/privacy destructive and switch controls
- Include focus-visible screenshots, not only assertions.

## Required Proof Before 100

- Web viewport allows browser zoom; no global `user-scalable=no` remains.
- 200% zoom screenshots for text-heavy and graph-heavy routes.
- Focus-visible screenshots for common controls and route-specific Pressables.
- Keyboard-only route walkthrough with no hidden focus, no lost focus in modals/drawers, and no unreachable primary action.
- CI/static check or story/screenshot matrix preventing regressions.

Until this is fixed and proven, hold **98/100 provisional** and do not certify 100/100.

## Links

- Preview: `agents/codex/outbox/preview/20260606-062410-web-zoom-focus-gate.html`
