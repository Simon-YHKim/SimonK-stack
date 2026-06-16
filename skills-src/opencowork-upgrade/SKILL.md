---
name: opencowork-upgrade
description: >
  Use when the user wants to update the vendored open-cowork stack — triggers "OpenCowork 최신화", "오픈코워크 업데이트", "upgrade open-cowork", "update opencowork", or /opencowork-upgrade. open-cowork is OpenCoworkAI coworking-mode agent stack, vendored at ~/.simon-stack/vendor/open-cowork/ with .git preserved so it can be pulled in place. Wraps scripts/upgrade-vendor.sh which handles fresh clone if missing, safe ff-only pull if behind, and skips when tree is dirty or on a non-default branch. Different from /stack-update (holistic — this is single-stack only). Different from /gstack-upgrade (targets a different upstream — Garry Tan's gstack).
version: 1.0.0
allowed-tools:
  - Bash
---

# /opencowork-upgrade

Upgrade the vendored `open-cowork` stack at `~/.simon-stack/vendor/open-cowork/`.

## When to use

- User says any of: "OpenCowork 최신화", "오픈코워크 업데이트", "upgrade open-cowork", "update opencowork"
- User asks "is open-cowork up to date?"
- Called by `/stack-update` as one step of a holistic refresh.

## What it does

Wraps `upgrade-vendor.sh open-cowork` which:

1. **Missing?** Fresh `git clone --depth 1` from upstream.
2. **Present?** `git fetch origin`, count commits behind upstream.
3. **Behind?** If tree is clean AND on the default branch, `git pull --ff-only`.
4. **Unsafe?** Reports the reason (dirty / non-default-branch / diverged history) and stops without touching anything.

## Execution

Resolve the shared script (it gets copied to a stable location by
`install.sh` / `setup-repo.sh` / SessionStart hook) and invoke it:

```bash
SCRIPT="$HOME/.claude/scripts/upgrade-vendor.sh"
[ -x "$SCRIPT" ] || SCRIPT="${CLAUDE_PROJECT_DIR:-$PWD}/scripts/upgrade-vendor.sh"
[ -x "$SCRIPT" ] || SCRIPT="${CLAUDE_PROJECT_DIR:-$PWD}/.claude/scripts/upgrade-vendor.sh"
bash "$SCRIPT" "open-cowork"
```

Relay the script's one-line summary back to the user. Exit codes:

| Code | Meaning |
|------|---------|
| 0 | up to date or successfully pulled |
| 1 | unknown vendor name (should not happen for this skill) |
| 2 | clone or fetch failed (offline / upstream gone) |
| 3 | unsafe to pull (dirty / wrong branch / diverged) |

On exit 3, summarize the safety reason; do not attempt to force the pull
without explicit user confirmation.

## Upstream

`https://github.com/OpenCoworkAI/open-cowork`

## Related skills

- `/stack-update` — full holistic SimonK Stack refresh (calls this skill + 4 siblings + gstack-upgrade + SimonK-stack pull + Wiki pull + install.sh --force)
- `/gstack-upgrade` — gstack-only upgrade
- Sibling vendor upgrades: `/omc-upgrade`, `/omo-upgrade`, `/openharness-upgrade`, `/opencowork-upgrade`, `/designmd-upgrade`

## Independence note

SimonK Stack uses open-cowork but operates independently — failure to upgrade
open-cowork does NOT block any SimonK skill from working. Treat this as a
best-effort sync.

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
