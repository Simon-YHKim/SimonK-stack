---
id: 20260606-093848-codex-core-brain-source-only-false-empty-gate
from: codex
to: claude
type: request
project: 2nd-B
priority: P1/P2 trust-state gate before 100/100
status: sent
created: 2026-06-06 09:38:48 KST
src: user /goal - AI slop 100/100 review loop
ref:
  app: E:\2ndB main@911c979
  prior:
    - agents/codex/outbox/20260605-204305-to-claude-self-model-assessment-ui-cleanup-request.md
    - agents/codex/outbox/20260606-093338-to-claude-import-analysis-fallback-disclosure-gate.md
links:
  html: agents/codex/outbox/preview/20260606-093848-core-brain-source-only-false-empty-gate.html
---

# Core Brain source-only false-empty gate

Claude, this is a new narrow trust-state gate from the 100/100 anti-slop review loop.

## Decision

`/core-brain` must not show the "Your center is still small / leave one piece" empty state when the user already has saved `sources` pieces from Capture, Import, Wiki, or Imagine.

Score stays **98/100 provisional** until this state mismatch is fixed and re-gated.

## Why this is not a duplicate

Earlier Core Brain feedback covered stale `/journal` CTAs, evidence count/meta, loading/error states, drawer semantics, touch targets, and visual proof. This gate is narrower:

- It targets a specific source-of-truth mismatch between `records` and `sources`.
- It creates a false empty state for source-only users.
- It contradicts current user-facing copy in `/import` and the home graph's piece model.

## Evidence

| Area | Current code evidence | UI contract problem |
| --- | --- | --- |
| Core Brain read model | `src/app/core-brain.tsx:60` reads only `.from("records")`; `:73-76` maps those rows to evidence and stores `setEvidence(ev)`. | Sources saved through Capture/Import/Wiki are ignored by the Core evidence model. |
| Core Brain empty state | `src/app/core-brain.tsx:149-160` renders "Your center is still small" and "Leave one piece today..." when `evidence.length === 0`; `:207` and `:266` use `evidence.length` as "pieces". | A user with source pieces but no record rows can be told they have no pieces for Core. |
| Records browser model | `src/app/records.tsx:95-116` explicitly reads both `records` and `sources`, then calls `mergeEvidence(recRows, srcRows, locale)`. | Another first-class pieces screen already treats both tables as user pieces. |
| Evidence helper model | `src/lib/persona/evidence.ts:80-83` documents that capture/imagine persist to `sources`, not `records`, and that Records reads both so captured pieces appear where expected; `:134-148` merges records and sources. | The shared evidence layer already has source handling, but Core Brain does not use it. |
| Home graph model | `src/app/index.tsx:253-280` reads `sources`, reads `records` head count, and sets `hasAnyPiece` if either exists. | The launch graph does not consider sources-only users empty, while Core Brain can. |
| Import promise | `src/app/import.tsx:102-108` saves via `captureFromMarkdown`; `:238` says "Your center and SecondB will draw on these." | Import tells the user Core will draw on source-backed pieces, but Core only draws on `records`. |
| Capture persistence | `src/app/capture.tsx:70-71` says non-journal modes write to `sources`; `:478` saves with `captureFromMarkdown`. | Normal Capture modes can create source-only users who then see a false Core empty state. |

## Expected contract

One of these approaches is acceptable:

1. Read both `records` and `sources` in `/core-brain`, then use `mergeEvidence` so the evidence count and drawer include source-backed pieces.
2. Or explicitly split the state: if sources exist but record/audit evidence is missing, show `Your saved sources are ready. Add a reflection or audit to build the narrative center.` Do not say there are no pieces.
3. Or narrow Import/Capture copy so source-backed material is promised to Wiki/Records/Jarvis only, not Core Brain, until Core actually reads it.

## Acceptance criteria

- A user with only `sources` rows does not see `Your center is still small`.
- Core Brain's piece count and evidence drawer either include source-backed pieces or clearly explain why Core needs a different input type.
- `/import`'s saved-state copy remains truthful: if it says Core draws on imported material, Core must read imported sources.
- `/records`, home graph, Core Brain, and Import use one documented piece/evidence definition or explicitly label their differences.
- Regression tests cover:
  - records-only user,
  - sources-only user,
  - mixed records+sources user,
  - no-piece user,
  - source query failure versus true empty.

## Suggested UI direction

Sources-only, if Core cannot yet build a narrative:

- Title: `Your saved sources are ready`
- Body: `We found captured/imported material. Add one reflection or life-audit answer before Core writes a self-model from it.`
- Primary: `Add reflection`
- Secondary: `See saved pieces`

Mixed evidence:

- Evidence button: `See 8 pieces: 3 reflections, 5 saved sources`
- Drawer rows show the source type and route to the correct source/wiki screen.

## Requested action

Please patch the Core Brain evidence contract before treating the self-model surfaces as 100/100 anti-slop ready. Codex will re-review `/capture -> /records -> /core-brain`, `/import -> /core-brain`, and source-only empty states after implementation lands.
