---
id: 20260814-124625-codex-re-digest-action-a11y
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-08-14 12:46:25 KST
---

# Digest action accessibility state

Codex autonomous poll cycle completed one new lane task. No actionable current open order was found for codex, so I fixed one 2nd-B UI accessibility gap on a fresh worktree from `origin/main`.

- Worktree: `C:\2ndB\.worktrees\codex-qa-20260814-124243`
- Branch: `codex/qa-cycle-20260814-124243`
- Local commit: `c2ffdef2d6d1138060c947f2477c875fd1930ce5`
- Push: not performed

Changed:

- `src/app/digest.tsx`: digest proposal dismiss and confirm buttons now expose `accessibilityState={{ disabled: busy, busy }}` while a decision is in flight.
- `src/lib/__tests__/deep-space-controls-a11y.test.ts`: added a static regression guard that expects both digest action buttons to expose that state.

Verified:

- `jest src/lib/__tests__/deep-space-controls-a11y.test.ts --runInBand`
- `prettier --check src/app/digest.tsx src/lib/__tests__/deep-space-controls-a11y.test.ts`
- `eslint src/app/digest.tsx src/lib/__tests__/deep-space-controls-a11y.test.ts`
- `npm run type-check`
- `npm run check:i18n`
- `npm run check:i18n-untranslated`
- `npm run check:lexicon`
- `npm run check:constraints`
- `npm run check:emdash`
- `npm run check:anti-anthro`
- `npm run check:mascot-voice`
- `npm run check:cycles`
- `git diff --check`
- changed diff sensitive-pattern scan

## Links

- HTML report: `agents/codex/outbox/preview/20260814-124625-digest-action-a11y.html`
