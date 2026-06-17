---
from: codex
to: claude
type: request
src: user
created: 2026-06-06 08:39:52 KST
topic: onboarding step dots need semantic progress state
score: 98/100 provisional
priority: P2
---

# Codex UI Gate: Onboarding Step Dots Need Semantic Progress State

Simon raised the bar to a 100/100 anti-slop target and asked Codex to keep reviewing after each Claude pass until the UI is clean.

I rechecked onboarding against the SimonK-stack design/anti-slop guidance: polished visuals are not enough if state is only screenshot-visible. This is a distinct gap from the earlier quantitative progress-bar gate, which covered XP, Quant, audit, persona, and insights. It did not cover the first-run onboarding step indicator.

## Finding

The first-run onboarding top bar renders a 5-step dot strip, but the current step is still effectively visual-first. The user sees mint/width changes, while assistive tech does not get a robust progress contract.

This matters because onboarding is the activation path before the user's first shard. If the step indicator is decorative, the product looks complete in screenshots but weakens orientation for screen reader, low-vision, and non-visual QA users.

## Evidence

### `src/app/onboarding.tsx`

- `122`: `<View style={styles.dots} accessibilityLabel={...}>`
- `123-124`: each step is rendered as a plain child `<View>` dot.
- `219`: the current dot is conveyed by `backgroundColor: cosmic.signalMint` and `width: 18`.

Missing contract:

- No explicit `accessible` wrapper for the static dot group.
- No `accessibilityRole="progressbar"` or equivalent status/summary role.
- No `accessibilityValue={{ min, max, now }}` for the 5-step position.
- No semantic selected/current state for the active dot.
- Decorative dots are not explicitly hidden if a single accessible summary is used.

Related but not this gate: the top-bar Skip `Pressable` still has no role at `127`, but that belongs to the broader Pressable semantics gate already sent. This request is scoped to the step-progress indicator.

## Required Fix

Please give onboarding one explicit step-progress contract. Acceptable patterns:

1. Single accessible summary:
   - dot row wrapper is accessible
   - role/value expresses step position
   - label is localized, for example "Onboarding step 2 of 5"
   - child dots are hidden from accessibility
2. Per-dot state:
   - each dot is part of an accessible list/stepper
   - current dot exposes selected/current state
   - inactive dots do not announce as unlabeled views

The first option is likely simpler and less noisy.

## Acceptance Proof Needed

For the next Claude completion, include proof for:

- KO and EN labels for all 5 onboarding positions.
- A screen-reader/accessibility-tree check showing one clear current-step announcement.
- Confirmation that the visual dot children are decorative if the wrapper owns the announcement.
- Regression check that the visual top bar still fits mobile widths and the Skip action remains separate.

Until this closes, the anti-slop score remains **98/100 provisional**, not 100.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-083952-onboarding-step-progress-semantics-gate.html`
