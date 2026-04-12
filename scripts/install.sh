#!/usr/bin/env bash
# simon-stack installer — sets up Gstack + simon-stack skills globally.
#
# Usage:
#   ./scripts/install.sh         # full install
#   ./scripts/install.sh --dry   # show what would happen
#
# Idempotent: re-running is safe. Existing files are NOT overwritten.

set -euo pipefail

DRY=${1:-}
log() { echo "[simon-stack] $*"; }
run() { [ "$DRY" = "--dry" ] && echo "  + $*" || "$@"; }

log "Starting install..."

# ---- Prereqs ----
command -v git >/dev/null  || { echo "ERROR: git required"; exit 1; }
command -v bun >/dev/null  || log "WARN: bun not found — Gstack runtime will be skipped"
command -v node >/dev/null || log "WARN: node not found"

# ---- Backup ----
if [ -d ~/.claude ]; then
  BACKUP=~/.claude.bak-$(date +%Y%m%d-%H%M%S)
  log "Backing up ~/.claude → $BACKUP"
  run cp -a ~/.claude "$BACKUP"
fi

# ---- Directories ----
run mkdir -p ~/.claude/skills ~/.claude/instincts

# ---- Install Gstack ----
if [ ! -d ~/.claude/skills/gstack ]; then
  log "Cloning Gstack..."
  TMP=$(mktemp -d)
  run git clone --depth 1 https://github.com/garrytan/gstack "$TMP/gstack-src"
  run cp -a "$TMP/gstack-src" ~/.claude/skills/gstack
  run rm -rf "$TMP"

  if command -v bun >/dev/null; then
    log "Installing Gstack dependencies..."
    run bash -c "cd ~/.claude/skills/gstack && bun install"
  fi

  # Also expose individual Gstack skills at ~/.claude/skills/<name>/
  log "Linking individual Gstack skills..."
  for d in ~/.claude/skills/gstack/*/; do
    name=$(basename "$d")
    # skip non-skill dirs
    [ -f "$d/SKILL.md" ] || continue
    [ -e ~/.claude/skills/"$name" ] && continue
    run cp -r "$d" ~/.claude/skills/"$name"
  done
else
  log "Gstack already installed, skipping"
fi

# ---- Install simon-stack skills ----
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
log "Installing simon-stack skills from $REPO_DIR/.claude/skills/"
for d in "$REPO_DIR"/.claude/skills/*/; do
  name=$(basename "$d")
  [ -f "$d/SKILL.md" ] || continue
  if [ -e ~/.claude/skills/"$name" ]; then
    log "  skip (exists): $name"
    continue
  fi
  run cp -r "$d" ~/.claude/skills/"$name"
  log "  installed: $name"
done

# ---- Instincts seed ----
for f in mistakes-learned.md project-patterns.md korean-context.md tool-quirks.md; do
  if [ ! -f ~/.claude/instincts/"$f" ]; then
    if [ -f "$REPO_DIR/.claude/instincts/$f" ]; then
      run cp "$REPO_DIR/.claude/instincts/$f" ~/.claude/instincts/"$f"
      log "  seeded instincts: $f"
    fi
  fi
done

# ---- SessionStart hook ----
if [ -f "$REPO_DIR/scripts/session-start-instincts.sh" ] && [ ! -f ~/.claude/session-start-instincts.sh ]; then
  run cp "$REPO_DIR/scripts/session-start-instincts.sh" ~/.claude/session-start-instincts.sh
  run chmod +x ~/.claude/session-start-instincts.sh
  log "SessionStart hook installed"
  log "ACTION REQUIRED: add to ~/.claude/settings.json hooks.SessionStart:"
  log "  { \"matcher\": \"\", \"hooks\": [{ \"type\": \"command\", \"command\": \"~/.claude/session-start-instincts.sh\" }] }"
fi

# ---- Global CLAUDE.md ----
if [ ! -f ~/.claude/CLAUDE.md ] && [ -f "$REPO_DIR/templates/CLAUDE.md" ]; then
  log "Installing ~/.claude/CLAUDE.md from template"
  run cp "$REPO_DIR/templates/CLAUDE.md" ~/.claude/CLAUDE.md
fi

# ---- Skills INDEX ----
if [ -f "$REPO_DIR/.claude/skills/INDEX.md" ] && [ ! -f ~/.claude/skills/INDEX.md ]; then
  run cp "$REPO_DIR/.claude/skills/INDEX.md" ~/.claude/skills/INDEX.md
fi

log "✅ Install complete"
log ""
log "Next steps:"
log "  1. Restart Claude Code to load new skills"
log "  2. Try: '새 앱 만들고 싶어' → app-dev-orchestrator should trigger"
log "  3. Read: ~/.claude/skills/INDEX.md for the full skill map"
