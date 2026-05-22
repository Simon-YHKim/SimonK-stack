---
name: wiki-ingest
description: Use when the user adds new source material to the SimonKWiki personal wiki and wants it compiled in. Triggers on "인제스트해줘", "raw에 저장한 글", "방금 클리퍼로 저장한", "이거 위키에 정리해줘", "wiki에 추가해줘", "ingest this", "add this to the wiki", or whenever the user shares a fresh article, paper, or note and shows intent to keep it. Detects the newest not-yet-ingested files under raw/, reads them without modifying raw/, produces a Key Claims / Entities / Concepts summary, asks the user four reflection questions, then on confirmation creates a wiki/sources/ page, updates related entity and concept pages with [[wikilinks]], runs a backlink audit, and updates wiki/index.md and wiki/log.md. For the SimonKWiki v2 Karpathy raw/wiki/Output model.
version: 0.1.0
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
compatibility:
  - claude-code
---

# Wiki Ingest

## Overview

Compiles new source material from `raw/` into the `wiki/` knowledge layer of the
SimonKWiki vault, following the Karpathy llm-wiki Ingest operation. Run from the
vault root (the directory holding `CLAUDE.md`, `raw/`, `wiki/`, `Output/`). This
skill never modifies `raw/` — raw is immutable. It produces a source-summary
page, updates entity and concept pages, and keeps `index.md` and `log.md` in sync.

## Workflow

A **two-phase** flow. Phase 2 starts only after the user answers Phase 1's questions.

### Phase 1 — Understand the source

1. **Detect new files.** List `raw/` recursively, newest first — for example
   `find raw -type f -name '*.md' -not -path '*/emotions/*' -printf '%T@ %p\n' | sort -rn`.
   A file is "not yet ingested" if its name is absent from `wiki/log.md` or its
   frontmatter has `ingested: false`. If several qualify, ask which to ingest;
   if one is the clear newest, proceed with it.
2. **Read the file** fully. **Never edit, rename, or delete anything in `raw/`**
   (raw immutability — the first wiki rule).
3. **Summarize** in three sections: **Key Claims** (main arguments),
   **Entities Mentioned** (people, tools, organizations), **Concepts Covered**
   (abstract ideas, frameworks).
4. **Ask four reflection questions, then stop and wait for the answer:**
   - 이 글을 왜 캡처했어? 어떤 점이 눈에 띄었어?
   - 지금 하고 있는 일이나 관심사와 어떻게 연결돼?
   - 이 글에서 너의 생각·경험과 다른 점은?
   - 이걸로 뭘 해보고 싶어?
   - **Gate:** do not advance to Phase 2 until the user responds.

### Phase 2 — Compile into the wiki

5. **Create the source page** at `wiki/sources/<YYYY-MM-DD-slug>.md`:
   - frontmatter: `title`, `category: source`, `created`, `last-updated`,
     `status`, `sources` (the `raw/` path), `tags`
   - sections: **Key Claims**, **Entities Mentioned**, **Concepts Covered**,
     **나의 코멘트** (built from the user's Phase 1 answers)
6. **Update related entity / concept pages.** For each entity or concept the
   source touches: if a page exists, merge the new information and add
   `[[wikilinks]]`; if not, create a new page in the right category.
7. **Backlink audit.** Scan every existing `wiki/` page; where a page is related
   to this source but not yet linked, add a `[[wikilink]]`.
8. **Update `wiki/index.md`** — add new pages, reflect changed ones (one line,
   120 chars or fewer each).
9. **Append to `wiki/log.md`:**
   `YYYY-MM-DD HH:MM | ingest | <source name> | <pages created/updated>`.
10. **Report** the source page path, pages created/updated, and links added.

## Principles

- **raw/ is immutable.** Read it, cite it, never write it.
- **Discuss before compiling.** The four Phase 1 questions are a gate, not a
  formality — the answers become the 나의 코멘트 section.
- **Update beats create.** Prefer merging into an existing page over spawning a
  near-duplicate (staleness defense).
- **Every operation is logged.** No silent wiki changes.
