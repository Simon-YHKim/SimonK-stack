---
name: guard
version: 0.2.3
description: "Use when asked for \"guard mode\", \"full safety\", \"lock it down\", \"maximum safety\", \"가드 모드\", \"풀 세이프티\", or before touching prod or debugging live systems. Combines /careful and /freeze: a PreToolUse Bash hook produces deny for HIGH destructive commands and ask for MEDIUM ones, and an Edit/Write hook produces deny outside the chosen directory, including Windows drive paths."
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "case \"$OS:$OSTYPE\" in Windows_NT:*|*:msys*|*:cygwin*) python -c 'import sys; sys.exit(sys.version_info < (3, 7))' >/dev/null 2>&1 && exit 0; r='[careful][RUNTIME FAILURE] Safety runtime failed, command not checked, so it is blocked (fail closed). Way out: repair the plugin safety runtime (Python, Git Bash and Node on PATH), or start a new session without /careful.';; *) r='[careful][WINDOWS ONLY] The SimonK safety runtime supports Windows only, so on this OS every Bash and PowerShell command is blocked on purpose (fail closed). This is not a verdict on the command. Way out: start a new session without /careful and /guard, or run /plugin disable simonk-core@simonk-stack (for /careful) or /plugin disable simonk-stack@simonk-stack (for /guard) and then start a new session.';; esac; printf '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"%s\"}}\\n' \"$r\"; printf '%s\\n' \"$r\" >&2; exit 2"
        - type: command
          command: "python"
          args: ["-B", "${CLAUDE_PLUGIN_ROOT}/.simonk-runtime/safety_runtime.py", "check", "careful", "--project", "${CLAUDE_PROJECT_DIR}"]
          statusMessage: "Checking for destructive commands..."
    - matcher: "Edit"
      hooks:
        - type: command
          command: "case \"$OS:$OSTYPE\" in Windows_NT:*|*:msys*|*:cygwin*) python -c 'import sys; sys.exit(sys.version_info < (3, 7))' >/dev/null 2>&1 && exit 0; r='[freeze] Safety runtime unavailable; blocked, fail closed.';; *) r='[freeze][WINDOWS ONLY] The SimonK safety runtime supports Windows only, so on this OS every Edit and Write is blocked on purpose (fail closed). This is not a verdict on the edit. /unfreeze cannot lift it here: the boundary state it clears exists only on Windows. Way out: start a new session without /freeze, /guard and /investigate, or run /plugin disable simonk-stack@simonk-stack and then start a new session.';; esac; printf '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"%s\"}}\\n' \"$r\"; printf '%s\\n' \"$r\" >&2; exit 2"
        - type: command
          command: "python"
          args: ["-B", "${CLAUDE_PLUGIN_ROOT}/.simonk-runtime/safety_runtime.py", "check", "freeze", "--project", "${CLAUDE_PROJECT_DIR}"]
          statusMessage: "Checking freeze boundary..."
    - matcher: "Write"
      hooks:
        - type: command
          command: "case \"$OS:$OSTYPE\" in Windows_NT:*|*:msys*|*:cygwin*) python -c 'import sys; sys.exit(sys.version_info < (3, 7))' >/dev/null 2>&1 && exit 0; r='[freeze] Safety runtime unavailable; blocked, fail closed.';; *) r='[freeze][WINDOWS ONLY] The SimonK safety runtime supports Windows only, so on this OS every Edit and Write is blocked on purpose (fail closed). This is not a verdict on the edit. /unfreeze cannot lift it here: the boundary state it clears exists only on Windows. Way out: start a new session without /freeze, /guard and /investigate, or run /plugin disable simonk-stack@simonk-stack and then start a new session.';; esac; printf '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"%s\"}}\\n' \"$r\"; printf '%s\\n' \"$r\" >&2; exit 2"
        - type: command
          command: "python"
          args: ["-B", "${CLAUDE_PLUGIN_ROOT}/.simonk-runtime/safety_runtime.py", "check", "freeze", "--project", "${CLAUDE_PROJECT_DIR}"]
          statusMessage: "Checking freeze boundary..."
---

# /guard — Full Safety Mode

Activates both destructive command warnings and directory-scoped edit restrictions.
This is the combination of `/careful` + `/freeze` in a single command.

Based on gstack 1.91.9 `/guard` (MIT, Garry Tan). SimonK runs the hook scripts
of its own `careful` and `freeze` skills through `$HOME`-anchored commands
(hub decisions D-56 and D-62, 2026-10-03).

**Candidate dependency:** This plugin carries reviewed safety runtime resources.
Python and Git Bash are required; native host activation remains unverified.

```bash
mkdir -p ~/.gstack/analytics
echo '{"skill":"guard","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","repo":"'$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "unknown")'"}'  >> ~/.gstack/analytics/skill-usage.jsonl 2>/dev/null || true
```

## Setup

Windows에서 investigate 잠금 금지. 편집이 전부 막히면 /unfreeze.

Ask the user which directory to restrict edits to. Use AskUserQuestion:

- Question: "Guard mode: which directory should edits be restricted to? Destructive command warnings are always on. Files outside the chosen path will be blocked from editing."
- Text input (not multiple choice) — the user types a path.

Once the user provides a directory path:

Use only an existing, one-line absolute Windows directory. Replace the
boundary placeholder in the raw-data block below; do not paste arbitrary
multi-line text or shell code. Leave host placeholders for the host to render.
If the launcher fails, STOP: do not report that the boundary is active.

```bash
python -B -c 'import ctypes,os,pathlib,runpy,sys; rows=sys.stdin.read(32769).splitlines(); len(rows)==4 or sys.exit(2); root=pathlib.Path(rows[0]); (os.name=="nt" and root.is_absolute() and len(root.drive)==2 and root.drive[0].isascii() and root.drive[0].isalpha() and root.drive[1]==":") or sys.exit(2); ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(root.anchor))==3 or sys.exit(2); target=root/".simonk-runtime"/"safety_runtime.py"; sys.argv=[str(target),"set","--project",rows[1],"--session",rows[2]]+["--boundary",rows[3]]; runpy.run_path(str(target),run_name="__main__")' <<'SIMONK_SAFETY_INPUT'
${CLAUDE_PLUGIN_ROOT}
${CLAUDE_PROJECT_DIR}
${CLAUDE_SESSION_ID}
<absolute-existing-Windows-directory>
SIMONK_SAFETY_INPUT
```

Tell the user:
- "**Guard mode active.** Two protections are now running:"
- "1. **Destructive command checks** — HIGH commands (rm -r of / or ~, force-push to the default branch) are blocked; MEDIUM ones (rm -rf, DROP TABLE, git reset --hard, ...) ask first."
- "2. **Edit boundary** — file edits restricted to `<path>/`. Edits outside this directory are blocked."
- "To remove the edit boundary, run `/unfreeze`. To deactivate everything, end the session."

## 결정 표 (Decision table)

| Tool | Case | Decision |
|------|------|----------|
| Bash | safe command | allow |
| Bash | MEDIUM destructive family (see `/careful`) | `ask` (confirmation prompt) |
| Bash | HIGH: simple `rm -r` of `/`, `~`, `$HOME`; force-push to the default branch | `deny` |
| Bash | careful hook failure (bad payload, missing helper, ...) | `deny` |
| Edit/Write | inside the boundary, or no boundary set | allow |
| Edit/Write | outside the boundary, in any path form or letter case | `deny` |
| Edit/Write | relative, UNC, `..`, missing parent, failed conversion | `deny` |
| Edit/Write | freeze hook failure or invalid state | `deny` |

Full rules: `/careful` for commands, `/freeze` for the edit boundary.

## Measured facts (2026-10-03, this machine, Claude Code bypassPermissions)

1. `${CLAUDE_SKILL_DIR}` is unset in frontmatter hooks, so the gstack form
   `bash ${CLAUDE_SKILL_DIR}/../careful/bin/check-careful.sh` never ran and was
   non-blocking. The commands above are anchored to `$HOME` instead.
2. `deny` blocks the call; `ask` shows a confirmation prompt (both measured in
   bypassPermissions mode).
3. Edit/Write send Windows paths (`C:\...`); `/freeze` normalizes them.

## Install and gstack setup ownership

No gstack banner and no `.gstack-owned` marker, so gstack `./setup` prints
"skipped guard: existing entry is not gstack-managed" and leaves this folder
alone. Do not add the marker.

## Verify

```bash
# <freeze-dir>, <careful-dir> = 각 스킬 폴더. guard 자체 테스트는 없다.
# 플러그인 빌드에서는 careful 이 다른 플러그인(SimonKCore)에 있으니 형제 경로로 짐작하지 않는다.
python -B <freeze-dir>/bin/test_check_freeze.py     # freeze + guard wiring
python -B <careful-dir>/bin/test_check_careful.py   # careful hook
```

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
