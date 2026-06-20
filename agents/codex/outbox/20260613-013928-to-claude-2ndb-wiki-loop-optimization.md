---
id: codex-20260613-013928-2ndb-wiki-loop-optimization
from: codex
to: claude
type: fyi
status: done
priority: high
project: 2ndb-wiki-hub
created: 2026-06-13 01:39:28 KST
---

# 2ndB latest + Wiki/Hub loop optimization

Simon asked Codex to work in parallel while Claude usage is unavailable:

1. Update local 2ndB to the latest GitHub state.
2. Apply two YouTube script insights to the system.

## 2ndB state

- Repo: `https://github.com/Simon-YHKim/2nd-B`
- Local path: `E:\2ndB`
- Current SHA: `f769d1d`
- `HEAD == origin/main`
- Worktree status: clean
- `npm run verify` passed:
  - 129 test suites passed
  - 1125 tests passed
  - lint: 0 errors, 4 existing unused eslint-disable warnings

## Script 1 applied: LLM Wiki intake + Vault policy

Applied to SimonKWiki:

- New protocol: `wiki/protocols/context-intake-and-loop-policy.md`
- New source summaries:
  - `wiki/sources/2026-06-13-youtube-llm-wiki-intake-vault.md`
  - `wiki/sources/2026-06-13-youtube-loop-engineering.md`
- Updated:
  - `wiki/CLAUDE.md`
  - `wiki/protocols/wiki-structure-policy.md`
  - `wiki/index.md`
  - `wiki/log.md`

Operational rules now encoded:

- Do not create material just to fill the wiki.
- Ingest when at least 2 of 3 are true: repeated use, decision impact, project/work connection.
- Prefer material that can be contextualized in 5 minutes.
- Default to one vault; use properties/tags/index notes for departments and domains.
- Split vaults only for security, different purpose, different workflow, or unresolved search pollution.

## Script 2 applied: Loop engineering

Applied to Communication hub:

- Updated `PROTOCOL.md` §12.1a with measurement-first loop rules.
- Updated `PROTOCOL.md` §18.0 with the Wiki intake gate.

Operational rules now encoded:

- No evolution without measurement.
- Baseline first.
- Change one meaningful thing per loop.
- Use a fixed golden set.
- Separate proposer and evaluator when possible.
- Merge only on measured gain or no regression.
- Keep a failure ledger.
- Run a subtractive cycle after repeated additive changes.
- Mark unrun E2E surfaces as proof gaps.

## Verification

- `npm run verify` in `E:\2ndB`: PASS.
- `wiki_lint.py`: Error=0, E1=0, E2=0, W2/W3/W4/FM=0.
- `raw_isolation.py`: isolated=0/26.
- Secret scan: no actual token/key found. Matches were only policy words like `credentials`.
- SimonKWiki pushed to GitHub at `origin/main@53043ed`.
- Communication hub has no remote, so the hub changes are local-only after commit.

## Claude restart notes

- Start from 2ndB `origin/main@f769d1d`.
- Use the latest SimonKWiki `origin/main@53043ed` for context.
- Keep hub `CONTROL.md` paused until Claude explicitly resumes orchestration.
- When restarting autonomous loops, treat §12.1a as the new loop discipline: baseline, one change, same test, measured merge, failure ledger.
