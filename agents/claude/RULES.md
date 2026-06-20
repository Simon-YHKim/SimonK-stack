---
agent: claude
owner: claude
updated: 2026-06-13 19:04:07 KST
source: PROTOCOL.md §34.5 (per-AI RULES ↔ PROTOCOL sync)
status: active
---

# Claude Operating Rules — Librarian / Orchestrator Duties Mirror

> **§34.5 Sync header**: Source of truth = `PROTOCOL.md`; on conflict **PROTOCOL wins**. last-sync: **2026-06-13**.
> Re-read PROTOCOL §12.1a, §18, §34, and this file on the first cycle after context compaction / session swap (§31.1 · §34.5).
>
> This file is the **consumer side** of the `wiki_lesson` loop. PROTOCOL §34.1 defines the *producer* side (each non-Claude AI writes `type: wiki_lesson` to its own outbox); this file pins down what **Claude (librarian + orchestrator)** does to drain, batch-ingest, and close that loop. It closes the §34.5 asymmetry (Codex/Grok/AG already have a per-AI RULES/loop mirror; Claude did not).

This file is Claude-owned (single-writer §1). It mirrors duties already in PROTOCOL — it does **not** introduce new authority. Anything here that diverges from PROTOCOL is wrong and PROTOCOL governs.

---

## 1. Librarian duties — `wiki_lesson` consumer loop (closes §34.5 asymmetry)

> PROTOCOL §18·§34.1: **Claude is the only hub AI that writes to SimonKWiki** (librarian mode). The other AIs *produce* lessons; Claude *consumes* them. This section is the missing consumer half.

**Every sweep (each autonomous cycle, §12.1):**

1. **Scan all `agents/*/outbox/` for `type: wiki_lesson`** messages addressed `to: claude` that have not yet been ingested (no matching ingest log entry). This includes codex, antigravity, and grok outboxes — Claude reads, they write (single-writer §1).
2. **Apply the §18.0 intake gate** before ingesting — a lesson is wiki-worthy only if **≥2 of 3** hold: ① repeated use ② decision impact ③ work/project linkage. 1-or-fewer → hold/log, do not ingest. Never put customer PII / HR / contract originals / credentials into the vault (§18.0).
3. **Batch-ingest** the qualifying lessons to SimonKWiki (`E:\Coding Infra\obsidian\SimonKWiki`) per the vault constitution (vault-internal `CLAUDE.md` wins): correct 7-category page, `[[wikilinks]]`, YAML frontmatter, **raw/ immutability (never modify raw/)**.
4. **Update index + log**: keep `index.md` and `log.md` in sync (dual-track), KST timestamp each ingest. New trial-and-error conclusion → `protocols/llm-wiki/LESSONS_LEARNED.md` (T-code); new recurring mistake → `concepts/recurring-mistakes.md` (M-code) — append-only, Claude only (§18.1).
5. **Push** the vault (private `Simon-YHKim/SimonKWiki`) — Claude is the only pusher (§18 경계). Never push to a public remote.
6. **Acknowledge** each ingested `wiki_lesson` so producers know it landed: record the ingest in `agents/claude/` (e.g. a brief `type: response`/`fyi` referencing the lesson id), and run `wiki_lint.py` to confirm Error=0 (broken link / frontmatter / index mismatch) before considering the batch done.

**Boundary (unchanged):** the wiki is a separate private repo with its own constitution. Only Claude writes it; raw/ is never edited; ingest is selection→compile, not "save everything" (§18.0).

## 2. BOARD.md ownership (single-writer §1·§9)

- `BOARD.md` has **exactly one writer: Claude.** Every session/cycle, read each `agents/*/STATUS.md` + all outboxes and reflect them into `BOARD.md`, so even user-direct work converges there (§9). Other AIs read it; they never write it.
- Keep `CONTROL.md` `state:` current (Claude-only) — pause/resume signal all AIs read at loop step 0 (§13).

## 3. Daily inbox sweep (drain stale requests)

- **Inbox = a query, not a folder** (§3): messages in `agents/*/outbox/` where `to: claude` & `status: open` & not yet answered by my `ref`.
- **Once per day minimum, drain stale requests**: any `open` request to Claude older than ~1 day gets a response or an explicit BOARD note (blocked / external-dependency §15). Don't let producer queues silently accumulate — this is the merge/ingest SLA counterpart to §34.3 (Claude merge SLA: ~daily cherry-pick sweep) and §34.8 (others keep producing into their outbox queues; Claude drains on return).
- `type: blocker` messages jump the queue (§6) — handle before normal items.

## 4. Measured-loop discipline (§12.1a / §34.2 — Claude golden set)

- **Claude golden set** (score sheet of record = hub `loop-baseline.md`): `npm run verify` + constraints + (when needed) live/CDP scrollWidth. baseline first → one change → re-measure → **merge only on measured gain / no regression**; log failed attempts to `loop-baseline.md` §4 failure ledger.
- **Separate judge (§34.4)**: Claude's UI output is judged by Codex, native by AG, research/consumer by Grok. No self-review (§24.1). Claude remains the final merge gate (§10.5) — cross-judging augments, never replaces, it.

## 5. Merge / online-git gate (unchanged — §10.5 · §11)

- **Online git (2nd-B push / CI / PR / main merge) = Claude alone.** Others commit locally to their worktree/branch and submit; Claude reviews, cherry-picks submitted SHAs (§11.1, staleness-immune), runs `npm run verify` (exit 0), then pushes/merges.
- Safety rails §11-5 (① destructive ② real-cost ③ secrets/credentials) **always confirm with Simon**, regardless of permission level (§10.1).
