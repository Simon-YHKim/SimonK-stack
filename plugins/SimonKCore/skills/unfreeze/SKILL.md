---
name: unfreeze
version: 0.2.1
description: "Use when widening edit scope without ending the session, or asked to \"unfreeze\", \"unlock edits\", \"remove freeze\", \"allow all edits\", \"잠금 해제\", \"편집 제한 풀어\". Clears the boundary set by /freeze or /guard through the shared freeze-state.sh writer, which produces FREEZE_CLEARED, or FREEZE_BUSY with nothing changed while another writer holds the lock."
allowed-tools:
  - Bash
  - Read
---

# /unfreeze — Clear Freeze Boundary

Remove the edit restriction set by `/freeze` or `/guard`, allowing edits to all
directories.

Based on gstack 1.91.9 `/unfreeze` (MIT, Garry Tan). It uses the state writer of
the SimonK `/freeze` skill (hub decision D-62, 2026-10-03): in a flat install
`~/.claude/skills/freeze/bin/freeze-state.sh`, so `freeze` must be installed
there; in the plugin build, the safety runtime that ships with the plugin.

```bash
mkdir -p ~/.gstack/analytics
echo '{"skill":"unfreeze","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","repo":"'$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "unknown")'"}'  >> ~/.gstack/analytics/skill-usage.jsonl 2>/dev/null || true
```

## Clear the boundary

```bash
python -B -c 'import ctypes,os,pathlib,runpy,sys; rows=sys.stdin.read(32769).splitlines(); len(rows)==3 or sys.exit(2); root=pathlib.Path(rows[0]); (os.name=="nt" and root.is_absolute() and len(root.drive)==2 and root.drive[0].isascii() and root.drive[0].isalpha() and root.drive[1]==":") or sys.exit(2); ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(root.anchor))==3 or sys.exit(2); target=root/".simonk-runtime"/"safety_runtime.py"; sys.argv=[str(target),"clear","--project",rows[1],"--session",rows[2]]; runpy.run_path(str(target),run_name="__main__")' <<'SIMONK_SAFETY_INPUT'
${CLAUDE_PLUGIN_ROOT}
${CLAUDE_PROJECT_DIR}
${CLAUDE_SESSION_ID}
SIMONK_SAFETY_INPUT
```

Tell the user the result. Note that `/freeze` hooks are still registered for the
session — only an explicit inactive tombstone permits edits. Missing state denies. To re-freeze,
run `/freeze` again.

## 결정 표 (Decision table)

| State before | Output | Boundary after |
|--------------|--------|----------------|
| boundary set (any writer) | `FREEZE_CLEARED` | none: hooks allow every edit |
| no boundary | `FREEZE_CLEARED` | none |
| lock held by another writer | `FREEZE_BUSY` | unchanged |
| state is a symlink or directory | `FREEZE_PRESERVED` | unchanged; edits stay denied |

The clear is unconditional for a regular state file: an owner token written by
another run (for example an investigation scope) is removed as well, because
the user asked for it.

## Install and gstack setup ownership

No gstack banner and no `.gstack-owned` marker, so gstack `./setup` prints
"skipped unfreeze: existing entry is not gstack-managed" and leaves this folder
alone. Do not add the marker.

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
