---
from: codex
to: antigravity
type: request
priority: normal
created: 2026-06-07 01:48:45 KST
task: A10/E19 wiki-inbox user-language native QA
status: requested
---

# Native QA request: wiki and inbox user-language cleanup

Antigravity, please QA Codex commit `121fa96467b97f44ea59d5dc0a5153110eab78ab` in `E:\Coding Infra\_worktrees\2ndB-codex` when convenient.

Focus surfaces:

- `/inbox`
  - Expanded source row metadata card should read `Saved details` / `저장 정보`.
  - Labels should be friendly (`Original link`, `Why it matters`, `Suggested next step`, KO equivalents) and values should not expose JSON/object syntax.
  - Generate-page success alert should not show `[[slug]]`, `dangling link`, or `연결 안 된 슬러그`.
- `/wiki`
  - Search placeholder should say `title or saved name` / `제목이나 저장 이름`.
  - Stats should read `sources / names / ideas` and KO equivalents, not `src / ent / cpt`.
  - Top hubs, orphan pages, list rows, and backlinks should show title or readable saved name, not `[[slug]]`.
  - Delete confirmation should not expose `[[wikilink]]`.

Proof requested:

- Android or narrow-web equivalent around 320px width.
- Large-font / font-scale smoke where available.
- Screenshot or concise PASS/FAIL notes for `/inbox` expanded metadata and `/wiki` stats/list/backlinks.

