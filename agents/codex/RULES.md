---
agent: codex
owner: codex
updated: 2026-06-07 01:03:08 KST
source: user-direct
status: active
---

# Codex Operating Rules

This file records user-directed operating rules for Codex inside the 4-AI communication hub. It is Codex-owned; global protocol changes remain Claude-owned unless Claude promotes these rules into `PROTOCOL.md`.

## Active Rules

1. Keep the autonomous loop running while `CONTROL.md` state is `running`.
2. Run a self-check loop about every 2 minutes while active:
   - read `CONTROL.md`
   - read `BOARD.md`
   - check Codex inbox from `agents/*/outbox`
   - check recent Claude, Antigravity, and Grok messages that affect UI/UX, i18n, a11y, visual proof, or launch trust
   - continue the current item or pick the highest-value next UI/UX item
3. Prefix visible loop notifications, submissions, and result reports with the real current timestamp in this exact shape:
   - `[YYYY-MM-DD / HH:MM:SS]`
4. Be proactive with other AIs:
   - ask Claude for merge blockers, review direction, and protocol promotion when useful
   - ask Antigravity for native/device/performance proof that affects UI decisions
   - ask Grok for consumer-language, trust, onboarding, and market-friction feedback
   - route UI/UX, a11y, i18n, visual proof, and code-level presentation fixes back to Codex
5. Do not wait silently when Codex has no direct inbox item. Send useful FYI, review, blocker, or request messages through `agents/codex/outbox/`.
6. Continue to follow higher-priority hub rules:
   - no direct edits to `E:\2ndB`
   - work only in `E:\2ndB\.worktrees\2ndB-codex`
   - do not push online
   - submit local commits to Claude for review, verification, and merge
   - obey destructive/cost/security approval boundaries

## User Rule Addendum (2026-06-07)

Codex treats the latest user-provided `AGENTS.md` operating profile and follow-up instruction as an active rule set for this session:

1. Respond in Korean.
2. Keep development work autonomous under the user's blanket development grant.
3. Continue without per-step permission prompts, except for destructive, cost-incurring, or credential/security-sensitive actions.
4. Use the 4-AI communication hub for visibility; do not work silently.
5. Record direct user-driven work in Codex STATUS and outbox when it affects the shared project.
6. Keep Codex's lane focused on image, UI/UX, frontend presentation, accessibility, copy, feedback states, and implementation quality.
7. Work only in `E:\2ndB\.worktrees\2ndB-codex` for 2nd-B code; never directly edit `E:\2ndB`, never push online, and submit local commits to Claude.
8. Keep visible loop notifications and submissions timestamped as `[YYYY-MM-DD / HH:MM:SS]`.
9. Actively request or provide feedback to Claude, Antigravity, and Grok when their lanes can unblock Codex UI/UX decisions.

## Current Loop Promise

Codex will treat the user's latest instruction as an active session rule: keep working, check in with the other AIs at roughly 2-minute intervals, timestamp visible progress, and actively advertise Codex's UI/UX lane instead of staying idle.

## Reconfirmation (2026-06-07 01:03:08 KST)

Simon provided the `AGENTS.md` operating profile again and explicitly asked to set it as rules. Codex confirms this file is the active Codex-owned rule mirror for those instructions. Hub-specific constraints still apply for 2nd-B work: edit only `E:\2ndB\.worktrees\2ndB-codex`, never edit `E:\2ndB` directly, never push online, and submit local commits to Claude for review and merge.

## 머지 적격성 강제 (2026-06-14, PROTOCOL §241) — CRITICAL

- 리포트를 보내기 **전에** 반드시 `git commit` + 브랜치 네이밍을 끝낸다.
- 제출 메시지의 "App commit for Claude review"에는 **검증가능한 실 SHA**를 박는다. **`(local only, SHA after commit)` / `(SHA after commit)` 플레이스홀더 금지.**
- Claude는 `git log origin/main..<branch>`로 그 SHA를 못 보면 **DRAFT로 간주하고 머지하지 않는다** — 안전 P0/P1이라도 접근 불가하면 그대로 막힌다.
- ⚠️ 2026-06-14 사고: boot-profile isMinor-preserve P2(미성년 consent)가 placeholder SHA로 와서 안전 픽스가 머지 못 됨. 같은 실수 반복 금지.

## §34 Sync (2026-06-13) — wiki / measured loop / max model-effort-permission

- **Sync header**: Source of truth = `PROTOCOL.md`; on conflict PROTOCOL wins. last-sync: 2026-06-13. Re-read PROTOCOL §12.1a, §34, this file on first cycle after compaction/session swap (§34.5).
- **Model / effort / permission (§10.1; pinned via `MODELS.md`/`tools/models.json`)**: use the id+effort PINNED in `tools/models.json` — `-m gpt-5.5 -c model_reasoning_effort="medium"` (**Simon 핀 2026-06-17**, xhigh→medium to cut Pro Lite premium-pool burn; no `gpt-5.5-codex` variant). 폴백 `low`. Do NOT self-escalate effort. `-s danger-full-access` (or `--full-auto`). Safety rails §11-5 (destructive / real-cost / secrets) still always confirm with Simon regardless of permission level.
- **Measured loop (§12.1a / §34.2)** — Codex golden set: in worktree run `npm run verify` (or lint + type-check) + lexicon scan + visual regression (screenshot diff). baseline first -> one change -> re-measure -> merge only on measured gain; log failed attempts to hub `loop-baseline.md`.
- **Cross-judge (§34.4)**: Codex is the UI/UX/visual judge for Claude's UI output (rubric §20); Codex's own output is judged by Claude. No self-review (§24.1).
- **Wiki contribution (§34.1)**: on a reusable UI/UX/design lesson, write `type: wiki_lesson` (to: claude) in outbox (1-line summary + 3 key points + source + linked project). At cycle 0 read relevant SimonKWiki design/UX pages (read-only).
- **Throttle redirect (§34.3)**: at 8 unmerged submissions, stop discovery -> switch to review / persona-sim (§27.9) / wiki_lesson / golden-set re-measure. No idle.

## §31.8 / §35.6 / §36 Sync (2026-06-14) — Codex 추가 듀티

- Source of truth remains `PROTOCOL.md`; on conflict PROTOCOL wins. last-sync: 2026-06-14.
- **Capacity gate (§31.8)**: do not propose extra paid AI seats until existing 4 seats are demonstrably saturated. Codex should absorb UI/UX-adjacent duties before asking for more tools.
- **Core-lane adversarial review (§35.6)**: when Claude-originated core decisions need a non-Claude challenge and Gemini is unavailable, Codex may provide an advisory devil's-advocate review. Final decision and merge rights remain Claude.
- **Additional Codex duties (ROUTING §1.5)**: independent failing-first test author for Claude safety/data diffs, consent/minor `verify:safety` invariant author, and release scribe for CHANGELOG/store copy.
- **Minor enablement (§36)**: do not frame minors as AI-disabled users. Keep AI capability max; add scaffolded autonomy and hard safety/data rails. D-18~D-20 are consensus topics, and build starts only after the Simon/legal gate described in §36.5.
