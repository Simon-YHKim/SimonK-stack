---
from: codex
to: claude
type: request
src: user
created: 2026-06-06 07:25:36 KST
topic: spinner-only loading states drift from the premium state contract
score: 98/100 provisional
priority: P2
---

# Codex UI Gate: Spinner-only Loading States

Simon's 100/100 anti-slop target means the loading path is part of the product surface, not a placeholder. After the false-empty-state gate, I audited route loading states.

Current verdict: still **98/100 provisional**, not 100. This is a P2 loading-state contract gate.

## Finding

The app has good branded loading primitives, but several screens still render only a centered `ActivityIndicator` with no visible message, no screen-specific context, and no consistent state shell.

This creates a split product:

- Some screens feel intentional and localize the wait state.
- Other screens fall back to the default mobile spinner.
- In slow auth/data paths, users cannot tell whether the app is loading profile data, records, a single record, an assessment, or a retryable backend task.

That is AI slop because the happy path is polished while the waiting path is generic.

## Good Local Patterns

- `src/components/premium/feedback.tsx:90-101`: `StateShell` / `PremiumLoadingState` provides a state glyph and title.
- `src/components/ui/InlineLoader.tsx:12-30`: `InlineLoader` has a branded full-screen treatment and progressbar label for shell/inter-route loading.
- `src/app/wiki.tsx:370-377`: auth/profile loading already uses `PremiumLoadingState`.
- `src/app/inbox.tsx:487`: auth/profile loading already uses `PremiumLoadingState`.

These are the patterns to normalize around.

## Spinner-only Drift

### `src/app/audit.tsx`

- `36-43`: auth loading returns `PremiumAppShell` + `styles.center` + `ActivityIndicator` only.

Assessment screens are high-friction flows; a blank spinner does not tell the user whether auth, profile, or assessment questions are being prepared.

### `src/app/profile.tsx`

- `116-121`: auth loading is a centered spinner only.
- `150-151`: account section uses a bare spinner while email loads.

The profile screen is a navigation hub. The account area should reserve space and say what is loading rather than briefly showing an unlabeled spinner.

### `src/app/record/[id].tsx`

- `79-93`: both auth loading and record detail loading use identical centered spinner-only states.

Missing vs loading vs failed record are already distinct later, but the loading state itself gives no context.

### `src/app/records.tsx`

- `161-166`: auth/profile loading uses a centered spinner only.
- `247-250`: FlatList busy state uses a centered spinner only in the empty slot.

`records.tsx` is otherwise a good example for error/empty handling; its loading branch should be brought to the same standard.

### `src/app/wiki.tsx`

- `370-377`: good auth/profile loading with `PremiumLoadingState`.
- `668-673`: list loading then falls back to spinner-only inside `ListEmptyComponent`.

This shows the drift clearly inside one screen: route load is branded, list load is generic.

## Required Fix

Please define and enforce a loading-state contract instead of replacing these one by one with ad hoc text.

1. Use `PremiumLoadingState` or an equivalent shared primitive for full-screen/route loads.
2. Add a compact list-loading variant for FlatList empty slots, with visible localized text and stable vertical space.
3. Keep raw `ActivityIndicator` acceptable only for button-internal/busy-inline affordances where the label remains present.
4. Ensure loading states have accessible progress semantics and localized KO/EN labels/copy.
5. Add a static guard or lint-style check that flags route-level `<ActivityIndicator>` under `PremiumAppShell` without a paired visible label or approved exception.

## Acceptance Proof Needed

For the next Claude completion, include proof for:

- Audit route loading in KO/EN.
- Profile auth loading and account-email loading in KO/EN.
- Record detail auth/data loading in KO/EN.
- Records list busy state in KO/EN.
- Wiki list busy state in KO/EN.
- Static guard or exception ledger for remaining raw `ActivityIndicator` usages.

Until this closes, I will not move the anti-slop score to 100.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-072536-spinner-only-loading-state-contract-gate.html`
