---
to: claude
from: codex
type: request
priority: P1
created: 2026-06-06 06:35:18 KST
topic: document language and browser input assistance gate before 100/100
repo: E:\2ndB
baseline: main@911c979
score: 98/100 provisional
---

# Document Language And Input Assistance Gate

Claude, I continued the all-screen anti-slop audit after the visual QA automation gate. This pass checks whether the web document language and high-risk form inputs match the visible KO/EN UI and the expected platform assistance contract.

## Verdict

Keep the score at **98/100 provisional**. This is a **P1 web accessibility and localization gate** plus a P2 form-polish gate. The UI can switch to English, but the root HTML document still declares Korean, and form input assistance is only partially specified outside the auth email/password happy path.

## Evidence

- `src/app/+html.tsx:44` hard-codes `<html lang="ko">`.
- `src/app/+html.tsx:50` already owns the web viewport metadata, so this is the same root place users and browsers inherit page-level semantics from.
- `src/lib/i18n/index.ts:36-48` initializes `i18next` from `detectLanguage()` and listens to `languageChanged`, but only persists the preference.
- `src/lib/i18n/languageDetector.ts:1-36` detects/saves `en` or `ko` through web `localStorage` or device locale, but does not update `document.documentElement.lang`.
- `rg` found no `document.documentElement` sync in `src/app`, `src/lib`, or `src/components`.
- Static input scan across `src/app` and `src/components`: `TextInput=12`, `<Input=26`, `autoComplete=4`, `textContentType=0`, `keyboardType=3`, `secureTextEntry=2`, `returnKeyType=3`, `submitBehavior=0`.
- Good precedent: sign-in and sign-up email/password fields use `keyboardType`, `autoComplete`, `secureTextEntry`, and one `returnKeyType` path.
- `src/components/auth/BirthDateField.tsx:39-45` collects consent-critical birth date with `keyboardType="numbers-and-punctuation"`, but no `autoComplete` or `textContentType` equivalent.
- `src/app/account.tsx:228-234` and `src/app/settings.tsx:518-524` use destructive confirmation inputs with `autoCapitalize="characters"` and `autoCorrect={false}`, but no explicit autofill-off/input-purpose contract.

## Findings

### P1 - English UI still declares the document as Korean

Why this blocks 100:

- Screen readers, browser translation, spellcheck, hyphenation, autofill heuristics, and search/snippet tools rely on the document language.
- The app exposes manual language switches in sign-in, sign-up, and manual, and many routes derive `locale` from `i18n.language`. When the visible UI is English, the root document still says Korean.
- This creates a polished-looking but semantically wrong web shell, which is classic AI-slop: the screen looks localized, but the platform contract is not localized.

Acceptance:

- Sync `document.documentElement.lang` to `en` or `ko` whenever i18n initializes and changes language.
- If possible, make the first web render use the detected/persisted language instead of a hard-coded Korean root.
- Add a regression check that fails if root `lang` cannot follow KO/EN language toggles.
- Provide proof from a browser/devtools or automated test that toggling KO/EN changes the document language.

### P2 - Input assistance is incomplete outside auth

Why this matters:

- Auth email/password is partly well handled, which proves the team already knows the pattern.
- Consent birth date, destructive confirmation, URL/clip capture, tags, template metadata, interview/Jarvis/wiki inputs, and account/settings flows do not have a documented field-by-field platform input contract.
- This can cause poor mobile keyboards, unwanted autofill, weak password manager behavior, and slower high-risk form completion.

Acceptance:

- Define a compact field contract for high-risk inputs:
  - auth email/password;
  - birth date and consent/profile fields;
  - destructive confirmation phrases;
  - URL/link clip fields;
  - tags/path/template metadata;
  - long-form capture/interview/Jarvis textareas.
- Apply the relevant `autoComplete`, `textContentType` where supported, `keyboardType`, `returnKeyType`, `autoCapitalize`, `autoCorrect`, and autofill-off semantics.
- Preserve current good auth behavior while extending the contract to consent, account, settings, capture, wiki, interview, and Jarvis.

### P2 - There is no automated guard for language or input-purpose regressions

Why this matters:

- The app has i18n key parity checks, but no check that the browser document language follows the selected locale.
- The input scan shows only four autocomplete callsites and zero `textContentType` callsites. Future forms can easily regress into generic text boxes.

Acceptance:

- Add either a static check or a small runtime/web test that covers:
  - root document language after KO/EN language selection;
  - required hints for auth and birth-date fields;
  - explicit no-autofill/no-autocorrect policy for destructive confirmation fields.

## Required Proof Before 100

- KO and EN screenshot or browser test evidence showing `document.documentElement.lang` matches the visible UI.
- Field-purpose ledger for login, sign-up, profile/consent, capture, interview, Jarvis, wiki/template, settings, and account.
- Automated or documented local verification for the highest-risk fields.

Until these semantics are fixed and proven, hold **98/100 provisional**.

## Links

- Preview: `agents/codex/outbox/preview/20260606-063518-document-lang-input-assist-gate.html`
