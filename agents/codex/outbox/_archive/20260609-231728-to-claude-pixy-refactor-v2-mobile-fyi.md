---
from: codex
to: claude
type: fyi
priority: normal
created: 2026-06-09 23:17:27 KST
topic: 2ndB Pixy refactor v2 mobile-ready assets
---

[2026-06-09 / 23:17:27 KST] Simon gave a quality correction after v1: v1 was too simple and did not communicate meaning well enough. Reference quality target: `C:\Coding\2ndB\assets\ChatGPT Image 2026년 6월 9일 오후 11_06_00.png`.

Generated a new v2 package:

- Output root: `C:\Coding\2ndB\assets\generated\pixy-refactor-v2`
- Scope: 7 tier/style anchors + 57 reusable button glyphs = 64 assets.
- Style changes from v1:
  - native grid increased from 32x32 to 64x64
  - thicker dark outlines
  - layered blue crystal/tesseract framing
  - clearer central semantic objects
  - app output sizes: `png_256`, `png_128`, `png_96`, `png_64`
  - mobile QA sheets added: `qa/mobile_64_contact_sheet.png`, `qa/mobile_48_sim_contact_sheet.png`
- Recommendation:
  - tier anchors: use for card/graph/core art at 64dp+.
  - button glyphs: use for mobile controls/tabs/chips, prefer `png_64`/`png_96` runtime assets.
- Verification:
  - Pixy `check_sprite.py`: 64/64 passed.
  - alpha corners: 64/64 passed for 256/128/96/64 output folders.
  - representative `tier2_wisdom_core` official Pixy render SHA matched current `png_256` byte-for-byte.
- No app source code overwritten.
- No push performed.
