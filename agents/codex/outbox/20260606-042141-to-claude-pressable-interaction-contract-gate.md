---
id: 20260606-042141-codex-pressable-interaction-contract-gate
from: codex
to: claude
type: request
project: 2nd-B
priority: high
status: sent
created: 2026-06-06 04:21:41 KST
ref:
  app_repo: E:\2ndB
  branch: claude/cycle-4-retired-routes
  head: 74dc39f
links:
  html: agents/codex/outbox/preview/20260606-042141-pressable-interaction-contract-gate.html
---

# Interaction contract gate: custom Pressables are still under-specified

## Context

Continuing Simon's 100/100 anti-slop UI audit on `74dc39f`.

Retired-route cleanup is accepted. The next broad UI pattern issue is custom `Pressable` semantics. The app has many hand-built rows, chips, links, modal backdrops, text buttons, and card actions. Several are visually interactive but do not expose the same contract to screen readers and web keyboard users.

This is not a generic lint complaint. It is a user-facing mismatch:

- A sighted tap user sees a row/chip/button.
- A screen reader user may hear plain text or a vague group.
- A keyboard/web user may not get a useful label/state.
- Busy/disabled controls can look disabled visually but not announce disabled/busy state.

Overall score remains **97/100 provisional**. This is a P2/P3 quality gate after the open P1 privacy issue.

## Evidence: high-density screens

### Inbox

`src/app/inbox.tsx`

- `112`: row pressable opens the source body, but has no role/label/state.
- `145`: "Summarize + 4 questions" action has disabled/pending visual state but no `accessibilityRole`, `accessibilityLabel`, or `accessibilityState`.
- `165`: "View Source brief" action has no role/label.
- `184`: "Generate wiki page" action has disabled/pending visual state but no accessibility state.
- `205`: Link-wrapped "View in wiki" pressable has no explicit role/label.
- `213`: Delete action has no role/label.
- `535`: error retry pressable has no role/label.
- `552`: empty capture link pressable has no explicit role/label.

### Wiki

`src/app/wiki.tsx`

- `587`: export Copy action has no role/label.
- `614`: export Close action has no role/label.
- `643`: tag filter chip has selected visual style but no role/selected state.
- `656`: clear tag filter action has no role/label.
- `778`: page row expands/collapses but has no role, label, or expanded state.
- `819`: inline tag action has no role/label.
- `848`: source-brief action needs role/label and busy/disabled state if running.
- `975`: delete page action has no role/label.

Some handoff buttons in this file already have `accessibilityRole="button"`; use those as the minimum baseline, not the ceiling.

### Research

`src/app/research.tsx`

- `139`: "All" framework filter chip has no role/selected state.
- `151`: framework chips have active visual state but no role/selected state.
- `206`: DOI/URL pressable opens an external link but has no role/label/hint.

### Interview / Trinity / Core Brain / Jarvis

- `src/app/interview.tsx:245`: life-period cards are buttons with no role/label.
- `src/app/trinity.tsx:203`: Link-wrapped capture action lacks explicit role/label.
- `src/app/core-brain.tsx:264`: evidence drawer button has role but no label; drawer evidence rows around `295` need row labels and modal semantics audit.
- `src/app/jarvis.tsx:288`: "Clear chat" text action lacks role/label. Intro modal actions and modal backdrop also need a pass; avoid making decorative backdrops noisy, but actionable controls need labels.

## Acceptance

Do this as a small, regression-safe UI cleanup pass:

1. Add `accessibilityRole` to every custom `Pressable` that behaves as a button, link, tab, row, chip, or menu item.
2. Add concise `accessibilityLabel` where visible text alone is insufficient, clipped, dynamic, or nested.
3. Add `accessibilityState` for selected, expanded, disabled, and busy states.
4. For link-like actions, use `accessibilityRole="link"` where supported or a button role plus label/hint that announces the destination.
5. For modal backdrops, keep them non-noisy unless they are intentionally dismiss controls; if dismissible, label them as "Close dialog".
6. Add a lightweight static test or helper checklist so future `Pressable` additions in high-density screens do not regress.

Suggested implementation order:

- First pass: `inbox`, `wiki`, `research`.
- Second pass: `jarvis`, `core-brain`, `records`, `interview`, `trinity`, `manual`.
- Then run `npm run verify`.

## Keep separate

Do not bundle this with the P1 privacy monotonicity fix unless the diff stays easy to review. The privacy issue remains the score blocker, but this interaction contract gate is a separate anti-slop cleanup class.

## Related open gates

Still open from previous Codex reports:

- P1 privacy opt-out monotonicity: `src/app/privacy.tsx:100`.
- P2 keyboard-safe shells for `account`, `audit`, `settings`.
- P2 stronger friction for broad partial deletes in `settings`.
- Runtime screenshot proof for all major screens and states.
