---
agent: antigravity
owner: antigravity
updated: 2026-06-13 KST
source: claude (PROTOCOL §34.7 — AG self-sufficiency parity)
status: active
sync: "Source of truth = PROTOCOL.md. On conflict, PROTOCOL wins. last-sync: 2026-06-13"
---

# Antigravity (Gemini) Operating Rules

Antigravity-owned rule mirror inside the 4-AI hub (parity with codex/RULES.md and grok/autonomous-loop-rules.md). Global protocol stays Claude-owned; this file restates AG-specific rules and must be re-synced when PROTOCOL changes (PROTOCOL §34.5).

## Lane (ROUTING / PROTOCOL §0)
Android / Google native development + device QA. Native fixes (keyboard, edge-to-edge, intent filters, AppState, elevation, perf/crash) — **directly coded and locally committed** to own branch/worktree, then submitted to Claude review-gate (§10.5). Multimodal rendering/perf pair with Codex (§19). **iOS is impossible on this Windows machine (§27.7) — never report iOS as run-verified.**

## Highest model / effort / permission (PROTOCOL §10.1, 2026-06-13)
- **Model**: the id PINNED in `tools/models.json` — `gemini-3.1-pro-preview` (agy picker label `Gemini 3.1 Pro (High)`). Do NOT "pick the latest" yourself; only re-pin after a CLI probe confirms a new id is callable — a hallucinated id silently kills the daemon (grok-4.3 incident). `gemini` CLI is sunset 2026-06-18 → use `agy`.
- **Effort**: maximum thinking — `Gemini 3.1 Pro (High)` (the `(High)` label = max thinking; agy default is `3.5 Flash (High)` so override).
- **Permission**: `agy --dangerously-skip-permissions` (after OAuth). Daemon/headless path = `node tools/agy-pty/agy-headless.js` (ConPTY wrapper — `agy -p` under redirected stdout emits ~0 bytes). Max autonomy for dev work.
- **Safety rails unchanged (§11-5)**: destructive ops, real cost, secrets/credentials always go to Simon regardless of permission level.

## Autonomous loop (PROTOCOL §12 / §34)
1. Cycle 0: read `CONTROL.md` state (paused/draining -> finish current cycle then stop). Re-ground on PROTOCOL §12.1a, §34, this file (§31.1). Read relevant **SimonKWiki** native-lesson pages (§34.1, read-only).
2. Sync: BOARD.md + AG inbox (`agents/*/outbox` to:antigravity) + DECISIONS.md.
3. Pick highest-value native/perf item in lane (priority §11-6).
4. **Measured loop (§12.1a / §34.2)** — golden set first, one change, re-measure, merge only on measured gain, log failures to `loop-baseline.md`.
   - **AG golden set**: `npx expo run:android` build green + emulator (`Pixel_9_Pro_XL`) smoke (boots + core screens) + perf numbers (frame time / memory). adb reverse 8081, USE_VERTEX=false.
5. Output: outbox md (machine) + HTML preview (§16) + evidence (screenshot/logcat). Commit with own identity (`tools/commit.ps1 -As antigravity`, own files only, `git add -A` forbidden §10.5).
6. Real timestamp `[YYYY-MM-DD / HH:MM:SS] KST` (§27.2, Get-Date — no guessing).

## Hard constraints
- Work only in own worktree (`E:\Coding Infra\_worktrees\2ndB-antigravity`) for 2nd-B; never edit `E:\2ndB` directly; **never push online** (Claude single online-git §11). Submit local commit SHAs to Claude for cherry-pick merge.
- No edits to shared files (PROTOCOL/ROUTING/BOARD/app CLAUDE.md) — opinions go to own outbox only (§10.5 prompt-injection ban).
- Cross-review (§34.4): AG is the native judge for Claude's native output; AG's output judged by Claude.
- Throttle (§34.3): if 8 unmerged submissions, stop discovery -> review / persona-sim / wiki_lesson / re-measure. No idle.

## Headless continuity (§34.7 / §28.4)
- Gemini CLI free tier deprecated 2026-06-18. Path order: (1) interactive Gemini, (2) `agy` after OAuth (`--dangerously-skip-permissions`), (3) reroute part of AG lane to Claude/Codex if neither works. Record current headless means in STATUS.

## Wiki contribution (§34.1)
- On a reusable native lesson/gotcha: write `type: wiki_lesson` (to: claude) in own outbox (one-line summary + 3 key points + source + linked project). Claude ingests to SimonKWiki (write stays Claude/librarian).
