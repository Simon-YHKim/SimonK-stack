# Stitch Prompt Template

Use this when `scripts/generate-prompts.sh` fails to parse a non-standard DESIGN.md, or when you want to hand-craft each prompt.

## Contents

- [Base Template](#base-template)
- [Slot Descriptions](#slot-descriptions)
- [Variant Presets](#variant-presets)
- [Example (filled in)](#example-filled-in)

---

## Base Template

```
Design a {SCREEN_NAME} for {PRODUCT_NAME}.
Pitch: {ONE_LINE_PITCH}
Target users: {AUDIENCE_DESCRIPTION}

Tone: {TONE_KEYWORDS}, leaning {Safe|Bold|Wild}
Primary color: {PRIMARY_HEX}
Secondary color: {SECONDARY_HEX}
Accent: {ACCENT_HEX}
Typography: {DISPLAY_FONT} for headings, {BODY_FONT} for body, {MONO_FONT} for code

Key elements:
- {ELEMENT_1}
- {ELEMENT_2}
- {ELEMENT_3}

Constraints:
- Mobile-first, 375px viewport baseline
- WCAG AA contrast ratios
- Korean + English copy (한/영 병기) — target market is Korean
- No stock photography — illustrations or abstract shapes only
- Max 3 typography weights per screen
- {CUSTOM_CONSTRAINT_IF_ANY}

Style reference: {REFERENCE_PRODUCTS}
Avoid: {ANTI_REFERENCE_PRODUCTS}
```

## Slot Descriptions

- **SCREEN_NAME**: `landing page`, `dashboard`, `product detail`, `checkout`, `settings`, etc.
- **PRODUCT_NAME**: Official product name from DESIGN.md title
- **ONE_LINE_PITCH**: The one-sentence "what this product is" from DESIGN.md (usually under the product name)
- **AUDIENCE_DESCRIPTION**: Who uses this — e.g. "Korean small business owners running Shopify-style stores"
- **TONE_KEYWORDS**: 2-4 adjectives from DESIGN.md — "modern, minimal, warm", "editorial, bold, playful", etc.
- **PRIMARY_HEX / SECONDARY_HEX / ACCENT_HEX**: Colors from DESIGN.md. Primary is the dominant brand color, secondary complements it, accent is used sparingly
- **DISPLAY_FONT / BODY_FONT / MONO_FONT**: Font families from DESIGN.md
- **ELEMENT_1..3**: Required UI pieces — "hero with CTA", "feature grid", "testimonial carousel", "pricing table"
- **CUSTOM_CONSTRAINT_IF_ANY**: Product-specific rules — "must show real-time data", "no modals (full page routing)", "supports keyboard-only navigation"
- **REFERENCE_PRODUCTS**: 2-3 products whose aesthetic you want to emulate
- **ANTI_REFERENCE_PRODUCTS**: 1-2 products to explicitly avoid mimicking — helps Stitch diverge from common patterns

## Variant Presets

### A — Safe (conservative)
```
Tone: modern, minimal, trustworthy, leaning Safe
Style reference: Stripe, Linear, Vercel, Notion's marketing pages
Avoid: experimental motion, unusual layouts, novelty typography
```

### B — Bold (differentiated)
```
Tone: expressive, confident, memorable, leaning Bold
Style reference: Figma, Arc Browser, Raycast marketing, Framer showcases
Avoid: corporate templated layouts, generic gradient backgrounds
```

### C — Wild (experimental)
```
Tone: experimental, provocative, hi-risk, leaning Wild
Style reference: Rauno Freiberg portfolio, Arena.social, Are.na, Linear's motion details, Awwwards winners
Avoid: anything that looks like a SaaS template, typical hero + features layout
```

## Example (filled in)

```
Design a dashboard for HanOkHunter.
Pitch: Discover and save authentic hanok accommodations across Korea.
Target users: Korean and international travelers seeking traditional stays, 25-45 yo, middle to upper income.

Tone: warm, cultural, editorial, leaning Bold
Primary color: #8B4513 (warm clay)
Secondary color: #F5E6D3 (rice paper)
Accent: #D2691E (persimmon)
Typography: Pretendard for headings, Noto Serif KR for body, JetBrains Mono for code

Key elements:
- Map of Korea with saved hanoks pinned by region
- Upcoming booking cards (swipeable)
- Recently viewed horizontal scroll
- Quick search with region filters (서울 북촌 / 전주 한옥마을 / 안동 등)

Constraints:
- Mobile-first, 375px viewport baseline
- WCAG AA contrast ratios
- Korean + English copy (한/영 병기)
- No stock photography — use traditional patterns or abstract ink-wash backgrounds
- Max 3 typography weights per screen
- Must feel "Korean traditional" without using cliché elements (paper lanterns, dragons)

Style reference: Figma, Arc Browser, Stayfolio (Korean hanok booking)
Avoid: generic Airbnb clone layout, Western hotel booking chrome
```
