---
name: freeze
version: 0.2.2
description: "Use when debugging to keep edits inside one module, or asked to \"freeze\", \"restrict edits\", \"only edit this folder\", \"lock down edits\", \"이 폴더만 수정\", \"편집 잠금\". Sets a session edit boundary: a PreToolUse Edit/Write hook produces deny for paths outside the chosen directory and for paths it cannot judge (relative, UNC, '..', failed conversion), handling Windows drive paths and /c/ paths."
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
hooks:
  PreToolUse:
    - matcher: "Edit"
      hooks:
        - type: command
          command: 'bash "$HOME/.claude/skills/freeze/bin/check-freeze.sh"'
          statusMessage: "Checking freeze boundary..."
    - matcher: "Write"
      hooks:
        - type: command
          command: 'bash "$HOME/.claude/skills/freeze/bin/check-freeze.sh"'
          statusMessage: "Checking freeze boundary..."
---

# /freeze — Restrict Edits to a Directory

Lock file edits to one directory. Any Edit or Write outside it is **denied**
(blocked, not warned), and so is any path the hook cannot judge.

Based on gstack 1.91.9 `/freeze` (MIT, Garry Tan): its hook and its shared state
writer `bin/freeze-state.sh` (vendored unchanged). SimonK adds the Windows path
handling and fail-closed deltas below (hub decision D-62, 2026-10-03).

```bash
mkdir -p ~/.gstack/analytics
echo '{"skill":"freeze","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","repo":"'$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "unknown")'"}'  >> ~/.gstack/analytics/skill-usage.jsonl 2>/dev/null || true
```

## Setup

Windows에서 investigate 잠금 금지. 편집이 전부 막히면 /unfreeze.

Ask the user which directory to restrict edits to. Use AskUserQuestion:

- Question: "Which directory should I restrict edits to? Files outside this path will be blocked from editing."
- Text input (not multiple choice) — the user types a path.

Once the user provides a directory path:

1. Check that both hook folders are installed. A hook whose script is missing
cannot start, and a hook that cannot start does not block anything:
```bash
for f in freeze/bin/check-freeze.sh freeze/bin/freeze-state.sh careful/bin/hook-extract.sh careful/bin/check-careful.sh; do [ -f "$HOME/.claude/skills/$f" ] || echo "FREEZE_MISSING: ~/.claude/skills/$f"; done
```
If anything printed `FREEZE_MISSING`, stop: tell the user the boundary would
not be enforced until `careful` and `freeze` are installed under
`~/.claude/skills`, and do not run step 2.

2. Record the boundary with the shared state writer. Put the path on the line
between the markers exactly as the user typed it (`C:\...`, `C:/...` or
`/c/...`); the quoted heredoc keeps spaces, `$`, quotes and a trailing
backslash literal:
```bash
IFS= read -r FREEZE_INPUT <<'FREEZE_PATH'
<user-provided-path>
FREEZE_PATH
bash "$HOME/.claude/skills/freeze/bin/freeze-state.sh" set "$FREEZE_INPUT"
```

3. Read the result before telling the user anything:
   - `FREEZE_DIR=<dir>` (exit 0): the boundary is active at `<dir>/`.
   - `FREEZE_BUSY: ...` (exit 1): another writer holds the state lock and
     nothing changed. Say the boundary is NOT set and retry once. If it
     repeats, show the user the `.freeze-mutation.lock` directory next to
     `freeze-dir.txt` (default `~/.gstack/`) and let them decide before anyone
     removes it.
   - Any other failure (`No such file or directory`, exit 2): NOT set. Ask for
     an existing directory.

Tell the user: "Edits are now restricted to `<path>/`. Any Edit or Write
outside this directory will be blocked. To change the boundary, run `/freeze`
again. To remove it, run `/unfreeze` or end the session."

## 결정 표 (Decision table)

| Case | Decision |
|------|----------|
| No state file (never frozen, or `/unfreeze` ran) | allow (`{}`) |
| Path inside the boundary, or the boundary itself | allow |
| New file whose parent directory exists inside the boundary | allow |
| Path outside the boundary (also when the session cwd is inside it) | `deny` |
| Same path in `C:\`, `C:/`, `/c/` or `/tmp`-alias form, any letter case | same decision |
| Relative, drive-relative (`C:x`) or root-relative (`\x`) path | `deny` (no cwd guess) |
| UNC or device path, or a `..` segment | `deny` |
| Parent directory does not exist yet | `deny` (create it, then retry) |
| Final component is a symlink | the target is judged; a loop denies |
| `cygpath` fails to convert or canonicalize | `deny` |
| Missing, empty or non-string `file_path`; invalid JSON; no `python3`/`node` | `deny` |
| State is a symlink, directory, unreadable, empty, or names a missing directory | `deny` |
| `careful/bin/hook-extract.sh` missing, broken or outdated; unexpected error | `deny` |

Every deny names the path and the reason. The way out of a wrong boundary is
`/freeze` again or `/unfreeze`.

## How it works

The hook reads `file_path` from the Edit/Write payload and the boundary from
line 1 of `freeze-dir.txt` under `${CLAUDE_PLUGIN_DATA:-$HOME/.gstack}` (the
same root `freeze-state.sh` writes; line 2 is its `gstack-freeze-v1:` owner
token). Both go through one pipeline:

1. Windows drive paths (`C:\...`, `C:/...`) become `/c/...` with `cygpath -u`;
   without `cygpath` a pure-bash conversion does the same. `/c/...` and other
   MSYS paths are taken as they are.
2. The parent directory is resolved physically (`cd` + `pwd -P`). Git Bash can
   name one folder `/tmp/...` or `/c/Users/.../Temp/...`, so with `cygpath`
   the result is folded to one `C:/...` key (`cygpath -am`).
3. On Windows the keys are compared case-insensitively; the trailing `/`
   keeps `/src` from matching `/src-old`.

Without `cygpath` the `/tmp` alias cannot be folded, so such a mismatch denies.

## Measured facts (2026-10-03, this machine, Claude Code bypassPermissions)

1. In a skill frontmatter hook `${CLAUDE_SKILL_DIR}` is unset: the gstack form
   `bash ${CLAUDE_SKILL_DIR}/bin/check-freeze.sh` never ran, and a hook that
   fails to start is non-blocking (fail-open). Hence the commands above run
   this skill's own installed copy at `~/.claude/skills/freeze`.
2. A hook `deny` blocks the call in bypassPermissions mode.
3. Edit/Write send `file_path` as a Windows absolute path (`C:\Users\...`).
   The installed gstack hook saw no leading `/`, joined it to the cwd and
   allowed out-of-boundary edits whenever the cwd was inside the boundary.

## Install and gstack setup ownership

- `bin/` holds `check-freeze.sh` (hook), `freeze-state.sh` (gstack state
  writer, vendored unchanged except an attribution header), `safety_runtime.py`
  (plugin candidate only) and the offline test `test_check_freeze.py`. The hook
  and the writer source `~/.claude/skills/careful/bin/hook-extract.sh`, so
  `careful` must be installed next to `freeze`.
- This SKILL.md carries **no** gstack gen-skill-docs banner and the folder has
  no `.gstack-owned` marker. gstack `./setup` treats an existing folder as its
  own only with that marker, a SKILL.md symlinked into gstack, a SKILL.md
  byte-identical to gstack's, or that banner; otherwise it prints "skipped
  freeze: existing entry is not gstack-managed" and leaves it untouched. Do not
  add a `.gstack-owned` file here, or setup will overwrite this skill.

## Verify

```bash
python -B skills-src/freeze/bin/test_check_freeze.py   # needs Git Bash on Windows
```

## Notes

- Covers the Edit and Write tools only. Read, Bash, PowerShell, Glob, Grep and
  NotebookEdit are not checked, so `sed` or a script can still change files
  outside the boundary. This prevents accidental edits; it is not a security
  boundary.
- On Windows the comparison is case-insensitive even inside a folder marked
  case-sensitive (WSL style).
- `/unfreeze` clears the boundary; the hooks stay registered for the session
  and allow everything while no state file exists.

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
