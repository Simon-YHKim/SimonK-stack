---
name: explain
description: "Use when the user asks \"how does X work\", \"walk me through\", \"explain this code\", \"이 코드 설명해줘\", \"what does this do\", \"이게 뭐하는거야\"—or wants to understand unfamiliar code, a module, or a system. Produces a structured walkthrough: entry points, data flow, key invariants, and where to make changes."
version: 1.0.0
author: general-dev
---

# Explain Skill

Help the user understand unfamiliar code by tracing it from entry point to behavior.

## Workflow

1. **Identify the target**
   - A function? A file? A module? A whole system?
   - Adjust depth accordingly — don't explain a 5-line function with a 500-word essay

2. **Read everything relevant**
   - The target code itself, in full
   - Its callers (use `Grep` to find usages)
   - Its dependencies (what does it call?)
   - Related types/interfaces

3. **Build a mental model**
   - What is the **purpose**? (one sentence)
   - What are the **inputs and outputs**?
   - What is the **control flow**? (sequential, branching, async, recursive)
   - What are the **side effects**? (DB writes, network, filesystem, mutation)
   - What are the **invariants and assumptions**?

4. **Explain in layers** — Match the user's level:
   - **High level first** — "This module handles user authentication via JWT"
   - **Then the flow** — "When a request comes in, it does A → B → C"
   - **Then specifics** — only the parts that are non-obvious or were asked about
   - **Cite line numbers** so the user can follow along: `auth.py:42`

5. **Highlight the non-obvious**
   - Surprising behavior, gotchas, historical baggage
   - Why it's designed this way (if you can tell from the code/comments/git log)
   - Where the complexity actually lives

## Principles

- **Don't just paraphrase the code.** "This loop iterates over users" is useless. Explain *why* it iterates and what it's accomplishing.
- **Use the user's vocabulary.** If they said "endpoint", don't switch to "route handler".
- **Diagrams help for flow** — ASCII arrows are fine for sequences.
- **Be honest about uncertainty.** "I'm not sure why this check exists — there's no comment and no test covering it" is more useful than a confident guess.
- **Stop when they understand.** Don't dump every detail — answer the question that was asked.

## Format suggestions

For a function: purpose → signature → flow → edge cases → callers
For a module: purpose → public API → key types → internal flow → dependencies
For a system: purpose → components → data flow → entry points → key files

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
