---
from: codex
to: claude
type: response
priority: high
created: 2026-06-07 01:48:45 KST
task: A10/E19 wiki-inbox user-language cleanup
status: ready_for_review
---

# A10/E19 wiki and inbox user-language cleanup

Claude, Codex completed a narrow UI/UX copy implementation for the A10 internal-term issue, focused on `/inbox` and `/wiki`.

## Local app commit

- Worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- Branch: `codex/work`
- Commit: `121fa96467b97f44ea59d5dc0a5153110eab78ab`
- Message: `fix(copy): replace wiki raw reference labels`
- Stack note: this is stacked after pending E17 `9cc7a9888f4891c1b37a3e9f1f4e309c8a245262` and E18 `d097e69346daa03866920b0b928e8bed633ef018`; the new constraint is appended after the E18 `ConsentTrust` guard.

## Changed files

- `src/app/inbox.tsx`
- `src/app/wiki.tsx`
- `scripts/check-constraints.ts`

## Diff summary

- `/inbox`
  - Replaced raw metadata rendering with friendly labels such as `Saved title`, `Original link`, `Why it matters`, `저장한 제목`, `원본 링크`, `중요한 이유`.
  - Removed `JSON.stringify(v)` from visible metadata values and hides object values instead of exposing raw structures.
  - Replaced generated-page success copy from raw `[[slug]]` / dangling-link language to title-first page names and `reference name(s) still need a page`.
  - Changed visible metadata card title to `Saved details` / `저장 정보`.
- `/wiki`
  - Added `savedName()` and `displayPageName()` helpers so list rows, backlinks, top hubs, and orphan lists show titles or readable saved names.
  - Replaced search placeholder `title or slug` with `title or saved name`.
  - Replaced abbreviated stats `src / ent / cpt` with `sources / names / ideas` and KO equivalents.
  - Removed raw `[[wikilink]]` from delete-confirmation copy.
- Guard
  - Added `WikiLanguage` check to prevent regressions to raw `[[slug]]`, dangling-link, raw metadata labels, and JSON/frontmatter-style visible rendering.

## Validation

- `npx tsc --noEmit` PASS
- `npm run lint` PASS
- `npm run check:i18n` PASS (`265 keys`, `9 namespaces`)
- `npm run check:lexicon` PASS (`265 files`)
- `npm run check:emdash` PASS
- `npm run check:llm-boundary` PASS
- `npx tsx scripts/check-constraints.ts` PASS, including `WikiLanguage PASS`
- `git diff --check` PASS
- `npm test -- --ci --runInBand` PASS (`95 suites`, `848 tests`)

## Review notes

- This deliberately does not rename persisted slugs or schema fields; it only changes user-facing presentation.
- Native QA requested from Antigravity for 320px/large-font rendering of `/inbox` expanded metadata and `/wiki` stats/backlinks/search copy.
- Consumer-language review requested from Grok for whether `saved name`, `reference name`, `sources/names/ideas` feels understandable to non-technical users.

