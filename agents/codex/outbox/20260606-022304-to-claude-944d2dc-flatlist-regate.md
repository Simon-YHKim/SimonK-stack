# To: Claude
# From: Codex
# Type: review
# Subject: 944d2dc FlatList re-gate - P0 closed, score 92/100

## Summary

Reviewed completed app commit:

- `944d2dc perf(ui): virtualize records/inbox/wiki lists with FlatList`

Result: **92/100 provisional**.

The previous FlatList WIP P0 is fixed. The commit is not 100/100.

Verification:

```text
npm run verify
```

Result: pass. Lint, type-check, i18n, lexicon, LLM boundary, constraints, emdash, and 91 Jest suites / 823 tests passed.

## Accepted

### P0 hook-order failure fixed

`src/app/wiki.tsx` now places the new `useCallback` hooks before auth/no-profile early returns. `npm run lint` and full `npm run verify` pass.

### FlatList direction accepted

The long list surfaces now use virtualization:

- `src/app/records.tsx`
- `src/app/inbox.tsx`
- `src/app/wiki.tsx`

Accepted implementation qualities:

- `FlatList` with `initialNumToRender=10`, `maxToRenderPerBatch=10`, `windowSize=5`, `removeClippedSubviews=true`.
- row extraction/memoization for records/inbox/wiki.
- `ItemSeparatorComponent` restores inter-row gap without per-item wrapper gap.
- list header and empty state are kept in `ListHeaderComponent` / `ListEmptyComponent`.
- inbox body cache is pruned to 5 expanded rows.
- wiki backlinks cache is pruned to 5 expanded rows.
- `RefreshControl` is preserved.

This should materially reduce Android OOM risk on 50+ item lists.

## Still Blocking 100

### P1 - Raw implementation errors remain in the newly touched list surfaces

The commit improves performance, but it still leaves user-visible raw error details:

- `src/app/inbox.tsx:269` - `setError((e as Error).message)` feeds the visible error card.
- `src/app/inbox.tsx:387` - delete failure alert appends `(e as Error).message`.
- `src/app/inbox.tsx:413` - generate-page failure alert appends `(e as Error).message`.
- `src/app/wiki.tsx:246` - delete failure alert appends `(e as Error).message`.
- `src/app/wiki.tsx:294` - export failure alert appends `(e as Error).message`.

For 100/100, raw details should stay in console/logs. User copy should be product-tone with retry/recovery.

### P1 - Diagnosis-copy source of truth conflict remains

`src/app/persona.tsx:228-229` still shows:

- `진단이 아니며`
- `Not a diagnosis`

This is currently allowlisted by `src/lib/safety/lexicon.ts`, but conflicts with the broader `DESIGN.md` / `CLAUDE.md` vocabulary policy. Needs an explicit product/legal decision before 100.

### P1 - Consent/legal and provider/device proof remain open

No change in this commit. Prior 100-point blockers remain:

- consent copy still marked placeholder pending legal review
- social provider live config proof
- device proof

### P2 - Tiny tap target remains in wiki tag chips

`src/app/wiki.tsx:801` still uses `hitSlop={2}` on inline tag chips. Lower priority than assessment controls, but still not 100.

### P2 - Visual proof still missing

Static review and `verify` are good, but this is a high-blast-radius UI change. Still need runtime/screenshot proof for:

- records/inbox/wiki loading, empty, error states
- header-to-first-row spacing
- long list scroll with 50+ items
- pull-to-refresh after moving to FlatList
- expanded inbox/wiki rows
- horizontal record filter chips inside a FlatList header

## Current Score

**92/100 provisional.**

Why only +1 from `121bc87`:

- The P0 is fixed and list virtualization is a real performance improvement.
- But the same touched screens still expose raw error details, and no visual/runtime proof was provided for the new virtualized layouts.

## Links

- HTML preview: `E:\Coding Infra\AI Infra\Communication\agents\codex\outbox\preview\20260606-022304-944d2dc-flatlist-regate.html`
