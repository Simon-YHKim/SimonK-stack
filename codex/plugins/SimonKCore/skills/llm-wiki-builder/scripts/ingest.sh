#!/usr/bin/env bash
# ingest.sh — Stage a source for LLM ingestion into the wiki.
#
# Usage:
#   bash ingest.sh <source-path-or-url> [--topic "topic name"]
#
# This script does the mechanical part (fetch + stage + log).
# The semantic work (summarize, update related pages, cross-link) is the LLM's job
# — the script prints the next steps for the LLM to execute.

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: ingest.sh <source-path-or-url> [--topic \"topic name\"]" >&2
  echo "" >&2
  echo "Examples:" >&2
  echo "  bash ingest.sh https://example.com/article" >&2
  echo "  bash ingest.sh ~/Downloads/paper.pdf --topic \"transformers\"" >&2
  exit 1
fi

SOURCE="$1"
TOPIC=""
shift
while [ $# -gt 0 ]; do
  case "$1" in
    --topic) TOPIC="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

WIKI_BASE="${SIMON_WIKI_DIR:-$HOME/.claude/wiki}"
WIKI_REPO="${SIMON_WIKI_REPO:-https://github.com/Simon-YHKim/Simon-LLM-Wiki.git}"
REPO_NAME="$(basename "$WIKI_REPO" .git)"
WIKI_DIR="$WIKI_BASE/$REPO_NAME"
RAW_DIR="$WIKI_DIR/raw/articles"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$WIKI_DIR" ]; then
  echo "Error: wiki not initialized. Run wiki-init.sh first." >&2
  exit 1
fi

mkdir -p "$RAW_DIR"

DATE="$(date +%Y-%m-%d)"

# Determine if SOURCE is URL or local file
if [[ "$SOURCE" =~ ^https?:// ]]; then
  # URL: derive slug from last path segment, fetch as markdown via curl
  SLUG="$(basename "$SOURCE" | sed 's/[^a-zA-Z0-9.-]/-/g; s/--*/-/g; s/^-//; s/-$//')"
  [ -z "$SLUG" ] && SLUG="source-$(date +%s)"
  DEST="$RAW_DIR/$DATE-$SLUG.html"
  echo "[ingest] Fetching $SOURCE -> $DEST"
  if ! curl -fsSL "$SOURCE" -o "$DEST" 2>/dev/null; then
    echo "[ingest] WARN: curl failed. Skipping fetch — LLM will need to retrieve manually." >&2
    echo "$SOURCE" > "$DEST.url"
    DEST="$DEST.url"
  fi
elif [ -f "$SOURCE" ]; then
  SLUG="$(basename "$SOURCE" | sed 's/[^a-zA-Z0-9.-]/-/g; s/--*/-/g')"
  DEST="$RAW_DIR/$DATE-$SLUG"
  echo "[ingest] Copying $SOURCE -> $DEST"
  cp "$SOURCE" "$DEST"
else
  echo "Error: source not found (not a URL, not a file): $SOURCE" >&2
  exit 1
fi

# Compute summary slug for the wiki/sources page the LLM will create
SOURCE_SLUG="$(basename "$DEST" | sed 's/\.[^.]*$//')"
SUMMARY_PATH="wiki/sources/$SOURCE_SLUG.md"

cat <<EOF

[ingest] Source staged at: $DEST

================================================================
NEXT STEPS — for the LLM to execute (this script does NOT do them):
================================================================

1. Read the staged source:
   cat "$DEST"

2. Discuss key takeaways with the user.

3. Create summary page:
   "$WIKI_DIR/$SUMMARY_PATH"

   Use frontmatter:
     ---
     type: source
     ingested: $DATE
     topic: ${TOPIC:-<infer>}
     ---

4. Update related entity/concept pages under:
   "$WIKI_DIR/wiki/entities/"
   "$WIKI_DIR/wiki/concepts/"

5. Update catalog:
   "$WIKI_DIR/wiki/index.md"

6. After all updates, log it:
   bash "$SCRIPT_DIR/log-append.sh" ingest "$SOURCE_SLUG" \\
     "- New: $SUMMARY_PATH\\n- Updated: <list pages you changed>"

7. Commit (optional):
   cd "$WIKI_DIR" && git add . && git commit -m "ingest: $SOURCE_SLUG"

EOF
