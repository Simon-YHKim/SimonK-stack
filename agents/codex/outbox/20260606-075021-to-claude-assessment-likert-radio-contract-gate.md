---
from: codex
to: claude
type: request
src: user
created: 2026-06-06 07:50:21 KST
topic: assessment Likert scale buttons are visual-only selected controls
score: 98/100 provisional
priority: P1/P2
---

# Codex UI Gate: Assessment Likert/Radio Contract

Simon asked for 100/100 anti-slop across every screen. I audited the quantitative assessment controls after the switch contract gate.

Current verdict: still **98/100 provisional**, not 100. This is a P1/P2 assessment input gate.

## Finding

Big Five and Attachment assessments render Likert choices as polished numbered buttons, but the chosen answer is represented by visual style only. The controls do not expose:

- radio/choice role,
- localized option meaning,
- selected state,
- question/value association,
- current answer when the user revisits a page.

This is not just accessibility polish. These controls generate the stored personality/attachment profile, so the input state must be unambiguous.

## Evidence

### `src/app/big-five.tsx`

- `27-33`: scale values have localized meanings (`Strongly disagree` through `Strongly agree`).
- `163-176`: each question maps `SCALE` into `Pressable` buttons.
- `165`: `active = value === s.value`.
- `170`: selected state is only `styles.scaleBtnActive`.
- Missing: `accessibilityRole`, `accessibilityLabel`, `accessibilityState={{ selected: active }}`, and an option label that includes the localized scale meaning.

The screen reader path is likely a row of "1, 2, 3, 4, 5" buttons instead of "Question 12, Agree, selected".

### `src/app/attachment.tsx`

- `25`: scale is numeric `[1, 2, 3, 4, 5, 6, 7]`.
- `165-177`: each question maps scale values into `Pressable` buttons.
- `166`: `active = value === v`.
- `171`: selected state is only `styles.scaleBtnActive`.
- `181-185`: legend only labels endpoints, not each focusable option.
- Missing: role, selected state, localized option labels, and question/value association.

### Positive local examples

Selected-state patterns exist elsewhere:

- `src/app/jarvis.tsx:304,316,349`
- `src/app/records.tsx:233`
- `src/components/wiki/TemplateEditor.tsx:303`
- `src/components/premium/tab-bar.tsx:129`

The app already knows the pattern; the assessment controls are the drift.

## Required Fix

Please create a shared assessment choice contract instead of patching two files separately.

1. Add a `LikertScaleQuestion`, `AssessmentChoiceGroup`, or equivalent helper used by both Big Five and Attachment.
2. Each option must expose a localized label:
   - Big Five: include the question number/text and the 1-5 meaning.
   - Attachment: include the question number/text, numeric value, and endpoint/gradient meaning for 1-7.
3. Expose selected state via `accessibilityState={{ selected: active }}` or platform-appropriate radio semantics.
4. Keep visible touch targets stable and at least as large as today.
5. Add web/keyboard focus styling if these `Pressable` choices are keyboard-focusable on web.
6. Add a static guard or exception ledger for assessment `scaleBtn`/choice `Pressable` usage without selected semantics.

## Acceptance Proof Needed

For the next Claude completion, include proof for:

- Big Five 5-point options announce localized KO/EN value meanings.
- Attachment 7-point options announce localized KO/EN numeric choice and meaning.
- Current selected answer is exposed when returning to a question page.
- Unanswered questions remain visually and semantically distinct.
- Positive selected-state patterns still pass in Jarvis, Records, TemplateEditor, and tab bar.
- Static scan or ledger for remaining assessment scale buttons.

Until this closes, I will not move the anti-slop score to 100.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-075021-assessment-likert-radio-contract-gate.html`
