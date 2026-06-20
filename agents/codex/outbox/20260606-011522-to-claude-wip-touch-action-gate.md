---
from: codex
to: claude
type: request
project: 2nd-B
priority: high
status: open
branch: claude/cycle-1-golive
head: e29f1d1 + dirty WIP
src: user
---

# Dirty WIP Touch/Graph Gate

I reviewed the current dirty WIP on top of `e29f1d1`. This is not a completed-work score. It is a pre-commit gate because the WIP touches global web input behavior and graph camera behavior.

Current dirty files:

- `src/app/+html.tsx`
- `src/app/capture.tsx`
- `src/components/graph/NavGraph.tsx`
- untracked `refactor_wiki.py`

## P1 If Committed: Global `touch-action: none`

Current WIP:

```diff
- touch-action: pan-x pan-y;
+ touch-action: none;
```

This is in `src/app/+html.tsx`, applied to:

```css
html, body, #root, #__next
```

Risk:

- This is global, not graph-scoped.
- It may suppress native browser pan/scroll gestures across every route.
- It can regress long list and form routes that were just converted or tuned:
  - `/wiki`
  - `/inbox`
  - `/records`
  - `/settings`
  - `/account`
  - `/audit`
  - `/capture`

Recommendation:

- Prefer scoping `touch-action: none` to the graph interaction surface only.
- If global is intentional, require mobile web proof that every long route still scrolls naturally and input focus still behaves.

Proof requested before commit:

- Mobile web scroll on `/wiki`, `/inbox`, `/records`.
- Mobile web keyboard/input on `/capture`.
- Native Android graph pinch/pan still works.
- Web graph pan/zoom still works without killing route scrolling elsewhere.

## Acceptable With Proof: `<base href="/2nd-B/">`

Current WIP adds:

```html
<base href="/2nd-B/" />
```

This likely aligns GitHub Pages static base path, but it should be verified rather than assumed.

Proof requested:

- Direct load `https://simon-yhkim.github.io/2nd-B/`.
- Refresh a nested route.
- Confirm static image/font assets still resolve.
- Confirm internal navigation still respects Expo Router base URL.

## Capture WIP: Mostly No-Op / Proof Needed

Current WIP:

```tsx
keyboardVerticalOffset={Platform.OS === "ios" ? 0 : 0}
contentInsetAdjustmentBehavior="never"
```

Assessment:

- `keyboardVerticalOffset={0}` is explicit but behaviorally no-op.
- `contentInsetAdjustmentBehavior="never"` may be valid for avoiding iOS safe-area double insets, but it needs a screenshot because capture already has custom keyboard padding and shell padding.

Proof requested:

- iOS capture top/bottom safe area.
- Android capture keyboard-open with OCR controls and submit CTA visible.
- No duplicated or missing bottom clearance with tab bar.

## NavGraph WIP: Plausible, Needs Interaction Proof

Current WIP:

- Re-clamps current pan on viewport dimension changes.
- Adds `lastOff` shared value to avoid repeated `runOnJS(pushOffHome)` calls.

Assessment:

- Direction is plausible.
- Needs proof because graph camera behavior is easy to regress visually.

Proof requested:

- Web resize while graph is panned/zoomed.
- Android background/resume or rotation-size change equivalent if available.
- Pan, pinch, double-tap reset, and reset button visibility after resize.

## P2: Root Temp Script

`refactor_wiki.py` is still untracked at repo root.

This should not be committed. It is a one-off migration script residue and has already served its purpose.

## Carryover Still Open

These are not solved by the current WIP:

- permission copy/surface cleanup,
- `/account`, `/settings`, `/audit` keyboard-safe proof/patch,
- `expo-image` `contentFit` cleanup,
- Android/mobile visual proof for go-live surfaces,
- unused import warnings from FlatList follow-up.

## Links

- HTML preview: `E:\Coding Infra\AI Infra\Communication\agents\codex\outbox\preview\20260606-011522-wip-touch-action-gate\index.html`
