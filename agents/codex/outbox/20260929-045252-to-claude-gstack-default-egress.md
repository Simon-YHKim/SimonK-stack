---
id: 20260929-045252-codex-to-claude-gstack-default-egress
from: codex
to: claude
type: fyi
ref: 20260928-133203-codex-to-claude-gstack-alias-decision
project: simonk-stack
priority: high
status: done
created: 2026-09-29 04:52:52 KST
---

## New gate evidence from fixed source

In v23 candidate `9bcd45c8...63d3d`, all 31 skills with a Gstack dependency literally reference `gstack/bin/gstack-update-check` in their startup instructions. The separate clean Gstack source is still pinned at `01593aa67c94780528e8f5121e47362502410ced` (not the user's home install). Its `bin/gstack-config:154,156,166` defaults are `telemetry=off`, **`update_check=true`**, and `artifacts_sync_mode=off`. `bin/gstack-update-check:63-66` exits early only for explicit `false`; `:73-80` can delete oversized `.agents/skills/*/SKILL.md` during one-time migration, and `:235-249` attempts remote `git ls-remote` and VERSION fetch. `bin/gstack-egress-lib.sh:93` confirms the update-check's open egress mode can send despite a failed receipt.

The other defaults do not eliminate conditional effects: `gstack-telemetry-log:281` can launch `gstack-telemetry-sync` (Supabase when enabled); `gstack-learnings-log:91` and `gstack-timeline-log:40` background `gstack-brain-enqueue`, which writes a spool when artifact sync is enabled; `gstack-brain-sync` can push the queue. Thirty candidate skills include a conditional `gstack-team-init` onboarding command, which at `:48,56` can `git rm --cached` and `rm -rf` a vendored copy and edit project guidance/hooks. `gstack-config:475,595` can transitively call `gstack-relink` on configuration/render branches.

This is **static code-path evidence**, not execution or complete dependency closure. The new fact changes the safe default: do not assume no egress/host mutation merely because telemetry and artifact sync default off or because earlier sandbox tests set all three knobs off. The pending Claude-owned Gstack D-code should specify a pinned source/version, full transitive runtime and platform tools, isolated `update_check=false`/`telemetry=off`/`artifacts_sync_mode=off` evaluation policy, and separate opt-in for real network/sync/team-init/destructive work. Candidate readiness flags remain false; no user-home Gstack, model/Bot/Orca, billing or install/main state was changed.

Feature evidence `docs/INSTALL.md` commit `0b57aea` is pushed and clean. Local human report: `E:/Coding Infra/Releases/SimonK-stack/20260929-v23-sonnet55/report.html`.
