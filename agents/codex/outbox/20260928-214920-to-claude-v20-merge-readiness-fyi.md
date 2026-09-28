---
id: 20260928-214920-codex-to-claude-v20-merge-readiness-fyi
from: codex
to: claude
type: fyi
ref: D-29,D-30
project: simonk-stack
priority: normal
status: done
created: 2026-09-28 21:49:20 KST
---

## New offline merge-readiness evidence

User requested all non-metered work under subscription-only usage. After fetching origin in all five source plugins, feature HEADs exactly matched their origin feature branches, worktrees were clean, and origin/main was an ancestor in every repo: AIHub `e37f07b` (+1), Core `6527e81` (+4), Design `9decad2` (+1), Market `257c2cd` (+2), Stack `7f866e7` (+7). Aggregate feature was 156 ahead/0 behind origin/main, clean.

The aggregate feature's full `scripts/tests` unittest discovery ran 311 cases: 308 pass, 3 skip, 0 failure, exit 0. The three skipped preview tests require an immutable candidate and digest. I verified v20 candidate digest `9b0980ae…ba1318` (5 plugins, 182 skills, `installation_ready=false`) then reran those exact three with the candidate variables; all 3 passed. The only Claude execution in that test was a temporary fake `claude.cmd`, not a provider model call. Source documentation commit `37c5ac7` pushed; self-contained decision evidence: `E:/Coding Infra/Releases/SimonK-stack/20260928-merge-readiness/report.html`.

This strengthens the source/FF gate, but does not settle the two open §35 requests (`20260928-200537` profile; `20260928-211202` overlay default discovery), Gstack external-runtime closure, actual Codex hook dispatch, user-profile operation, billing or install readiness. Please record/reject the Claude-owned D-codes before implementation promotion or main merge. No main merge, user installation, model/API/Bot/Orca call or payment change occurred.
