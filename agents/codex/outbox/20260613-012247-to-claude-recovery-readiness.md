---
id: codex-20260613-012247-claude-recovery-readiness
from: codex
to: claude
type: fyi
status: done
priority: high
project: relocation-recovery
created: 2026-06-13 01:22:47 KST
---

# Claude recovery readiness after relocation

Simon asked Codex to repair the environment while Claude usage is unavailable, so Claude can resume without repeating relocation mistakes.

## Ready state

- Communication hub exists and works at `E:\Coding Infra\AI Infra\Communication`.
- `CONTROL.md` remains `state=paused`. This is intentional from 2026-06-08; do not restart autonomous loops until Claude explicitly resumes.
- Communication repo has no remote configured. Local commits exist, but there is no hub push target.
- `E:\2ndB` is clean and current with `origin/main@f769d1d`.
- `SimonKWiki` is clean and pushed to `origin/main@9a954e6`.

## 2ndB repair

- `E:\2ndB` was 144 commits behind; fast-forward pull completed.
- Copied/broken directories under `E:\Coding Infra\_worktrees\2ndB-*` had no `.git` file, so they were not usable git worktrees.
- Those directories were moved, not deleted, to `E:\Coding Infra\_worktrees_stale\20260613-010900\`.
- Backup branches were created before recreating live work branches:
  - `codex/work-stale-20260613-010900`
  - `antigravity/work-stale-20260613-010900`
- Recreated live worktrees:
  - `E:\Coding Infra\_worktrees\2ndB-codex` -> `codex/work`
  - `E:\Coding Infra\_worktrees\2ndB-antigravity` -> `antigravity/work`
- Both live worktrees have `node_modules` junctions pointing to `E:\2ndB\node_modules`.
- `npm run verify` passes in `E:\2ndB`: 129 test suites, 1125 tests. Lint has 0 errors and 4 existing unused eslint-disable warnings.
- `npm install --legacy-peer-deps` was required because `npm ci` failed on package-lock drift and normal `npm install` hit a TypeScript peer dependency conflict.
- `npm audit` reports 11 moderate vulnerabilities. I did not run `npm audit fix` because that can change dependency versions broadly.

## Wiki repair

- `wiki/protocols/multi-agent-hub-lessons.md` is usable as the AI hub lessons source for reducing repeated mistakes.
- Fixed broken external path wikilinks and Output report wikilinks so the main wiki graph is not polluted by vault-external HTML paths.
- Restored `wiki/protocols/llm-wiki/LESSONS_LEARNED.md` frontmatter position.
- `wiki/index.md` now matches the 160 wiki files.
- `wiki_lint.py` result: Error=0, E1=0, E2=0, W2/W3/W4/FM=0. Only W1=2 known historical contradictions remain.
- `raw_isolation.py` result: isolated=0/26 after fixing HTML stem normalization in the checker.
- Nested `Simon-LLM-Wiki/` reappeared inside the vault and was moved outside the vault to `E:\Coding Infra\obsidian\BACKUP_Simon-LLM-Wiki-reappeared\20260613-011117\`. `.gitignore` now blocks recurrence.

## Claude restart notes

- Use `E:\Coding Infra\_worktrees\2ndB-codex` for Codex-side 2ndB work and `E:\Coding Infra\_worktrees\2ndB-antigravity` for Antigravity-side work.
- Do not use the backed-up stale worktree directories as active repos.
- Keep Communication hub paused until Claude changes `CONTROL.md` back to `running`.
- If this external drive mounts with a different letter on another laptop, absolute references to `E:\Coding Infra`, `E:\2ndB`, and `C:\Users\202502` still need path remapping.
- Main remaining infrastructure gap: Communication hub has no remote.
