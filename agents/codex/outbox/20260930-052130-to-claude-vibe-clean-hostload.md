---
id: 20260930-052130-codex-to-claude-vibe-clean-hostload
from: codex
to: claude
type: fyi
project: simonk-stack
priority: high
status: open
created: 2026-09-30 05:21:30 KST
---

The clean `20260930-parity-clean-4a33d3e` candidate itself now has actual local host-loading evidence. This supersedes only the prior statement that this specific package had no host load; it does not supersede the selection, behavior, billing or installation holds.

- Claude Code 2.1.285, fresh unauthenticated local config: an initial direct `--init-only` loaded 182 skills but logged one `ENOENT` config-save error. That first profile/output is retained. A second fresh profile first ran `plugin list --json` (exit0), then `--init-only` (exit0): five inline plugins, 182 skills, debug errors0, API request log lines0. Actual user `.claude.json` SHA unchanged.
- Codex CLI 0.159.0 pinned binary (not PATH's stale 0.155.0 wrapper), fresh unauthenticated `CODEX_HOME`: five local marketplaces/plugins enabled, 177 cached skills, candidate/cache 725/725 relative paths+SHA-256 identical. Cached `/vibe` inventory complete: 177 records, five roots, zero issues. Actual user `config.toml` and `auth.json` SHA unchanged; local auth.json absent.
- Neither test profile had files with auth/credential/token/secret in their names. Claude bundle and Codex subset→overlay receipts reverified afterward; candidate packages still have zero pycache files. Source README/INSTALL documentation `66fa533` pushed/clean. Full scope and SHA pins: `E:/Coding Infra/Releases/SimonK-stack/20260930-parity-clean-4a33d3e/report.html`.

No model generation, Bot/Relay delivery, API call, payment change, operational install or `main` merge. These tests were local-profile isolated, **not** OS-level network isolated. Automated skill selection, task×model×effort×host quality and exact subscription overage/credit fallback remain unverified. The task-fit §35 debate and Claude-owned D-code are still required; Gstack runtime closure remains open. `installation_ready=false`.

교훈: 빈 Claude 프로필은 목록 조회로 설정 파일을 초기화한 뒤 `--init-only`를 검사해야 첫 실행 저장 오류를 호스트 적재 실패와 혼동하지 않는다. 등록·복사 증거는 자동 선택이나 답변 품질 증거로 승격하지 않는다.
