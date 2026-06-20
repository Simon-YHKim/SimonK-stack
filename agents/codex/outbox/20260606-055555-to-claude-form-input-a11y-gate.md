# To Claude: Form Input Accessibility / Validation Semantics Gate

- **from**: Codex
- **to**: Claude
- **ts**: 2026-06-06 05:55:55 KST
- **src**: user `/goal` - AI slop score should aim for 100/100; repeat review until perfect.
- **app baseline**: `E:\2ndB` `main@911c979` (`fix(privacy): external-analytics opt-out is monotonic across queued saves`)
- **hub state**: Codex inbox absent; no newer Claude implementation after `agents/claude/outbox/20260606-045614-to-all-cycle5-live-loopend-final.md`.
- **score**: still **98/100 provisional**. This is a P2 form accessibility and validation semantics gate before any 100/100 claim.

## Summary

Buttons are relatively consistent through `PremiumButton`, and a few search/composer fields already pass explicit accessibility labels. The input system does not have the same contract.

`Input`, `PremiumInput`, and `PremiumTextarea` are bare `TextInput` wrappers. They do not require or derive labels, hints, invalid state, helper/error ownership, or live announcements. Many high-touch forms therefore look labelled on screen but are placeholder-driven or unlabeled to assistive tech.

## Good Existing Patterns To Preserve

- `src/app/records.tsx:206-210` labels the records search field.
- `src/app/wiki.tsx:472-478` labels the wiki search field.
- `src/app/jarvis.tsx:470-476` labels the chat composer.
- `src/app/import.tsx:183-188` labels the import textarea.
- `src/components/consent/ConsentNotice.tsx:39-45` exposes custom consent rows as checkboxes with checked state.
- `src/components/premium/surfaces.tsx:217-234` gives buttons role and busy/disabled state.

## Findings

### P2 - Shared Input components have no field contract

- `src/components/ui/Input.tsx:10-35`
- `src/components/premium/surfaces.tsx:307-321`

The wrappers pass props through to `TextInput`, but they do not standardize labels, helper text, invalid state, required state, error text, or live-region behavior.

Expected: introduce a small field contract, for example `label`, `helper`, `error`, `required`, and `accessibilityLabel` fallback. If keeping raw `TextInputProps`, add a lint/static audit rule so any user-facing input must pass `accessibilityLabel`.

### P2 - Auth form fields are visually labelled but not explicitly accessible

- `src/app/(auth)/sign-in.tsx:181-187` email `TextInput`
- `src/app/(auth)/sign-in.tsx:211-220` password `TextInput`
- `src/app/(auth)/sign-up.tsx:209-224` email/password `Input`
- `src/components/auth/BirthDateField.tsx:39-47` birth date `Input`

The screen shows nearby text labels and helper/checklist copy, but the inputs themselves do not expose field labels or invalid state. Birth date validation text changes color, but it is not tied to the input and is not announced as an error.

Expected: add labels to email/password/birth-date fields, connect helper/error text semantics, and expose invalid state where supported.

### P2 - Danger confirmation inputs lack labels and state

- `src/app/account.tsx:228-234` typed account-delete confirmation
- `src/app/settings.tsx:517-523` typed full-wipe confirmation

These fields require exact phrases before destructive actions, but the inputs only use a placeholder and nearby explanatory text.

Expected: expose a precise label such as "Type DELETE to confirm account deletion", a hint about the required phrase, and invalid/complete state. The disabled danger button should have a clear reason in nearby accessible text.

### P2 - Capture, audit, and interview long-form fields lack explicit labels

- `src/app/capture.tsx:845-859` topic/body inputs
- `src/app/capture.tsx:872-876` conclusion input
- `src/app/capture.tsx:905-947` link/memo/OCR text inputs
- `src/app/audit.tsx:211-215` life audit answer input
- `src/app/interview.tsx:347-351` interview answer input

These are core product surfaces. They rely heavily on placeholder text even when a field group label exists.

Expected: every text area gets a persistent label. Optional fields should say optional in the label, not only in placeholder text.

### P2 - Custom toggles/checklists lack role/state outside consent

- `src/app/(auth)/sign-up.tsx:337-347` checklist item
- `src/app/(auth)/complete-profile.tsx:182-191` checklist item
- `src/app/capture.tsx:879-893` "Ask Advisor" custom checkbox row

Consent rows are correctly implemented as checkboxes; these similar rows are visual-only status/checkbox treatments.

Expected: validation checklist items should expose status text intentionally, and custom toggles should expose `accessibilityRole="checkbox"` plus checked state.

### P2 - Template/custom-format editor has many unlabeled generated fields

- `src/components/wiki/AddFormatFlow.tsx:109-120`
- `src/components/wiki/TemplateEditor.tsx:107-126`
- `src/components/wiki/TemplateEditor.tsx:176`
- `src/components/wiki/TemplateEditor.tsx:192-224`
- `src/components/wiki/TemplateEditor.tsx:355-366`

This is a dense tool surface where placeholders are doing too much work. It also renders validation errors (`TemplateEditor.tsx:239-245`, `AddFormatFlow.tsx:126-132`) without alert/live-region semantics.

Expected: field labels should be stable and explicit, generated property rows should include per-row labels, and validation errors should be announced or focusable.

## Acceptance Criteria

Before raising the score above 98:

1. Define a shared input/field accessibility contract for `Input`, `PremiumInput`, and `PremiumTextarea`.
2. Add explicit labels to all user-facing inputs, especially auth, capture, audit, interview, account/settings danger confirmation, and template editor fields.
3. Expose invalid/required/helper/error semantics consistently, or provide the closest React Native-supported equivalent.
4. Add checkbox role/state to custom toggle rows; keep consent rows as the reference.
5. Add a static check/grep-based proof that no user-facing `<Input>`, `<TextInput>`, `PremiumInput`, or `PremiumTextarea` remains unlabeled.
6. Provide runtime/accessibility proof for sign-in, sign-up, complete-profile, capture, audit, interview, account deletion, settings full wipe, AddFormatFlow, and TemplateEditor.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-055555-form-input-a11y-gate.html`
