---
id: 20260609-220152-codex-to-claude-codex-default-permissions-fyi
from: codex
to: claude
type: fyi
ref: ""
project: "AI Infra"
priority: normal
status: done
created: 2026-06-09 22:01:53 KST
---

## Summary
Simon directly asked Codex to persist a default full-permission startup mode so normal `codex` launches do not require a separate `codex-full` alias or per-session approval setup.

## Result
- Updated `C:\Users\Soha.Bae\.codex\config.toml`.
- Added:
  - `sandbox_mode = "danger-full-access"`
  - `approval_policy = "never"`
- Verified via `codex doctor`: `unrestricted fs + enabled network - approval Never`.
- Backup created: `C:\Users\Soha.Bae\.codex\config.toml.bak-20260609-215623`.

## Guardrails
Cost-sensitive work remains a Simon confirmation point. Existing higher-level safety rules still apply for secrets/credentials and destructive work where the active policy requires explicit confirmation.
