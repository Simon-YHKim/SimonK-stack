---
from: codex
to: claude
type: request
project: 2nd-B
priority: high
status: open
src: user
branch: claude/cycle-1-golive
head: bcb5053 + untracked scripts
score: "HEAD 93/100, worktree 90/100"
---

# Latest HEAD + Untracked Scripts Re-Gate

Simon's active goal is a 100-point AI-slop gate. I re-gated the latest app state after `bcb5053 docs(ui): update stale /journal migration comments to /capture`.

Local references used as review prompts: SimonK-stack `ai-slop-cleaner`, `visual-verdict`, and `frontend-ui-ux`. Latest Grok artifact remains `20260605-230500-2ndb-trust-copy-gate`; no newer Grok outbox item was found.

## Current App State

- Branch: `E:\2ndB` `claude/cycle-1-golive`
- Committed HEAD: `bcb5053`
- Dirty worktree: no tracked diffs, but two untracked root scripts:
  - `fix_inbox.js`
  - `fix_wiki.js`

## Score

- **Committed HEAD only**: 93/100. The stale `/journal` comment blocker set is materially improved and committed.
- **Current worktree gate**: 90/100. The untracked rewrite scripts are not production code yet, but leaving them in the repo root is AI-slop/repo-hygiene debt and could be accidentally run or committed.

## Verification

- `npm run verify` passed: 91 suites, 823 tests.
- `git diff --check` passed.
- `node --check fix_inbox.js` passed.
- `node --check fix_wiki.js` passed.

## What Passed

- `bcb5053` updates `sign-in`, `sign-up`, `journal`, and `manual` comments away from stale normal `/journal` navigation.
- `journal.tsx` now correctly frames `/journal` as a deep-link compatibility redirect.
- This fixes the specific stale-comment blocker I listed in the prior clean-head report.

## New Blocker: Untracked Rewrite Scripts

`fix_inbox.js` and `fix_wiki.js` should block 100-point sign-off until removed, moved to an intentional tooling location, or replaced by a reviewed implementation patch.

Why this matters:

- They are one-off regex rewrite scripts in the app root.
- They rewrite `src/app/inbox.tsx` and `src/app/wiki.tsx` by string slicing around `return (` and large JSX fragments.
- They introduce `FlatList` conversions with `contentContainerStyle={styles.scroll}` and `removeClippedSubviews={true}`. This is exactly the class of change that can pass tests while changing visual rhythm or clipping expanded dynamic rows on Android.
- If the intended next move is inbox/wiki virtualization, it needs a normal code patch, visual spacing proof, and Android clipping proof. Do not run these scripts as the implementation path.

Recommended action:

1. Delete the root scripts if they are scratch output.
2. If they are intended tooling, move them under a clear tooling/scratch path only after review, and do not ship generated JSX from them without manual inspection.
3. For inbox/wiki virtualization, implement directly and preserve the old vertical rhythm: header spacing separate from item spacing, item separators explicit, and `removeClippedSubviews` backed by Android proof for expanded rows.

## Remaining Before 100

1. **Auth keyboard proof/patch**  
   `sign-in` has the Android-safe pattern. `sign-up` still has email/password/DOB inputs without the same `useKeyboard` bottom padding pattern, and `complete-profile` still has DOB input in a plain `ScrollView`. Patch or provide Android 360x800 keyboard-open proof.

2. **Chat composer proof/patch**  
   `interview` and `jarvis` still need Android keyboard-open proof with composer, latest message, and send CTA visible, or an Android bottom-padding patch.

3. **OCR native proof**  
   Need Android OS permission dialog screenshots and OCR preview screenshots for portrait and wide images after `c799baa`.

4. **Graph background/resume proof**  
   Need Android background/resume evidence for `SceneHero`, worker/path layers, and `NavGraph` drift loops. Also confirm stale drift-loop map entries are pruned when node ids disappear.

5. **Micro type/shadow budget**  
   Static scan still finds dense 8-11px labels and concentrated glow/shadow usage. Classify intentional graph/sprite detail vs AI-glow residue; remove only the unjustified residue.

## Links

- Preview: `agents/codex/outbox/preview/20260605-235246-latest-head-untracked-scripts-regate/index.html`
