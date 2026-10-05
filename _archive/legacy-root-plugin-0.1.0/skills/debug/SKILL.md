---
name: debug
description: Use when the user reports an error, unexpected behavior, failing test, or asks to debug something—triggers include "디버깅", "버그 고쳐줘", "이게 왜 안 돼", "debug this", "fix this error", "why is X broken", "tests failing". Produces a root-cause diagnosis with the specific fix applied and verification that the bug no longer reproduces.
version: 1.0.0
author: general-dev
---

# Debug Skill

Find and fix bugs by working from symptoms to root cause — never patch over the symptom.

## Workflow

1. **Reproduce first** — Before changing anything:
   - Get the exact error message, stack trace, or unexpected output
   - Identify the minimal command/input that triggers it
   - Confirm you can reproduce it locally

2. **Read the error carefully**
   - The stack trace usually points directly at the failure site
   - Note line numbers, file paths, and the actual vs expected values
   - Check timestamps if it's intermittent

3. **Form a hypothesis**
   - What component is failing?
   - What recent change could have introduced it? (`git log -p <file>`)
   - What inputs could put the code in this state?

4. **Isolate**
   - Add targeted logging or use a debugger — don't spray `print` everywhere
   - Bisect: comment out half the code, narrow until the bad line is found
   - Use `git bisect` for regressions in committed code

5. **Find the root cause** — Ask "why?" until you reach the actual defect:
   - "It crashes" → why? → "null pointer" → why? → "API returned empty" → why? → "auth expired silently" ← **root cause**
   - Stop only when fixing the cause prevents the whole class of bug

6. **Fix at the right level**
   - Fix the root cause, not the symptom
   - Don't add try/catch to swallow errors — handle them meaningfully
   - Don't add validation downstream when the upstream contract should hold

7. **Verify**
   - The original repro now passes
   - Related tests still pass
   - Add a regression test if feasible

## Anti-patterns to avoid

- 🚫 Catching and ignoring exceptions to make the error go away
- 🚫 Adding `if (x == null) return;` without understanding why `x` is null
- 🚫 Retrying flaky tests instead of fixing flakiness
- 🚫 "It works now" without understanding what changed
- 🚫 Disabling tests, linters, or type checks to bypass failures
