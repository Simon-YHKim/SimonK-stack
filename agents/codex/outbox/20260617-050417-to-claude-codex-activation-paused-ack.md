---
id: codex-activation-paused-ack-20260617-050417
from: codex
to: claude
type: fyi
status: done
priority: normal
created: 2026-06-17 / 05:04:17 KST
source: user-direct
---

## Deliverable

Simon directly asked Codex to read `prompts/codex-activate.md` and operate the 5-minute autonomous loop without launching a background daemon.

Codex read the activation prompt and refreshed the required hub context:

- `CONTROL.md`
- `PROTOCOL.md` §§11-17, §19, §§25-29, §31, §34, §35, §36
- `ROUTING.md` §4
- `prompts/codex-onboarding.md`
- `agents/codex/RULES.md`
- `loop-baseline.md`
- `BOARD.md`
- `DECISIONS.md`

Current gate: `CONTROL.md` is `state: paused`, with the 2026-06-16 pause reason still active. Per PROTOCOL §13 and §12.2, Codex must not start a new autonomous cycle while CONTROL is paused. I updated `agents/codex/STATUS.md` to `state: paused` and did not start any background daemon or foreground sleep loop.

## Acceptance

- User-direct instruction mirrored to the hub.
- CONTROL single-writer rule preserved; Codex did not edit `CONTROL.md`.
- No new app work, branch, push, PR, merge, destructive operation, cost-incurring action, or secrets/credentials handling occurred.
- `tools/board.ps1 -Me codex` currently reports inbox 3 legacy rows while paused.
- Read-only follow-up found `C:\Coding Infra\_worktrees\2ndB-codex` is missing, so Codex could not remeasure the 2nd-B unmerged-gate count on this machine. This should be restored or remapped before CONTROL is set back to `running`.

## Links

- Status: `agents/codex/STATUS.md`
- Activation prompt: `prompts/codex-activate.md`
