---
name: stack-update
description: >
  Use when the user wants to fully refresh the entire SimonK Stack — triggers
  "SimonK stack 최신화", "스택 업데이트", "전체 최신화", "stack 다 받아", "update
  the stack", "refresh everything", "/stack-update", or any holistic update
  phrasing where the user clearly means MORE than just gstack. Orchestrates
  five concerns in order: (1) SimonK-stack repo git pull, (2) SimonKWiki /
  Simon-LLM-Wiki git pull, (3) /gstack-upgrade for the gstack runtime, (4)
  five vendored external stacks via /omc-upgrade /omo-upgrade
  /openharness-upgrade /opencowork-upgrade /designmd-upgrade, (5) scripts/
  install.sh --force to land any new skills into ~/.claude/skills/. Produces
  a per-step summary with commits-pulled counts and a final state report.
  Different from /gstack-upgrade (gstack only) and from each /*-upgrade
  sibling (single-stack only).
version: 1.0.0
allowed-tools:
  - Bash
  - Read
---

# /stack-update

Holistic refresh entry point for the entire SimonK Stack ecosystem.

## Why this exists

`/gstack-upgrade` only updates gstack. SimonK-stack itself and the wiki rely
on the SessionStart hook auto-pull, which only fires once per session start.
If the user is mid-session and says "최신화", they expect a real refresh, not
a partial one. This skill closes that gap.

SimonK Stack is the **independent operator**. It uses other stacks (gstack,
oh-my-claudecode, oh-my-openagent, OpenHarness, open-cowork, design.md) but
none of those is required for SimonK skills to function. Each upgrade step
below is best-effort — failure in one does not abort the rest.

## Execution sequence

Each step prints a one-line summary. Roll the summaries up into a final
report at the end.

### 1. SimonK-stack core (this repo)

```bash
cd "${CLAUDE_PROJECT_DIR:-$PWD}"
BEFORE=$(git rev-parse --verify HEAD 2>/dev/null || echo unknown)
git fetch --quiet origin 2>/dev/null
BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo HEAD)
DIRTY=$(git status --porcelain | wc -l | tr -d ' ')
BEHIND=$(git rev-list HEAD..@{u} --count 2>/dev/null || echo 0)
if [ "$BRANCH" = "main" ] && [ "$DIRTY" = "0" ] && [ "$BEHIND" -gt 0 ]; then
  git pull --ff-only --quiet && echo "[simon-stack] ✓ pulled $BEHIND commit(s)"
elif [ "$BEHIND" = "0" ]; then
  echo "[simon-stack] ✓ up to date"
else
  echo "[simon-stack] ✗ $BEHIND behind but branch='$BRANCH' dirty=$DIRTY — manual"
fi
```

### 2. Wiki (SimonKWiki primary, Simon-LLM-Wiki legacy)

Locate the vault by the same probe order as `user-prompt-submit.sh`:

```bash
WIKI=""
for cand in \
  "${SIMON_WIKI_DIR:-}" \
  "$HOME/.claude/wiki/SimonKWiki" \
  "$HOME/SimonKWiki" \
  "E:/Coding Infra/obsidian/SimonKWiki" \
  */obsidian/SimonKWiki \
  "$HOME/.claude/wiki/Simon-LLM-Wiki" \
  "$HOME/Simon-LLM-Wiki"; do
  [ -d "$cand/.git" ] && WIKI="$cand" && break
done

if [ -n "$WIKI" ]; then
  cd "$WIKI"
  git fetch --quiet origin 2>/dev/null
  BEHIND=$(git rev-list HEAD..@{u} --count 2>/dev/null || echo 0)
  DIRTY=$(git status --porcelain | wc -l | tr -d ' ')
  if [ "$DIRTY" = "0" ] && [ "$BEHIND" -gt 0 ]; then
    git pull --ff-only --quiet && echo "[wiki] ✓ pulled $BEHIND commit(s) from $(basename $WIKI)"
  elif [ "$BEHIND" = "0" ]; then
    echo "[wiki] ✓ up to date ($(basename $WIKI))"
  else
    echo "[wiki] ✗ $BEHIND behind, dirty=$DIRTY — manual"
  fi
else
  echo "[wiki] ⚠ no wiki vault found (skipping)"
fi
```

### 3. gstack — delegate to /gstack-upgrade

Invoke the existing skill instead of duplicating its logic:

> Call `/gstack-upgrade` and capture its summary.

If `/gstack-upgrade` is not available (e.g., user disabled it via "Never ask
again"), report `[gstack] ⚠ skipped — /gstack-upgrade disabled` and continue.

### 4. Vendored external stacks (5)

Run each sibling skill in order. Each wraps `scripts/upgrade-vendor.sh <name>`:

```bash
# Resolve shared upgrade-vendor.sh (canonical: ~/.claude/scripts/, fallback to repo).
SCRIPT="$HOME/.claude/scripts/upgrade-vendor.sh"
[ -x "$SCRIPT" ] || SCRIPT="${CLAUDE_PROJECT_DIR:-$PWD}/scripts/upgrade-vendor.sh"
[ -x "$SCRIPT" ] || SCRIPT="${CLAUDE_PROJECT_DIR:-$PWD}/.claude/scripts/upgrade-vendor.sh"

for vendor in oh-my-claudecode oh-my-openagent OpenHarness open-cowork design.md; do
  bash "$SCRIPT" "$vendor"
done
```

The script prints one line per vendor. Collect them.

### 5. Re-install skills into ~/.claude/skills/

After SimonK-stack got pulled in step 1, the on-disk SKILL.md files may have
changed. Force-reinstall so the changes land in the user's global skill dir:

```bash
# install.sh lives only in the simon-stack repo proper (not vendored).
# In vendor-mode target repos, it's not present — skip that step there.
INSTALL_SH="${CLAUDE_PROJECT_DIR:-$PWD}/scripts/install.sh"
if [ -x "$INSTALL_SH" ]; then
  "$INSTALL_SH" --force --no-backup 2>&1 \
    | grep -E "simon-stack: installed|Skills:|Install complete" | head -5
else
  echo "[install] ⚠ scripts/install.sh not in this repo — skill re-sync deferred to next SessionStart"
fi
```

If the user has a customized `~/.claude/CLAUDE.md`, omit `--force` for that
file — `install.sh` already handles the backup-then-overwrite policy.

## Final report format

Roll up all step summaries into a single message to the user:

```
SimonK Stack 최신화 결과:

[simon-stack] ✓ pulled 3 commit(s)
[wiki]        ✓ up to date (SimonKWiki)
[gstack]      ✓ pulled 7 commit(s)
[omc]         ✓ pulled 1 commit(s)
[omo]         ✓ up to date
[openharness] ✓ up to date
[opencowork]  ✗ on branch 'feature/x' — skipped for safety
[designmd]    ✓ up to date
[install]     ✓ 110 skills resynced via install.sh --force

총 4 개 stack 갱신, 1 개 수동 처리 필요.
```

## Safety

This skill performs **read + ff-only writes** to repos under user control. It
never:

- Force-pushes
- Resets hard
- Touches branches that aren't the default
- Pulls into a dirty working tree

If a sub-step reports an unsafe condition (exit 3 from `upgrade-vendor.sh`,
or `BEHIND>0` with `DIRTY>0` for any repo), the orchestrator includes the
reason in the final report and the user resolves manually.

## Related skills

- `/gstack-upgrade` — gstack-only (step 3 of this skill).
- `/omc-upgrade`, `/omo-upgrade`, `/openharness-upgrade`, `/opencowork-upgrade`, `/designmd-upgrade` — individual vendored stack upgrades (step 4).
- `scripts/install.sh` — used in step 5; can be invoked manually anytime.

## Why not auto-run?

Because the user expressly invoking `/stack-update` is the gate. The
SessionStart hook already auto-pulls SimonK-stack + Wiki when safe at the
start of every session (see CLAUDE.md `## 🚀 세션 시작 정책`). This skill is
the **mid-session** counterpart for when the user wants a refresh without
restarting.
