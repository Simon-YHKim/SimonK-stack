---
name: founder-context
description: >
  Use when the user wants the four founder-context files (me.md,
  vision.md, design.md, workingstyle.md) at a project root — triggers
  "/founder-context", "/personal-bootstrap", "4 파일 만들어",
  "프로젝트 컨텍스트 세팅", "founder context", "bootstrap project
  foundation". Produces all four via per-file grilling-style interview
  (3-4 questions each), pre-populating from existing SimonK Stack
  assets when present: me.md from SimonKWiki entities/simon-yhkim,
  workingstyle.md from LESSONS_LEARNED + instincts, design.md from
  prior simon-design-first outputs. vision.md is interview-only.
  Supports single-file mode (`/founder-context vision`) and refresh
  with overwrite confirm. Different from /project-context-md (creates
  CLAUDE.md for Claude verification) and /domain-glossary (creates
  CONTEXT.md term dictionary) — these four files are HUMAN-facing
  founder docs: identity, vision, design principles, work patterns.
version: 1.0.0
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - AskUserQuestion
---

# /founder-context

Create the four founder-context files at the project root via guided
interview, importing where existing SimonK Stack assets cover the same
ground.

## The four files (project root)

| File | Scope | Source when seeding |
|---|---|---|
| `me.md` | Who the founder is — tech preferences, communication style, work hours, languages spoken | SimonKWiki `entities/simon-yhkim.md` § Tech Preferences (import option) |
| `vision.md` | What this project IS and why — one-liner, target user, value prop, success after 3mo/1yr, out-of-scope | Interview only (project-specific) |
| `design.md` | Visual & UX principles for THIS project — tone, palette (≤3 colors), fonts (Pretendard 한국어 + en sans-serif), reference URLs | `simon-design-first` skill prior outputs if any; otherwise interview |
| `workingstyle.md` | How the founder works on THIS project — branch strategy, test strategy, commit style, anti-patterns | SimonKWiki `LESSONS_LEARNED.md` relevant decision entries + `~/.claude/instincts/project-patterns.md` (import option) |

All four files live at the project root next to `CLAUDE.md` — never in
`.claude/`, never in `docs/`. This is deliberate: these are documents
people read, not tooling config.

## Why four (not three, not five)

Each file answers exactly one founder question:

- `me.md` — "who is shipping this?"
- `vision.md` — "what is being shipped, and why?"
- `design.md` — "how should it look and feel?"
- `workingstyle.md` — "how does the shipper work?"

Collapsing any two muddles the questions. Adding a fifth (e.g.
`strategy.md`, `roadmap.md`) crosses into living documents that change
weekly — founder-context files are intended to be **slow-changing**.

## Execution modes

### Mode A — Full bootstrap (default)

Triggered by `/founder-context` with no argument, "4 파일 만들어",
"프로젝트 컨텍스트 세팅", etc.

1. **Inventory existing files at the project root.** For each of the
   four, record present / missing.
2. **Inventory available SimonK Stack assets** for seeding:
   - `~/.claude/wiki/SimonKWiki/wiki/protocols/llm-wiki/entities/simon-yhkim.md` (or `Simon-LLM-Wiki` legacy)
   - `~/.claude/wiki/SimonKWiki/wiki/protocols/llm-wiki/LESSONS_LEARNED.md`
   - `~/.claude/instincts/project-patterns.md`
3. **For each of the four (in order: me → vision → design → workingstyle):**
   - If the file already exists at the project root, ASK whether to skip / update / overwrite. Default: skip.
   - Else, run the per-file interview (see below).
   - Write the file using the matching template at `templates/<file>.md` filled in with interview answers + imports.
4. **Final report**: which files were created / skipped / updated, and the next-step suggestion (commit + add references to CLAUDE.md if applicable).

### Mode B — Single-file update

Triggered by `/founder-context <file>` where `<file>` is one of
`me`, `vision`, `design`, `workingstyle` (no `.md` suffix needed).

Run only that file's interview + write step. Skip the others. Useful
when the founder's vision evolved and they want to refresh just
`vision.md` without re-interviewing about typography.

### Mode C — Refresh with overwrite

Triggered by `/founder-context --refresh [<file>]` or "다시 만들어".

Forces overwrite of existing files. Always show the existing content
in a code block first and confirm with `AskUserQuestion` before
discarding. If the user backs out, fall through to update mode (append
new section instead of overwriting).

## Per-file interview (grilling style)

Each file gets 3-4 questions, asked **one at a time** (not bulk).
Provide a recommended answer with each question so the founder can
just say "go with that" and proceed.

### me.md (3 questions)

1. **Role + tech bias** — "What do you ship most often (web app /
   mobile / data tool / infra)? And what's your default stack for
   that?" (recommended: read from imported `entities/simon-yhkim.md`
   if present, else ask)
2. **Communication preferences** — "Korean primary or English primary
   for code comments / commits / docs? Any words you don't want to
   see in your repos (e.g., 'leverage', 'robust')?"
3. **Work cadence** — "Solo or with collaborators on this project?
   What hours / timezone? How do you want async issues to ping you?"

### vision.md (4 questions)

1. **One-liner** — "If a friend asks 'what are you building?' what's
   the single sentence?"
2. **Target user** — "Who's the FIRST user? Be specific — name a real
   person if possible. Not 'developers' but 'me + 3 friends who do X'."
3. **Success in 3 months** — "What's the simplest observable thing
   that would say 'this is working'? (DAU, revenue, qualitative
   feedback — pick one metric)"
4. **Out of scope** — "What are you DELIBERATELY not building? List
   2-3 features people will ask for that you'll say no to."

### design.md (4 questions)

1. **Tone** — "Professional / friendly / premium / experimental? Pick
   one anchor word."
2. **References** — "3-5 sites whose feel you want this to match. Drop
   the URLs." (recommended: pull from
   `simon-design-first` skill prior session if available; else
   suggest 21st.dev / lapa.ninja / awwwards)
3. **Palette** — "Pick exactly 3 colors: accent, text, background. No
   pure black (#000), use tinted dark (e.g. #0F0E1A). No pure white
   either."
4. **Fonts** — "한국어: Pretendard (default) or other? English: which
   sans-serif? (NOT Inter — too AI-generated.)"

### workingstyle.md (3 questions)

1. **Branch + commit strategy** — "Main-only? Feature branches? Squash
   merges? Conventional Commits or freeform?" (recommended: pull from
   `~/.claude/instincts/project-patterns.md` if SimonK Stack is
   installed)
2. **Test strategy** — "TDD strict / write tests after / manual QA
   only / E2E only? What command runs the full suite?"
3. **Repeated mistakes to avoid** — "What 2-3 things does Claude
   keep doing on THIS project that you want explicitly banned in
   workingstyle.md?" (recommended: pull from
   `~/.claude/instincts/mistakes-learned.md` if present)

## Templates

The skill ships four templates at `templates/<name>.md`. Each has
placeholders like `{{ROLE}}`, `{{ONE_LINER}}` that the skill fills in
from interview answers. Templates are intentionally short — a founder
doc people don't read isn't worth writing.

## Synchronization rules

After creating files, surface (do NOT auto-execute) the sync options:

- **`me.md` → SimonKWiki `entities/simon-yhkim.md`** — if Tech
  Preferences in the wiki differ from `me.md`, ask which is the source
  of truth and propose a one-direction sync.
- **`workingstyle.md` → `~/.claude/instincts/project-patterns.md`** —
  if a new anti-pattern was named in the interview, propose appending
  it via the `simon-instincts` skill.
- **`design.md` ← `simon-design-first`** — note in `design.md` that
  any future design work should re-read this file first; this skill
  does not yet auto-wire that hook (separate PR).
- **`vision.md`** — no SimonK Stack counterpart; standalone.

The skill never silently mirrors. Each sync is a one-question
`AskUserQuestion` so the founder controls the source of truth.

## Anti-patterns (do NOT do)

- ❌ Creating any of the four files in `.claude/`, `docs/`, or
  `~/`-relative paths. They belong at the project root.
- ❌ Running all 14 questions in a single AskUserQuestion. Use
  per-file batches; the founder needs to think between files.
- ❌ Auto-overwriting an existing file. Always confirm first via
  Mode C's preview.
- ❌ Auto-syncing back to the wiki without explicit confirmation —
  the wiki is authoritative for cross-project content, and `me.md`
  is project-local.
- ❌ Treating `vision.md` as a marketing pitch. It's the founder's
  internal compass, not external copy. Out-of-scope is as important
  as in-scope.
- ❌ Adding emojis to any of the four files unless the founder
  explicitly asked. These are read by humans; the founder's voice,
  not the LLM's, should come through.

## Success criteria

The skill is only complete when:

1. All four files (or the targeted single file) exist at the project
   root with content reflecting the interview answers.
2. The founder confirmed (Mode A) or selected (Mode B/C) the scope.
3. No file imports were silent — every imported section is annotated
   with `> Imported from <source>` in the file.
4. The skill reported next-step sync suggestions without executing
   them.

## Related skills (explicit boundaries)

- `/project-context-md` — creates `CLAUDE.md` for Claude Code's
  verification loop (test commands, dev server, lint). Different
  audience (Claude vs human) and different content (tools vs context).
- `/domain-glossary` — creates `CONTEXT.md` term dictionary for
  industry-specific vocabulary. Complements `vision.md` (which is
  about WHAT/WHY) by handling jargon (HOW you describe it).
- `/simon-design-first` — interactive design intake before any UI
  code. Reads `design.md` if present (after this skill writes it),
  so the founder doesn't re-answer the same tone/palette questions.
- `/simon-instincts` — appends anti-patterns to global
  `~/.claude/instincts/`. Complements `workingstyle.md`
  (project-local) by handling cross-project patterns.
- `/grill-me` — relentless 1-Q-at-a-time interview for plans/specs
  in general. This skill borrows that interview pattern but is
  scoped to the four-file output.
- `/founder-context` is **not** a substitute for any of the above —
  it's the human-facing identity/vision/design/style layer that
  sits on top of them.

## Trigger phrases (matched by description block above)

- `/founder-context`, `/personal-bootstrap`
- `/founder-context me`, `/founder-context vision`, etc. (single-file)
- `/founder-context --refresh [<file>]`
- "4 파일 만들어", "프로젝트 컨텍스트 세팅"
- "founder context", "create me/vision/design files"
- "bootstrap project foundation"

## Operational notes

- The four files are tracked by git but never auto-committed by this
  skill. The founder commits when they're satisfied with the
  contents — sometimes that means writing one file, sleeping on it,
  and committing tomorrow.
- For multi-repo founders: `me.md` will be near-identical across
  projects. That's fine — it's the per-project COMMITMENT to the
  identity, not the duplication, that matters. The wiki holds the
  master.
