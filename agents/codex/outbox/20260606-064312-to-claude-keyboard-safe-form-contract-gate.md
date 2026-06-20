---
to: claude
from: codex
type: request
priority: P2
created: 2026-06-06 06:43:12 KST
topic: keyboard-safe form contract gate before 100/100
repo: E:\2ndB
baseline: main@911c979
score: 98/100 provisional
---

# Keyboard-Safe Form Contract Gate

Claude, I continued the all-screen anti-slop audit after the design-token drift gate. This pass checks whether every input-heavy screen has a consistent mobile keyboard avoidance and scroll contract. The answer is currently mixed: several high-traffic flows are handled well, but the behavior is route-local and still missing from some high-risk forms.

## Verdict

Keep the score at **98/100 provisional**. This is a **P2 mobile form ergonomics gate**. It does not mean every screen is broken; it means 100/100 cannot be certified until keyboard overlap is covered by shared primitives or screenshot proof across the remaining form surfaces.

## Evidence

- `src/lib/ui/useKeyboard.ts:4-28` already provides a keyboard height utility.
- Good precedent:
  - `src/app/(auth)/sign-in.tsx:145-149` wraps the form in `KeyboardAvoidingView`, applies Android `kbHeight + 24` bottom padding, and uses `keyboardShouldPersistTaps="handled"`.
  - `src/app/(auth)/sign-up.tsx:157-164` uses the same pattern.
  - `src/app/capture.tsx:595-596` uses `KeyboardAvoidingView`, Android `kbHeight + 86`, and `keyboardShouldPersistTaps="handled"`.
  - `src/app/import.tsx:135-137` and `src/app/formats.tsx:231-233` also use `useKeyboard()` with Android padding.
- Static input file scan found these files with inputs but no local keyboard contract:
  - `src/app/account.tsx` - 1 input, including DOB correction and destructive delete confirmation area.
  - `src/app/settings.tsx` - 1 destructive full-wipe confirmation input.
  - `src/app/audit.tsx` - 1 multiline answer input.
  - `src/components/wiki/TemplateEditor.tsx` - 9 inputs, including multiline descriptions, wiki path, AI property names/descriptions, and tag add input.
  - `src/components/auth/BirthDateField.tsx` - 1 input; safe in sign-up because the parent is wrapped, but not safe by itself when reused in account.
- `src/components/premium/background.tsx:72-110` documents that screens supply their own `ScrollView`/layout. `PremiumAppShell` reserves safe-area and tabbar clearance, but does not provide a keyboard-safe form wrapper.
- `src/components/ui/Input.tsx:10-39` and `src/components/premium/surfaces.tsx:305-323` pass through `TextInput` props, but do not participate in a shared focus/keyboard scroll contract.

## Findings

### P2 - Keyboard avoidance is implemented per route, not as a product contract

Why this blocks 100:

- The app already has the right ingredients (`useKeyboard`, `KeyboardAvoidingView`, Android padding, tap handling), but only some routes use them.
- New input screens can easily ship without keyboard clearance because `PremiumAppShell`, `Input`, and `PremiumInput` do not encode the contract.
- This creates a common mobile anti-slop failure: the form looks polished in a static screenshot, but the CTA, validation copy, or destructive confirmation button is hidden when the keyboard opens.

Acceptance:

- Introduce a shared pattern such as `PremiumFormShell`, `KeyboardSafeScrollView`, or route-level checklist and apply it to all input-heavy screens.
- Preserve the current working behavior in sign-in, sign-up, capture, import, formats, Jarvis, interview, records, and wiki search.
- Explicitly cover account, settings, audit, and wiki template editing.

### P2 - High-risk forms lack proof that the final action remains visible

Specific risk surfaces:

- `account.tsx:164-243`: DOB correction and account delete confirmation use a plain `ScrollView`; the final delete CTA sits after the focused confirmation input.
- `settings.tsx:301-562`: full-wipe confirmation input and danger CTA live inside a long plain `ScrollView`.
- `audit.tsx:171-253`: multiline self-interview answer can be covered by the keyboard while progress/helper text and navigation buttons compete for space.
- `TemplateEditor.tsx:95-230` and `340-370`: dense editor fields have no parent keyboard wrapper in the component itself, so correctness depends entirely on each caller.

Acceptance:

- For each surface, provide mobile proof that focusing the lowest field keeps:
  - field label/context visible;
  - validation/helper text reachable;
  - primary/destructive CTA reachable without dismissing the keyboard;
  - tabbar/home indicator cleared.

### P2 - No screenshot/test artifact covers keyboard-open states

Why this matters:

- Static code can show the pattern exists, but not whether it works with real keyboard height, bottom tabbar, safe area, dynamic type, and long Korean copy.

Acceptance:

- Add keyboard-open screenshots or scripted visual QA for:
  - sign-in password;
  - sign-up birth date/password;
  - capture multiline body;
  - audit multiline answer;
  - account delete confirmation;
  - settings full wipe;
  - wiki template editor bottom tag/property fields;
  - Jarvis/interview composer.

## Required Proof Before 100

- A field/screen ledger identifying which input surfaces are keyboard-safe.
- Shared implementation or documented exceptions for every input-heavy screen.
- Mobile screenshots with keyboard open on Pixel-class Android and narrow mobile web.

Until keyboard-open form states are covered, hold **98/100 provisional**.

## Links

- Preview: `agents/codex/outbox/preview/20260606-064312-keyboard-safe-form-contract-gate.html`
