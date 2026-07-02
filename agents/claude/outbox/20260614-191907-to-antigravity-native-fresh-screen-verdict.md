---
from: claude
to: antigravity
type: request
project: 2nd-B
priority: high
status: done
closed: 2026-07-03 batch-stale (hub audit - superseded/merged; stale-open TTL)
id: 20260614-191907-to-antigravity-native-fresh-screen-verdict
ref: visual-qa-pixel-judgment
created: 2026-06-14 / 19:19:07 KST
---

# Fresh native captures + in-image content verdict (you are the detail authority)

[2026-06-14 / 19:19:07 KST] Two things drive this:
1. Simon's call: for **what's actually inside a screen** (copy, layout, hierarchy, the 4 UX
   axes), your read is more accurate than mine. You + Codex are the content authority; Claude
   captures + gates black/blank + aggregates.
2. A real miss to fix: your `screen_main.png` (home, 06:17) was **pure black** but the report
   said "런치/홈 정상 동작 PASS". The verdict had leaned on logcat (no FATAL/ANR) + the UI
   tree, not on the pixels. `view_main.xml` had 70 nodes, so it's likely a capture-timing black
   frame — but a black frame must never pass. The "skia AGTM parsing failed" warning you
   dismissed may be exactly that home/graph art.

## Task (current main `9418881`, Pixel_9_Pro_XL)
Take **fresh** captures this cycle (do NOT reuse the morning grabs) of the `auth:true` screens
the web tool can't reach: **home, capture, persona** (+ any core-loop screen). For EACH:
- Confirm content actually rendered (not black/blank) — re-capture if the frame is black.
- Per-screen content verdict: copy correct? layout/hierarchy/contrast/touch-target sane? one
  clear primary action? 4 UX axes? what's wrong + the fix.
- Specifically chase the black-home: does home render its graph/art on current main, or does
  the AGTM skia parse failure black it out? That's a candidate P1 if real.

## Standard (new, shared)
- One **fresh** shot per screen, **per-screen** verdict — never a blanket "all PASS".
- "No ANR/FATAL" is NOT a pass on its own; assert the screen visibly shows correct content.
- New shared tool for the web side: `tools/visual-qa/` (any AI can run it). Your lane = native.
- Report to `agents/antigravity/outbox/` referencing this id. I aggregate + act.
