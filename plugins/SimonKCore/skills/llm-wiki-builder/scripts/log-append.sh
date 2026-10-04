#!/usr/bin/env bash
# log-append.sh — Append a parseable entry to wiki/log.md.
#
# Usage:
#   bash log-append.sh <action> <subject> [body]
#
# Example:
#   bash log-append.sh ingest "Karpathy llm-wiki gist" \
#     "- Updated: concepts/RAG.md\n- New: sources/2026-04-04-karpathy-llm-wiki.md"

set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: log-append.sh <action> <subject> [body]" >&2
  echo "Actions: ingest, query, lint, refactor" >&2
  exit 1
fi

ACTION="$1"
SUBJECT="$2"
BODY="${3:-}"

WIKI_BASE="${SIMON_WIKI_DIR:-$HOME/.claude/wiki}"
WIKI_REPO="${SIMON_WIKI_REPO:-https://github.com/Simon-YHKim/Simon-LLM-Wiki.git}"
REPO_NAME="$(basename "$WIKI_REPO" .git)"
LOG_FILE="$WIKI_BASE/$REPO_NAME/wiki/log.md"

if [ ! -f "$LOG_FILE" ]; then
  echo "Error: $LOG_FILE not found. Run wiki-init.sh first." >&2
  exit 1
fi

case "$ACTION" in
  ingest|query|lint|refactor) ;;
  *)
    echo "Error: invalid action '$ACTION'. Must be one of: ingest, query, lint, refactor" >&2
    exit 1 ;;
esac

DATE="$(date +%Y-%m-%d)"
{
  echo ""
  echo "## [$DATE] $ACTION | $SUBJECT"
  if [ -n "$BODY" ]; then
    printf '%b\n' "$BODY"
  fi
} >> "$LOG_FILE"

echo "[log-append] Appended to $LOG_FILE: [$DATE] $ACTION | $SUBJECT"
