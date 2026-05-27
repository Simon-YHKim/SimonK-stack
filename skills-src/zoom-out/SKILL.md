---
name: zoom-out
description: >
  Use when the user is unfamiliar with a section of code and needs the
  bigger picture — triggers "줌아웃", "전체 그림", "이 코드 어디에 속해",
  "큰 그림 보여줘", "이 모듈 어디서 쓰여", "zoom out", "go up a layer",
  "where does this fit", "give me a map", or "/zoom-out". Produces a
  one-layer-up map of relevant modules and callers, named using the project
  domain glossary vocabulary when CONTEXT.md exists. Manual-only — does not
  auto-trigger to avoid noise during normal coding flow.
version: 1.0.0
author: simon-stack
disable-model-invocation: true
---

# Zoom Out

코드 한 구역에 머물지 말고 한 layer 위로 올라가서 전체 그림 그리기. mattpocock/skills 의 동명 skill에서 영감.

Differs from `/explain` (which traces inside one function or module) — this is the *escalation* when one-layer-down detail is not enough. Use when explain alone leaves the user still asking "but where does this fit?"

## Behavior

I don't know this area of code well. Go up a layer of abstraction. Give me:

1. **A map of the relevant modules** — what 3-7 modules surround this code
2. **Caller graph** — who invokes this, with what intent
3. **Domain naming** — use the project's `CONTEXT.md` glossary terms if it exists; otherwise infer canonical names from the codebase

Keep it short. One-screen output. No deep dive into any single module — that's `/explain`.

## Output shape

```
[Domain area] — one-line purpose

Callers:
  - module-a   → calls when <intent>
  - module-b   → calls when <intent>

Surrounds:
  - module-x   → upstream dependency
  - module-y   → sibling, same boundary

This module fits at: <one-line position in system>
Next stop if drilling down: <pointer to /explain target>
```

## Composition

- Pair with `/explain` — `/zoom-out` first to orient, `/explain` to drill in
- Pair with `domain-glossary` — if `CONTEXT.md` exists, reuse its terms; if absent, this skill can flag canonical terms worth promoting to a glossary
- Pair with `karpathy-guidelines` — when the zoom-out reveals an architectural smell

## When NOT to use

- User already knows the area (use `/explain` for surgical detail)
- Bug fix in a known module (use `/debug`)
- Whole-system architecture review (use `/improve-codebase-architecture` if available, or `karpathy-guidelines`)
