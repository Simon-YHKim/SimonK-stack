---
name: stitch-design-flow
description: Google Stitch (stitch.withgoogle.com) 용 디자인 프롬프트 생성기. DESIGN.md 를 읽고 Safe/Bold/Wild 3가지 방향의 붙여넣기 가능한 프롬프트를 출력한다. Use this skill proactively whenever the user says things like "디자인 시안 만들어줘", "UI 초안", "Stitch 프롬프트", "와이어프레임 프롬프트 써줘", "목업 프롬프트", "design mockup prompts", "UI prompt for Stitch"—even without mentioning Stitch by name, if they want AI-generated UI mockups for a product defined in DESIGN.md. This skill produces text only (no API calls, no MCP, no image generation). The user pastes the prompts into Stitch web UI manually. Do NOT trigger for live design feedback, HTML generation, or visual QA (use /design-review, /design-html, /design-shotgun instead).
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
version: 1.1.0
author: simon
---

# Stitch Design Flow

**Pure text prompt generator.** No API, no MCP, no image generation. The skill's entire job is turning a product's DESIGN.md into 3 strategically-different prompts that the user pastes into https://stitch.withgoogle.com manually.

## Why three directions

Generating one prompt gives one answer. Generating three strategically different prompts forces the user (and the model) to compare tradeoffs. The "Safe / Bold / Wild" axis is deliberately pessimistic → optimistic → experimental so the user sees the full range before committing.

| Variant | Strategy | Reference aesthetics |
|---|---|---|
| **A — Safe** | Industry conventions, proven patterns, low risk | Stripe, Linear, Vercel |
| **B — Bold** | Differentiated personality, strong visual voice | Figma, Notion, Arc |
| **C — Wild** | Experimental, hi-risk / hi-reward | Raycast, Rauno Freiberg, Framer showcases |

## Workflow

### 1. Locate DESIGN.md

Run `test -f DESIGN.md` at repo root. If missing, stop and request `/design-consultation` first — this skill cannot invent brand directions; it only translates an existing DESIGN.md into prompts.

### 2. Extract the six brand inputs

Parse from DESIGN.md:
- Product name + one-line pitch
- Target audience
- Tone keywords (modern / playful / minimal / editorial / brutalist / glassmorphism / neumorphic / ...)
- Color palette (primary / secondary / accent / neutral, hex)
- Typography (display / body / mono fonts)
- Key screens (usually 3: e.g. landing / dashboard / detail)

If anything is missing, ask the user inline — don't guess.

### 3. Generate three prompts

For **each** key screen, produce three variants (A/B/C). Use the template in `references/prompt-template.md`. For industry-specific flourishes see `references/prompt-recipes.md` (SaaS, 커머스, 부동산, 블로그, 핀테크, 교육, 모빌리티, AI 제품, 커뮤니티, 헬스케어).

Alternatively, let the bundled script do the parsing + output for you:

```bash
bash scripts/generate-prompts.sh DESIGN.md
```

The script reads DESIGN.md, extracts the six inputs, and writes `docs/design/stitch-prompts-<YYYY-MM-DD>.md` with A/B/C × N screens. If DESIGN.md is non-standard and parsing fails, fall back to manual template application.

### 4. Constraint defaults

Every prompt inherits these unless the user overrides:
- Mobile-first, 375px viewport baseline
- WCAG AA contrast ratios
- Korean + English copy when the target market is Korean (한/영 병기)
- No stock photography — illustrations or abstract shapes only
- Max 3 typography weights per screen

### 5. Output location

Save prompts to `docs/design/stitch-prompts-<YYYY-MM-DD>.md` and print them to the chat. Users must paste **one prompt at a time** into Stitch — batching prompts in a single paste confuses Stitch's parser.

After Stitch produces images, ask the user to save results as:
```
docs/design/stitch-output-A-<screen>.png
docs/design/stitch-output-B-<screen>.png
docs/design/stitch-output-C-<screen>.png
```

### 6. Next step

Once images are saved, hand off to `/design-shotgun` (variant exploration), `/design-review` (visual QA), or `/design-html` (HTML/CSS conversion). This skill's job ends at prompts.

## Absolutely no API or MCP

Earlier attempts considered a Stitch MCP server. **There is no such thing.** Stitch is a web UI only — no public API, no MCP, no CLI. If a user pastes a Stitch "API key" into the conversation, do not store it, do not write it to `.env`, do not call any endpoint with it. Ask the user to rotate it and proceed with the text-only workflow. The same applies to any variant like "stitch-mcp", "stitch-sdk", "figma-to-stitch" — all out of scope.

## Checklist

- [ ] DESIGN.md exists (or `/design-consultation` run first)
- [ ] All six brand inputs parsed successfully
- [ ] Three variants A / B / C produced for each key screen
- [ ] Constraint defaults applied (mobile-first, WCAG AA, bilingual)
- [ ] Output saved to `docs/design/stitch-prompts-<date>.md`
- [ ] User guided to paste one prompt at a time into Stitch web UI
- [ ] No API calls, no MCP registration, no secret storage

## Common mistakes and corrections

- **Generating prompts without DESIGN.md** — produces generic designs with no brand alignment. Stop and run `/design-consultation` first; DESIGN.md is the source of truth, not an optional nicety.
- **A / B / C variants too similar** — if the three prompts read as paraphrases, the comparison is worthless. Deliberately stretch: A leans on Stripe-like conservative conventions, B picks a strong visual voice, C pushes experimental territory. If you can't tell them apart at a glance, rewrite.
- **Monolingual prompts for Korean products** — AI mockup tools default to English stock copy, which looks broken for Korean services. Every constraint block must list Korean copy requirements when the target is Korean.
- **Batching prompts in one paste** — Stitch processes one prompt at a time. Concatenated prompts produce mangled output. Tell the user to paste one variant, wait for output, then next.
- **Missing save path** — images without a stable filename can't be fed to `/design-shotgun` later. Always specify `docs/design/stitch-output-<variant>-<screen>.png`.

## Related skills

- `/design-consultation` — **Upstream**. Produces the DESIGN.md this skill consumes. If DESIGN.md is missing or thin, run this first.
- `/design-shotgun` — **Downstream**. Takes Stitch-generated images and explores variants / collects feedback. Run after you have 3+ mockups saved.
- `/design-review` — **Parallel**. Visual QA for live sites. Different role — use when production UI already exists.
- `/design-html` — **Downstream**. Turns an approved mockup into production HTML/CSS. Usually the step after `/design-shotgun`.
- `app-dev-orchestrator` — Step 5 of the 21-stage pipeline calls this skill.
