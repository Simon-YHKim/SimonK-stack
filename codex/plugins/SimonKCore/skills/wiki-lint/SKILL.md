---
name: wiki-lint
description: Use when the user wants to check the health, consistency, and integrity of the SimonKWiki personal wiki. Triggers on "wiki 점검", "wiki 린트", "위키 점검해줘", "위키 건강검진", "lint the wiki", "wiki health check", "check the wiki". Scans all of wiki/ for eight issue classes across three severities — Error (broken [[wikilinks]], index.md vs file mismatch), Warning (contradictory page pairs, orphan pages with no inbound links, mentioned-but-missing concepts, stale claims), Info (missing cross-references, raw/ sources not yet ingested) — and produces a severity-grouped report giving what / where / how-to-fix for every finding. Proposes fixes only; never auto-applies them. For the SimonKWiki v2 vault.
version: 0.1.0
allowed-tools: Read, Bash, Grep, Glob
compatibility:
  - claude-code
---

# Wiki Lint

## Overview

Audits the `wiki/` layer of the SimonKWiki vault for consistency and integrity,
following the Karpathy llm-wiki Lint operation. Run from the vault root. Produces
a categorized findings report. **It proposes fixes — it does not apply them.**
The user decides what to fix.

## Workflow

1. **Build the inventory.** List every `*.md` under `wiki/`. Collect their
   basenames and every `[[wikilink]]` target across all pages.
2. **Run the eight checks**, grouped by severity:

   **Error — must fix (red)**
   1. **Broken `[[wikilinks]]`** — links pointing to a page that does not exist.
   2. **index.md vs reality mismatch** — pages missing from `wiki/index.md`, or
      index entries with no matching file.

   **Warning — should fix (yellow)**
   3. **Contradictory page pairs** — two pages whose claims conflict. Cite both
      sources; do not pick a side.
   4. **Orphan pages** — pages with no inbound `[[wikilink]]` from any other page.
   5. **Stub candidates** — concepts or entities mentioned across pages but with
      no page of their own.
   6. **Stale claims** — pages whose `last-updated` frontmatter is old, or
      content that reads as outdated.

   **Info — nice to have (blue)**
   7. **Missing cross-references** — pages clearly related but not linked.
   8. **Un-ingested raw sources** — files in `raw/` not yet recorded in
      `wiki/log.md`.

3. **Write the report.** For every finding state what / where / how to fix
   (무엇이 / 어디서 / 어떻게 고칠지). Group findings under the three severities.
   Optionally save it as `wiki/lint-report-<YYYY-MM-DD>.md`.
4. **Stop. Do not fix.** Present the proposals and wait — the user chooses which
   fixes to apply.
5. **Append `wiki/log.md`:**
   `YYYY-MM-DD HH:MM | lint | wiki/ | <error/warning/info counts>`.

## Principles

- **Propose, never auto-fix.** The user owns every change to the wiki.
- **Contradictions are surfaced, not resolved.** Cite both sides; let the user
  decide.
- **Severity is honest.** Only true breakage is an Error. Do not inflate
  warnings.
- **Loud findings, quiet when clean.** If the wiki is healthy, say so in one line
  rather than padding the report.

## Related skills

- `wiki-ingest` — 새 source 추가 직후 lint 권장
- `wiki-query` — lint 통과 후 조회 안전성 확보
- `llm-wiki-builder` — wiki 초기 구조 + 운영 패턴

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
