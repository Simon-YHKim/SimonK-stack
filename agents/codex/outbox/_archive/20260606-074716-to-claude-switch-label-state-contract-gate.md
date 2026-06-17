---
from: codex
to: claude
type: request
src: user
created: 2026-06-06 07:47:16 KST
topic: switch controls rely on adjacent row copy instead of a shared label/state contract
score: 98/100 provisional
priority: P2
---

# Codex UI Gate: Switch Label/State Contract

Simon asked for 100/100 anti-slop across every screen. I audited switches/toggles after the form-field semantics gate.

Current verdict: still **98/100 provisional**, not 100. This is a P2 switch semantics gate.

## Finding

Several switch controls look correct because they sit beside visible text, but the switch itself is a separate interactive target with no consistent label, hint, disabled reason, pending state, or row-level semantic wrapper.

This affects privacy preferences and testimonial consent. Those are high-trust surfaces: if the user cannot clearly identify what a switch changes, the visual polish is not enough.

## Root Cause

There is no shared `SwitchRow`, `PreferenceToggle`, or equivalent design-system contract. Each screen wires `Switch` directly.

The current pattern depends on adjacent text layout rather than a governed semantic unit.

## Evidence

### `src/app/privacy.tsx`

- `162-188`: `PRIVACY_PREF_KEYS.map` renders a visual row with:
  - label text: `t(\`privacy.keys.${key}.label\`)`
  - description text: `t(\`privacy.keys.${key}.desc\`)`
  - optional locked tag
  - bare `Switch`
- `181-188`: the `Switch` only passes `value`, `disabled`, `onValueChange`, and `trackColor`.
- Missing: explicit switch label, description/hint, locked reason, checked/disabled state contract, and pending/save-failure announcement tied to the changed preference.

Minor-locked rows especially need the switch to expose why it is disabled, not only show a locked badge next to nearby text.

### `src/components/consent/ConsentDialog.tsx`

- `44-50`: testimonial consent uses two rows with visible text and bare switches:
  - `testimonial.shareWithJudges`
  - `testimonial.approveForPublic`
- Missing: explicit labels/hints on the switches or a row-level control wrapper.

These are consent flags, so they need stronger semantics than a generic switch.

### Positive local examples

- `src/components/consent/ConsentNotice.tsx:38-45` makes the whole row a checkbox and exposes `accessibilityRole="checkbox"` plus `accessibilityState={{ checked }}`.
- `src/app/formats.tsx:349-355` gives the share switch an explicit `accessibilityLabel`.

The building blocks exist, but raw switch usage is still inconsistent.

## Required Fix

Please define a shared switch/preference toggle contract instead of fixing isolated screens ad hoc.

1. Add a `SwitchRow` / `PreferenceToggle` component, or equivalent, that owns:
   - label,
   - description/helper text,
   - checked state,
   - disabled state and disabled reason,
   - pending/busy state when writes are in flight.
2. Use it in `/privacy` for every privacy preference.
3. Use it in `ConsentDialog` for testimonial consent flags.
4. Consider migrating `/formats` share toggle into the same component so pending share writes expose disabled/busy state consistently.
5. Add a static guard or exception ledger for raw `<Switch>` usage outside the shared component.

## Acceptance Proof Needed

For the next Claude completion, include proof for:

- `/privacy` switches expose localized KO/EN labels and descriptions.
- Minor-locked privacy switches expose a disabled/locked reason.
- Privacy save failure is announced or clearly associated with the changed preference.
- Testimonial consent dialog switches expose localized KO/EN labels and hints.
- `/formats` share switch still exposes the format name, checked state, and pending disabled/busy state.
- Static scan or ledger for remaining raw `<Switch>` usage.

Until this closes, I will not move the anti-slop score to 100.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-074716-switch-label-state-contract-gate.html`
