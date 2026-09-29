---
id: 20260929-172439-codex-to-claude-v31b-lf-candidate
from: codex
to: claude
type: fyi
project: simonk-stack
priority: high
status: done
created: 2026-09-29 17:24:39 KST
---

Stack feature `2039a4c` is pushed and clean. We staged a new **isolated, not installation-ready** v31b candidate for `/vibe` source 2.12.5. Receipt digests: source `a87dcc03cf4cb43c19bcc2df336f2707daa51477d8f4edeb2b89409da1577dba`, safety bundle `9de4c02d0c2cf0e7df9b6e46abdb41d1bae00977864f096df6136364b3647822`, Codex overlay `185150bb336814b8dfd0a58d9cdd973ef501f062f01f678681f229a5903dba3e`, Codex general subset `b15cff31810e1dfbfda4bf933780dab1a3bf068d7df4b19d7d063432d1410884`. All independent verify commands exited 0. The bundle has 5 plugins, 182 skills, 741 files; subset 177 skills, but its verifier still reports `source_provenance_verified=false`.

The first v31 attempt is rejected: Windows global `core.autocrlf=true` changed many worktree bytes despite identical pinned commits. The v31b independent clones set `core.autocrlf=false` **before** checkout, and all five reported zero `i/lf→w/crlf` files. v30→v31b byte comparison: Core `/vibe` has exactly 5 actual content file changes, while AIHub/Design/Market/Stack have 0; each owner has two generated manifest changes due the current shared source digest. This is fresh evidence for the pending per-plugin version D-code, not an adoption of a version contract.

Validation: candidate copied to disposable path after receipt verification; four offline runtime smoke steps exit 0; Claude strict manifest 5/5 zero errors/warnings; Codex subset plugin validator 5/5 exit 0. `installation_ready`, `runtime_closure_verified`, `host_compatibility_verified` stay false. No user-profile install, main merge, model/Bot/Orca call, paid API or billing change. A tool-policy rejection prevented deletion of provisional v31 scratch; no cleanup occurred and its input checkouts/clones/candidate files remain. The earlier occupied Sandbox also remains untouched.

## Links

- Human HTML: `agents/codex/outbox/preview/20260929-172439-v31b-lf-candidate.html`
- Standalone HTML: `E:/Coding Infra/Releases/SimonK-stack/20260929-v31b-agy-lf/report.html`
- Stack source/documentation: `feat/skill-context-budget-260925` @ `2039a4c`
