# O-3 P1 analytics handoff

## Branch
- Worktree: `E:\Coding Infra\_worktrees\2ndB-o3-p1-analytics`
- Branch: `codex/o3-p1-analytics`
- Commit: `d691bbf2fc7e68ba8241bf85adbc977f93859226`
- Commit subject: `feat(analytics): activate web observability`

## Change summary
- Activated web observability path for GA4, Microsoft Clarity, and Sentry without hardcoded IDs.
- Added `@sentry/browser` and wired Sentry through `EXPO_PUBLIC_SENTRY_DSN`, with `sendDefaultPii: false` and no consent dependency because this is operational error tracking.
- Kept product analytics consent-gated: GA4, Clarity, and PostHog load only after external analytics consent and only when IDs exist.
- Added PIPA/C10 defense in depth:
  - 14-17 high-privacy users cannot load product analytics.
  - Under-14 users, if any malformed profile slips through, cannot load product analytics.
  - GA4 ad storage, ad user data, and ad personalization are always denied.
- Added canonical event taxonomy helpers for exactly three axes:
  - `page_view`
  - `capture`
  - `secondb_session`
- Preserved no-op behavior when IDs are missing or platform is not web.
- Added tests for taxonomy helpers, PIPA/C10 analytics gate, no-op behavior, and `EXPO_PUBLIC_SENTRY_DSN` env parsing.
- Updated `.env.example` slots:
  - `EXPO_PUBLIC_GA4_MEASUREMENT_ID=`
  - `EXPO_PUBLIC_CLARITY_PROJECT_ID=`
  - `EXPO_PUBLIC_SENTRY_DSN=`

## Verify
- `npm run verify`: PASS
- Coverage of verify run:
  - lint PASS
  - type-check PASS
  - i18n, lexicon, llm-boundary, constraints, emdash checks PASS
  - Jest PASS: 99 suites, 870 tests

## EAS and CI variable injection path
These three values are client-side public identifiers, not private server secrets. They must not be hardcoded in source.

EAS Dashboard path:
- Expo dashboard -> project -> Environment Variables -> add the variables for `production` and any preview environment used.
- Use `plaintext` visibility, or `sensitive` if Simon wants dashboard value masking. Do not use `secret` visibility for `EXPO_PUBLIC_*` values that must be substituted into app JavaScript.

EAS CLI equivalent:
```bash
eas env:create --environment production --visibility plaintext --name EXPO_PUBLIC_GA4_MEASUREMENT_ID --value <GA4_MEASUREMENT_ID>
eas env:create --environment production --visibility plaintext --name EXPO_PUBLIC_CLARITY_PROJECT_ID --value <CLARITY_PROJECT_ID>
eas env:create --environment production --visibility plaintext --name EXPO_PUBLIC_SENTRY_DSN --value <SENTRY_DSN>
```

Repeat for `preview` if preview builds should report analytics:
```bash
eas env:create --environment preview --visibility plaintext --name EXPO_PUBLIC_GA4_MEASUREMENT_ID --value <GA4_MEASUREMENT_ID>
eas env:create --environment preview --visibility plaintext --name EXPO_PUBLIC_CLARITY_PROJECT_ID --value <CLARITY_PROJECT_ID>
eas env:create --environment preview --visibility plaintext --name EXPO_PUBLIC_SENTRY_DSN --value <SENTRY_DSN>
```

GitHub Pages or GitHub Actions web export path:
- Repository -> Settings -> Secrets and variables -> Actions -> Variables.
- Add the same three `EXPO_PUBLIC_*` names with Simon-provided values.
- Re-run the web export/deploy workflow after adding values, because Expo substitutes `EXPO_PUBLIC_*` values into the JavaScript bundle at build/export time.

Reference:
- Expo EAS env docs: https://docs.expo.dev/eas/environment-variables/
- Expo EAS env management: https://docs.expo.dev/eas/environment-variables/manage/
