---
id: 20260930-054209-codex-to-claude-vibe-path-guard
from: codex
to: claude
type: fyi
project: simonk-stack
priority: high
status: open
created: 2026-09-30 05:42:09 KST
---

Simon direct follow-up: avoid SimonKStack degradation between Claude and Codex hosts. Feature `feat/skill-context-budget-260925` is pushed and clean at `37b2a43` (code `6cbef21`, docs `37b2a43`). `/vibe` 2.12.11 now has a local-only preflight `python -B scripts/check_tooling.py --local-codex`: current PATH Codex 0.155.0 vs adjacent npm package 0.159.0 returns `뒤처짐`/exit1 without invoking npm registry, Orca or model generation. Global PATH/shim was **not** changed. Four RED→GREEN tests passed in source and both packaged variants; validator 0 errors/0 warnings, orchestration101, runtime27, registry29 and table-sync3 passed. The Bash TDD guard cannot resolve this Windows worktree Git path; staged source+test pairing was reviewed manually.

New preserved candidate: `E:/Coding Infra/Releases/SimonK-stack/20260930-path-6cbef21/report.html`. Source, Claude five-plugin, Codex overlay, Codex D-29 subset receipt digests are in that report; all independently reverified. Claude182/Codex177, 176 identical common SKILL bodies, approved `zoom-out` projection1, five D-29 exclusions, candidate pycache0. Fresh unauthenticated local profiles: Claude Code2.1.285 `--init-only` 5 plugins/182 skills, exit0/debug rg errors0/API request lines0; Codex CLI0.159.0 registered five enabled plugins/177 skills with 726/726 cache paths+SHA matching candidate, actual user Codex config/auth hashes unchanged. Both default catalogs returned 182/177. First Claude profile's missing cache-directory rg error was preserved; a second fresh profile with precreated empty cache directory passed.

Current candidate path audit: local unresolved/unportable0; pinned Gstack direct helper targets9 present; external runtime still pending (Claude31 skills/646 refs, Codex30/625). No OS-level network isolation or automatic skill selection/answer-quality comparison was performed. Exact subscription-included model and purchased-credit fallback remain unverified; no generation/API/Bot/Orca calls, extra charge, payment changes, user-profile install or main merge. `installation_ready=false`. Claude-owned task-fit and plugin-version D-code, Gstack runtime closure, model-quality/host parity and safe operational migration remain needed. This is progress, not release approval.

교훈: a PATH-selected worker CLI can lag behind a newer local package while isolated direct-binary tests pass; the local-only guard catches the mismatch without touching Orca. Package load and byte equality are not response-quality or billing proofs.
