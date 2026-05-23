#!/usr/bin/env bash
# stop.sh — Stop hook. Auto-persist any LLM modifications to wiki / instincts.
#
# Runs when Claude finishes a response. Silent on no-op. If wiki or instincts
# directory has uncommitted changes AND we're on main, auto-commit + push.
#
# Safety:
# - branch must be 'main'
# - ff-only push (no force)
# - silent on any failure (don't disrupt the conversation)

set -uo pipefail

# Locate wiki — same multi-candidate strategy as user-prompt-submit.sh
WIKI=""
PROJ_PARENT=""
[ -n "${CLAUDE_PROJECT_DIR:-}" ] && PROJ_PARENT=$(dirname "$CLAUDE_PROJECT_DIR")
for candidate in \
  "${SIMON_WIKI_DIR:-}" \
  "${SIMON_WIKI_DIR:-}/SimonKWiki" \
  "$PROJ_PARENT/SimonKWiki" \
  "$HOME/.claude/wiki/SimonKWiki" \
  "$HOME/SimonKWiki" \
  "${SIMON_WIKI_DIR:-}/Simon-LLM-Wiki" \
  "$PROJ_PARENT/Simon-LLM-Wiki" \
  "$HOME/.claude/wiki/Simon-LLM-Wiki" \
  "$HOME/Simon-LLM-Wiki" \
  "/home/user/Simon-LLM-Wiki" \
  "/root/Simon-LLM-Wiki"; do
  [ -z "$candidate" ] && continue
  if [ -d "$candidate/.git" ]; then
    WIKI="$candidate"; break
  fi
done

# Repos to auto-persist. Skip silently if not found.
REPOS=()
[ -n "$WIKI" ] && REPOS+=("$WIKI")

# Stop hook receives JSON on stdin; ignore it (we don't need transcript here).
cat >/dev/null 2>&1 || true

SUMMARY=()

for REPO in "${REPOS[@]}"; do
  [ -d "$REPO/.git" ] || continue
  cd "$REPO" 2>/dev/null || continue

  CUR_BRANCH=$(git branch --show-current 2>/dev/null || echo "?")
  [ "$CUR_BRANCH" = "main" ] || continue

  DIRTY_COUNT=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  [ "$DIRTY_COUNT" -gt 0 ] || continue

  # Only auto-commit if the changes look like LLM-driven content updates
  # (markdown / scripts in wiki context). Skip if package-lock or other
  # tool-generated files dominate.
  MD_CHANGED=$(git status --porcelain 2>/dev/null | grep -cE '\.(md|json)$' || echo 0)
  TOTAL=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  if [ "$MD_CHANGED" -lt 1 ] || [ "$MD_CHANGED" -lt "$((TOTAL / 2))" ]; then
    continue
  fi

  git add -A 2>/dev/null
  MSG="auto(session): wiki update — $(date -Iseconds)

Auto-committed by Stop hook. $DIRTY_COUNT file(s) changed during session.
"
  if git -c commit.gpgsign=false commit -m "$MSG" --quiet 2>/dev/null; then
    if git push origin main --quiet 2>/dev/null; then
      SUMMARY+=("auto-synced: $(basename "$REPO") ($DIRTY_COUNT files)")
    else
      SUMMARY+=("committed locally (push failed): $(basename "$REPO")")
    fi
  fi
done

# Print summary (visible to next turn / log)
if [ ${#SUMMARY[@]} -gt 0 ]; then
  echo "[stop-hook] $(IFS=, ; echo "${SUMMARY[*]}")"
fi

exit 0
