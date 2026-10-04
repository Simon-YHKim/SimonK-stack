---
name: careful
version: 0.2.4
description: "Use when touching prod, live systems or a shared machine, or asked to \"be careful\", \"safety mode\", \"careful mode\", \"조심해\", \"신중 모드\", \"위험한 명령 경고\". Installs session PreToolUse Bash and PowerShell hooks; the check produces deny for HIGH commands (recursive delete of /, a drive root or ~, force-push to the default branch), ask for MEDIUM Bash ones (rm -r, DROP, git reset --hard), and always deny when the hook itself fails."
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
    - matcher: "PowerShell"
      hooks:
        - type: command
          command: 'bash "$HOME/.claude/skills/careful/bin/check-careful.sh" powershell'
          statusMessage: "Checking PowerShell for catastrophic commands..."
---

# /careful — Destructive Command Guardrails

Safety mode is now **active**. Every Bash and PowerShell command is checked
before it runs. HIGH patterns are blocked, MEDIUM Bash patterns ask first
(PowerShell is deny-only), and if the check itself breaks the command is
blocked instead of slipping through.

Based on gstack 1.91.9 `/careful` (MIT, Garry Tan). SimonK adds only the
fail-closed deltas listed below (hub decision D-56, 2026-10-03), the
Windows-shaped HIGH targets (hub decision D-62 A1, 0.2.1) and the deny-only
PowerShell tool check (D-62 minimal B, 0.2.2).

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
| HIGH: simple `rm -r`/`-R` whose every target is a root, drive root or home (incl. `/*`, `~/*`, `$HOME/*`) | `deny` | end the /careful session |
| HIGH: simple `cmd /c rd\|rmdir\|del /s` or `powershell\|pwsh -c Remove-Item -Recurse` of a drive root or home | `deny` | end the /careful session |
| HIGH: simple force-push (`-f`, `--force`, `+ref`) to the default branch | `deny` | end the /careful session |
| `--force-with-lease` (any branch) | never HIGH; MEDIUM `ask` | user, per call |
| PowerShell tool: catastrophic shape (section below) | `deny` | end the /careful session |
| PowerShell tool: anything else | allow (never `ask`) | — |
| Internal hook failure (section below) | `deny` | fix the hook or start a session without /careful |
| Other tools (`tool_name` neither Bash nor PowerShell) | allow | — |

Bash compound commands (`;`, `&&`, `||`, `|`, newline) are never HIGH: string
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

Two catastrophic shapes are **denied**, not asked: a recursive delete whose
every target is root class (below), and force-push to the repo's **default
branch** (`origin/HEAD`, else `origin/main`, else `origin/master`; a bare
`git push --force` counts only while on that branch). SIMPLE commands only —
`--force-with-lease` is never HIGH. A best-effort advisory hard-stop, not a
policy boundary: the escape hatch is ending the opt-in, session-scoped
/careful session.

**Root class** (0.2.1, hub decision D-62 A1). Every quote character is removed
first (`"$HOME"/*` is `$HOME/*`); then a target is root class when it is:

| Kind | Spellings (each may end in one `*`, `.*` or `*.*` glob level) |
|------|------------------------------------------------------------------|
| Filesystem root | `/`, `//`, `/*`, `/.*` |
| MSYS / WSL / Cygwin drive | `/c`, `/c/`, `/c/*`, `/mnt/c`, `/cygdrive/d` (any letter) |
| Windows drive | `C:`, `C:/`, `C:\`, `C:\*`, `C:/*`, `c:\\` |
| Home | `~`, `~/`, `~/*`, `~/.*`, `$HOME`, `$HOME/*`, `${HOME}`, `${HOME}/*` |

Recursive deleters checked: `rm` with `-r`/`-R`/`--recursive` in any flag
spelling (`-rf`, `-fr`, `-r -f`, `--`, `sudo rm`), and, launched from the Bash
tool, `cmd[.exe] /c|//c rd|rmdir|del|erase` with `/s`, and
`powershell|pwsh[.exe] [host options] -c|-Command Remove-Item|ri|rm|del|rd|rmdir|erase`
with `-Recurse` (any prefix such as `-r`, `-rec`). For cmd/PowerShell, `\`
(current-drive root) and `~\`, `$HOME\*` also count, matched case-insensitively.
`-WhatIf` is a dry run and never HIGH.

**Kept at the previous tier on purpose** (ambiguous by string matching):
project subfolders (`rm -rf /c/Users/me/project/build` stays on the
build-artifact allowlist; `./C`, `"$HOME/project/tmp"` stay `ask`), literal
profile or system paths (`/c/Users/<name>`, `/c/Windows`, `C:\Users`),
variables other than HOME (`$USERPROFILE`, `$TMPDIR`, `%USERPROFILE%`,
`$env:USERPROFILE`, `$env:SystemDrive`), globs deeper than one level
(`/c/*/*`, `~/*/`), `/mnt` and `/mnt/*`, relative `.` `..` `*`, `C:*`, a mix of
root and non-root targets, compound commands, `-EncodedCommand`, pipes, and
other destroyers (`find / -delete`, `git clean -fdx`, `chmod -R`, `mv ~`).
Since 0.2.2 cmd and PowerShell launched from Bash also spell home as
`%USERPROFILE%` / `$env:USERPROFILE` (deny); Bash `rm -rf $USERPROFILE` stays `ask`.

## PowerShell tool (deny-only, 0.2.2, hub decision D-62 minimal B)

A second frontmatter entry (`matcher: "PowerShell"`) runs the same script with
the argument `powershell`. Measured live 2026-10-03 23:50 KST: the matcher
fires (when the PowerShell tool is enabled), the payload carries
`tool_name: "PowerShell"` and `tool_input {command, description}`, and a deny
blocks the command. PowerShell carries most commands on this machine, so this
check **never asks**: the shapes below deny, everything else is allowed.

The command is split into simple commands at `;`, `|`, `||`, `&&`, newlines and
`{ } ( )` (backtick line continuations joined, `${name}` read as `$name`,
commas as spaces); each one is checked on its own, case-insensitively, with
every quote character removed.

| Shape (literal targets only) | Example |
|------|---------|
| `Remove-Item` / `ri` / `rm` / `rmdir` / `rd` / `del` / `erase` with `-Recurse` (any prefix, e.g. `-r`) or cmd-style `/s`, every target a drive root or home | `Remove-Item -Recurse -Force C:\`, `ri -r -fo $HOME\*`, `rd /s /q C:\` |
| `cmd /c rd\|rmdir\|del\|erase /s` at a drive root or home | `cmd /c rd /s /q C:\`, `cmd /c rd /s /q %USERPROFILE%` |
| nested `powershell\|pwsh -Command` with the same delete | `pwsh -c "Remove-Item -Recurse C:\"` |
| `Format-Volume`, `Clear-Disk`, `Initialize-Disk`, `Remove-Partition` as the command | `Clear-Disk -Number 1 -RemoveData` |
| force-push to the default branch (Bash HIGH logic), whole command one simple command | `git push --force origin main` |

Drive root / home for PowerShell: `C:`, `C:\`, `C:/`, `C:\*`, `\`, `~`, `~\*`,
`$HOME`, `$HOME\*`, `$env:USERPROFILE`, `$env:USERPROFILE\*` (also `-Path:C:\`,
`-LiteralPath 'C:\'`, `C:\,D:\`). `-WhatIf` never denies. Allowed (not asked):
`Remove-Item -Recurse .\build`, `Remove-Item C:\Users\me\project\tmp -Recurse`,
`Get-ChildItem C:\`, `git push --force-with-lease`, `git push --force origin feature-x`,
`git reset --hard`, and a force-push after another statement (a `Set-Location`
could have changed the repo).

**Gaps** (not guessed — string matching cannot see them): variables other than
HOME and USERPROFILE (`$env:SystemDrive\`, `$sp`), splatting (`@params`),
`-EncodedCommand`, `Invoke-Expression`, `Start-Process`, pipeline input
(`gci C:\ | Remove-Item -Recurse`), array syntax `@('C:\')`, here-strings,
`diskpart`/`format.com`, and disk cmdlets inside a nested `powershell -Command`.
The plugin candidate (SimonKCore) keeps this entry: its safety runtime runs the
plugin's copy of this script with `powershell` (`check careful-powershell`).
That runtime passes the script's deny through unchanged and denies when it
cannot run the check itself (hub decision D-62 follow-up 5).

## Internal failure = deny (SimonK fail-closed delta)

Upstream degrades some of these to `ask` or silently allows them. Here every one
returns `deny`, because only `deny` is measured to hold under bypassPermissions:

1. Unexpected script error — an `EXIT` trap backstop emits the deny JSON.
2. `hook-extract.sh` missing, broken, or out of date (lacks a needed function).
3. Empty payload, invalid JSON, non-object JSON, or no `python3`/`node` parser.
4. A Bash or PowerShell payload whose `tool_input.command` is missing, empty,
   non-string or contains NUL. (A missing `tool_name` means the tool of the
   entry that ran the script: Bash without an argument, PowerShell with
   `powershell`.) An unknown hook mode argument also denies.
5. The pattern matcher errors (`grep` exit > 1) — an error is not a non-match.
6. A per-project pattern file exists but `bin/gstack-slug.sh` cannot resolve
   the project slug.

The reason always reads `[careful][HOOK FAILURE] The careful hook itself
failed: ... This command was NOT safety-checked, so it is blocked.` and names
the way out: fix the hook in `~/.claude/skills/careful/bin`, or start a new
session without /careful.

Other tools stay allowed. Upstream told them apart by "no command field",
which also let a Bash call with an unreadable command through; this version
reads `tool_name` instead (case-insensitive `bash` or `powershell`).

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
3. `ask` **does** show a confirmation prompt under bypassPermissions (measured
   2026-10-03 23:50 KST with a Bash hook; it is not auto-approved). Even so,
   the PowerShell check stays deny-only so normal PowerShell work is not
   interrupted.
4. A skill hook with `matcher: "PowerShell"` fires on the PowerShell tool and
   its deny blocks the command (same measurement; the tool must be enabled,
   e.g. `CLAUDE_CODE_USE_POWERSHELL_TOOL=1`).

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
# <skill-dir> = 이 스킬 폴더 (소스 체크아웃에서는 skills-src/careful)
python -B <skill-dir>/bin/test_check_careful.py   # needs Git Bash on Windows
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
