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
