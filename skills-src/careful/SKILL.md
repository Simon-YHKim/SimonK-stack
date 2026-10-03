---
name: careful
version: 0.2.0
description: "Use when touching prod, live systems or a shared machine, or asked to \"be careful\", \"safety mode\", \"careful mode\", \"조심해\", \"신중 모드\", \"위험한 명령 경고\". Installs a session PreToolUse Bash hook that produces deny for HIGH commands (rm -rf / or ~, force-push to the default branch), ask for MEDIUM destructive ones (rm -r, DROP, git reset --hard), and always deny when the hook itself fails."
allowed-tools:
  - Bash
  - Read
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: 'bash "$HOME/.claude/skills/careful/bin/check-careful.sh"'
          statusMessage: "Checking for destructive commands..."
---

# /careful — Destructive Command Guardrails

Safety mode is now **active**. Every Bash command is checked for destructive
patterns before it runs. HIGH patterns are blocked, MEDIUM patterns ask first,
and if the check itself breaks the command is blocked instead of slipping through.

Based on gstack 1.91.9 `/careful` (MIT, Garry Tan). SimonK adds only the
fail-closed deltas listed below (hub decision D-56, 2026-10-03).

```bash
mkdir -p ~/.gstack/analytics
echo '{"skill":"careful","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","repo":"'$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "unknown")'"}'  >> ~/.gstack/analytics/skill-usage.jsonl 2>/dev/null || true
```

## 결정 표 (Decision table)

| Case | Decision | Who can override |
|------|----------|------------------|
| Safe command (`git status`), safe build-artifact `rm -rf node_modules` | allow (`{}`) | — |
| MEDIUM destructive family (table below) | `ask` | user, per call |
| Shell obfuscation (`${IFS}`, base64 piped to a shell) | `ask` | user, per call |
| HIGH: simple `rm -r`/`-R` of exactly `/`, `~`, `$HOME`, `/*` | `deny` | end the /careful session |
| HIGH: simple force-push (`-f`, `--force`, `+ref`) to the default branch | `deny` | end the /careful session |
| `--force-with-lease` (any branch) | never HIGH; MEDIUM `ask` | user, per call |
| Internal hook failure (section below) | `deny` | fix the hook or start a session without /careful |
| Non-Bash payload (`tool_name` is not Bash) | allow | — |

Compound commands (`;`, `&&`, `||`, `|`, newline) are never HIGH: string
matching cannot tell what they do, so they fall to the MEDIUM `ask`.

## What's protected (MEDIUM, `ask`)

| Pattern | Example | Risk |
|---------|---------|------|
| `rm -rf` / `rm -r` / `rm --recursive` | `rm -rf /var/data` | Recursive delete |
| `DROP TABLE` / `DROP DATABASE` | `DROP TABLE users;` | Data loss |
| `TRUNCATE` | `TRUNCATE orders;` | Data loss |
| `git push --force` / `-f` / `+ref` | `git push -f origin topic` | History rewrite |
| `git reset --hard` | `git reset --hard HEAD~3` | Uncommitted work loss |
| `git checkout .` / `git restore .` | `git checkout .` | Uncommitted work loss |
| `kubectl delete` | `kubectl delete pod` | Production impact |
| `docker rm -f` / `docker system prune` | `docker system prune -a` | Container/image loss |

## Safe exceptions

A single standalone `rm -r` whose every target is a build artifact is allowed
without a prompt: `node_modules`, `.next`, `dist`, `__pycache__`, `.cache`,
`build`, `.turbo`, `coverage` (optionally under a plain path prefix). Anything
compound, multi-line or containing `$(...)`/backticks loses the exception.

## HIGH tier (hard deny)

Two catastrophic shapes are **denied**, not asked: `rm -r`/`-R` of exactly
`/`, `~`, or `$HOME`, and force-push to the repo's **default branch**
(`origin/HEAD`, else `origin/main`, else `origin/master`; a bare
`git push --force` counts only while on that branch). SIMPLE commands only —
`--force-with-lease` is never HIGH. A best-effort advisory hard-stop, not a
policy boundary: the escape hatch is ending the opt-in, session-scoped
/careful session.

## Internal failure = deny (SimonK fail-closed delta)

Upstream degrades some of these to `ask` or silently allows them. Here every one
returns `deny`, because only `deny` is measured to hold under bypassPermissions:

1. Unexpected script error — an `EXIT` trap backstop emits the deny JSON.
2. `hook-extract.sh` missing, broken, or out of date (lacks a needed function).
3. Empty payload, invalid JSON, non-object JSON, or no `python3`/`node` parser.
4. A Bash payload whose `tool_input.command` is missing, empty, non-string or
   contains NUL. (A missing `tool_name` is treated as Bash, the only matcher.)
5. The pattern matcher errors (`grep` exit > 1) — an error is not a non-match.
6. A per-project pattern file exists but `bin/gstack-slug.sh` cannot resolve
   the project slug.

The reason always reads `[careful][HOOK FAILURE] The careful hook itself
failed: ... This command was NOT safety-checked, so it is blocked.` and names
the way out: fix the hook in `~/.claude/skills/careful/bin`, or start a new
session without /careful.

Non-Bash payloads stay allowed. Upstream told them apart by "no command field",
which also let a Bash call with an unreadable command through; this version
reads `tool_name` instead (case-insensitive `bash`).

## Measured facts (2026-10-03, this machine, Claude Code bypassPermissions)

1. In a skill frontmatter `hooks:` command, `${CLAUDE_SKILL_DIR}` is **not**
   available: the variable is unset and `bash ${CLAUDE_SKILL_DIR}/bin/x.sh`
   never ran (2 runs). A hook that fails to start (exit 127) is non-blocking, so
   the tool call proceeds (fail-open). Hence the hook command above is anchored
   to this skill's own installed copy:
   `bash "$HOME/.claude/skills/careful/bin/check-careful.sh"` (not the gstack
   folder, not `CLAUDE_SKILL_DIR`). If this folder is missing, the hook cannot
   start and nothing is checked.
2. A PreToolUse hook returning `hookSpecificOutput.permissionDecision: "deny"`
   **does** block the Bash call in bypassPermissions mode (measured).
3. Whether `ask` prompts or is auto-approved under bypassPermissions is
   **unmeasured** (and undocumented). Treat MEDIUM `ask` as a warning that may
   not stop anything in that mode; only HIGH and hook failures are known to block.

## Project patterns (additive only)

Add warn rules — one POSIX ERE per line, `#` comments OK — in
`<state>/careful-patterns.txt` (global) or
`<state>/projects/<slug>/careful-patterns.txt` (per project), where `<state>` is
`${CLAUDE_PLUGIN_DATA:-$HOME/.gstack}` (the root SimonK freeze also uses) and
`<slug>` comes from the vendored `bin/gstack-slug.sh`. Consulted after the
built-in families and only when none matched, so config can only ADD an `ask`,
never suppress a baseline warning or a HIGH deny. Invalid regex lines are skipped.

## Install and gstack setup ownership

- `bin/` is self-contained: `check-careful.sh`, `hook-extract.sh` (shared with
  SimonK freeze), `gstack-slug.sh`, plus the offline test `test_check_careful.py`.
- This SKILL.md deliberately carries **no** gstack gen-skill-docs banner. gstack
  `./setup` (no-prefix mode, target `~/.claude/skills/careful`) only treats an
  existing real folder as its own when it has a `.gstack-owned` marker, a
  SKILL.md symlinked into gstack, a SKILL.md byte-identical to gstack's, or that
  two-line banner. Without any of them setup prints "skipped careful: existing
  entry is not gstack-managed" and leaves the folder untouched. Do not add a
  `.gstack-owned` file here, or setup will overwrite this skill.

## Verify

```bash
python -B skills-src/careful/bin/test_check_careful.py   # needs Git Bash on Windows
```

Commands are only fed as stdin JSON; the tests never execute them.

## Deactivate

Hooks are session-scoped: end the conversation or start a new one without
/careful. That is also the only way past a HIGH or hook-failure deny.

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
