---
name: unfreeze
version: 0.2.0
description: "Use when widening edit scope without ending the session, or asked to \"unfreeze\", \"unlock edits\", \"remove freeze\", \"allow all edits\", \"잠금 해제\", \"편집 제한 풀어\". Clears the boundary set by /freeze or /guard through the shared freeze-state.sh writer, which produces FREEZE_CLEARED, or FREEZE_BUSY with nothing changed while another writer holds the lock."
allowed-tools:
  - Bash
  - Read
---

# /unfreeze — Clear Freeze Boundary

Remove the edit restriction set by `/freeze` or `/guard`, allowing edits to all
directories.

Based on gstack 1.91.9 `/unfreeze` (MIT, Garry Tan). It uses the state writer of
the SimonK `/freeze` skill, `~/.claude/skills/freeze/bin/freeze-state.sh`
(hub decision D-62, 2026-10-03), so `freeze` must be installed there.

```bash
mkdir -p ~/.gstack/analytics
echo '{"skill":"unfreeze","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","repo":"'$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "unknown")'"}'  >> ~/.gstack/analytics/skill-usage.jsonl 2>/dev/null || true
```

## Clear the boundary

```bash
bash "$HOME/.claude/skills/freeze/bin/freeze-state.sh" clear
```

Read the result before telling the user anything:
- `FREEZE_CLEARED: ...` (exit 0): edits are allowed everywhere again.
- `FREEZE_BUSY: ...` (exit 1): another writer holds the state lock, so the
  boundary is still active. Say so and retry once; if it repeats, show the
  user the `.freeze-mutation.lock` directory next to `freeze-dir.txt`
  (default `~/.gstack/`) and let them decide before anyone removes it.
- `FREEZE_PRESERVED: unexpected state type ...` (exit 1): `freeze-dir.txt` is
  a symlink or a directory and was left in place. Show it to the user; do not
  delete it on your own.
- `No such file or directory`: `/freeze` is not installed at
  `~/.claude/skills/freeze`; nothing was cleared.

Tell the user the result. Note that `/freeze` hooks are still registered for the
session — they will just allow everything since no state file exists. To re-freeze,
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
