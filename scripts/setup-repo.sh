#!/usr/bin/env bash
# setup-repo.sh — install simon-stack into ANY target repo.
#
# Two modes:
#   --mode vendor     (default) Copy all simon-stack skills + instincts +
#                     hook into the target repo. Self-contained, no network
#                     dependency at session start. Works even if this
#                     simon-stack repo is private.
#
#   --mode bootstrap  Drop a tiny 2-file hook into target repo that clones
#                     simon-stack at session start and delegates to its hook.
#                     Requires this simon-stack repo to be publicly accessible
#                     from the Claude Code web environment.
#
# Usage:
#   # From inside simon-stack repo:
#   ./scripts/setup-repo.sh /path/to/target-repo                  # vendor mode
#   ./scripts/setup-repo.sh --mode bootstrap /path/to/target-repo # bootstrap mode
#
#   # Defaults to current directory as target if no path given.
#
# After setup, opening the target repo in Claude Code web will auto-activate
# simon-stack on every session start.

set -euo pipefail

MODE="vendor"
TARGET=""

while [ $# -gt 0 ]; do
  case "$1" in
    --mode)
      MODE="$2"; shift 2 ;;
    --mode=*)
      MODE="${1#--mode=}"; shift ;;
    -h|--help)
      sed -n '1,35p' "$0" | grep '^#' | sed 's/^# \?//'
      exit 0 ;;
    *)
      TARGET="$1"; shift ;;
  esac
done

TARGET="${TARGET:-$PWD}"

if [ "$MODE" != "vendor" ] && [ "$MODE" != "bootstrap" ]; then
  echo "ERROR: --mode must be 'vendor' or 'bootstrap'"
  exit 1
fi

log() { echo "[setup-repo] $*"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SIMON_STACK_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ ! -d "$TARGET" ]; then
  log "ERROR: $TARGET is not a directory"
  exit 1
fi

log "Mode:   $MODE"
log "Source: $SIMON_STACK_DIR"
log "Target: $TARGET"

cd "$TARGET"
mkdir -p .claude/hooks .claude/skills .claude/instincts

# Backup helper
backup_if_exists() {
  local path="$1"
  if [ -e "$path" ] && [ ! -L "$path" ]; then
    cp -a "$path" "$path.bak-$(date +%s)" 2>/dev/null || true
    log "  backed up existing: $path"
  fi
}

# =============================================================================
# MODE: VENDOR
# =============================================================================
if [ "$MODE" = "vendor" ]; then
  log "--- vendor mode: copying all simon-stack files ---"

  # 1. Hook — vendor hook is a copy of simon-stack's session-start.sh but
  #    knows to look at the LOCAL .claude/ (target repo) as the source
  #    instead of cloning anything.
  cat > .claude/hooks/session-start.sh <<'HOOK_EOF'
#!/usr/bin/env bash
# simon-stack vendored SessionStart hook — self-contained.
# Installs simon-stack skills + Gstack runtime on every Claude Code web session.
# Reads simon-stack skills from THIS repo's .claude/skills/ (no network).
# Clones Gstack from upstream at session start.

set -euo pipefail

REPO_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
log() { echo "[simon-stack-vendor] $*"; }

log "Starting. repo=$REPO_DIR remote=${CLAUDE_CODE_REMOTE:-false}"

# Idempotency marker
MARKER=~/.claude/.simon-stack-installed
CURRENT_SHA=$(cd "$REPO_DIR" && git rev-parse --verify HEAD 2>/dev/null) || \
  CURRENT_SHA=vendor-$(cd "$REPO_DIR" && find .claude/skills -name SKILL.md -type f -exec stat -c %Y {} \; 2>/dev/null | md5sum | cut -c1-12)

if [ -f "$MARKER" ] && [ "$(cat "$MARKER" 2>/dev/null)" = "$CURRENT_SHA" ]; then
  log "Already installed at $CURRENT_SHA, skipping"
  exit 0
fi

mkdir -p ~/.claude/skills ~/.claude/instincts

# --- Gstack runtime (clone from upstream — public repo, always accessible) ---
if [ ! -d ~/.claude/skills/gstack ]; then
  log "Cloning Gstack..."
  TMP=$(mktemp -d)
  if git clone --depth 1 https://github.com/garrytan/gstack "$TMP/gstack-src" 2>&1 | tail -3; then
    cp -a "$TMP/gstack-src" ~/.claude/skills/gstack
    rm -rf "$TMP"
    if command -v bun >/dev/null 2>&1; then
      (cd ~/.claude/skills/gstack && bun install >/dev/null 2>&1) || log "WARN: bun install failed"
    fi
  else
    log "WARN: Gstack clone failed — continuing with local skills only"
    rm -rf "$TMP"
  fi
fi

# --- Expose individual Gstack skills ---
if [ -d ~/.claude/skills/gstack ]; then
  for d in ~/.claude/skills/gstack/*/; do
    name=$(basename "$d")
    [ -f "$d/SKILL.md" ] || continue
    [ -e ~/.claude/skills/"$name" ] && continue
    cp -r "$d" ~/.claude/skills/"$name"
  done
fi

# --- simon-stack skills from THIS repo ---
for src_dir in "$REPO_DIR"/skills-src "$REPO_DIR"/.claude/skills; do
  [ -d "$src_dir" ] || continue
  for d in "$src_dir"/*/; do
    name=$(basename "$d")
    [ -f "$d/SKILL.md" ] || continue
    [ -e ~/.claude/skills/"$name" ] && continue
    cp -r "$d" ~/.claude/skills/"$name"
  done
done

# --- INDEX + instincts + shared scripts ---
[ -f "$REPO_DIR/.claude/skills/INDEX.md" ] && [ ! -f ~/.claude/skills/INDEX.md ] && \
  cp "$REPO_DIR/.claude/skills/INDEX.md" ~/.claude/skills/INDEX.md

for f in mistakes-learned.md project-patterns.md korean-context.md tool-quirks.md; do
  [ -f "$REPO_DIR/.claude/instincts/$f" ] && [ ! -f ~/.claude/instincts/"$f" ] && \
    cp "$REPO_DIR/.claude/instincts/$f" ~/.claude/instincts/"$f"
done

# Shared scripts (upgrade-vendor.sh etc.) so SKILL.md absolute-path refs work.
mkdir -p ~/.claude/scripts
for s in upgrade-vendor.sh; do
  # Vendor mode keeps scripts in target's .claude/scripts/; fall back to
  # repo-level scripts/ for the standalone install case.
  for src in "$REPO_DIR/.claude/scripts/$s" "$REPO_DIR/scripts/$s"; do
    if [ -f "$src" ] && [ ! -f ~/.claude/scripts/"$s" ]; then
      cp "$src" ~/.claude/scripts/"$s"
      chmod +x ~/.claude/scripts/"$s"
      break
    fi
  done
done

# --- Global CLAUDE.md ---
if [ ! -f ~/.claude/CLAUDE.md ] && [ -f "$REPO_DIR/.claude/CLAUDE.md.template" ]; then
  cp "$REPO_DIR/.claude/CLAUDE.md.template" ~/.claude/CLAUDE.md
fi

# --- Marker ---
echo "$CURRENT_SHA" > "$MARKER"
log "✅ Bootstrap complete"
HOOK_EOF
  chmod +x .claude/hooks/session-start.sh
  log "✅ Hook installed: .claude/hooks/session-start.sh"

  # 2. Copy simon-stack skills (from both skills-src/ and .claude/skills/)
  copied=0
  for src_dir in "$SIMON_STACK_DIR"/skills-src "$SIMON_STACK_DIR"/.claude/skills; do
    [ -d "$src_dir" ] || continue
    for d in "$src_dir"/*/; do
      name=$(basename "$d")
      [ -f "$d/SKILL.md" ] || continue
      if [ -e ".claude/skills/$name" ]; then
        log "  skip (exists): $name"
        continue
      fi
      cp -r "$d" ".claude/skills/$name"
      copied=$((copied + 1))
    done
  done
  log "✅ Copied $copied skills to .claude/skills/"

  # 3. INDEX.md
  [ -f "$SIMON_STACK_DIR/.claude/skills/INDEX.md" ] && [ ! -f .claude/skills/INDEX.md ] && \
    cp "$SIMON_STACK_DIR/.claude/skills/INDEX.md" .claude/skills/INDEX.md

  # 4. Instincts seeds
  for f in mistakes-learned.md project-patterns.md korean-context.md tool-quirks.md; do
    if [ -f "$SIMON_STACK_DIR/.claude/instincts/$f" ] && [ ! -f ".claude/instincts/$f" ]; then
      cp "$SIMON_STACK_DIR/.claude/instincts/$f" ".claude/instincts/$f"
    fi
  done
  log "✅ Instincts seeded: $(ls .claude/instincts/ | wc -l) files"

  # 5. CLAUDE.md template (stored as .template so hook can copy to global)
  if [ -f "$SIMON_STACK_DIR/templates/CLAUDE.md" ] && [ ! -f .claude/CLAUDE.md.template ]; then
    cp "$SIMON_STACK_DIR/templates/CLAUDE.md" .claude/CLAUDE.md.template
  fi

  # 6. Shared scripts used by skills (upgrade-vendor.sh + future siblings).
  #    Placed in .claude/scripts/ so SKILL.md absolute-path references work
  #    in the target repo as well as in user HOME after install.
  mkdir -p .claude/scripts
  for s in upgrade-vendor.sh; do
    if [ -f "$SIMON_STACK_DIR/scripts/$s" ] && [ ! -f ".claude/scripts/$s" ]; then
      cp "$SIMON_STACK_DIR/scripts/$s" ".claude/scripts/$s"
      chmod +x ".claude/scripts/$s"
    fi
  done

# =============================================================================
# MODE: BOOTSTRAP
# =============================================================================
elif [ "$MODE" = "bootstrap" ]; then
  log "--- bootstrap mode: 2-file drop-in (requires public simon-stack repo) ---"

  backup_if_exists .claude/hooks/session-start.sh
  cp "$SIMON_STACK_DIR/templates/bootstrap-session-start.sh" .claude/hooks/session-start.sh
  chmod +x .claude/hooks/session-start.sh
  log "✅ Bootstrap hook installed"
fi

# =============================================================================
# SETTINGS.JSON (both modes)
# =============================================================================
SETTINGS=".claude/settings.json"
if [ -f "$SETTINGS" ]; then
  if grep -q '"SessionStart"' "$SETTINGS" 2>/dev/null; then
    log "⚠️  $SETTINGS already has a SessionStart hook. Please verify manually."
  else
    log "⚠️  $SETTINGS exists without SessionStart hook. Manual merge required."
  fi
else
  cp "$SIMON_STACK_DIR/templates/bootstrap-settings.json" "$SETTINGS"
  log "✅ Settings created: $SETTINGS"
fi

# =============================================================================
# NEXT STEPS
# =============================================================================
echo ""
log "=========================================="
log "✅ simon-stack installed in $TARGET (mode: $MODE)"
log ""
log "Next steps:"
log "  1. Review changes: git status"
log "  2. Commit:         git add .claude/ && git commit -m 'chore(claude): add simon-stack ($MODE)'"
log "  3. Push to your default branch"
log "  4. Open repo in Claude Code web — hook auto-runs"
log ""
if [ "$MODE" = "vendor" ]; then
  log "Vendor mode: all simon-stack files are embedded in this repo."
  log "  To update later: re-run setup-repo.sh from an updated simon-stack checkout."
else
  log "Bootstrap mode: target repo only has 2 files, fetches simon-stack at session start."
  log "  Requires simon-stack repo to be publicly accessible from Claude Code web."
fi
log "=========================================="
