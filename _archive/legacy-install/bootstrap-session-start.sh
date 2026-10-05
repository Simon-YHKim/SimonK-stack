#!/usr/bin/env bash
# simon-stack bootstrap — drop-in SessionStart hook for ANY Claude Code repo.
#
# What it does:
#   1. Clones or updates github.com/Simon-YHKim/SimonK-stack
#      into ~/.simon-stack-src (cached between hook invocations in the same session)
#   2. Delegates to that repo's .claude/hooks/session-start.sh which installs:
#      - Gstack runtime (~/.claude/skills/gstack/)
#      - 36 Gstack skills + 100+ simon-stack skills
#      - instincts seed files + global CLAUDE.md template
#
# Usage:
#   cp this file → <your-repo>/.claude/hooks/session-start.sh
#   chmod +x <your-repo>/.claude/hooks/session-start.sh
#   # also copy bootstrap-settings.json → .claude/settings.json
#
# Override upstream (e.g. fork):
#   SIMON_STACK_REPO=https://github.com/you/fork SIMON_STACK_REF=main ./session-start.sh

set -euo pipefail

# --- Optional async mode (disabled by default for determinism) ---
# echo '{"async": true, "asyncTimeout": 300000}'

SIMON_STACK_REPO="${SIMON_STACK_REPO:-https://github.com/Simon-YHKim/SimonK-stack}"
SIMON_STACK_REF="${SIMON_STACK_REF:-main}"
SIMON_STACK_DIR="${SIMON_STACK_DIR:-$HOME/.simon-stack-src}"

log() { echo "[simon-stack-bootstrap] $*"; }

log "host=${CLAUDE_PROJECT_DIR:-$(pwd)} remote=${CLAUDE_CODE_REMOTE:-false}"

# --- 1. Clone or update simon-stack ---
if [ ! -d "$SIMON_STACK_DIR/.git" ]; then
  log "Cloning simon-stack from $SIMON_STACK_REPO ($SIMON_STACK_REF)..."
  rm -rf "$SIMON_STACK_DIR"
  git clone --depth 1 --branch "$SIMON_STACK_REF" "$SIMON_STACK_REPO" "$SIMON_STACK_DIR" 2>&1 | tail -3
else
  log "Updating simon-stack ($SIMON_STACK_REF)..."
  (
    cd "$SIMON_STACK_DIR"
    git fetch --depth 1 origin "$SIMON_STACK_REF" 2>/dev/null || log "WARN: fetch failed, using cached"
    git reset --hard "origin/$SIMON_STACK_REF" 2>/dev/null || log "WARN: reset failed, using cached"
  )
fi

# --- 2. Delegate to simon-stack's session-start hook ---
# Force rerun by clearing the marker (optional — comment out to respect cache).
# rm -f ~/.claude/.simon-stack-installed

if [ -x "$SIMON_STACK_DIR/.claude/hooks/session-start.sh" ]; then
  log "Delegating to simon-stack session-start..."
  CLAUDE_PROJECT_DIR="$SIMON_STACK_DIR" bash "$SIMON_STACK_DIR/.claude/hooks/session-start.sh"
else
  log "ERROR: $SIMON_STACK_DIR/.claude/hooks/session-start.sh not found or not executable"
  exit 1
fi

log "✅ Bootstrap delegated. Skills available in ~/.claude/skills/"
exit 0
