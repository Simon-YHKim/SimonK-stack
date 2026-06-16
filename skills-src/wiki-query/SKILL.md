---
name: wiki-query
description: >
  Use when the user asks a question that the SimonKWiki personal wiki could
  answer — about Simon's self-analysis, circuits, projects, relationships,
  career, events, assessments, or any topic the wiki covers. Also triggers
  on "위키에서 찾아줘", "wiki에 물어봐", "wiki에서 찾아봐", "query the wiki",
  "ask the wiki". Reads wiki/index.md first to locate relevant pages, reads
  those pages, answers with [[wikilink]] citations, falls back to raw/ only
  when the wiki is insufficient, and when the answer has standalone value
  files it back as a new wiki page (the Knowledge Flywheel — every question
  enriches the wiki), then updates wiki/index.md and wiki/log.md. For the
  SimonKWiki v2 vault.
version: 0.1.0
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
compatibility:
  - claude-code
---

# Wiki Query

## Overview

Answers questions from the SimonKWiki knowledge layer and feeds good answers back
into the wiki. Run from the vault root. Implements the Karpathy llm-wiki Query
operation plus the **Knowledge Flywheel** — a question worth answering becomes a
new page, so the wiki compounds with use.

## Workflow

1. **Read `wiki/index.md` first.** Use it to identify which pages and categories
   are relevant to the question — index before raw is the search-order rule.
2. **Read the relevant `wiki/` pages** and answer from them. Cite every claim
   inline with `[[wikilink]]` — the reader must be able to trace each statement
   back to a page.
3. **Fall back to `raw/` only if needed.** If the wiki pages do not hold enough,
   search `raw/` with `Grep`/`Glob`. If even `raw/` has no answer, say so plainly
   — do not guess.
4. **File the answer back (Knowledge Flywheel).** If the answer has standalone,
   reusable value:
   - create `wiki/<category>/<slug>.md` (usually `concepts/` for a synthesized
     idea, or a `queries/` page) with proper frontmatter and `[[wikilinks]]`;
   - if a closely related page already exists, merge into it instead;
   - a throwaway or trivial answer is NOT filed — only durable knowledge.
5. **Sync.** Update `wiki/index.md` with the new or changed page, and append
   `wiki/log.md`:
   `YYYY-MM-DD HH:MM | query | <question> | <page filed, or no file>`.
6. **Report** the answer, then note what (if anything) was filed back.

## Principles

- **Index first, raw last.** The compiled wiki is the fast path; `raw/` is the
  expensive fallback.
- **Cite everything.** An answer without `[[wikilink]]` citations is not done.
- **The flywheel turns only on durable answers.** Do not file trivia — that
  bloats the wiki and accelerates staleness.
- **Never invent.** If the wiki and `raw/` do not answer it, say the wiki does
  not cover it yet.

## Related skills

- `wiki-ingest` — 새 source 를 raw → wiki 로 ingest (조회 전 단계)
- `wiki-lint` — query 결과 신뢰성 검증 전 wiki 정합성 점검
- `llm-wiki-builder` — wiki 초기 구조 + 운영 패턴

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
