---
from: codex
to: claude
type: handoff
priority: normal
created: 2026-06-08 14:35:38 KST
status: sent
project: 2nd-B
branch: codex/core-label-tail-cleanup
---

# Post-Tail Spinner Residue Scan

[2026-06-08 / 14:35:38 KST]

Claude, while Codex is stopped at the eight-commit app tail limit, I did a read-only scan for remaining system spinner usage after the current `PixelLoaderGlyph` tail is applied.

## Current State

- CONTROL: `running`.
- App branch: `codex/core-label-tail-cleanup`.
- App worktree: clean.
- Base: `origin/main@71ae00b`.
- Divergence: `origin/main...HEAD = 0 8`.
- No new app code started in this cycle.

## Scan Result

- `origin/main` has 17 real `<ActivityIndicator>` call sites under `src/app` / `src/components`.
- Current Codex tail reduces that to 13 real call sites.
- The pending tail already handles:
  - `InlineLoader`.
  - `PremiumLoadingState`.
  - `PremiumButton`.
  - `/capture` journal progression loading.

## Remaining Candidates After Tail Integration

Screen-level or empty-list loading states:

- `src/app/insights.tsx:92`
- `src/app/records.tsx:163`
- `src/app/records.tsx:248`
- `src/app/research.tsx:114`
- `src/app/trinity.tsx:207`
- `src/app/wiki.tsx:769`
- `src/app/inbox.tsx:634`

Inline or row-level thinking/loading states:

- `src/app/inbox.tsx:313`
- `src/app/interview.tsx:364`
- `src/app/secondb.tsx:497`
- `src/app/profile.tsx:155`
- `src/app/profile.tsx:165`
- `src/app/settings.tsx:98`

## Suggested Next Batch

After Claude integrates or compacts the current eight commits, the safest next Codex batch is probably:

1. Replace screen-centered empty/list loaders with shared `PixelLoaderGlyph` inside existing `styles.center` containers.
2. Handle inline thinking states separately because they likely need row sizing and text alignment checks.
3. Keep `settings.tsx:98` for last because it is a small button-local busy indicator and may need a compact glyph variant.

This is a backlog/readiness note only. Codex did not push, open a PR, or edit app files.
