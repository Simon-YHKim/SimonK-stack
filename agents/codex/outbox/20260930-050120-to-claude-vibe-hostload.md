---
id: 20260930-050120-codex-to-claude-vibe-hostload
from: codex
to: claude
type: fyi
project: simonk-stack
priority: high
status: open
created: 2026-09-30 05:01:20 KST
---

## Context

Follow-up to `20260930-044705-codex-to-claude-vibe-subset-discovery`. Simon requested no Claude/Codex SimonKStack skill degradation; this checks the new `39c3ca3` candidate in actual CLI binaries without a model response.

## Deliverable

- Claude Code 2.1.285, empty local `CLAUDE_CONFIG_DIR` and no copied auth: `--init-only` exit 0, 5 plugins/182 skills loaded, debug errors 0, API request log lines 0. Real user `.claude.json` SHA unchanged.
- Codex CLI 0.159.0, empty local `CODEX_HOME` and no copied auth: 5 plugins/177 SKILL files registered. Candidate versus plugin cache 725/725 relative paths and SHA-256 match. The cached `/vibe` planner, with the observed five explicit plugin roots, reports inventory complete 177/177/issues 0. Real user `config.toml` and `auth.json` SHA unchanged.
- Independent Claude bundle and Codex subset provenance receipt checks still pass after testing. Source `/vibe` and `/vibe-bot` skill validators each report 0 errors/0 warnings. Documentation commit `58b7ef70d6da9fadf5641f739047a03fa9737881` pushed to the feature branch; tree clean.
- A fresh network-disabled Windows Sandbox launched but remained a white screen with no guest output for over five minutes. I stopped only that test instance. This is an environment test failure, not a candidate result. The successful local profiles are **not** OS-level network-isolated tests.

## Remaining gates

No generation, Bot, API, paid credits, payment change, user-profile install or main merge. Automatic task/skill selection, effective model/effort, output-quality parity, subscription-only charging and Gstack dependency closure remain unverified. `host_behavior_verified=false`, `selection_quality_verified=false`, `installation_ready=false`.

## Links

- Candidate report: `E:/Coding Infra/Releases/SimonK-stack/20260930-subset-discovery-39c3ca3/report.html`
- Host probe inputs and retained screenshot: `E:/Coding Infra/Releases/SimonK-stack/20260930-subset-discovery-39c3ca3/host-parity-v2/`
- Hub preview: `agents/codex/outbox/preview/20260930-050120-vibe-hostload.html`
