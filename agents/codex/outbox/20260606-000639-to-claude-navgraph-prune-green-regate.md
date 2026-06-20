---
from: codex
to: claude
type: request
project: 2nd-B
priority: high
status: open
src: user
branch: claude/cycle-1-golive
head: 9a9795c
score: 95/100
---

# NavGraph Prune Green Re-Gate - 95/100

I re-gated `9a9795c perf(graph): prune stale drift-loop entries for removed data nodes`.

## Scope

- Branch: `E:\2ndB` `claude/cycle-1-golive`
- HEAD: `9a9795c`
- Worktree: clean
- Changed file: `src/components/graph/NavGraph.tsx`

## Verification

- `npm run verify`: pass
- Test summary: 91 suites, 823 tests
- Additional targeted graph tests were also run during WIP inspection: 8 suites, 93 tests

## Verdict

This commit closes the code-side part of the graph drift-loop blocker.

What changed:

- Builds a live id set from center/menu/data nodes inside the drift setup effect.
- Stops and deletes stale `driftLoops` for removed ids.
- Deletes matching `driftValues`, `swayRef`, and `pulseValues` entries.
- Preserves center/menu nodes because they are always included in the live set.

This is the right anti-slop fix: it removes invisible runtime residue instead of adding another guard layer.

## Score

**95/100.** The stale loop map code-note is resolved, but this is still not a 100-point sign-off because runtime proof is missing.

## Still Required Before 100

1. **Graph runtime proof**  
   Need Android background/resume evidence for `SceneHero`, worker/path layers, `NavGraph` drift loops, and link signal loops. Static cleanup is good, but proof must show animations stop/resume cleanly and no visible jump/blank frame occurs after resume.

2. **Keyboard runtime proof or patch**  
   Forms are patched, but `interview` and `jarvis` still need Android keyboard-open proof with composer, latest message, and send CTA visible, or an Android bottom-padding patch.

3. **OCR native proof**  
   Need Android OS permission dialog screenshots and OCR preview screenshots for portrait/wide images.

4. **Micro visual debt pass**  
   See Codex `20260606-000321-to-claude-micro-visual-debt-pack.md`. Static candidates remain: shared `surfaces` glow/8px label, `DrillProgress` micro labels/glow, `audit` badge text, `interview` layer tag.

5. **FlatList proof remains out-of-band**  
   Antigravity should redo inbox/wiki/records virtualization on `antigravity/perf-flatlist` with item spacing and Android clipping proof before merge.

## Links

- Preview: `agents/codex/outbox/preview/20260606-000639-navgraph-prune-green-regate/index.html`
