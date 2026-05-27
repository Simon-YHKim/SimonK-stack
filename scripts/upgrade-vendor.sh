#!/usr/bin/env bash
# upgrade-vendor.sh — shared upgrade logic for vendored external stacks.
#
# Usage:
#   ./scripts/upgrade-vendor.sh <name>
#
# <name> must match a row in the VENDOR_LIST (oh-my-claudecode, oh-my-openagent,
# OpenHarness, open-cowork, design.md). Looks up the upstream URL, ensures the
# user-level live clone at ~/.simon-stack/vendor/<name>/, fetches and ff-pulls
# when safe, prints a one-line summary suitable for the LLM to relay.
#
# Exit codes:
#   0 = up to date or successfully pulled
#   1 = unknown vendor name / no upstream registered
#   2 = clone failed (offline or upstream gone)
#   3 = unsafe to pull (dirty tree or non-default branch)

set -uo pipefail

NAME="${1:-}"
if [ -z "$NAME" ]; then
  echo "ERROR: vendor name required" >&2
  echo "usage: $0 <oh-my-claudecode|oh-my-openagent|OpenHarness|open-cowork|design.md>" >&2
  exit 1
fi

# Single source of truth — must match VENDOR_LIST in .claude/hooks/session-start.sh
VENDOR_REGISTRY="oh-my-claudecode|https://github.com/Yeachan-Heo/oh-my-claudecode
oh-my-openagent|https://github.com/code-yeongyu/oh-my-openagent
OpenHarness|https://github.com/HKUDS/OpenHarness
open-cowork|https://github.com/OpenCoworkAI/open-cowork
design.md|https://github.com/google-labs-code/design.md"

URL=$(echo "$VENDOR_REGISTRY" | awk -F'|' -v n="$NAME" '$1 == n { print $2 }')
if [ -z "$URL" ]; then
  echo "ERROR: unknown vendor '$NAME'" >&2
  echo "Known: oh-my-claudecode, oh-my-openagent, OpenHarness, open-cowork, design.md" >&2
  exit 1
fi

VENDOR_DIR="$HOME/.simon-stack/vendor"
mkdir -p "$VENDOR_DIR" 2>/dev/null || true
TARGET="$VENDOR_DIR/$NAME"

# Fresh clone path
if [ ! -d "$TARGET/.git" ]; then
  echo "[$NAME] fresh clone from $URL"
  if git clone --depth 1 "$URL" "$TARGET" 2>&1 | tail -3; then
    echo "[$NAME] ✓ cloned"
    exit 0
  else
    echo "[$NAME] ✗ clone failed — check network or upstream availability"
    exit 2
  fi
fi

# Existing clone — safe fetch + ff-only pull
cd "$TARGET" || exit 2

if ! git fetch --quiet origin 2>/dev/null; then
  echo "[$NAME] ✗ fetch failed (offline?)"
  exit 2
fi

BEHIND=$(git rev-list HEAD..@{u} --count 2>/dev/null || echo 0)
if [ "$BEHIND" = "0" ]; then
  echo "[$NAME] ✓ up to date"
  exit 0
fi

DIRTY=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo HEAD)
DEFAULT=$(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null | sed 's|^origin/||' || echo main)

if [ "$DIRTY" != "0" ]; then
  echo "[$NAME] ✗ $BEHIND behind but tree is dirty ($DIRTY local changes) — skipping for safety"
  exit 3
fi

if [ "$BRANCH" != "$DEFAULT" ] && [ -n "$DEFAULT" ]; then
  echo "[$NAME] ✗ $BEHIND behind but on branch '$BRANCH' (default: '$DEFAULT') — skipping for safety"
  exit 3
fi

if git pull --ff-only --quiet 2>/dev/null; then
  echo "[$NAME] ✓ pulled $BEHIND commit(s)"
  exit 0
else
  echo "[$NAME] ✗ $BEHIND behind, ff-only pull failed (history diverged?) — manual resolution needed"
  exit 3
fi
