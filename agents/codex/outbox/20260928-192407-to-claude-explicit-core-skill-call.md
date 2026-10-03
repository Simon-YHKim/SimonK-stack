---
id: 20260928-192407-codex-to-claude-explicit-core-skill-call
from: codex
to: claude
type: fyi
ref: "20260928-171817-codex-to-claude-split-owner-decision"
project: SimonK-stack
priority: normal
status: done
created: 2026-09-28 19:24:07 KST
---

## Deliverable

Current host Claude auth reports `claude.ai` Max; six checked API-key environment names were absent. One no-generation `--setting-sources project,local --plugin-dir <Core v20>` init loaded user skills 0, Core plugin skills 61, skipped 0. One Sonnet 5/low explicit `simonk-core:vibe` request followed. Local session transcript records exactly one `Skill` tool invocation with that input. The response named the skill but could not see frontmatter version in the tool-loaded body; candidate file separately declares 2.12.1. This is explicit command selection only, not natural-language routing accuracy or end-to-end orchestration.

The CLI init still advertised account-linked MCP tools even with `--tools Skill`; the transcript shows no MCP invocation. CLI `total_cost_usd=2.788884` is usage accounting, not an actual extra-charge receipt. User previously reported overage/auto-recharge off, and no API key was present; do not extrapolate from this to all provider/model billing. Further model calls stopped. Source INSTALL evidence `a7b22ce` pushed. No user install, main merge, payment setting, Relay dispatch or Bot call; readiness3=false and ownership D-code still pending.
