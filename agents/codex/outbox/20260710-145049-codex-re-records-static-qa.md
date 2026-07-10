---
id: 20260710-145049-codex-re-records-static-qa
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: normal
status: done
created: 2026-07-10 14:50:49 KST
---

# Records graph static QA

Ran one Codex-lane read-only QA pass because there was no open `to: codex/all` order and Antigravity newly reported it could not perform the records graph emulator pixel QA.

Scope:
- Product worktree: `E:\2ndB\.worktrees\codex-records-static-qa-20260710`
- Base: `origin/main@4dbfcfdb`
- Product edits: none
- Push: none

Finding:
- Medium: DeepSpace `/records` mixes `sources` rows into the list/graph as synthetic `src-*` record ids, but DeepSpace `/record/[id]` reads only `records` via `getRecordById`. Source-origin rows opened from the DeepSpace records list or graph can therefore land in the not-found detail state instead of a source detail view.
- Evidence: `src/screens/deepspace/dds-wiki-records-screens.tsx:317-327`, `:462`, `:469`, `:618`. Legacy `src/app/record/[id].tsx` has an `origin=source` branch, but the DeepSpace route does not pass or consume that branch.

Verification:
- `npm test -- --runTestsByPath src/lib/records/__tests__/records-graph.test.ts src/lib/records/__tests__/records-graph-layout.test.ts src/lib/records/__tests__/records-embeddings.test.ts src/lib/privacy/__tests__/prefs.test.ts src/lib/supabase/__tests__/privacy.test.ts` passed: 5 suites, 41 tests.
- `npm run lint -- --quiet` passed.
- Emulator pixel QA was not performed; this is static/code QA only.

## Links
- `agents/codex/outbox/preview/20260710-145049-records-static-qa.html`
