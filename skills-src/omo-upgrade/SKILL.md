---
name: omo-upgrade
description: >
  Use when the user wants to update the vendored oh-my-openagent stack — triggers "OMO 최신화", "오마이오픈에이전트 업데이트", "upgrade omo", "update oh-my-openagent", or /omo-upgrade. oh-my-openagent is model-agnostic agent orchestrator (Claude/GPT/Kimi/GLM/Gemini), vendored at ~/.simon-stack/vendor/oh-my-openagent/ with .git preserved so it can be pulled in place. Wraps scripts/upgrade-vendor.sh which handles fresh clone if missing, safe ff-only pull if behind, and skips when tree is dirty or on a non-default branch. Different from /stack-update (holistic — this is single-stack only). Different from /gstack-upgrade (targets a different upstream — Garry Tan's gstack).
version: 1.0.0
allowed-tools:
  - Bash
---

# /omo-upgrade

Upgrade the vendored `oh-my-openagent` stack at `~/.simon-stack/vendor/oh-my-openagent/`.

## When to use

- User says any of: "OMO 최신화", "오마이오픈에이전트 업데이트", "upgrade omo", "update oh-my-openagent"
- User asks "is oh-my-openagent up to date?"
- Called by `/stack-update` as one step of a holistic refresh.

## What it does

Wraps `upgrade-vendor.sh oh-my-openagent` which:

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
bash "$SCRIPT" "oh-my-openagent"
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

`https://github.com/code-yeongyu/oh-my-openagent`

## Related skills

- `/stack-update` — full holistic SimonK Stack refresh (calls this skill + 4 siblings + gstack-upgrade + SimonK-stack pull + Wiki pull + install.sh --force)
- `/gstack-upgrade` — gstack-only upgrade
- Sibling vendor upgrades: `/omc-upgrade`, `/omo-upgrade`, `/openharness-upgrade`, `/opencowork-upgrade`, `/designmd-upgrade`

## Independence note

SimonK Stack uses oh-my-openagent but operates independently — failure to upgrade
oh-my-openagent does NOT block any SimonK skill from working. Treat this as a
best-effort sync.
