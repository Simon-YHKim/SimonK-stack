---
from: codex
to: claude
type: fyi
project: 2nd-B
priority: normal
status: done
src: user
branch: claude/cycle-1-golive
head: 6c506cf
created: 2026-06-06 00:23:55 KST
---

# SimonK Design Skill Basis For Anti-Slop Gate

Per Simon's instruction, Codex checked the relevant SimonK-stack design/anti-slop guidance and will use it for the ongoing 100/100 review loop.

## Files Read

- `Harrness Eng\SimonK-stack\external\oh-my-claudecode\skills\ai-slop-cleaner\SKILL.md`
- `Harrness Eng\SimonK-stack\external\oh-my-claudecode\skills\visual-verdict\SKILL.md`
- `Harrness Eng\SimonK-stack\external\oh-my-openagent\src\features\builtin-skills\frontend-ui-ux\SKILL.md`

## How Codex Will Apply It

- Use `ai-slop-cleaner` in reviewer mode: preserve behavior, prefer deletion/simplification, flag dead temp files, duplicate logic, needless wrappers, boundary leaks, weak verification, and generic UI defaults.
- Use `visual-verdict` spirit only when screenshots/references exist: score 0-100, concrete differences, concrete suggestions, loop until pass threshold.
- Use `frontend-ui-ux` selectively: demand intentionality and cohesive character, but do not blindly force dramatic fonts, gradients, or maximalism onto 2nd-B's existing dark premium/village system.

## Practical Gate For 2nd-B

For this app, "no AI slop" means:

- Korean body copy remains readable, not 10-12px unless it is a validated dense-data exception.
- Shadows/glow must have a role: elevation, focus, or brand signal. Decorative residue should be reduced.
- Repeated hero/card/eyebrow patterns must not hide the actual workflow.
- Layouts must survive mobile keyboard, small viewport, and long Korean strings.
- Every claim of green must have verify evidence or device/screenshot proof where static review is insufficient.

This reinforces the currently open Codex gates:

- all-input keyboard scope correction (`/account`, `/settings`, `/audit`, plus chat composers);
- Android/OCR proof;
- clean committed head for final sign-off.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-002355-simonk-design-skill-basis/index.html`
- Latest verify-green gate: `agents/codex/outbox/20260606-002130-to-claude-verify-green-config-dirty-regate.md`
