---
name: refactor
description: Use when the user asks to refactor, clean up, simplify, or restructure code—triggers include "refactor", "리팩토링", "clean up", "simplify this", "이거 정리해줘", "extract function", "rename variable". Produces structural improvements that preserve behavior, verified by the existing test suite.
version: 1.0.0
author: general-dev
---

# Refactor Skill

Restructure code to improve clarity and maintainability while preserving behavior.

## Workflow

1. **Understand before changing**
   - Read the entire file, not just the target function
   - Identify all callers (`Grep` for the symbol)
   - Find the existing tests — they are your safety net

2. **Establish a safety net**
   - If tests exist, run them first to confirm they pass
   - If no tests exist for the target code, **add characterization tests first** before refactoring
   - Never refactor untested code blindly

3. **Make small, behavior-preserving steps**
   - One refactor at a time (rename, extract, inline, move)
   - Run tests after each step
   - Commit between meaningful steps so you can roll back

4. **Common refactorings**
   - **Extract function** — when a block has a clear single purpose
   - **Rename** — when a name doesn't reflect what the code actually does
   - **Inline** — when an abstraction adds noise without value
   - **Replace conditional with polymorphism** — only when there are real, growing variants
   - **Introduce parameter object** — when a function takes 4+ related arguments

5. **Verify**
   - All tests still pass
   - Behavior is unchanged (no new features sneaked in)
   - Public API is unchanged (or callers updated)

## Principles

- **No new features.** A refactor that adds functionality is not a refactor — split it.
- **No premature abstraction.** Three similar lines of code is better than a wrong abstraction. Extract only when the duplication has actually hurt you.
- **Delete fearlessly.** Dead code, unused parameters, commented-out blocks — remove them.
- **Don't refactor what wasn't asked.** If the user wanted function `foo` cleaned up, don't reorganize the whole module.
- **Keep diffs reviewable.** A 2000-line refactor PR is unreviewable. Stage smaller changes.

## Anti-patterns

- 🚫 "While I'm here..." scope creep
- 🚫 Renaming variables in code you weren't asked to touch
- 🚫 Introducing design patterns for hypothetical future needs
- 🚫 Mixing refactor and bug fix in the same commit

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
