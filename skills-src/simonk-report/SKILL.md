---
name: simonk-report
description: >
  Use when the user wants a rich HTML report of what simonK or the
  current session accomplished — triggers "/simonk-report", "리포트
  만들어줘", "보고서 작성", "html 보고서", "executive briefing",
  "session report". Auto-invoked by simonK Phase 6 as the standard
  final deliverable (unless SIMONK_REPORT=off). Produces a single
  self-contained HTML at .simonk/reports/YYYY-MM-DD-HHMM.html (inline
  CSS, no external deps — opens anywhere) covering executive summary,
  decisions log, phase trace, diff summary, verification, perspectives
  audit if ran, next-up backlog. Sends proactively via SendUserFile
  so user receives it on mobile. Different from /landing-report
  (product landing), /document-release (README sync), /release-notes
  (announcement copy), and /html-default-output (generic — this is
  simonk-session-specific with a fixed schema).
version: 1.0.0
allowed-tools:
  - Bash
  - Read
  - Write
  - SendUserFile
---

# /simonk-report

Generate a rich HTML report of the current session (or just-completed
simonK sprint) and send it proactively to the user as a file.

## Why this skill exists

simonK's Phase 6 final report has historically been text-only —
useful in the session but lost the moment the conversation scrolls.
A self-contained HTML report:

- **Lives outside the session** — can be sent, shared, archived
- **Renders the structure** — phase-by-phase trace, diffs, verifications
- **Reaches the user on mobile** — via `SendUserFile` proactive status
- **Accumulates as a sprint log** — `.simonk/reports/` becomes a
  diary of what each sprint shipped, scannable later

## When to invoke

| Trigger | Source |
|---|---|
| `/simonk-report` | Manual user request, any time |
| simonK Phase 6 | Auto (unless `SIMONK_REPORT=off` env or user opted out) |
| "리포트 만들어줘", "보고서 작성" | Korean trigger |
| "html 보고서", "executive briefing" | Variant triggers |

## Execution sequence

### Step 1 — Gather session state

Run the same inventory as `/perspectives` (the two skills are
complementary — perspectives audits blind spots, this skill
documents the work):

```bash
# Project + session identity
PROJECT_NAME=$(basename "${CLAUDE_PROJECT_DIR:-$PWD}")
TIMESTAMP=$(date +%Y-%m-%d-%H%M)
TITLE_TIMESTAMP=$(date +"%Y-%m-%d %H:%M")

# Git diff context (since simonK started — fall back to today's commits)
COMMITS=$(git log --oneline --since="6 hours ago" 2>/dev/null)
FILES_CHANGED=$(git log --since="6 hours ago" --name-only --pretty=format: 2>/dev/null | sort -u | grep -v '^$')
STAT=$(git diff --stat HEAD~$(git log --oneline --since="6 hours ago" | wc -l) 2>/dev/null || git diff --stat HEAD)
BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo HEAD)
```

Pull from the conversation context (not raw transcripts):

- **Task**: what the user asked simonK to do (Phase 1 input)
- **Plan**: the sprint plan if Phase 2 produced one (`.simonk/plan.md`)
- **Phase outcomes**: what each Phase 1-6 produced
- **Decisions**: explicit user choices via AskUserQuestion
- **Skips**: anything explicitly deferred
- **Verification**: which tests / validators ran and their results
- **Perspectives findings**: top 3 from `/perspectives` if it ran

### Step 2 — Render the HTML

Read the template at `templates/report.html`, fill placeholders, and
write to `.simonk/reports/<TIMESTAMP>.html`. Template is fully
self-contained (CSS inline in `<style>`, no external fonts, no JS).

If `.simonk/reports/` does not exist, create it. If the file already
exists for this timestamp (multiple invocations in the same minute),
append `-2`, `-3`, etc.

### Step 3 — Send to the user

```
SendUserFile(
  files=[".simonk/reports/<TIMESTAMP>.html"],
  status="proactive",  # ensures mobile / desktop notification
  caption="simonK 스프린트 보고서 — <한 줄 요약>"
)
```

Proactive status because by Phase 6 the user may have stepped away
from the terminal — they should get the report on whatever device
they're on.

### Step 4 — Brief text follow-up

After the file send, post a single short message:

```
✓ 보고서 발송: .simonk/reports/<TIMESTAMP>.html
  - 5 작업 완료 / 2 deferred / 0 failed
  - 다음 권장: <next-up 첫 항목>
```

Do NOT repeat the full content of the HTML in the chat. The chat is
ephemeral; the HTML is the durable artifact.

## HTML report structure (template sections)

The template has these sections in order. Omit any section that has
no content for this session — empty placeholders are not rendered.

| Section | Purpose | Length |
|---|---|---|
| **Header** | Task title, timestamp, duration, repo, branch | 1 line each |
| **Executive Summary** | What shipped / what didn't / next | 3-5 bullets |
| **Decisions Log** | Key choices made (Phase 1 ambiguity Q&A, Phase 2 scope cuts, user-explicit choices) | 3-10 items |
| **Phase Trace** | simonK Phase 1-6 each with input / output / duration | 6 cards |
| **Diff Summary** | Files changed (grouped by area), +/- LOC, key commits with SHAs | Table |
| **Verification** | What ran (validators, tests, lints, smoke tests), pass / fail counts | Table |
| **Perspectives** | If `/perspectives` ran — Core 5 + session-specific findings | Conditional |
| **Next-up Backlog** | Deferred items, follow-up PRs, manual to-do tasks | Bulleted |
| **Appendix** | Raw commit log, full file list (collapsed `<details>`) | Collapsible |

## Visual design

Tinted neutral palette (per CLAUDE.md design rules):
- Background: `#0F0E1A` (deep violet-tinted dark) for dark mode
- Text: `#E8E6F0` (warm off-white)
- Accent: `#7B68EE` (medium slate blue — calm, professional)
- No emojis in body text. Section icons use simple Unicode geometric shapes (▸ ◆ ●)
- Font: system sans (`-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif`) — NEVER Inter
- 100% width on mobile, max 720px on desktop
- Code blocks: monospace with `#1A1828` background
- No JavaScript

## Anti-patterns (do NOT do)

- ❌ External CSS / fonts / images. The HTML must open offline.
- ❌ Emojis throughout (one in the title is the limit).
- ❌ Dumping the chat transcript. The report is a DIGEST.
- ❌ Generating before Phase 6 fires (mid-sprint reports lie because
  later phases may change the conclusion).
- ❌ Skipping `SendUserFile`. If the user only sees a path, they may
  not see the file at all — they're often on mobile by Phase 6.
- ❌ Auto-committing the report. The user decides whether
  `.simonk/reports/` is tracked or `.gitignore`'d (it's their call).

## Success criteria

The skill is complete when:

1. `.simonk/reports/<TIMESTAMP>.html` exists and is non-empty.
2. The file is fully self-contained (no `<link rel="stylesheet">`,
   no `<script src=>`, no external `<img>`).
3. `SendUserFile` succeeded — the user has a notification with the
   attachment.
4. A brief text follow-up has been posted in the chat (3-4 lines).
5. The HTML opens cleanly in any modern browser (Chrome, Safari,
   Firefox, mobile Safari, mobile Chrome).

## simonK Phase 6 integration

When invoked by simonK Phase 6, the flow is:

```
Phase 5 finishes (commit + push complete)
   │
   └─ Phase 6 invokes /simonk-report
         │
         ├─ inherits session inventory (no re-scan)
         ├─ writes .simonk/reports/<ts>.html
         ├─ SendUserFile(proactive)
         └─ posts 3-line chat summary
```

To opt out for one session: prefix the simonK invocation with
`SIMONK_REPORT=off simonK "..."` (the harness respects the env).

To opt out permanently: add `SIMONK_REPORT=off` to project `.envrc`
or shell profile.

## Related skills (explicit boundaries)

- `/landing-report` (gstack) — product landing page report, different
  audience (external prospects) and format (marketing landing).
- `/document-release` (gstack) — post-ship sync of
  README/CHANGELOG/ARCHITECTURE. Different concern (docs upkeep).
- `/release-notes` (gstack) — release-day announcement copy
  (developer vs user voice split). Different output (copy, not
  internal report).
- `/html-default-output` — generic "make this HTML" trigger for
  arbitrary artifacts. This skill is **simonk-session-specific** with
  a fixed schema.
- `/perspectives` — blind-spot audit. Reports if it ran; doesn't
  replace it.
- `/retro` (gstack) — weekly engineering retro. Different cadence
  (weekly, not per-sprint) and analysis target (commit history).
- `/simon-handoff` — cross-session handoff (docs/HANDOFF.md). This
  skill is the **current session's deliverable**; handoff is the
  pointer to the **next session**.

## Trigger phrases (matched by description block above)

- `/simonk-report`
- "리포트 만들어줘", "보고서 작성", "html 보고서"
- "executive briefing", "session report"
- simonK Phase 6 auto-invocation

## Operational notes

- For sprints under 30 minutes with only 1-2 files touched, the
  report skeleton is overkill. The skill detects this and produces a
  collapsed single-card report instead of the full 9-section layout.
- For sprints over 4 hours, the appendix (commit log + file list)
  grows. Use `<details>` HTML tags so it's collapsed by default.
- The skill never includes secret strings (tokens, passwords) even
  if they appear in commit messages. Pattern-mask `[A-Z0-9_]{32,}`
  and known prefixes (`sk-`, `pk_`, `xoxb-`) before rendering.
- Timestamps are local time, not UTC, because the user reads them.
- The file path returned uses `.simonk/reports/` relative to the
  project root — never absolute paths in the chat reply (privacy).
