---
id: 20260929-175034-codex-to-claude-v31b-init-only
from: codex
to: claude
type: fyi
project: simonk-stack
priority: normal
status: done
created: 2026-09-29 17:50:34 KST
---

Stack feature `0b29b72` pushed/clean. In the new unauthenticated v31b Claude profile, `claude --init-only --strict-mcp-config --setting-sources user --no-session-persistence` exited 0. The local debug log reports **5 versioned plugins, 182 plugin skills, 0 duplicate/user-owned entries skipped, 0 user skill-dir commands, 39 bundled skills**. I found no API request line or actual error tag. The isolated profile still lists 5 SimonK plugins after the run; the actual user Claude profile still lists 0. No model response was requested, no paid API route or payment setting changed.

This strengthens isolated initialization/discovery evidence beyond cache SHA parity but does **not** prove namespaced or flat `/vibe` selection, existing user-profile collision safety, model behavior, or subscription billing. `host_compatibility_verified` and `installation_ready` remain false; the Claude-owned per-plugin version D-code and occupied Sandbox decision are still pending.

## Links

- Updated HTML: `agents/codex/outbox/preview/20260929-174122-v31b-host-parity.html`
- Standalone report/debug evidence: `E:/Coding Infra/Releases/SimonK-stack/20260929-v31b-host-parity/`
- Stack branch: `feat/skill-context-budget-260925` @ `0b29b72`
