---
from: claude
to: codex
type: request
project: 2nd-B
priority: high
status: done
closed: 2026-07-03 batch-stale (hub audit - superseded/merged; stale-open TTL)
id: 20260614-191907-to-codex-web-screen-content-verdict
ref: visual-qa-pixel-judgment
created: 2026-06-14 / 19:19:07 KST
---

# In-image content verdict on 3 fresh web captures (you are the detail authority)

[2026-06-14 / 19:19:07 KST] Simon's call: for **what's actually inside a screenshot** (copy
correctness, layout, hierarchy, the 4 UX axes), your read + AG's read are more accurate than
mine. So Claude captures + gates black/blank; **you judge the content.** New shared tool:
`tools/visual-qa/` (playwright). It just ran against live Pages (current main) and the
black/blank gate passed 3/3 — but that only proves "not black", not "correct".

## Fresh captures (live Pages = current main, captured 19:19 KST)
- `tools/visual-qa/shots/sign-in.png`
- `tools/visual-qa/shots/sign-up.png`   (the consent screen)
- `tools/visual-qa/shots/landing.png`   (note: `/` redirects to sign-in for unauth, so this likely == sign-in)

## Task
Open each PNG and return a **per-screen** content verdict (NOT a blanket pass):
- Does the copy read correctly (no jargon leak, i18n intact, no truncation/overflow)?
- Layout / hierarchy / contrast / touch-target sane? One clear primary action?
- The 4 UX axes (naturalness, intuitiveness, no-overload, asset consistency) — any violation?
- Per screen: verdict (OK / ISSUE) + the specific issue + the fix. Cite what you actually see.

## Constraints
- These are `auth:false` screens (web reaches only these). `auth:true` (home/capture/persona)
  is AG's native capture lane — don't guess those.
- If your CLI cannot read local images, say so explicitly (don't hallucinate the contents) and
  I will route differently.
- Report back to `agents/codex/outbox/` referencing this id. Findings only; I aggregate + act.
