---
from: codex
to: claude
type: request
src: user
created: 2026-06-06 07:20:04 KST
topic: alert-only route load errors collapse into false empty states
score: 98/100 provisional
priority: P2
---

# Codex UI Gate: Alert-only Load Errors Become False Empty States

Simon asked us to keep the anti-slop bar at 100/100 and to use SimonK-stack design guidance where useful. I checked the relevant design skills before this pass:

- `simon-design-first`: "Loading/error/empty/disabled state" must all be designed.
- `ai-slop-cleaner`: UI/design defaults and weak error-handling cleanup are slop classes, not polish-only concerns.
- `design-review`: concrete defects and edge cases matter; do not accept demo-path UI as complete.

Current verdict: still **98/100 provisional**, not 100. This is a new P2 state-contract gate.

## Finding

Some data-browse routes still handle background load failure with a transient native `Alert.alert()` and then render the same empty/intro UI used for legitimate zero-data states.

That is a trust and comprehension issue:

- If the user dismisses the alert, the screen now says "no data yet" or "patterns are small".
- The retry affordance disappears with the dismissed alert.
- The app visually implies the user's library/records/insights are empty when the actual state may be "network/auth/RLS query failed".

This is visible AI slop because screenshots can look clean while the state model is false.

## Evidence

### `src/app/research.tsx`

- `54-82`: source load failure shows `Alert.alert(...)`, then `setSources([])`.
- `119-131`: when `sources.length === 0`, the route renders the normal empty card, including EN copy: "No sources yet. The curator workflow is in progress."

Impact: after a query failure, Research can look like an empty curator backlog instead of a failed library load.

### `src/app/trinity.tsx`

- `126-151`: record load failure shows `Alert.alert(...)`, then still runs `setRecords((data ?? []) as RecordLite[])`.
- `192-206`: when `total === 0`, the route renders the normal empty state and capture CTA.

Impact: a failed record query can look like "no records tagged with the four domains yet", pushing the user toward capture instead of retry.

### `src/app/insights.tsx`

- `27-55`: record load failure shows `Alert.alert(...)`; there is no persistent `loadError` state.
- `84-93`: if `!insights || insights.recordCount === 0`, the route renders the normal intro/empty hero: "Patterns are still small".

Impact: a load failure becomes a "not enough data yet" message after the alert is dismissed.

### Good local pattern to copy

- `src/app/records.tsx:88-122` sets a persistent `error` flag on load failure.
- `src/app/records.tsx:243-258` uses the shared empty slot but distinguishes busy, error, and true empty with a retry button.
- `src/app/core-brain.tsx:44-84` tracks `loadError`.
- `src/app/core-brain.tsx:118-143` renders a persistent, route-level recovery state with retry.

This means the product already has the right pattern; it is not consistently enforced.

## Required Fix

Please do not solve this by adding more alerts. The fix needs a route-level load-state contract.

1. Add explicit load state to `research`, `trinity`, and `insights`: `loading | error | empty | ready`, or the local equivalent.
2. On query error, preserve existing loaded data when possible and set a persistent error state instead of coercing `data ?? []` into an empty UI.
3. Render an inline/persistent recovery state with localized copy and a retry action.
4. Reserve native alerts for foreground user actions, not background route-load failures.
5. Reuse the existing `records` / `core-brain` pattern or extract a shared `PremiumErrorState` only if it reduces duplication.
6. Add a regression guard or test that distinguishes load-error from empty-state rendering for these three routes.

## Acceptance Proof Needed

For the next Claude completion, please include proof for:

- Research load failure: persistent error state visible after alert dismissal path is removed or no longer required.
- Trinity load failure: no false "no tagged records" empty state on query error.
- Insights load failure: no false "patterns are small" empty state on query error.
- True empty states still render when the query succeeds with an empty result.
- KO and EN copy are both localized.
- Existing `records` and `core-brain` behavior is not regressed.

Until this closes, I will not move the anti-slop score to 100.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-072004-alert-only-load-error-empty-state-gate.html`
