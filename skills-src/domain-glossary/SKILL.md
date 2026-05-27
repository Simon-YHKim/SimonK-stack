---
name: domain-glossary
description: >
  Use when the user wants a shared project-domain vocabulary that reduces
  verbosity across agent sessions — triggers "도메인 용어 정리", "프로젝트 용어집",
  "CONTEXT.md 만들어줘", "용어 통일", "domain glossary", "ubiquitous language",
  "build a CONTEXT.md", "project terminology", or "/domain-glossary". Produces
  and maintains a project-root CONTEXT.md as a pure glossary (no
  implementation details, no specs) following the ubiquitous-language pattern
  from Domain-Driven Design and mattpocock/skills grill-with-docs. Separates
  cleanly from instincts/ (which logs Claude mistakes) and project-context-md
  (which lists verification tools) — this is the domain language layer.
version: 1.0.0
author: simon-stack
---

# Domain Glossary

프로젝트 도메인 용어집 생성·유지. Eric Evans 의 ubiquitous language 패턴을 simon-stack 에 흡수. Inspired by [mattpocock/skills `grill-with-docs`](https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/SKILL.md) and his CONTEXT.md convention.

## Why this skill exists

세션마다 같은 개념을 다른 단어로 부르면 — 사용자는 "주문 취소", 코드는 `cancelOrder`, ADR 은 "rescission", Claude 는 "voiding the transaction" — Claude 는 매번 매핑을 다시 학습한다. 토큰 낭비 + 일관성 위험.

해법: 프로젝트 루트에 `CONTEXT.md` 한 페이지짜리 *glossary only* 파일. Spec 아님, 구현 디테일 아님, 결정 로그 아님 (그건 `docs/adr/`).

### 다른 simon-stack 파일과의 분리

| 파일 | 역할 | 누가 씀 |
|---|---|---|
| `~/.claude/instincts/` 4개 | Claude 의 *실수* 누적 | Claude 가 자동 append |
| `CLAUDE.md` (project) | 검증 도구·관용·금기 | 사람이 작성, 매 세션 로드 |
| **`CONTEXT.md`** | **프로젝트 도메인 용어집만** | **사람 + 이 skill 공동 관리** |
| `docs/adr/NNNN-*.md` | 의사결정 로그 | 결정 시점에 append |
| `wiki/` | 메타·자기분석 | 사용자 vault |

각각 다른 layer. 섞이면 안 됨.

## CONTEXT.md format

```markdown
# <Project Name>

<one-line description of what this project is>

## Language

**Term**:
<one-paragraph definition in the project's voice. Avoid implementation details.>
_Avoid_: <synonyms or older names this term replaces>

**Another Term**:
<...>

## Relationships

- A **Term** owns many **Other Terms**
- An **Other Term** belongs to exactly one **Term**

## Flagged ambiguities

- "<old fuzzy word>" was used for both X and Y — resolved: split into **Term A** and **Term B**.
```

Reference: `references/CONTEXT-FORMAT.md` (this skill's bundled spec).

## When to create or update

### Lazy creation

Do **not** scaffold an empty CONTEXT.md. Create it lazily the first time a domain term needs resolving — typically during a `/grill-me` session, or when you notice the same concept being called three different things in the codebase.

### Triggers to add a term

- User uses a fuzzy or overloaded word ("account" — Customer or User?)
- Two modules name the same concept differently (`Order` vs `Purchase`)
- A term from external API (Stripe `customer`) clashes with project term (`Customer`)
- During architecture review, a deep module deserves a canonical name

### Triggers to NOT add a term

- It's a UI label, not a domain concept
- It's an implementation detail (e.g., function name, table column)
- It's already in widespread CS vocabulary (no project-specific meaning)
- It will only appear once

## Anti-patterns

- **CONTEXT.md as spec dump** — kept being asked "where does X go?" Resist. Specs go in PRDs or issues.
- **CONTEXT.md as ADR replacement** — decisions with trade-offs go in `docs/adr/`. CONTEXT.md captures *what things are called*, not *why we chose them*.
- **CONTEXT.md as code documentation** — that's docstrings and `/explain`. CONTEXT.md is one layer up: the *concepts* the code expresses.

## Composition with simon-stack

- **`/grill-me`** — during interview, when a term is resolved, update CONTEXT.md inline (same turn). Don't batch.
- **`simon-research`** — when research surfaces an industry-standard term (e.g., "idempotency key" from Stripe docs), promote it to CONTEXT.md if the project uses it.
- **`autoplan`, `app-dev-orchestrator`** — planning phase should *read* CONTEXT.md first if it exists, and the planning output should use those exact terms.
- **`refactor`** — when renaming variables/files, check CONTEXT.md first; if the new name disagrees, surface the conflict to the user.
- **`karpathy-guidelines`** — naming consistency principle aligns with this skill.

## CONTEXT-MAP.md for multi-context repos

Large repos with multiple bounded contexts: place a `CONTEXT-MAP.md` at root pointing to per-context `CONTEXT.md` files:

```
/
├── CONTEXT-MAP.md                 ← lists contexts and where they live
├── docs/adr/                      ← system-wide ADRs
└── src/
    ├── ordering/
    │   ├── CONTEXT.md             ← ordering bounded context
    │   └── docs/adr/              ← ordering-specific ADRs
    └── billing/
        ├── CONTEXT.md
        └── docs/adr/
```

Only do this once the project has clearly separate domains — premature splitting wastes effort.

## Output

- `CONTEXT.md` (or `CONTEXT-MAP.md` + per-context files) created or updated
- The specific terms added or revised, listed in the response
- If a contradiction was surfaced (e.g., user's verbal term disagreed with code), the contradiction stated explicitly
