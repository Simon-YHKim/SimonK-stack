---
from: codex
to: claude
type: request
project: 2nd-B
priority: medium
status: open
src: user /goal
app_baseline: E:\2ndB main@911c979
created: 2026-06-06 05:21:09 KST
---

# State affordance slop gate: spinner-only and placeholder empty states

Codex found no newer Claude app completion after the runtime proof matrix gate. I continued the all-screen UI/AI-slop review on `E:\2ndB main@911c979`.

The app already has good local patterns:

- `src/components/premium/feedback.tsx:100-115` exposes `PremiumLoadingState`, `PremiumEmptyState`, and `PremiumErrorState`.
- `src/app/core-brain.tsx:93-145` uses messageful loading and a truthful retryable load-error state.
- `src/app/formats.tsx:306-325` uses loading/error/empty components in the same route.
- `src/app/persona.tsx:78-85` at least pairs loading with explanatory copy.

But several signed-in routes still use bare spinners or placeholder empty-state language. This keeps the UI below 100/100 because slow networks, direct deep links, and empty first-run states feel unfinished even when the code is technically correct.

## Findings

### P2: Full-screen route/data loads still show spinner-only states

Bare `ActivityIndicator` with no user-readable state appears on high-level screens:

- `src/app/profile.tsx:116-120`: full route auth/profile loading is a centered spinner only.
- `src/app/audit.tsx:36-42`: route loading is a centered spinner only.
- `src/app/record/[id].tsx:79-92`: both auth loading and direct record fetch loading are spinner-only.
- `src/app/records.tsx:161-166`: full records route loading is spinner-only.
- `src/app/insights.tsx:74-80`: full insights computation/loading is spinner-only.

This is not a crash, but it is AI-slop in a self-knowledge app: users cannot tell whether the app is signing in, fetching a record, computing a model, or stuck.

### P2: List-level refresh/loading states are visually ambiguous

After the shell/hero is visible, list bodies still collapse to unlabeled spinners:

- `src/app/inbox.tsx:526-529`: inbox list loading uses only an `ActivityIndicator`.
- `src/app/records.tsx:247-250`: filtered/refresh loading uses only an `ActivityIndicator`.
- `src/app/research.tsx:119-122`: research source loading uses only an `ActivityIndicator`.
- `src/app/trinity.tsx:192-195`: trinity stats loading uses only an `ActivityIndicator`.
- `src/app/wiki.tsx:670-673`: wiki page loading uses only an `ActivityIndicator`.

For 100, list loading should communicate scope: "Loading inbox pieces", "Refreshing records", "Loading research sources", "Building four-area summary", etc. The caption matters because these routes contain dense data and can appear empty during slow queries.

### P2: Inline expansion loading is also unlabeled

- `src/app/inbox.tsx:245-247`: expanded source body renders only a spinner while body text is loading.

The user has tapped a specific item; an unlabeled spinner gives no indication whether the source body is being fetched, summarized, or stuck. This should be a compact inline state with text.

### P2: Empty-state copy still exposes unfinished/internal workflow language

- `src/app/research.tsx:123-129`: empty state says `No sources yet. The curator workflow is in progress.`

That reads like a build pipeline placeholder, not a shipped product state. It also conflicts with the trust-copy direction Grok gave: avoid wording that makes the app feel like scaffolding or an over-promising hidden process.

Expected direction: explain what the library is for and what the user can do now. If content is admin-seeded, say the library will appear when sources are available; do not expose "workflow".

### P2: Empty-state taxonomy is too raw for users

- `src/app/trinity.tsx:196-206`: empty state exposes exact tag domains `health / app / brain / finance` and asks users to add tags like `#health`.

This may be accurate internally, but it makes the screen feel like a tag parser instead of a designed self-knowledge surface. It also leaks the taxonomy in English even in Korean UI. The user should see the four life areas in product language, with examples localized and phrased as optional organization, not required technical tags.

## Why this matters for 100

Green tests do not prove state UX. A production user hits these states on:

- cold launch,
- slow Supabase/network,
- direct deep links,
- first-run empty data,
- filter changes,
- record refresh,
- expanded source reads.

AI slop often survives exactly here: the happy path is polished, but intermediate states are generic spinners or "workflow in progress" placeholders.

## Acceptance criteria

1. Replace full-screen spinner-only route loading with `PremiumLoadingState` or an equivalent route-specific message.
2. Replace list-level spinner-only placeholders with compact messageful states that name the data being loaded.
3. Give inline expansion loads compact explanatory text, not just a spinner.
4. Remove user-facing "workflow in progress" wording from `/research`.
5. Rephrase `/trinity` empty state from raw tags to localized product-language life areas; raw tags may stay in docs, debug, or advanced helper text only if clearly optional.
6. Ensure loading/error/empty states have screenshots in the 100-point runtime proof gallery:
   - `profile`
   - `record/[id]`
   - `records`
   - `inbox`
   - `wiki`
   - `research`
   - `trinity`
   - `insights`
7. Run `npm run verify` after code changes.

## Score impact

This is a P2 polish/trust gate. Overall score remains **98/100 provisional** until state affordances and proof screenshots are clean.
