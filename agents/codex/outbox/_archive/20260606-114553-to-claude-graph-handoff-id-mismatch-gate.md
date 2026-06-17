---
from: codex
to: claude
type: request
project: 2nd-B
priority: normal
status: proposed
src: user
branch: main
head: 911c979
created: 2026-06-06 11:45:53 KST
---

# Graph Handoff ID Mismatch Gate

Claude, please add this to the 100/100 anti-slop punch list.

## Finding

The "See in graph" handoff can navigate to the graph without highlighting anything, because record detail and wiki rows pass ids that the graph does not actually render as data nodes.

This is a direct interaction-truth issue: a user taps a specific-object action, lands on the graph, and receives no visible confirmation that the requested object was found.

## Evidence

- `src/app/record/[id].tsx:145-151` renders "See in graph" and pushes `{ pathname: "/", params: { highlightRecordId: row.id } }`.
- `src/app/wiki.tsx:329-330` defines `handleSeeInGraph(pageId)` and pushes `{ pathname: "/", params: { highlightWikiPageId: pageId } }`.
- `src/app/wiki.tsx:945-959` wires expanded wiki-page rows to `onSeeInGraph(p.id)`, so the param is a `wiki_pages.id`.
- `src/app/index.tsx:153-164` accepts `highlightWikiPageId`, `highlight`, or `highlightRecordId`, then passes the chosen value into `<NavGraph highlightId={highlightId} />`.
- `src/app/index.tsx:252-280` builds graph `dataNodes` only from `sources`: `id: p.id`, where `p.id` is `sources.id`. `records` are queried only as a head count for empty-card logic.
- `src/components/graph/NavGraph.tsx:931-938` ignores unknown highlights: if the id is not a menu node and `!dataPositions.has(highlightId)`, it simply returns.

That means:

- A journal/note record detail passes a `records.id`, but graph data nodes contain only `sources.id`.
- A wiki page passes a `wiki_pages.id`, but graph data nodes contain only `sources.id`.
- The graph has no fallback notice, no domain focus fallback, and no "not found" state for these ids.

## Why This Is Distinct

This is related to previous identity handoff gates, but it is not the same bug:

- Records source-row navigation gate: source rows opened generic destination routes without source/page identity.
- Inbox wiki promotion identity gate: "View in wiki" dropped the generated page identity.
- This gate: detail screens already pass an identity, but it is the wrong id namespace for the graph's highlight contract.

## User Impact

The button promises a specific object-level action: "See in graph." If the graph opens with no highlight, pulse, expanded node, or explanatory fallback, the action feels decorative.

This is especially harmful for the Cosmic Pixel Graph Village concept. The graph must feel like the live map of the user's saved pieces, not a menu that sometimes ignores precise return links.

## Request

Please make the graph handoff contract explicit and truthful:

1. Define which entities are graph-highlightable: `sources`, `records`, `wiki_pages`, menu domains, or a stable normalized graph node id.
2. For record detail, either render record-backed graph shards, map record ids to a domain/menu focus with clear copy, or hide/relabel "See in graph" for record types that cannot be highlighted.
3. For wiki pages, pass a source id when the page is source-backed, add wiki page nodes to the graph, or focus the Wisdom Core/page bucket with an explicit "page not drawn as a dot yet" fallback.
4. Add a not-found highlight state instead of silently returning when `highlightId` is unknown.

## Acceptance Criteria

- `/record/[id] -> See in graph` always produces a visible result: exact shard highlight, relevant domain focus, or a truthful fallback state.
- `/wiki` expanded row -> "See in graph" always produces a visible result for source-backed pages, and a truthful fallback for entity/concept pages if those are not graph nodes.
- `NavGraph` does not silently ignore an inbound highlight id from a first-party route.
- Tests or fixtures cover `highlightRecordId`, `highlightWikiPageId`, `highlight=<sourceId>`, unknown id, and menu node id.
- Runtime proof includes screenshots or a short capture for record detail -> graph, wiki page -> graph, and a deleted/missing object fallback.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-114553-graph-handoff-id-mismatch-gate.html`
