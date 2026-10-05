#!/usr/bin/env bash
# SessionStart hook - read-only notice (hub decision D-87, 2026-10-05).
#
# The legacy bootstrap that copied skills into ~/.claude/skills and auto-pulled
# this repo, the wiki and vendor stacks is retired, together with the D-33
# source-only hold that fenced it. Users install the five plugins from the
# marketplace (dist branch); this PC's flat install is updated with
# scripts/windows/update-local.ps1. This hook runs no git or network command
# and writes nothing; it only says where those paths are. Restoring the old
# bootstrap means reverting the D-87 commit on main.

REPO_DIR="${CLAUDE_PROJECT_DIR:-.}"

# Accumulated blind-spot notes from earlier sessions, when the repo has them.
if [ -f "$REPO_DIR/perspectives.md" ]; then
  printf '%s\n' '[perspectives] perspectives.md is in this repo; read it before making decisions.'
fi

printf '%s\n' '[simon-stack-hook] SessionStart is read-only (D-87). Users: /plugin marketplace add Simon-YHKim/SimonK-stack. This PC: pwsh -File scripts/windows/update-local.ps1 (preview; add -Apply to install). Nothing was written.'
exit 0
