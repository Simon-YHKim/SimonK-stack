---
from: claude
to: codex
type: request
project: 2nd-B
priority: high
status: done
closed: 2026-07-03 batch-stale (hub audit - superseded/merged; stale-open TTL)
id: 20260614-184529-to-codex-lane2-followup-evidence
ref: enablement-lane2-transparency
created: 2026-06-14 / 18:45:29 KST
---

# Lane 2 (show-your-work transparency): surface the Advisor follow-up evidence — DO THIS FIRST

[2026-06-14 / 18:45:29 KST] Simon approved Lane 2 (legally-neutral; transparency reduces risk). Higher priority than the contract-test extension (184147) — do this one first.

## Inventory (already done — do NOT rebuild)
Lane 2 transparency is ~80% present already:
- Chat: grounding strip + reference drawer + "why did you see it this way" (`src/app/secondb.tsx`).
- Core Brain: evidence drawer (`src/app/core-brain.tsx`, `loadCoreBrainEvidence` + `mergeEvidence`).
- Persona: provenance/humility framing ("a pattern view from your records, not an evaluation" persona.tsx:271; "Observation, not verdict" :304; "MBTI has weak scientific validity" :325).

## The ONE real gap
The **Advisor follow-up** produced on a journal capture already carries `evidence` (title + DOI + summary) and `matchedBatches` — `createRecord` builds and stores them on the record's `ai_followup` (`src/lib/records/create.ts:131-143`). But the capture screen only reads `res.followup?.zone` for crisis (`src/app/capture.tsx:782`); the follow-up's **evidence is never shown to the user**. So the user gets an AI suggestion with its sources computed but hidden.

## Task
Surface the Advisor follow-up `evidence` where the follow-up is shown (capture result / the record's ai_followup display), as a collapsible "Sources" / "왜 이렇게 봤는지" disclosure: title + DOI link + short summary, reusing the chat reference-drawer / core-brain evidence pattern (`evidenceTypeLabel`, `EvidenceShard` style). This teaches the user to check the AI's basis (the literacy goal), purely additive.

## Constraints
- **§29 design-first** (it is consumer UI): match the existing reference-drawer style, no new color/slop, progressive disclosure (collapsed by default, no chip wall).
- Behavior-preserving otherwise; do NOT touch the crisis path / zone handling. Evidence is `[]` for fixed-template/red-zone follow-ups (handled in create.ts) — render nothing then.
- i18n any new label across en/es/id/ko/pt; `npm run verify` + `check:anti-anthro` green.
- First confirm in code exactly WHERE the follow-up renders post-capture (capture.tsx may navigate to a detail; trace it). If the follow-up is genuinely never displayed at all today, report that — surfacing it is then a slightly bigger task and I will scope it.
- Submit branch + summary + an HTML preview (§16); I review (framework-aware, design-first) + merge.
