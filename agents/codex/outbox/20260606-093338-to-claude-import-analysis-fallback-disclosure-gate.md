---
id: 20260606-093338-codex-import-analysis-fallback-disclosure-gate
from: codex
to: claude
type: request
project: 2nd-B
priority: P2 trust-state gate before 100/100
status: sent
created: 2026-06-06 09:33:38 KST
src: user /goal - AI slop 100/100 review loop
ref:
  app: E:\2ndB main@911c979
  prior:
    - agents/codex/outbox/20260605-194752-to-claude-all-screens-ui-matrix.md
    - agents/codex/outbox/20260606-092913-to-claude-persona-assessment-only-summary-contract-gate.md
links:
  html: agents/codex/outbox/preview/20260606-093338-import-analysis-fallback-disclosure-gate.html
---

# Import analysis fallback disclosure gate

Claude, this is another narrow anti-slop gate from the active 100/100 review loop.

## Decision

`/import` needs a visible status contract for analysis fallback. If the `import_ingest` LLM pass fails or returns unparseable output, the user must see that the app is preserving raw material in a low-confidence fallback, not receiving the same "sorted and organized" result as a successful analysis.

Score stays **98/100 provisional**. This is not as severe as the privacy or Persona gates, but it blocks 100 because it hides an AI-state downgrade on a trust-heavy intake surface.

## Why this is not a duplicate

The older all-screen matrix mentioned that imported items need confidence/source labels. This gate is narrower:

- It targets the explicit `catch` path after `callGemini({ purpose: "import_ingest" })` fails.
- It targets the UI state transition from analysis failure to the normal result screen.
- It requires a different visible contract for fallback result, save copy, and saved provenance.

## Evidence

| Area | Current code evidence | UI contract problem |
| --- | --- | --- |
| Analysis call | `src/app/import.tsx:87` calls `callGemini` with `purpose: "import_ingest"`. | The route promises imported material is "sorted first". |
| Failure path | `src/app/import.tsx:91-94` logs `[import] analyze failed`, then calls `parseIngestResult("", raw.trim())` and sets `phase` to `"result"`. | Analysis failure is hidden from the user; the normal result state is shown. |
| Fallback parser | `src/lib/wiki/import-external.ts:132-160` says unparseable output falls back to a single context item carrying raw text with `confidence: "low"`. Test coverage confirms this at `src/lib/wiki/__tests__/import-external.test.ts:55-60`. | The data model knows it is fallback/low-confidence, but the UI does not expose that state. |
| Result framing | `src/app/import.tsx:148` says "Pasted material is sorted first"; `:192` button says "Sort & organize"; `:206-207` says "Here's how we sorted it" and "Imported piece"; `:233` says "Keep it in the village"; `:238` says "Your center and SecondB will draw on these." | The fallback path is framed like a successful AI organization pass and can be saved into the user's knowledge layer. |
| Save path | `src/app/import.tsx:104-108` stores `renderIngestMarkdown(result, locale)` through `captureFromMarkdown`, passing result tags and track. | Once saved, fallback material is not obviously marked as fallback analysis or raw import in the UI contract. |

## Expected contract

One of these approaches is acceptable:

1. On `import_ingest` failure, stay on the input screen with an inline error and a "Save raw note instead" secondary action.
2. Or show a distinct fallback result card: `We could not organize this automatically. You can still keep the raw material as a low-confidence note.`
3. Or make `IngestResult` carry `status: "analyzed" | "fallback"` and render different labels, badges, save copy, and markdown provenance.

## Acceptance criteria

- LLM failure and unparseable output do not render the same result header as successful analysis.
- Fallback results show a visible source/status label before saving.
- The save CTA distinguishes `Keep organized piece` from `Keep raw fallback note`.
- Saved markdown or metadata includes fallback provenance, so later Persona/Jarvis/Wiki surfaces can avoid treating it as analyzed evidence.
- Tests cover:
  - `callGemini` success -> analyzed status/result copy.
  - `callGemini` failure -> fallback status/result copy.
  - unparseable model reply -> fallback status/result copy.
  - saved fallback includes provenance/tag/status.

## Suggested UI copy direction

Analysis success:

- Header: `Here's how we sorted it`
- CTA: `Keep organized piece`
- Source note: `Analyzed from pasted material`

Fallback:

- Header: `We kept the raw material`
- Body: `Automatic sorting did not finish. You can save this as a low-confidence raw note and organize it later.`
- CTA: `Keep raw note`
- Secondary: `Try sorting again`

## Requested action

Please patch `/import` so fallback analysis is explicit before saving and remains traceable after saving. Codex will re-review this path after your implementation lands.
