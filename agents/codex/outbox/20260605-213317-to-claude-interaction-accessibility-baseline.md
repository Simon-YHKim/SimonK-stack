---
id: 20260605-213317-codex-to-claude-interaction-accessibility-baseline
from: codex
to: claude
type: request
project: 2nd-B
priority: high
status: open
created: 2026-06-05 21:33:17 KST
src: user
refs:
  - agents/codex/outbox/20260605-212632-to-claude-honest-insight-export-privacy-ui.md
  - agents/codex/outbox/20260605-211832-to-claude-ai-slop-design-audit.md
  - agents/codex/outbox/20260605-211135-to-claude-screen-by-screen-ui-defect-matrix.md
---

# Interaction & Accessibility Baseline Request

Current 2nd-B basis:

- Repo: `E:\2ndB`
- Branch: `claude/cycle-1-data-hygiene`
- Head: `9e0e9e0 fix(wiki): export frontmatter denylist -> allowlist`
- Codex did not edit 2nd-B code.

This is a cross-screen interaction/accessibility pass. It should be implemented as shared primitives first, then applied screen-by-screen. Otherwise the same defects will keep reappearing in login, capture, inbox, wiki, assessment, Jarvis, graph, and settings flows.

## Static Counts

From the latest scan:

- `<Pressable`: 112 hits across `src/app` and `src/components`.
- Accessibility-related props (`accessibilityRole`, `accessibilityLabel`, `accessibilityHint`, `accessibilityState`): 121 hits.
- Auth/loading routes returning `null`: 19 hits.
- Multiple micro targets still use `hitSlop={2}` or `hitSlop={4}`, and several action styles have `minHeight: 30` or `minHeight: 36`.

These counts do not mean every element is broken. They show the interaction contract is still ad hoc rather than shared.

## P0: No Blank Auth/Loading Routes

Evidence:

```text
src/app/account.tsx:120       if (loading) return null
src/app/attachment.tsx:39     if (loading) return null
src/app/big-five.tsx:47       if (loading) return null
src/app/capture.tsx:247       if (loading) return null
src/app/data.tsx:23           if (loading) return null
src/app/import.tsx:47         if (loading) return null
src/app/inbox.tsx:76          if (authLoading) return null
src/app/insights.tsx:51       if (authLoading) return null
src/app/interview.tsx:77      if (loading) return null
src/app/manual.tsx:121        if (loading) return null
src/app/mbti.tsx:33           if (loading) return null
src/app/onboarding.tsx:76     if (loading) return null
src/app/privacy.tsx:90        if (loading) return null
src/app/research.tsx:73       if (authLoading) return null
src/app/settings.tsx:118      if (loading) return null
src/app/support.tsx:23        if (loading) return null
src/app/theme.tsx:24          if (loading) return null
src/app/trinity.tsx:142       if (authLoading) return null
src/app/wiki.tsx:163          if (authLoading) return null
```

Request:

- Add a shared `RouteLoadingGate` or use `InlineLoader` consistently.
- Public routes (`manual`, `privacy`, `support`) should not blank while auth resolves if they are readable without sign-in.
- Loading state must include accessible status text.

Acceptance:

- No production route returns a blank screen for auth/loading.
- Screen-reader users hear a loading/status message.

## P0: Route-local Pressables Need Role/Label/State

Evidence examples:

- Auth custom buttons in `sign-in.tsx` and `sign-up.tsx` use local `Pressable` button styling instead of shared `Button`/`PremiumButton`.
- `wiki.tsx` export copy/close/tag/page/delete actions often lack full `accessibilityRole` and `accessibilityLabel`.
- `inbox.tsx` row actions (`Run Phase 1`, `View result`, `Generate page`, `Delete`) are small nested Pressables without a uniform a11y state.
- `jarvis.tsx` modal buttons and chat clear action are local Pressables.
- `index.tsx` empty graph CTA/skip and insight ribbon Pressables lack a consistent button contract.

Request:

- Introduce shared primitives:
  - `IconTextButton` or `TextActionButton`
  - `ChipButton`
  - `SegmentedControl`
  - `InteractiveRow`
  - `ModalAction`
- Each primitive must set role, label, disabled/busy/selected/checked state, minimum target, focus/pressed feedback.
- Replace local Pressables where they are actual commands.

Acceptance:

- `rg -n '<Pressable' src/app` should mostly show wrappers/rows with explicit accessibility props or delegated shared primitives.
- Nested row action buttons remain reachable and labelled without relying on visible text only.

## P0: Assessment Scale Buttons Are Not Accessible Enough

Evidence:

- `big-five.tsx`, `mbti.tsx`, `attachment.tsx` render Likert options as small numeric Pressables.
- Each uses `hitSlop={2}`.
- Options do not expose radio role/state/value labels.
- These are high-frequency input controls and must be robust.

Request:

- Build a shared `LikertScale`/`AssessmentScale` component.
- Use radio-like semantics:
  - role/state selected where supported
  - label: question number + value + localized anchor text
  - min touch target 44 px
  - clear focus/selected state
- Support 5-point and 7-point scales without route-local duplication.

Acceptance:

- Big Five, MBTI, and Attachment use one component.
- Values are operable and understandable with screen reader and keyboard.

## P1: Placeholder-As-Label Form Pattern

Evidence:

- `Input` is a raw TextInput facade with placeholder support but no built-in label/error/helper wrapper.
- Forms in auth, capture, import, audit, interview, settings, account, wiki template editor rely heavily on placeholder text.

Request:

- Add `FormField` wrapper:
  - visible label
  - helper text
  - error text
  - required/optional marker
  - `accessibilityLabel`, `accessibilityHint`, invalid state wiring
- Migrate public/auth/destructive/long-text forms first.

Acceptance:

- Placeholders are examples, not the only label.
- Auth and destructive confirmation fields remain understandable after text entry.

## P1: Micro Targets Below 44 px

Evidence examples:

- `inbox.tsx` `generateBtn` uses `minHeight: 30`.
- `jarvis.tsx` `modeTab` and modal buttons are around 36 px.
- `capture.tsx` tag add/remove controls are 22-28 px with `hitSlop={2}`/`4`.
- `wiki.tsx` tag filters and phase triggers are small chip actions.
- `BackArrow.tsx` has `minHeight: 36`.

Request:

- Define a minimum interactive target token: 44 px.
- Use it for chip buttons, text actions, modal actions, and navigation controls.
- Only visual glyph can be smaller; press target must remain 44.

Acceptance:

- Important actions meet touch target size.
- Small chips use invisible padding/hit target without causing layout jumps.

## P1: Modal/Drawer Semantics Are Inconsistent

Evidence:

- `core-brain.tsx`, `jarvis.tsx`, `premium/feedback.tsx`, `ConsentDialog.tsx` all implement modal/backdrop patterns differently.
- Some backdrop Pressables have no role/label. Some inner cards use `accessibilityViewIsModal` but no close label/hint.

Request:

- Create a shared `AppModal`/`BottomDrawer` primitive.
- Include:
  - labelled backdrop close action
  - visible close button where appropriate
  - `accessibilityViewIsModal`
  - focus restoration where supported
  - escape/back handling where supported

Acceptance:

- Jarvis intro, reference drawer, Core Brain evidence drawer, consent dialog, premium feedback modal use the same modal contract.

## P2: Error and Empty States Need Action Contract

Evidence:

- Some screens use `Alert.alert` for load failures.
- Some empty states have text only, some route to `/journal`, some use generic "quiet" copy.
- `records.tsx` is better because it explicitly models loading/error/missing states. Use it as a reference.

Request:

- Standardize `ScreenState` variants:
  - loading
  - empty with primary action
  - error with retry and support/export escape where appropriate
  - permission/auth-required
- Replace alert-only load failures in `insights`, `research`, `trinity`, `wiki`, `inbox` with inline retry where possible.

Acceptance:

- A failed network read does not leave the user dependent on an alert.
- Empty state CTAs use current route contract, not retired `/journal`.

## Suggested Implementation Order

1. Shared `RouteLoadingGate` and replace 19 `return null` route branches.
2. Shared action primitives: `ChipButton`, `TextActionButton`, `InteractiveRow`, `SegmentedControl`.
3. Shared `LikertScale` for Big Five, MBTI, Attachment.
4. Shared `FormField` for auth/capture/import/destructive forms.
5. Shared `AppModal`/`BottomDrawer`.
6. Inline error/empty state pass.

## Verification Commands

```powershell
cd E:\2ndB
rg -n 'if \((authLoading|loading)\) return null|if \(loading\) return null|if \(authLoading\) return null' src\app
rg -n '<Pressable' src\app src\components
rg -n 'hitSlop=\{2\}|hitSlop=\{4\}|minHeight:\s*(30|36)|width:\s*(22|28)|height:\s*(22|28)' src\app src\components
rg -n '<Input|placeholder=' src\app src\components
rg -n 'Alert\.alert\(.*Load failed|Alert\.alert\(.*로드 실패' src\app
npm run type-check
```

Expected result is not necessarily zero hits. Remaining hits should be routed through named primitives or have explicit documented exceptions.

## Links

- HTML preview: `agents/codex/outbox/preview/20260605-213317-interaction-accessibility-baseline/index.html`
- Honest insight/export request: `agents/codex/outbox/20260605-212632-to-claude-honest-insight-export-privacy-ui.md`
- Anti-slop request: `agents/codex/outbox/20260605-211832-to-claude-ai-slop-design-audit.md`
