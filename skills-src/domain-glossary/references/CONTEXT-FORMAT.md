# CONTEXT.md format

A pure glossary for a project's domain concepts. Read at session start; updated lazily when terms get resolved.

## Contents

- [Structure](#structure) — the file template
- [Rules](#rules) — term definitions, relationships, flagged ambiguities
- [What NOT to put in CONTEXT.md](#what-not-to-put-in-contextmd) — exclusions
- [Example](#example) — Course Video Manager sample
- [Sizing guidance](#sizing-guidance) — when to split
- [Maintenance](#maintenance) — update cadence

## Structure

```markdown
# <Project Name>

<one-line description of what this project is and who uses it>

## Language

**TermName**:
<one-paragraph definition in the voice the project actually uses.
Avoid implementation details — say what the term *means* in the domain,
not how it's coded.>
_Avoid_: <older synonyms, fuzzy words this term replaces>

**AnotherTerm**:
<...>

## Relationships

- A **TermName** owns many **OtherTerms**
- An **OtherTerm** belongs to exactly one **TermName**
- A **TermName** can be in states: `pending`, `active`, `archived`

## Flagged ambiguities

- "<old fuzzy word>" was previously used to mean both X and Y — resolved: split into **TermA** and **TermB**.
- "<another fuzzy word>" — still unresolved. Tracked in #issue-123.
```

## Rules

### Term definitions

- **One paragraph max.** If you need more, you're writing a spec, not a glossary.
- **Use the term in the project's voice.** "Order" not "Purchase Object". "Materialization" not "FileSystem Entry Creation".
- **No implementation details.** Don't say "stored in `orders` table with FK to `users.id`" — say "an Order belongs to one Customer".
- **List avoid-synonyms.** If "ticket" was used in the past for what's now an Issue, list it so the agent flags drift.

### Relationships section

- One-liners only. Cardinality + ownership.
- If a relationship has interesting nuance, that nuance belongs in an ADR, not here.

### Flagged ambiguities section

- Living section. Add when ambiguity is *discovered*. Remove when *resolved*.
- Each flagged term should link to where it's being decided (issue, ADR, grill-me transcript).

## What NOT to put in CONTEXT.md

- API endpoints
- Database schemas
- Function signatures
- File paths
- Architecture decisions (those go in `docs/adr/`)
- TODO lists or sprint plans
- User stories or PRDs
- Verification commands (those go in `CLAUDE.md`)

If you find yourself adding any of the above, you are writing the wrong file.

## Example

```markdown
# Course Video Manager

A tool for organizing video lessons inside course sections, supporting drafts that
later get promoted to "real" lessons with file-system presence.

## Language

**Course**:
The top-level container students enroll in. Has metadata, marketing pages, and
ordered Sections.
_Avoid_: class, program

**Section**:
An ordered group of Lessons inside one Course. Sections themselves are not
purchasable — students buy access to the Course as a whole.
_Avoid_: chapter, module

**Lesson**:
A single learning unit (video + transcript + exercises). Lives in exactly one
Section.
_Avoid_: video, unit, item

**Materialization**:
The act of giving a draft Lesson a spot in the file system, making it real for
publishing. Once materialized, a Lesson can be exported.
_Avoid_: realization, manifestation, file creation

**Materialization Cascade**:
The bug-prone process where materializing a Lesson inside a non-materialized
Section forces the Section (and possibly its parent Course) to materialize too.
_Avoid_: parent cascade, cascading creation

## Relationships

- A **Course** owns many **Sections**
- A **Section** belongs to one **Course** and owns many **Lessons**
- A **Lesson** belongs to one **Section**
- Materialization cascades upward: materializing a **Lesson** materializes its
  ancestors

## Flagged ambiguities

- "promote" was used for both "materialize" and "publish to learners" — resolved:
  "materialize" is internal file-system promotion; "publish" is making available
  to students.
```

## Sizing guidance

- 5–30 terms: typical project
- 30–80 terms: large project, consider per-context split via `CONTEXT-MAP.md`
- 80+ terms: split is overdue
- Under 5 terms: probably not worth the file yet — defer

## Maintenance

- Update inline during `/grill-me` — don't batch
- During `/refactor` rename: if the new name disagrees with CONTEXT.md, fix one or the other (don't let them drift)
- During code review: flag any new module name that introduces a synonym for an existing term
