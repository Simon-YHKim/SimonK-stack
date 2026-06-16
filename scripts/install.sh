#!/usr/bin/env bash
# simon-stack installer — sets up Gstack + the SimonK 5-plugin suite globally.
#
# Usage:
#   ./scripts/install.sh                # install (skip existing skills)
#   ./scripts/install.sh --dry          # show what would happen
#   ./scripts/install.sh --force        # overwrite existing skills (for updates)
#   ./scripts/install.sh --no-backup    # skip ~/.claude backup
#   ./scripts/install.sh --help         # this help
#
# Plugin cutover (2026-06): skills now come from the 5-plugin suite
#   (SimonK-stack[this] + SimonKCore/Design/Market/AIHub). Legacy skills-src/
#   is kept ONLY as an offline fallback if plugin repos can't be fetched.
# Safe local test (no touch to ~/.claude): SIMONK_SKILLS_TARGET=/tmp/t ./scripts/install.sh --force
#
# Idempotent. After `git pull`, run with --force to apply skill updates.

set -euo pipefail

DRY=""
FORCE=""
NO_BACKUP=""
for arg in "$@"; do
  case "$arg" in
    --dry|--dry-run) DRY="--dry" ;;
    --force) FORCE="1" ;;
    --no-backup) NO_BACKUP="1" ;;
    -h|--help)
      sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "ERROR: Unknown arg: $arg (try --help)" >&2 ; exit 1 ;;
  esac
done

log() { echo "[simon-stack] $*"; }
run() { [ "$DRY" = "--dry" ] && echo "  + $*" || "$@"; }

MODE_DESC="install"
[ "$DRY" = "--dry" ] && MODE_DESC="$MODE_DESC dry-run"
[ "$FORCE" = "1" ]   && MODE_DESC="$MODE_DESC force"
[ "$NO_BACKUP" = "1" ] && MODE_DESC="$MODE_DESC no-backup"
log "Starting ($MODE_DESC)..."

# ---- Plugin-suite cutover vars ----
# Skills install target. Override SIMONK_SKILLS_TARGET to a temp dir for a SAFE
# local test — that auto-enables TEST_MODE which skips every section that would
# touch the real ~/.claude (backup, gstack, instincts, hooks, CLAUDE.md, etc.),
# running ONLY the plugin-skill gather into the target.
SKILLS_TARGET="${SIMONK_SKILLS_TARGET:-$HOME/.claude/skills}"
PLUGIN_CACHE="${SIMONK_PLUGIN_CACHE:-$HOME/.simon-stack/plugins}"
TEST_MODE=""
if [ "$SKILLS_TARGET" != "$HOME/.claude/skills" ]; then
  TEST_MODE=1
  log "TEST MODE — skills → $SKILLS_TARGET (env-touching sections skipped)"
fi

# ---- Prereqs ----
command -v git >/dev/null  || { echo "ERROR: git required"; exit 1; }
command -v bun >/dev/null  || log "WARN: bun not found — Gstack runtime will be skipped"
command -v node >/dev/null || log "WARN: node not found"

# ---- Backup (opt-out via --no-backup) ----
if [ -z "$TEST_MODE" ] && [ -z "$NO_BACKUP" ] && [ -d ~/.claude ]; then
  BACKUP=~/.claude.bak-$(date +%Y%m%d-%H%M%S)
  log "Backing up ~/.claude → $BACKUP (skip with --no-backup)"
  run cp -a ~/.claude "$BACKUP"
fi

# ---- Directories ----
run mkdir -p "$SKILLS_TARGET"
[ -z "$TEST_MODE" ] && run mkdir -p ~/.claude/instincts

# ---- Install Gstack runtime (optional, for browse/qa) ----
if [ -z "$TEST_MODE" ] && [ ! -d ~/.claude/skills/gstack ]; then
  log "Cloning Gstack runtime..."
  TMP=$(mktemp -d)
  if run git clone --depth 1 https://github.com/garrytan/gstack "$TMP/gstack-src"; then
    run cp -a "$TMP/gstack-src" ~/.claude/skills/gstack
    run rm -rf "$TMP"

    if command -v bun >/dev/null; then
      log "Installing Gstack dependencies..."
      run bash -c "cd ~/.claude/skills/gstack && bun install"
    fi

    log "Linking individual Gstack skills..."
    g_linked=0
    for d in ~/.claude/skills/gstack/*/; do
      name=$(basename "$d")
      [ -f "$d/SKILL.md" ] || continue
      if [ -e ~/.claude/skills/"$name" ]; then
        [ "$FORCE" = "1" ] || continue
        run rm -rf ~/.claude/skills/"$name"
      fi
      run cp -r "$d" ~/.claude/skills/"$name"
      g_linked=$((g_linked + 1))
    done
    log "  Gstack skills linked: $g_linked"
  else
    log "WARN: Gstack clone failed (non-fatal — simon-stack skills will still install)"
    run rm -rf "$TMP"
  fi
elif [ -z "$TEST_MODE" ]; then
  log "Gstack already present at ~/.claude/skills/gstack/"
fi

# ---- Install SimonK 5-plugin suite skills (plugin cutover; legacy fallback) ----
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Resolve plugin skill sources: this repo's own skills/ (SimonKStack) + the four
# sibling plugin repos (cloned/pulled into a cache, best-effort, non-fatal).
PLUGIN_SKILL_DIRS=()
[ -d "$REPO_DIR/skills" ] && PLUGIN_SKILL_DIRS+=("$REPO_DIR/skills")

run mkdir -p "$PLUGIN_CACHE"
for entry in \
  "SimonKCore https://github.com/Simon-YHKim/SimonKCore.git" \
  "SimonKDesign https://github.com/Simon-YHKim/SimonKDesign.git" \
  "SimonKMarket https://github.com/Simon-YHKim/SimonKMarket.git" \
  "SimonKAIHub https://github.com/Simon-YHKim/SimonKAIHub.git" ; do
  # shellcheck disable=SC2086
  set -- $entry
  pname="$1"; purl="$2"; pdest="$PLUGIN_CACHE/$pname"
  if [ -d "$pdest/.git" ]; then
    [ "$DRY" = "--dry" ] || (cd "$pdest" && git pull --ff-only -q 2>/dev/null) || log "  WARN: $pname pull failed (using cached copy)"
  else
    run git clone --depth 1 "$purl" "$pdest" 2>/dev/null || log "  WARN: $pname clone failed (skipping this plugin)"
  fi
  [ -d "$pdest/skills" ] && PLUGIN_SKILL_DIRS+=("$pdest/skills")
done

# Fallback: if no plugin skills resolved (offline / all clones failed), use the
# legacy monolith sources so the user is NEVER left without skills.
if [ "${#PLUGIN_SKILL_DIRS[@]}" -eq 0 ]; then
  log "WARN: no plugin skill sources resolved — falling back to legacy skills-src/"
  [ -d "$REPO_DIR/skills-src" ]    && PLUGIN_SKILL_DIRS+=("$REPO_DIR/skills-src")
  [ -d "$REPO_DIR/.claude/skills" ] && PLUGIN_SKILL_DIRS+=("$REPO_DIR/.claude/skills")
fi

log "Installing skills into $SKILLS_TARGET from ${#PLUGIN_SKILL_DIRS[@]} source(s)"
installed=0
updated=0
skipped=0
for src_dir in "${PLUGIN_SKILL_DIRS[@]}"; do
  [ -d "$src_dir" ] || continue
  for d in "$src_dir"/*/; do
    name=$(basename "$d")
    [ -f "$d/SKILL.md" ] || continue
    if [ -e "$SKILLS_TARGET"/"$name" ]; then
      if [ "$FORCE" = "1" ]; then
        run rm -rf "$SKILLS_TARGET"/"$name"
        run cp -r "$d" "$SKILLS_TARGET"/"$name"
        updated=$((updated + 1))
      else
        skipped=$((skipped + 1))
      fi
    else
      run cp -r "$d" "$SKILLS_TARGET"/"$name"
      installed=$((installed + 1))
    fi
  done
done
log "  suite skills: installed=$installed updated=$updated skipped=$skipped"
if [ "$skipped" -gt 0 ] && [ "$FORCE" != "1" ]; then
  log "  ($skipped skills already present — use --force to update them)"
fi

# ===== TEST_MODE stops here (only the plugin-skill gather runs) =====
if [ -z "$TEST_MODE" ]; then

# ---- Instincts seed ----
for f in mistakes-learned.md project-patterns.md korean-context.md tool-quirks.md; do
  if [ -f "$REPO_DIR/.claude/instincts/$f" ]; then
    if [ ! -f ~/.claude/instincts/"$f" ] || [ "$FORCE" = "1" ]; then
      run cp "$REPO_DIR/.claude/instincts/$f" ~/.claude/instincts/"$f"
      log "  seeded instincts: $f"
    fi
  fi
done

# ---- User-level SessionStart hook (rich instincts summary) ----
if [ -f "$REPO_DIR/scripts/session-start-instincts.sh" ]; then
  if [ ! -f ~/.claude/session-start-instincts.sh ] || [ "$FORCE" = "1" ]; then
    run cp "$REPO_DIR/scripts/session-start-instincts.sh" ~/.claude/session-start-instincts.sh
    run chmod +x ~/.claude/session-start-instincts.sh
    log "SessionStart hook installed at ~/.claude/session-start-instincts.sh"
    log "  To activate: add to ~/.claude/settings.json hooks.SessionStart:"
    log '    { "matcher": "", "hooks": [{ "type": "command", "command": "~/.claude/session-start-instincts.sh" }] }'
  fi
fi

# ---- Global CLAUDE.md ----
if [ -f "$REPO_DIR/templates/CLAUDE.md" ]; then
  if [ ! -f ~/.claude/CLAUDE.md ]; then
    log "Installing ~/.claude/CLAUDE.md from template"
    run cp "$REPO_DIR/templates/CLAUDE.md" ~/.claude/CLAUDE.md
  elif [ "$FORCE" = "1" ]; then
    BACKUP_CLAUDE=~/.claude/CLAUDE.md.bak-$(date +%Y%m%d-%H%M%S)
    log "Backing up ~/.claude/CLAUDE.md → $BACKUP_CLAUDE (--force)"
    run cp ~/.claude/CLAUDE.md "$BACKUP_CLAUDE"
    run cp "$REPO_DIR/templates/CLAUDE.md" ~/.claude/CLAUDE.md
  fi
fi

# ---- Skills INDEX ----
if [ -f "$REPO_DIR/.claude/skills/INDEX.md" ]; then
  if [ ! -f ~/.claude/skills/INDEX.md ] || [ "$FORCE" = "1" ]; then
    run cp "$REPO_DIR/.claude/skills/INDEX.md" ~/.claude/skills/INDEX.md
  fi
fi

# ---- Shared scripts used by skills (stack-update + 5 vendor-upgrade) ----
# These scripts are referenced from SKILL.md by absolute path ~/.claude/scripts/
# so they remain reachable regardless of CWD or whether simon-stack is
# vendored / bootstrapped / locally installed.
run mkdir -p ~/.claude/scripts
for s in upgrade-vendor.sh; do
  if [ -f "$REPO_DIR/scripts/$s" ]; then
    if [ ! -f ~/.claude/scripts/"$s" ] || [ "$FORCE" = "1" ]; then
      run cp "$REPO_DIR/scripts/$s" ~/.claude/scripts/"$s"
      run chmod +x ~/.claude/scripts/"$s"
    fi
  fi
done

# ---- External vendored repos (sprint v22-EXT) ----
EXT_DIR="$REPO_DIR/external"
EXT_MARKER=~/.claude/.simon-stack-external-installed

if [ -d "$EXT_DIR" ] && { [ ! -f "$EXT_MARKER" ] || [ "$FORCE" = "1" ]; }; then
  log "External vendor setup (best-effort, non-fatal)..."

  for r in oh-my-claudecode oh-my-openagent; do
    if [ -d "$EXT_DIR/$r" ] && [ ! -d "$EXT_DIR/$r/node_modules" ]; then
      if command -v bun >/dev/null 2>&1; then
        log "  - $r: bun install"
        (cd "$EXT_DIR/$r" && bun install >/dev/null 2>&1) || log "  - $r: bun install failed (continuing)"
      elif command -v npm >/dev/null 2>&1; then
        log "  - $r: npm install --no-audit --no-fund"
        (cd "$EXT_DIR/$r" && npm install --no-audit --no-fund >/dev/null 2>&1) || log "  - $r: npm install failed (continuing)"
      else
        log "  - $r: skip deps (bun/npm not found — dist/ pre-built will still work)"
      fi
    fi
  done

  if [ -d "$EXT_DIR/OpenHarness" ] && [ -f "$EXT_DIR/OpenHarness/pyproject.toml" ]; then
    if command -v pip >/dev/null 2>&1; then
      log "  - OpenHarness: pip install -e (--ignore-installed pyjwt)"
      pip install -e "$EXT_DIR/OpenHarness" --ignore-installed pyjwt --quiet 2>&1 | tail -3 || log "  - OpenHarness: pip install failed (continuing)"
    elif command -v pip3 >/dev/null 2>&1; then
      log "  - OpenHarness: pip3 install -e (--ignore-installed pyjwt)"
      pip3 install -e "$EXT_DIR/OpenHarness" --ignore-installed pyjwt --quiet 2>&1 | tail -3 || log "  - OpenHarness: pip3 install failed (continuing)"
    else
      log "  - OpenHarness: skip (pip not found — pyproject.toml accessible for manual install)"
    fi
  fi

  run touch "$EXT_MARKER"
  log "External vendor setup complete (marker: $EXT_MARKER)"
fi

# ---- Windows: heal machine-specific path refs (env vars + scheduled tasks) ----
# After a drive/folder move (e.g. C:\Coding -> "C:\Coding Infra") the User env
# vars + SimonK scheduled tasks still point at the OLD root because they don't
# travel with git. heal-coding-paths.ps1 repoints them to wherever this repo now
# lives. Idempotent no-op when already healthy; best-effort + non-fatal; only
# runs on Windows (skipped when powershell.exe is absent).
HEAL_PS="$REPO_DIR/scripts/heal-coding-paths.ps1"
if [ -f "$HEAL_PS" ] && command -v powershell.exe >/dev/null 2>&1; then
  HEAL_WIN="$(cygpath -w "$HEAL_PS" 2>/dev/null || echo "$HEAL_PS")"
  log "Healing Windows path refs (env vars + scheduled tasks)..."
  run powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$HEAL_WIN" 2>&1 | sed 's/^/  /' \
    || log "  (heal step non-fatal failure — run manually: scripts/heal-coding-paths.ps1)"
fi

# ---- Record installed SHA for session-start.sh selective-update logic ----
if [ "$DRY" != "--dry" ]; then
  CURRENT_SHA=$(cd "$REPO_DIR" && git rev-parse --verify HEAD 2>/dev/null) || CURRENT_SHA=unknown
  echo "$CURRENT_SHA" > ~/.claude/.simon-stack-installed
  log "Recorded installed SHA: $CURRENT_SHA"
fi

log "✅ Install complete"
log ""
log "Next steps:"
log "  1. Restart Claude Code to load new skills"
log "  2. Try: '새 앱 만들고 싶어' → app-dev-orchestrator should trigger"
log "  3. Read: ~/.claude/skills/INDEX.md for the full skill map"
log ""
log "After future \`git pull\`, run: ./scripts/install.sh --force"

else
  log "✅ TEST MODE complete — gathered suite skills into $SKILLS_TARGET (no ~/.claude changes)"
fi
