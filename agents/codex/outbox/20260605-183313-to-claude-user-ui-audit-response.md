---
id: 20260605-183313-codex-to-claude-user-ui-audit
from: codex
to: claude
type: response
ref: user-direct-20260605-182313-ui-overall-audit
project: 2nd-B
priority: high
status: done
created: 2026-06-05 18:33:13 KST
---

# 2nd-B Overall UI Audit

## User Request

`src: user` - "ui에 대해 전체적으로 다시 검사해봐."

## Scope

- Project: `E:\2ndB`
- Static scope: `src/app/` all 43 route files, shared premium UI, graph/art components, DESIGN.md consistency.
- Runtime scope: Expo web at `http://localhost:8090`, Chrome headless screenshots at desktop `1440x1100` and mobile `390x844`.
- HTML report: `agents/codex/outbox/preview/20260605-182313-ui-audit/index.html`

## Summary

The brand direction is visually strong, especially the cosmic pixel graph assets and the dark mint/violet identity. The app is not launch-ready from a UI standpoint because first-run environment validation can crash the whole app, and mobile layouts currently overflow horizontally on the main public screens.

## Findings

### P0 - App can crash before any UI renders

- Evidence: first Chrome captures showed an Expo error overlay with zod `too_small` on `EXPO_PUBLIC_SUPABASE_ANON_KEY`.
- Code basis: `src/lib/env.ts` accepts empty env through demo placeholders, but intentionally throws when a non-empty malformed value exists.
- Impact: a local or preview environment with a short placeholder key shows no product UI at all.
- Recommendation: keep strict production validation, but make dev/preview env setup impossible to misconfigure. For example, update local sample env and add a preflight check that fails before the browser opens.

### P0 - Mobile horizontal overflow on public screens

- Evidence:
  - `signin-mobile-ok.png`: login form is clipped on the right.
  - `signup-mobile-ok.png`: hero and consent body are clipped on the right.
  - `manual-mobile-ok.png`: card body text is clipped on the right.
  - `asset-preview-mobile-ok.png`: right graph node and top segmented control are clipped.
- Likely implementation basis:
  - `src/app/(auth)/sign-in.tsx:301-306` has padded ScrollView but the form has no viewport-bound width/maxWidth policy.
  - `src/app/(auth)/sign-in.tsx:339-350` and `src/app/(auth)/sign-up.tsx:332-343` make full panels with shadows but no responsive max width.
  - Graph preview is route-accessible and appears optimized for desktop canvas.
- Recommendation: define one auth/support page width contract: mobile `width: "100%"`, desktop `maxWidth: 560-720`, `alignSelf: "center"`, and no horizontal overflow. Apply the same pattern to manual/support cards.

### P1 - DESIGN.md no-gradient/no-glass/no-shadow rules are not implemented

- Evidence:
  - `src/components/premium/background.tsx` uses `LinearGradient` and `RadialGradient`.
  - `src/components/premium/surfaces.tsx` labels panels as glassy and uses `shadowColor`, `shadowOpacity`, `shadowRadius`.
  - scan count: 180 `shadow*` or `elevation` uses in `src/app` and `src/components`.
  - runtime warning: React Native Web repeatedly warns `"shadow*" style props are deprecated. Use "boxShadow".`
- Impact: DESIGN.md and actual UI tokens disagree. This makes future visual QA subjective.
- Recommendation: either revise DESIGN.md to allow named signal glows, or remove generalized panel/button shadows in favor of pixel borders and semantic strokes.

### P1 - Long Korean body copy is too dense in pixel font

- Evidence: signup consent body and manual cards are hard to scan and clip on mobile.
- Code basis: `src/theme/typography.ts` comments say long Korean paragraphs should use readable sans, but `fontFamilies.sans` still maps to NeoDunggeunmo.
- Recommendation: keep NeoDunggeunmo for headings, labels, badges, graph labels; use `fontFamilies.readable` for legal copy, manual body, long assistant text, and dense support content.

### P1 - IA leftovers surface in UI

- `/journal` is retired but `src/app/+not-found.tsx:41` still exposes "일기 / Journal".
- `/mbti` is exposed while `src/app/manual.tsx:110-111` says MBTI is not used.
- `/manual` and `/settings` still use Big Five (TIPI) copy while `src/app/big-five.tsx` is BFI-44.
- Dev preview routes are reachable in production URL space, including `/asset-motion-preview`.

### P2 - Web runtime polish warnings

- Repeated warnings:
  - `"shadow*" style props are deprecated. Use "boxShadow".`
  - `props.pointerEvents is deprecated. Use style.pointerEvents`
  - `Animated: useNativeDriver is not supported...`
- Impact: not all are user-facing defects, but they add noise and indicate RN Web polish debt.

## Positive Signals

- Desktop login and graph preview show a clear, differentiated identity.
- `npm run lint` passed.
- `npm run type-check` passed.
- `npm run check:i18n` passed.
- `npm run check:emdash` passed.
- `npm run check:constraints` passed, with existing C11 PART noted by the script.
- `npm run check:lexicon` passed.

## Suggested Claude Implementation Requests

1. Fix mobile overflow globally and on auth/support screens.
2. Add a launch preflight for malformed public env values so UI does not fail inside AuthProvider.
3. Decide whether DESIGN.md permits named signal glow. If not, remove generalized shadows/glass/gradients from shared premium components.
4. Hide dev preview routes from production routing.
5. Migrate stale `/journal`, MBTI, and TIPI copy in user-visible screens.
6. Split long-form body typography from pixel label typography.

## Links

- HTML report: `agents/codex/outbox/preview/20260605-182313-ui-audit/index.html`
- Screenshot folder: `agents/codex/outbox/preview/20260605-182313-ui-audit/`
- Runtime logs: `E:\2ndB\.codex-ui-audit-expo.log`, `E:\2ndB\.codex-ui-audit-expo-dummy.log`
