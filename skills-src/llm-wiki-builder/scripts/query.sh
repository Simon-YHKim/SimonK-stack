#!/usr/bin/env bash
# query.sh — Set up a wiki query: surface the index + recent log for the LLM,
# then prompt the LLM to answer with citations and optionally file the answer back.
#
# Usage:
#   bash query.sh "question text"

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: query.sh \"question text\"" >&2
  exit 1
fi

QUESTION="$1"

WIKI_BASE="${SIMON_WIKI_DIR:-$HOME/.claude/wiki}"
WIKI_REPO="${SIMON_WIKI_REPO:-https://github.com/Simon-YHKim/Simon-LLM-Wiki.git}"
REPO_NAME="$(basename "$WIKI_REPO" .git)"
WIKI_DIR="$WIKI_BASE/$REPO_NAME"
INDEX="$WIKI_DIR/wiki/index.md"
LOG="$WIKI_DIR/wiki/log.md"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -f "$INDEX" ]; then
  echo "Error: $INDEX not found. Run wiki-init.sh first." >&2
  exit 1
fi

# Slug for potential file-back
SLUG="$(echo "$QUESTION" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9가-힣]/-/g; s/--*/-/g; s/^-//; s/-$//' | cut -c1-60)"
[ -z "$SLUG" ] && SLUG="query-$(date +%s)"

cat <<EOF

[query] Question: $QUESTION
[query] Wiki: $WIKI_DIR

================================================================
WIKI INDEX (for LLM to identify relevant pages):
================================================================
EOF
cat "$INDEX"

if [ -f "$LOG" ]; then
  echo ""
  echo "================================================================"
  echo "RECENT WIKI ACTIVITY (last 10 log entries):"
  echo "================================================================"
  grep "^## \[" "$LOG" | tail -10 || echo "(no log entries yet)"
fi

cat <<EOF

================================================================
NEXT STEPS — for the LLM to execute:
================================================================

1. From the index above, identify candidate pages relevant to:
   "$QUESTION"

2. Read those pages:
   cat "$WIKI_DIR/wiki/<page>.md"

3. Synthesize answer with citations: \`(see [[page-name]])\`.

4. Decide: does this answer have standalone value worth keeping?
   - YES: file it to "$WIKI_DIR/wiki/queries/$SLUG.md"
     Use frontmatter:
       ---
       type: query
       asked: $(date +%Y-%m-%d)
       cites: [<page1>, <page2>, ...]
       ---
   - NO: skip file-back, just answer in chat.

5. Log the activity:
   bash "$SCRIPT_DIR/log-append.sh" query "$QUESTION" \\
     "- Cited: <pages>\\n- Filed back: queries/$SLUG.md (yes|no)"

EOF
