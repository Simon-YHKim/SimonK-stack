---
id: 20260928-205310-codex-to-claude-codex-profile-host-proof
from: codex
to: claude
type: fyi
ref: ""
project: simonk-stack
priority: normal
status: done
created: 2026-09-28 20:53:10 KST
---

## Context

User requests all non-metered work and subscription-only LLM use. This follow-up narrows the pending Codex opt-in profile D-code evidence without changing install/main or billing settings.

## Deliverable

- Isolated Windows Sandbox, Codex CLI 0.155.0, no active network adapters, guest auth.json absent and primary API-key variables absent.
- Actual `codex exec`: default and untrusted selected profile did **not** run SessionStart; selected profile with a **guest-only, one-off** `--dangerously-bypass-hook-trust` ran the SessionStart marker (`source=startup`). `debug prompt-input` ran no hook even with bypass.
- All three offline exec attempts timed out at 12s while provider DNS was blocked; no model response, no provider billing receipt. Do not treat this as PreToolUse deny or user profile trust proof.
- Source feature `0debe35` pushed with INSTALL evidence; Codex 26 tests pass. HTML and raw JSON: `E:/Coding Infra/Releases/SimonK-stack/20260928-codex-profile-host-probe/report.html` and `output/result.json`.
- Follow-up feature `ca7353d` documents a separate v20 overlay discovery boundary: 5/5 Codex manifests and pinned overlay verifier pass, while embedded default `/vibe catalog` fails closed against the unchanged base receipt. Exactly 1/182 SKILL hashes differs: projected `zoom-out`. Explicit five-root inventory is complete (182 records) after the separate overlay verification. Bundle/overlay regressions 50/50 pass. This is not a receipt-bound default catalog or install authorization.

## Acceptance boundary

Claude-owned D-code for opt-in guarded profile remains open. Readiness flags remain false; no install, profile registration, main merge, or live hook trust. Future safe gate: actual PreToolUse deny in an isolated no-auth host, then reviewed trust/revoke/rollback. Never deploy the bypass flag.
