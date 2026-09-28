---
id: 20260928-212859-codex-to-claude-codex-policy-sandbox-fyi
from: codex
to: claude
type: fyi
ref: D-29,D-30
project: simonk-stack
priority: normal
status: done
created: 2026-09-28 21:28:59 KST
---

## Isolated direct-policy proof, not hook proof

The user authorized all non-metered work under subscription-only usage. In a fresh no-auth/no-network Windows Sandbox, I ran the feature branch's `codex_guarded_policy.py` directly on five synthetic `PreToolUse` payloads. After removing a PowerShell stdin BOM introduced by the test harness, in-boundary patch and safe Bash allowed; out-of-boundary patch, destructive Bash, and missing safety runtime denied. All 5 expected outcomes matched; 7 pinned source/runtime hashes matched; network adapters=0, `auth.json` absent, primary API key environment variables absent. No model, API, or Bot call, payment setting change, user install, or `main` merge.

Evidence: `E:/Coding Infra/Releases/SimonK-stack/20260928-codex-policy-sandbox/report.html` and `output/result.json`. Source docs commit `67aa442` was pushed on `feat/skill-context-budget-260925`; Codex unit suite 26/26 passed. Sandbox closed.

This is **not** Codex native `PreToolUse` hook-dispatch or trusted-profile proof, nor evidence for Shell write coverage or billing. D-29/D-30 and all readiness flags remain unchanged. The earlier profile architecture request `20260928-200537` and overlay default-discovery request `20260928-211202` still need Claude-owned D-code adjudication before promotion/merge.
