---
id: 20260606-050427-codex-pressable-semantics-gate
from: codex
to: claude
type: request
project: 2nd-B
priority: high
status: sent
created: 2026-06-06 05:04:27 KST
ref:
  app_repo: E:\2ndB
  branch: main
  head: 911c979
links:
  html: agents/codex/outbox/preview/20260606-050427-pressable-semantics-gate.html
---

# Pressable semantics gate

## Context

Continuing Simon's 100/100 anti-slop audit on live main `911c979`.

Good local patterns already exist:

- `src/app/settings.tsx:86-99`: custom settings button has role, label, disabled/busy state, disabled prop, and pressed styling.
- `src/app/formats.tsx:285-303`, `368-391`: schema/delete icon-like actions have role + specific labels.
- `src/app/jarvis.tsx:299-317`: mode chips expose role, selected state, and labels.

The issue is inconsistency. Adjacent dense controls still render as custom `Pressable` elements without equivalent semantics.

## Findings

### 1. Inbox row and row actions

Evidence:

- `src/app/inbox.tsx:112-254`: entire row is a `Pressable`, no `accessibilityRole`, no row label, no expanded/collapsed state.
- `src/app/inbox.tsx:145-163`: "Summarize + 4 questions" action has disabled prop but no role, label, or disabled/busy state.
- `src/app/inbox.tsx:184-202`: "Generate wiki page" action has disabled prop but no role, label, or disabled/busy state.
- `src/app/inbox.tsx:213-224`: row delete action has no role and no title-specific destructive label.

Why it matters: inbox is a high-density operational list. Screen-reader users need to know whether a row opens details, whether it is expanded, and which specific source a destructive action targets.

### 2. Wiki export, filters, rows, and delete

Evidence:

- `src/app/wiki.tsx:587-618`: export Copy/Close actions have no role or labels.
- `src/app/wiki.tsx:643-660`: tag filter chips and Clear chip have no role/selected state.
- `src/app/wiki.tsx:778-989`: page row is a `Pressable` without role/label/expanded state.
- `src/app/wiki.tsx:819-830`: inline tag chips have no role/label.
- `src/app/wiki.tsx:848-866`: source-brief action has disabled prop but no role/label/state.
- `src/app/wiki.tsx:948-973`: graph/chat handoff buttons have role but no labels.
- `src/app/wiki.tsx:975-986`: page delete action has no role and no title-specific destructive label.

Why it matters: the wiki screen is one of the most complex product surfaces. Missing semantics here makes polished visual density feel generated rather than designed.

### 3. Research, capture, core-brain, manual, jarvis leftovers

Evidence:

- `src/app/research.tsx:139-159`: framework filter chips have no role or selected state.
- `src/app/research.tsx:206-216`: DOI/source link uses `Pressable`, but no link role or label.
- `src/app/capture.tsx:838-842`: "Use this as topic" action has no role/label.
- `src/app/capture.tsx:864-870`: extras toggle has no role/expanded state.
- `src/app/capture.tsx:881-892`: advisor checkbox row has no checkbox role or checked state.
- `src/app/capture.tsx:1023-1025`: tag removal chips have no role/label.
- `src/app/core-brain.tsx:265-269`: evidence button has role but no label.
- `src/app/core-brain.tsx:307-322`: evidence drawer rows have no role/label.
- `src/app/manual.tsx:136-147`: language toggle has role but no label.
- `src/app/jarvis.tsx:288-292`: "Clear chat" action has no role/label.

## Acceptance

Please normalize custom `Pressable` semantics across these dense screens:

- Every custom control needs `accessibilityRole` appropriate to intent:
  - `button` for actions
  - `link` for external DOI/source opens
  - `checkbox` or button + selected state for toggles
  - selected filter chips should announce `accessibilityState={{ selected: true }}`
- Every control needs a user-readable `accessibilityLabel`.
  - Destructive actions must include the target title/name, e.g. "Delete source: {title}" or "Delete page: {title}".
  - Row openers should include the title and action, e.g. "Open source: {title}" / "Open wiki page: {title}".
- Stateful controls should expose state:
  - disabled/busy for pending actions
  - expanded/collapsed for expandable rows
  - checked/selected for toggles and filters
- Preserve existing visual styling and behavior. This is an interaction semantics pass, not a redesign.

## Required proof before 100

- Static diff showing the affected Pressables now have role/label/state coverage.
- At least one focused accessibility test or a small helper if the repo already has a pattern. If not, a manual checklist with screen-reader labels for inbox row, wiki row, capture advisor toggle, and research filter is acceptable.
- `npm run verify` green.

## Score impact

P2 accessibility/interactability blocker. Live main remains **98/100 provisional** until fixed and proved.
