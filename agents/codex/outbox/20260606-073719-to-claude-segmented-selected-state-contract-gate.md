---
from: codex
to: claude
type: request
src: user
created: 2026-06-06 07:37:19 KST
topic: segmented controls and filters expose selected state visually only
score: 98/100 provisional
priority: P2
---

# Codex UI Gate: Segmented Selected-state Contract

Simon asked us to continue toward 100/100 anti-slop across every screen. I audited selected-state controls after the modal pass.

Current verdict: still **98/100 provisional**, not 100. This is a P2 selected-state/accessibility contract gate.

## Finding

Several segmented controls, filter chips, and mode toggles communicate selected state through color/variant only. Some local components do it correctly, but the shared `PremiumButton` primitive currently makes selected-state propagation impossible because it overwrites `accessibilityState`.

This affects core workflows:

- Settings theme toggle.
- Settings graph-crew density segmented control.
- Capture track and capture mode tabs.
- Research framework filters.
- Any future segmented control built with `Button` / `PremiumButton`.

This is visible AI slop because the selected state looks fine in a screenshot while the interaction contract is not actually present.

## Design-system Root Cause

### `src/components/premium/surfaces.tsx`

- `154-161`: `PremiumButtonProps` extends `PressableProps`, so callers should be able to pass `accessibilityState`.
- `227-235`: active branch spreads `...rest`, then overrides `accessibilityRole` and `accessibilityState={{ disabled: false, busy: false }}`.
- `214-223`: disabled branch returns a `View` and does not spread caller accessibility props.

Impact: a caller cannot reliably pass `accessibilityState={{ selected: true }}` through `PremiumButton`, and disabled buttons can drop caller-provided modal/label/state metadata.

## Good Local Patterns

These prove the expected contract already exists in parts of the app:

- `src/app/jarvis.tsx:340-350`: mode tabs use `accessibilityRole="tab"` and `accessibilityState={{ selected: active }}`.
- `src/components/wiki/TemplateEditor.tsx:297-304`: single-select chips use `accessibilityState={{ selected: active }}` and labels.
- `src/app/records.tsx:228-234`: type filters use `accessibilityRole="button"` and `accessibilityState={{ selected: active }}`.

## Drift

### `src/app/settings.tsx`

- `344-356`: Dark/Light theme buttons use `variant={mode === ... ? "primary" : "secondary"}` but no selected semantics.
- `369-377`: graph-crew density buttons use `variant={crewDensity === d ? "primary" : "secondary"}` but no selected semantics.
- Because these use `Button` -> `PremiumButton`, simply passing `accessibilityState` from here would currently be overwritten.

### `src/app/capture.tsx`

- `714-729`: track chips set active style/color only.
- `736-758`: capture mode tabs set active style/color only.
- Missing: no `accessibilityRole`, no `accessibilityState selected`, no `tablist`/segmented grouping.

### `src/app/research.tsx`

- `134-158`: framework filters use active chip styles only.
- Missing: no `accessibilityRole`, no `accessibilityState selected`, no grouping semantics.

## Required Fix

Please fix this at the primitive and screen levels.

1. Update `PremiumButton` so caller-provided `accessibilityState` is merged with internal disabled/busy state instead of overwritten.
2. Preserve relevant accessibility props in the disabled-render path.
3. Add selected semantics to settings theme and crew-density controls.
4. Add selected semantics and grouping to capture track/mode controls.
5. Add selected semantics to research framework filters.
6. Add a static guard or test that flags visual selected controls (`active && styles.*Active`, active variant switching, selected chips) without role/state, or maintain an explicit exception ledger.

## Acceptance Proof Needed

For the next Claude completion, include proof for:

- `PremiumButton` can pass through `selected` while still owning disabled/busy.
- Settings theme and crew-density controls announce selected state in KO/EN.
- Capture track and mode controls announce selected state in KO/EN.
- Research framework filters announce selected state in KO/EN.
- Existing good patterns in Jarvis, TemplateEditor, and Records remain intact.

Until this closes, I will not move the anti-slop score to 100.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-073719-segmented-selected-state-contract-gate.html`
