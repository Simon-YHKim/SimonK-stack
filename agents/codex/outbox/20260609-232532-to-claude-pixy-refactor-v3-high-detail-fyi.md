---
from: codex
to: claude
type: fyi
priority: normal
created: 2026-06-09 23:25:30 KST
topic: 2ndB Pixy refactor v3 high-detail mobile assets
---

[2026-06-09 / 23:25:30 KST] Simon requested a higher pixel count and quality increase after v2. Generated v3.

- Output root: `C:\Coding\2ndB\assets\generated\pixy-refactor-v3`
- Scope: 7 tier/style anchors + 57 reusable button glyphs = 64 assets.
- v3 changes from v2:
  - native source grid increased to 128x128
  - richer central pictorial objects
  - stronger reference-like blue crystal bevels
  - outputs: `png_512`, `png_256`, `png_128`, `png_96`, `png_64`
  - mobile QA sheets: `qa/mobile_96_contact_sheet.png`, `qa/mobile_64_contact_sheet.png`, `qa/mobile_48_sim_contact_sheet.png`
- App usage recommendation:
  - tier/core anchors: graph nodes, cards, profile panels, hero/card art at 64dp+.
  - button glyphs: tabs, chips, icon buttons; use `png_64` for compact controls and `png_96`/`png_128` for larger buttons/cards.
- Verification:
  - Pixy `check_sprite.py`: 64/64 passed.
  - alpha corners: passed for 512/256/128/96/64 output folders.
  - representative `tier2_wisdom_core` official Pixy render SHA matched current `png_256` byte-for-byte.
  - secret scan only matched the UI label `password visibility`; no credential pattern found.
- No app source code overwritten.
- No push performed.
