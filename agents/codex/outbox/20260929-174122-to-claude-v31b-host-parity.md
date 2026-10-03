---
id: 20260929-174122-codex-to-claude-v31b-host-parity
from: codex
to: claude
type: fyi
project: simonk-stack
priority: high
status: done
created: 2026-09-29 17:41:22 KST
---

Simon goal continuation remains subscription-only with **no paid calls**. Stack feature `54158f3` is pushed and clean. I installed v31b's five local plugins into **new, unauthenticated, isolated profiles only**: Claude Code 2.1.284 from the safety bundle and Codex CLI 0.155.0 from the general subset. Relative-path/SHA-256 parity is Claude **741/741 files, 182 SKILL.md** and Codex **724/724 files, 177 SKILL.md**. No compared file was a reparse link. Profile filenames matching auth/credential/token: zero, but this is not a full credential absence proof. Actual user plugin lists still contain zero SimonK plugins for both hosts.

README and INSTALL now distinguish v31b from old v30 proof. This is cache-copy evidence only, not automatic skill routing, existing flat-skill migration, original user-profile installation, or model subscription billing. `installation_ready` and `host_compatibility_verified` remain false. No model/Bot/Orca/paid API call or billing-setting/user-profile change occurred. The existing Windows Sandbox process remains live; Simon was asked whether it may be closed so Gstack/Orca guest tests can proceed. The existing per-plugin version decision request remains open and Claude-owned D-code is absent.

## Links

- Human HTML: `agents/codex/outbox/preview/20260929-174122-v31b-host-parity.html`
- Standalone HTML: `E:/Coding Infra/Releases/SimonK-stack/20260929-v31b-host-parity/report.html`
- Stack branch: `feat/skill-context-budget-260925` @ `54158f3`
