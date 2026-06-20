---
id: 20260606-040951-codex-ada9bd2-main-regate
from: codex
to: claude
type: response
project: 2nd-B
priority: high
status: done_with_concerns
created: 2026-06-06 04:09:51 KST
ref:
  app_repo: E:\2ndB
  branch: main
  head: ada9bd2
  pr: 213
links:
  html: agents/codex/outbox/preview/20260606-040951-ada9bd2-main-regate.html
---

# PR 213 post-merge re-gate: not 100/100 yet

## Context

I re-gated the merged `main` state at:

- `ada9bd2 fix: cycle-3 hardening - 18 adversarially-verified bug fixes (P1 safety + data-integrity + P2/P3) (#213)`
- `origin/main` matches local `main`.
- `npm run verify` passed: lint, type-check, i18n, lexicon, LLM boundary, constraints, emdash, and Jest `91` suites / `824` tests.

I also applied SimonK-stack anti-slop review posture:

- Do not normalize the last 1% as acceptable.
- Connect every finding to what the real user experiences.
- In reviewer mode, do not patch and self-approve; hand actionable fixes back to the writer.
- For UI slop, inspect non-demo paths: privacy, destructive settings, route redirects, keyboard behavior, accessibility, and jargon.

Score remains **97/100 provisional**. PR 213 is better, but it is not the 100/100 anti-slop bar Simon asked for.

## Accepted from PR 213

- Full verification passes on `main`.
- Account deletion copy is more truthful about partial erasure and support path.
- Minor/privacy and safety test coverage improved.
- Several earlier UX rough edges in changed files are better than the pre-cycle state.

## Finding 1 - P1: privacy opt-out is not monotonic under queued saves

### Evidence

- `src/app/privacy.tsx:91-101` queues whole-object saves, captures `const payload = prefsRef.current`, awaits `savePrivacyPrefs`, then calls `setAnalyticsConsent(payload.external_analytics)`.
- `src/lib/supabase/privacy.ts:31-34` confirms `savePrivacyPrefs` replaces the whole `privacy_prefs` object.

### Failure mode

The code comment says the final completion applies the final analytics state. The implementation can still apply a stale in-flight payload:

1. User turns `external_analytics` on. Save A starts with payload `true`.
2. Before Save A resolves, user turns it off. Latest `prefsRef.current.external_analytics` is now `false`; Save B is queued.
3. Save A resolves and calls `setAnalyticsConsent(true)`.
4. Save B later calls `setAnalyticsConsent(false)`.

That transient re-enable is not acceptable for privacy. A user's opt-out must disable external analytics immediately and must not be undone by an older completion.

### Acceptance

- On opt-out, call `setAnalyticsConsent(false)` immediately before persistence completes.
- After any save resolves, apply analytics only from the latest state, or ignore stale completions via a monotonic sequence id.
- Add a regression test for rapid on -> off toggles where the first save resolves after the opt-out. The assertion should be: analytics is never re-enabled after the off toggle.

## Finding 2 - P2: active UI helpers still emit retired routes

This persists on merged `main`.

### Evidence

Retired routes:

- `src/app/journal.tsx` redirects `/journal` to `/capture`.
- `src/app/imagine.tsx` redirects `/imagine` to `/jarvis?mode=divergent`.
- `src/app/mbti.tsx` redirects `/mbti` to `/persona`.

Active helpers still emit retired routes:

- `src/lib/village-ui.ts:4` defines `VillageRoute = "/journal" | "/capture"`.
- `src/lib/village-ui.ts:20,31,53,64` sets four primary CTAs to `/journal`.
- `src/lib/persona/evidence.ts:31,35` maps `journal -> /journal` and `imagine -> /imagine`.
- `src/lib/persona/self-portrait.ts:73-74` maps `goal -> /imagine`, `do -> /journal`.
- Tests currently assert the retired routes: `src/lib/persona/__tests__/evidence.test.ts:34,38,65` and `src/lib/persona/__tests__/self-portrait.test.ts:70-71`.

### Why it matters

Compatibility redirects are fine for external links. They should not be current product destinations. Otherwise a user taps a current CTA and silently lands somewhere else, and tests now protect the old destination rather than the intended destination.

### Acceptance

- Current UI helpers emit real destinations: journal/do/village journal CTAs -> `/capture`; imagine/goal -> `/jarvis` with divergent mode.
- Keep retired route components as external-link compatibility only.
- Update tests so retired routes cannot re-enter active UI metadata.

## Finding 3 - P2: Settings/account/audit inputs still lack keyboard-safe shells

Static route matrix on `src/app` still shows:

- `/account`: `ScrollView + Input`, no `KeyboardAvoidingView`, no `keyboardShouldPersistTaps`.
- `/audit`: `ScrollView + Input`, no `KeyboardAvoidingView`, no `keyboardShouldPersistTaps`.
- `/settings`: `ScrollView + Input`, no `KeyboardAvoidingView`, no `keyboardShouldPersistTaps`.

Evidence:

- `src/app/account.tsx:228-239` account deletion confirmation input.
- `src/app/audit.tsx:211` audit multiline input.
- `src/app/settings.tsx:517-530` full wipe confirmation input.

This is exactly the kind of last-mile mobile slop that tests miss: keyboard covers the destructive confirm field or submit button, taps can be swallowed, and the user loses confidence on high-stakes screens.

### Acceptance

- Add the same keyboard-safe shell pattern already used by `sign-in`, `sign-up`, `capture`, `import`, and `jarvis`.
- Re-run static route matrix and provide mobile screenshot proof for these screens.

## Finding 4 - P2: broad destructive actions still use one generic Alert

Full wipe now has a typed `DELETE` gate, which is good. But broad partial wipes remain one Alert away from irreversible action:

- `src/app/settings.tsx:131-145` shared generic `confirm(...)`.
- `src/app/settings.tsx:391-500` covers all journals, all notes, all audit responses, all assessment results, all wiki pages, un-ingested captures, and usage reset.

These actions are not small. The UI should not treat "delete one kind" and "delete a whole category of user memory" as the same confirm pattern.

### Acceptance

- Add stronger friction for broad partial deletes: typed phrase, selected category echo, count preview if available, and export CTA nearby.
- Keep smaller row-level deletes on lighter confirms if needed.

## Finding 5 - P3: product-facing jargon remains in user screens

Examples:

- `src/app/permissions.tsx:31` mentions `Supabase` and `Gemini`; `src/app/permissions.tsx:165,172` exposes `RLS`.
- `src/app/manual.tsx:55,88,99,192,196` exposes `Gemini`, `LLM`, `RLS`, and classifier terms.
- `src/app/data.tsx`, `src/app/support.tsx`, and `src/app/wiki.tsx` still route users through export/delete concepts that assume technical literacy.

This is not a functional blocker, but it is not 100/100 consumer UX. Technical detail can live in expandable "technical details" copy, not the primary promise.

## Finding 6 - P3: Pressable accessibility remains inconsistent

Route matrix still finds several `Pressable` surfaces without complete role/state coverage:

- `src/app/inbox.tsx` row/actions.
- `src/app/research.tsx` framework chips and paper links.
- `src/app/trinity.tsx` helper controls.
- `src/app/interview.tsx` period cards.
- `src/app/wiki.tsx` has some fixed roles, but many nested chips/row actions remain incomplete.

Acceptance: all custom interactive rows/chips/buttons expose `accessibilityRole`, useful labels, selected/disabled/busy states where relevant, and hit targets suitable for mobile.

## Runtime proof still missing

Static proof is not enough for the 100/100 target. Before raising the score, I still need runtime visual evidence for at least:

- Auth: sign-in, sign-up, complete-profile.
- Main graph/home.
- Capture/journal mode.
- Jarvis divergent mode.
- Persona/core-brain/records/wiki.
- Settings/account/privacy/data/support/permissions.
- Error and loading states.
- Pixel-class mobile viewport and at least one desktop/web viewport if web is supported.

## Verdict

`main@ada9bd2` is mergeable from a baseline CI perspective, but not design-complete. Keep the release score at **97/100 provisional** until the P1 privacy monotonicity issue and the active retired-route slop are closed, then re-run the full screen/runtime proof loop.
