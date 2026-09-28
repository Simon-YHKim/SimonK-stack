---
id: 20260929-000152-codex-to-all-pr54-instruction-unit
from: codex
to: all
type: fyi
ref: ""
project: SimonK-stack
priority: normal
status: done
created: 2026-09-29 00:01:52 KST
---

## Context
Simon requested all non-paid work to continue. This unit integrates the instruction-source half of PR #54 without touching user installs or main.

## Deliverable
- Feature branch `feat/skill-context-budget-260925` now contains pushed commit `002508e` (four files: one instruction source and three generated copies).
- `python -B instructions/split.py --verify` PASS: generated SHA mismatch 0, section composition OK, broken cross-refs remain baseline 3 with no increase. `git diff --check` PASS; branch clean.
- The next PR commit `709c1ed` remains unmerged. Read-only merge preflight found one CHANGELOG conflict; skills and template merge mechanically. Next bounded unit should preserve both CHANGELOG bullets, then validate skill/template behavior and rebuild candidate only after source is sound.
- No main merge, installation, external model/Bot/API call, billing-setting change, or extra paid usage.

## Links
- HTML: `agents/codex/outbox/preview/20260929-000152-pr54-instruction-unit.html`
- Source: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925` at `002508e`
