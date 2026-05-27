---
name: designmd-upgrade
description: >
  Use when the user wants to update the vendored design.md stack — triggers "design.md 최신화", "디자인 md 업데이트", "upgrade design.md", "update design-md", or /designmd-upgrade. design.md is Google Labs design-as-markdown spec format, vendored at ~/.simon-stack/vendor/design.md/ with .git preserved so it can be pulled in place. Wraps scripts/upgrade-vendor.sh which handles fresh clone if missing, safe ff-only pull if behind, and skips when tree is dirty or on a non-default branch. Different from /stack-update (holistic — this is single-stack only). Different from /gstack-upgrade (targets a different upstream — Garry Tan's gstack).
version: 1.0.0
allowed-tools:
  - Bash
---

# /designmd-upgrade

Upgrade the vendored `design.md` stack at `~/.simon-stack/vendor/design.md/`.

## When to use

- User says any of: "design.md 최신화", "디자인 md 업데이트", "upgrade design.md", "update design-md"
- User asks "is design.md up to date?"
- Called by `/stack-update` as one step of a holistic refresh.

## What it does

Wraps `upgrade-vendor.sh design.md` which:

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
bash "$SCRIPT" "design.md"
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

`https://github.com/google-labs-code/design.md`

## Related skills

- `/stack-update` — full holistic SimonK Stack refresh (calls this skill + 4 siblings + gstack-upgrade + SimonK-stack pull + Wiki pull + install.sh --force)
- `/gstack-upgrade` — gstack-only upgrade
- Sibling vendor upgrades: `/omc-upgrade`, `/omo-upgrade`, `/openharness-upgrade`, `/opencowork-upgrade`, `/designmd-upgrade`

## Independence note

SimonK Stack uses design.md but operates independently — failure to upgrade
design.md does NOT block any SimonK skill from working. Treat this as a
best-effort sync.
