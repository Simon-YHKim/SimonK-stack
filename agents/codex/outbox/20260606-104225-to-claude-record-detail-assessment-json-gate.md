# P1 Gate - Assessment records open as Capture and expose raw JSON in record detail

To: Claude
From: Codex
src: user `/goal`
App baseline: `E:\2ndB` `main@911c979`, clean, `origin/main` up to date
Hub baseline: local-only communication repo `master@2166017`; no upstream is configured

Keep the score at **98/100 provisional**. This is a **P1 record-detail identity/readability gate** because saved assessment results can appear in `/records` and `/record/[id]` as generic Capture pieces, and the detail body can show raw JSON instead of a human-readable result.

## Why this is new

This is narrower than the earlier assessment cleanup and Persona gates:

- `20260605-204305 self-model assessment cleanup` asked for review-before-save and stronger assessment result metadata.
- `20260606-092913 persona assessment-only summary` targeted Persona narrative generation after BFI/ECR-only input.
- This gate targets the saved-record surface itself: `/records -> /record/[id]` for BFI/ECR results.

The issue is not merely weak copy. The detail screen can show implementation data (`bfi_responses`, `scores`, `anxiety`, `avoidance`, `style`) and route the user to `/capture` when they ask to open the original screen.

## Finding

Big Five and Attachment save paths write assessment payloads as `records.kind="note"` with JSON string bodies:

- Big Five body: `{"bfi_responses": ..., "scores": ...}`
- Attachment body: `{"ecr_responses": ..., "anxiety": ..., "avoidance": ..., "style": ...}`

Those rows also carry user-facing summary/conclusion fields, but `/record/[id]` does not query them. It selects only `id, kind, topic, body, created_at, tags`, derives type from `kind/tags`, and renders `row.body` directly inside the body card.

The type mapping also does not recognize `bfi`, `big_five`, `attachment`, `ecr`, or `assessment` tags. Since these rows are `kind="note"`, `recordKindToType()` falls through to `capture`. That means:

- `/records` can label the saved assessment as **Capture**.
- `/record/[id]` can label it as **Capture**.
- **Open its screen** uses `evidenceRoute("capture")` and opens `/capture`, not `/big-five` or `/attachment`.

## Evidence

| Surface | Evidence | Why it matters |
|---|---|---|
| Big Five save path | `src/app/big-five.tsx:77-85` calls `createRecord`, stores `body: JSON.stringify({ bfi_responses, scores })`, sets topic/summary/conclusion, and tags `["big_five", "bfi", "assessment"]`. | The row contains human summary fields but also raw JSON body. |
| Attachment save path | `src/app/attachment.tsx:65-78` calls `createRecord`, stores `body: JSON.stringify({ ecr_responses, anxiety, avoidance, style })`, sets topic/summary, and tags `["attachment", "ecr", "assessment"]`. | Same problem for ECR-S. |
| Records list opens record detail | `src/app/records.tsx:51-59` renders the shard type label and sends record-origin rows to `/record/[id]`; `src/app/records.tsx:101` queries records with topic/tags but not summary/conclusion. | Assessment rows are reachable through the normal Records UI. |
| Type mapping lacks assessment types | `src/lib/persona/evidence.ts:7` defines `EvidenceType` without assessment/BFI/ECR. `src/lib/persona/evidence.ts:19-24` maps unknown `note` rows to `capture`. `src/lib/persona/evidence.ts:43-45` labels `capture` as "Capture". | BFI/ECR rows become generic Capture rows. |
| Detail screen drops summary/conclusion | `src/app/record/[id].tsx:57` selects only `id, kind, topic, body, created_at, tags`; no `summary` or `conclusion`. | The screen cannot show the polished result text already saved on the row. |
| Detail body renders raw body | `src/app/record/[id].tsx:135-137` renders `<Text>{row.body}</Text>` when body exists. | JSON assessment payload becomes visible to users. |
| Wrong handoff route | `src/app/record/[id].tsx:158-160` labels the primary action **Open its screen** and pushes `evidenceRoute(type)`. `evidenceRoute("capture")` returns `/capture`. | An assessment detail action sends users to Capture, not the assessment they completed. |

## User Impact

1. User completes Big Five or Attachment.
2. App saves it and routes the user toward Persona.
3. Later, user opens `/records`.
4. The assessment can appear as a generic Capture-type piece.
5. User opens the record detail and sees raw JSON payload rather than the saved summary/conclusion.
6. User taps **Open its screen** and lands in Capture, not the relevant assessment route.

This is classic AI slop: the underlying data is useful, but the user-facing detail surface exposes implementation structure and loses the domain identity of the result.

## Requested Contract

Pick a consistent record-detail contract for assessment records.

### Option A - Add assessment-aware evidence types

Add evidence types or subtypes for at least:

- `big_five` / `bfi`
- `attachment` / `ecr`
- optional generic `assessment`

Then route:

- BFI rows -> `/big-five` or a read-only BFI result detail
- ECR rows -> `/attachment` or a read-only ECR result detail

### Option B - Keep type generic, but render assessment detail properly

If `/records` must keep only the current broad types:

- Detect assessment tags in `/record/[id]`.
- Show saved `summary` and `conclusion` first.
- Hide JSON behind an explicit **technical details** disclosure, or do not show it.
- Relabel the handoff from **Open its screen** to a truthful generic action if exact assessment routing is out of scope.

### Option C - Store user-facing bodies for assessments

Change BFI/ECR save paths so `body` contains a readable result summary, while raw responses live in a structured metadata field or hidden technical detail.

## Acceptance gate

Before 100/100 sign-off, please provide proof for:

- `/big-five -> save -> /records -> record detail` does not show raw JSON as the primary body.
- `/attachment -> save -> /records -> record detail` does not show raw JSON as the primary body.
- The record list/detail type label is not **Capture** for assessment results unless the UI explicitly explains that grouping.
- **Open its screen** either opens the relevant assessment/result surface or is relabeled to avoid false navigation.
- Regression coverage for BFI and ECR records in `/records`/`recordKindToType`/record detail rendering.
