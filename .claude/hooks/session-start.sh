#!/usr/bin/env bash
# SessionStart hook — bootstraps simon-stack on every Claude Code session.
#
# What it does (idempotent):
#   1. Backup existing ~/.claude (if present)
#   2. Install Gstack runtime (~/.claude/skills/gstack/) + bun install
#   3. Expose individual Gstack skills at ~/.claude/skills/<name>/
#   4. Copy simon-stack skills from this repo to ~/.claude/skills/
#   5. Seed ~/.claude/instincts/ with this repo's seed files
#   6. Create ~/.claude/CLAUDE.md from templates/CLAUDE.md
#   7. Install ~/.claude/session-start-instincts.sh (for user-level hook)
#
# Runs synchronous by default — guarantees skills ready before session loop.
# Switch to async by uncommenting the echo '{"async": ...}' line.

set -euo pipefail

# --- Async opt-in (disabled by default) ---
# echo '{"async": true, "asyncTimeout": 300000}'

# --- Paths ---
REPO_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
LOG_PREFIX="[simon-stack-hook]"
LOG_FILE="/tmp/simon-stack-session-start-$(date +%s).log"

log() { echo "$LOG_PREFIX $*" | tee -a "$LOG_FILE"; }

log "Starting. repo=$REPO_DIR remote=${CLAUDE_CODE_REMOTE:-false}"

# --- Short-circuit if already installed ---
# We use a marker file that embeds the commit SHA that installed.
MARKER=~/.claude/.simon-stack-installed
CURRENT_SHA=$(cd "$REPO_DIR" && git rev-parse --verify HEAD 2>/dev/null) || CURRENT_SHA=unknown

if [ -f "$MARKER" ] && [ "$(cat "$MARKER" 2>/dev/null)" = "$CURRENT_SHA" ]; then
  log "Already installed at $CURRENT_SHA, skipping bootstrap"

  # --- Mandatory update checks (LLM acts on these BEFORE first user turn) ---
  # Dual delivery: stdout for hook-visible LLMs + ~/.claude/.update-pending
  # file-based fallback for environments where hook stdout is not piped into
  # LLM context.
  PENDING_FILE="$HOME/.claude/.update-pending"
  rm -f "$PENDING_FILE"
  ANY_UPGRADE=0
  emit_header() {
    if [ "$ANY_UPGRADE" = "0" ]; then
      log ""
      log "============================================================"
      log "[UPGRADE_AVAILABLE] Per CLAUDE.md 'Session start policy',"
      log "the LLM MUST address these BEFORE the first user-facing turn:"
      {
        echo "# [UPGRADE_AVAILABLE] $(date -Iseconds)"
        echo ""
        echo "Hook detected pending updates. Per CLAUDE.md 'Session start policy',"
        echo "the LLM must handle these BEFORE the first user-facing turn."
        echo ""
      } > "$PENDING_FILE"
      ANY_UPGRADE=1
    fi
  }
  append_pending() {
    [ -f "$PENDING_FILE" ] && printf '%s\n' "$1" >> "$PENDING_FILE"
  }

  # 1) SimonK-stack — auto-pull when safe (clean tree, on main, ff-only)
  if (cd "$REPO_DIR" && git fetch --quiet origin 2>/dev/null); then
    BEHIND=$(cd "$REPO_DIR" && git rev-list HEAD..origin/main --count 2>/dev/null || echo 0)
    if [ "$BEHIND" -gt 0 ]; then
      CUR_BRANCH=$(cd "$REPO_DIR" && git branch --show-current 2>/dev/null || echo "?")
      DIRTY=$(cd "$REPO_DIR" && git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
      if [ "$CUR_BRANCH" = "main" ] && [ "$DIRTY" = "0" ]; then
        # Safe auto-pull
        if (cd "$REPO_DIR" && git pull --ff-only --quiet origin main 2>/dev/null); then
          emit_header
          log "  - SimonK-stack: auto-pulled $BEHIND commit(s) from origin/main ✓"
          append_pending "- SimonK-stack: auto-pulled $BEHIND commit(s) ✓ (no action needed)"
        else
          emit_header
          log "  - SimonK-stack: $BEHIND behind, auto-pull failed → cd $REPO_DIR && git pull"
          append_pending "- SimonK-stack: auto-pull FAILED, $BEHIND behind → cd $REPO_DIR && git pull"
        fi
      else
        emit_header
        log "  - SimonK-stack: $BEHIND commit(s) behind origin/main"
        log "    (branch=$CUR_BRANCH, dirty=$DIRTY — auto-pull skipped for safety)"
        log "    → manually: cd $REPO_DIR && git pull --ff-only origin main"
        append_pending "- SimonK-stack: $BEHIND behind, SKIPPED (branch=$CUR_BRANCH, dirty=$DIRTY) → manual pull needed"
      fi
    fi
  fi

  # 2) gstack upstream (live clone)
  for GPATH in "$HOME/.claude/skills/gstack" "$HOME/.gstack/repos/gstack"; do
    if [ -d "$GPATH/.git" ]; then
      if (cd "$GPATH" && git fetch --quiet origin 2>/dev/null); then
        GBEHIND=$(cd "$GPATH" && git rev-list HEAD..origin/main --count 2>/dev/null || echo 0)
        if [ "$GBEHIND" -gt 0 ]; then
          emit_header
          log "  - gstack upstream: $GBEHIND commit(s) behind ($GPATH)"
          log "    → run \`/gstack-upgrade\` to apply"
          append_pending "- gstack upstream: $GBEHIND behind → run /gstack-upgrade"
        fi
      fi
      break
    fi
  done

  # 3) Wiki (SimonKWiki primary 2026-05-23+, Simon-LLM-Wiki legacy repo name) — auto-pull when safe
  WIKI_DIR=""
  WIKI_PROJ_PARENT=$(dirname "$REPO_DIR" 2>/dev/null)
  for _wcand in \
    "${SIMON_WIKI_DIR:-}" \
    "$HOME/.claude/wiki/SimonKWiki" \
    "$HOME/.claude/wiki/Simon-LLM-Wiki" \
    "$WIKI_PROJ_PARENT/SimonKWiki" \
    "$WIKI_PROJ_PARENT/Simon-LLM-Wiki"; do
    [ -z "$_wcand" ] && continue
    if [ -d "$_wcand/.git" ]; then WIKI_DIR="$_wcand"; break; fi
  done
  if [ -n "$WIKI_DIR" ] && (cd "$WIKI_DIR" && git fetch --quiet origin 2>/dev/null); then
    WBEHIND=$(cd "$WIKI_DIR" && git rev-list HEAD..origin/main --count 2>/dev/null || echo 0)
    if [ "$WBEHIND" -gt 0 ]; then
      WBRANCH=$(cd "$WIKI_DIR" && git branch --show-current 2>/dev/null || echo "?")
      WDIRTY=$(cd "$WIKI_DIR" && git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
      if [ "$WBRANCH" = "main" ] && [ "$WDIRTY" = "0" ]; then
        if (cd "$WIKI_DIR" && git pull --ff-only --quiet origin main 2>/dev/null); then
          emit_header
          log "  - Simon-LLM-Wiki: auto-pulled $WBEHIND commit(s) ✓ — re-read LESSONS_LEARNED.md"
          append_pending "- Simon-LLM-Wiki: auto-pulled $WBEHIND ✓ → re-read $WIKI_DIR/LESSONS_LEARNED.md"
        else
          emit_header
          log "  - Simon-LLM-Wiki: $WBEHIND behind, auto-pull failed → cd $WIKI_DIR && git pull"
          append_pending "- Simon-LLM-Wiki: auto-pull FAILED, $WBEHIND behind → cd $WIKI_DIR && git pull"
        fi
      else
        emit_header
        log "  - Simon-LLM-Wiki: $WBEHIND commit(s) behind (branch=$WBRANCH, dirty=$WDIRTY)"
        log "    → manually: cd $WIKI_DIR && git pull"
        append_pending "- Simon-LLM-Wiki: $WBEHIND behind, SKIPPED (branch=$WBRANCH, dirty=$WDIRTY)"
      fi
    fi
  fi

  if [ "$ANY_UPGRADE" = "1" ]; then
    log "============================================================"
    log ""
    log "[fallback] Pending state also written to: $PENDING_FILE"
    log "  → LLM 가 stdout 못 봤다면 \`cat $PENDING_FILE\` 로 확인 가능"
  fi

  exit 0
fi

log "Bootstrap required. current=$CURRENT_SHA"

# --- Directories ---
mkdir -p ~/.claude/skills ~/.claude/instincts

# --- 1. Gstack runtime (optional, for browse/qa tools only) ---
# Skill definitions are now vendored in skills-src/ — no clone needed for skills.
# The runtime clone is only needed for Gstack's browse daemon and QA tools.
if [ ! -d ~/.claude/skills/gstack ]; then
  log "Cloning Gstack runtime (optional, for browse/QA tools)..."
  TMP=$(mktemp -d)
  if git clone --depth 1 https://github.com/garrytan/gstack "$TMP/gstack-src" 2>>"$LOG_FILE"; then
    cp -a "$TMP/gstack-src" ~/.claude/skills/gstack
    rm -rf "$TMP"
    log "Gstack runtime cloned OK"

    if command -v bun >/dev/null 2>&1; then
      log "Running bun install in Gstack..."
      (cd ~/.claude/skills/gstack && bun install >>"$LOG_FILE" 2>&1) || log "WARN: bun install failed (non-fatal)"
    else
      log "WARN: bun not found — Gstack runtime scripts will be limited"
    fi
  else
    log "WARN: Gstack runtime clone failed (non-fatal — all skill definitions are vendored)"
    rm -rf "$TMP"
  fi
fi

# --- 2. Expose individual Gstack skills (skip if already vendored in skills-src) ---
if [ -d ~/.claude/skills/gstack ]; then
  log "Exposing individual Gstack skills..."
  count=0
  for d in ~/.claude/skills/gstack/*/; do
    name=$(basename "$d")
    [ -f "$d/SKILL.md" ] || continue
    [ -e ~/.claude/skills/"$name" ] && continue
    cp -r "$d" ~/.claude/skills/"$name"
    count=$((count + 1))
  done
  log "Exposed $count Gstack skills"
fi

# --- 3. simon-stack skills from this repo ---
# Source: skills-src/ (distributable) + .claude/skills/ (dev-essential).
#
# Update policy (fixes stale-global problem):
#   - new skill → always copy
#   - existing skill → keep, UNLESS:
#       (a) $SIMON_STACK_FORCE_SYNC=1   (manual full overwrite)
#       (b) SKILL changed in git diff between previously-installed SHA
#           and $CURRENT_SHA   (selective auto-update)
log "Copying simon-stack skills..."

# Compute changed-skill set since previous install (for selective overwrite).
PREV_SHA=$(cat "$MARKER" 2>/dev/null || echo "")
CHANGED_SET=""
if [ -n "$PREV_SHA" ] && [ "$PREV_SHA" != "$CURRENT_SHA" ]; then
  if (cd "$REPO_DIR" && git cat-file -e "${PREV_SHA}^{commit}" 2>/dev/null); then
    CHANGED_FILES=$(cd "$REPO_DIR" && git diff --name-only "$PREV_SHA" "$CURRENT_SHA" -- 'skills-src/' '.claude/skills/' 2>/dev/null || true)
    # NOTE: use '#' as sed separator to avoid clash with ERE alternation '|'.
    CHANGED_SET=" $(echo "$CHANGED_FILES" | sed -E 's#^(skills-src|\.claude/skills)/([^/]+)/.*#\2#' | { grep -v '^$' || true; } | sort -u | tr '\n' ' ')"
    if [ -n "$(echo "$CHANGED_SET" | tr -d ' ')" ]; then
      log "  changed skills since $PREV_SHA → $CHANGED_SET"
    fi
  else
    log "  (prev SHA $PREV_SHA not in local git history — selective diff skipped; use SIMON_STACK_FORCE_SYNC=1 to force overwrite)"
  fi
fi

count_new=0
count_updated=0
count_skipped=0
for src_dir in "$REPO_DIR"/skills-src "$REPO_DIR"/.claude/skills; do
  [ -d "$src_dir" ] || continue
  for d in "$src_dir"/*/; do
    name=$(basename "$d")
    [ -f "$d/SKILL.md" ] || continue

    # Skip connect-chrome — duplicate name field (open-gstack-browser).
    # Gstack auto-generated SKILL.md uses alias-via-duplicate-name pattern
    # which Claude Code's skill loader dedupes. The folder is a zombie.
    [ "$name" = "connect-chrome" ] && continue

    FORCE_THIS=0
    if [ "${SIMON_STACK_FORCE_SYNC:-0}" = "1" ]; then
      FORCE_THIS=1
    elif [ -n "$CHANGED_SET" ] && echo "$CHANGED_SET" | grep -q " $name "; then
      FORCE_THIS=1
    fi

    if [ -e ~/.claude/skills/"$name" ]; then
      if [ "$FORCE_THIS" = "1" ]; then
        rm -rf ~/.claude/skills/"$name"
        cp -r "$d" ~/.claude/skills/"$name"
        count_updated=$((count_updated + 1))
      else
        count_skipped=$((count_skipped + 1))
      fi
    else
      cp -r "$d" ~/.claude/skills/"$name"
      count_new=$((count_new + 1))
    fi
  done
done
log "Skills: new=$count_new updated=$count_updated skipped=$count_skipped"

# INDEX.md at skill root
if [ -f "$REPO_DIR/.claude/skills/INDEX.md" ] && [ ! -f ~/.claude/skills/INDEX.md ]; then
  cp "$REPO_DIR/.claude/skills/INDEX.md" ~/.claude/skills/INDEX.md
fi

# --- 4. Instincts seeds ---
log "Seeding instincts..."
for f in mistakes-learned.md project-patterns.md korean-context.md tool-quirks.md; do
  if [ -f "$REPO_DIR/.claude/instincts/$f" ] && [ ! -f ~/.claude/instincts/"$f" ]; then
    cp "$REPO_DIR/.claude/instincts/$f" ~/.claude/instincts/"$f"
  fi
done

# --- 5. Global CLAUDE.md ---
if [ ! -f ~/.claude/CLAUDE.md ]; then
  if [ -f "$REPO_DIR/templates/CLAUDE.md" ]; then
    cp "$REPO_DIR/templates/CLAUDE.md" ~/.claude/CLAUDE.md
    log "Installed ~/.claude/CLAUDE.md from template"
  fi
fi

# --- 6. User-level SessionStart hook script (for rich instincts summary) ---
if [ -f "$REPO_DIR/scripts/session-start-instincts.sh" ] && [ ! -f ~/.claude/session-start-instincts.sh ]; then
  cp "$REPO_DIR/scripts/session-start-instincts.sh" ~/.claude/session-start-instincts.sh
  chmod +x ~/.claude/session-start-instincts.sh
fi

# --- 6b. LLM Wiki auto-bootstrap ---
# If llm-wiki-builder skill exists, auto-init the wiki repo so it's always ready.
# Idempotent: wiki-init.sh skips if already cloned, just pulls latest.
WIKI_INIT="$REPO_DIR/skills-src/llm-wiki-builder/scripts/wiki-init.sh"
if [ -f "$WIKI_INIT" ]; then
  log "Bootstrapping LLM Wiki..."
  if bash "$WIKI_INIT" >>"$LOG_FILE" 2>&1; then
    log "LLM Wiki ready"
  else
    log "WARN: wiki-init failed (non-fatal, may need SIMON_WIKI_REPO set)"
  fi
fi

# --- 7. External vendored repos activation (sprint v22-EXT) ---
# 3 vendored repos in external/: oh-my-claudecode, oh-my-openagent, OpenHarness.
# Idempotent: marker file tracks setup. Best-effort install (non-fatal).
EXT_DIR="$REPO_DIR/external"
EXT_MARKER=~/.claude/.simon-stack-external-installed

if [ -d "$EXT_DIR" ] && [ ! -f "$EXT_MARKER" ]; then
  log "External vendor setup (3 repos, best-effort)..."

  for r in oh-my-claudecode oh-my-openagent; do
    if [ -d "$EXT_DIR/$r" ] && [ ! -d "$EXT_DIR/$r/node_modules" ]; then
      if command -v bun >/dev/null 2>&1; then
        log "  - $r: bun install"
        (cd "$EXT_DIR/$r" && bun install >>"$LOG_FILE" 2>&1) || log "  - $r: bun install failed (non-fatal)"
      elif command -v npm >/dev/null 2>&1; then
        log "  - $r: npm install"
        (cd "$EXT_DIR/$r" && npm install --no-audit --no-fund >>"$LOG_FILE" 2>&1) || log "  - $r: npm install failed (non-fatal)"
      else
        log "  - $r: skip (bun/npm not found, dist/ pre-built usable)"
      fi
    fi
  done

  if [ -d "$EXT_DIR/OpenHarness" ] && [ -f "$EXT_DIR/OpenHarness/pyproject.toml" ]; then
    PIPCMD=""
    command -v pip >/dev/null 2>&1 && PIPCMD=pip
    [ -z "$PIPCMD" ] && command -v pip3 >/dev/null 2>&1 && PIPCMD=pip3
    if [ -n "$PIPCMD" ]; then
      log "  - OpenHarness: $PIPCMD install -e (--ignore-installed pyjwt)"
      # --ignore-installed pyjwt: skip uninstall of the debian-shipped PyJWT
      # which lacks a RECORD file. Without this, the install aborts with
      # "Cannot uninstall PyJWT ... RECORD file not found" on debian-based
      # container images (the default Claude Code remote runtime).
      if ! $PIPCMD install -e "$EXT_DIR/OpenHarness" --ignore-installed pyjwt --quiet >>"$LOG_FILE" 2>&1; then
        log "  - OpenHarness: install failed (see $LOG_FILE)"
      fi
    else
      log "  - OpenHarness: skip (pip not found)"
    fi
  fi

  touch "$EXT_MARKER"
  log "External vendor setup complete"
fi


# --- 7b. User-level vendor (~/.simon-stack/vendor/) auto-pull each session ---
# Sprint v34: live clone (.git preserved) of 5 vendor repos for "직접 설치 + 실행 시 update".
# Layout independent from repo-local external/ (sprint v22-EXT legacy).
# Safety: only fetch+pull when clean + ff-only. Non-fatal on any failure.
VENDOR_DIR="$HOME/.simon-stack/vendor"
mkdir -p "$VENDOR_DIR" 2>/dev/null || true

# Repo list: name|url (one per line)
VENDOR_LIST="oh-my-claudecode|https://github.com/Yeachan-Heo/oh-my-claudecode
oh-my-openagent|https://github.com/code-yeongyu/oh-my-openagent
OpenHarness|https://github.com/HKUDS/OpenHarness
open-cowork|https://github.com/OpenCoworkAI/open-cowork
design.md|https://github.com/google-labs-code/design.md"

VENDOR_PULLED=0
VENDOR_BEHIND=0
echo "$VENDOR_LIST" | while IFS='|' read -r vname vurl; do
  [ -z "$vname" ] && continue
  VTARGET="$VENDOR_DIR/$vname"
  if [ ! -d "$VTARGET/.git" ]; then
    log "[vendor] $vname: fresh clone from $vurl"
    git clone --depth 1 "$vurl" "$VTARGET" >>"$LOG_FILE" 2>&1 \
      || log "[vendor] $vname: clone failed (non-fatal)"
  else
    if (cd "$VTARGET" && git fetch --quiet origin 2>/dev/null); then
      VBEHIND_N=$(cd "$VTARGET" && git rev-list HEAD..@{u} --count 2>/dev/null || echo 0)
      if [ "$VBEHIND_N" -gt 0 ]; then
        VDIRTY_N=$(cd "$VTARGET" && git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
        if [ "$VDIRTY_N" = "0" ]; then
          if (cd "$VTARGET" && git pull --ff-only --quiet 2>/dev/null); then
            log "[vendor] $vname: auto-pulled $VBEHIND_N commit(s) ✓"
          else
            log "[vendor] $vname: $VBEHIND_N behind, auto-pull failed (manual update)"
          fi
        else
          log "[vendor] $vname: $VBEHIND_N behind, dirty — skipped"
        fi
      fi
    fi
  fi
done


# --- Context Guardian self-healing (repo-local) ---
# Ensure CLAUDE.md has the Context Guardian Rules block. If the marker is
# missing (e.g. user deleted CLAUDE.md), re-run install-rules.sh from the
# repo root. This is idempotent and self-healing.
if [ -d "$REPO_DIR/.claude/skills/context-guardian" ]; then
  if ! grep -qF "<!-- context-guardian-rules:v1 -->" "$REPO_DIR/CLAUDE.md" 2>/dev/null; then
    log "Context Guardian rules missing from CLAUDE.md — re-installing"
    (cd "$REPO_DIR" && bash .claude/skills/context-guardian/scripts/install-rules.sh >> "$LOG_FILE" 2>&1) \
      || log "WARN: context-guardian install-rules.sh failed (non-fatal)"
  else
    log "Context Guardian rules present in CLAUDE.md"
  fi
fi

# --- 7. Marker ---
echo "$CURRENT_SHA" > "$MARKER"

log "✅ Bootstrap complete. log=$LOG_FILE"

# --- Post-install env for current session (via $CLAUDE_ENV_FILE) ---
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    echo "export SIMON_STACK_INSTALLED=1"
    echo "export SIMON_STACK_SHA=$CURRENT_SHA"
  } >> "$CLAUDE_ENV_FILE"
fi

exit 0
