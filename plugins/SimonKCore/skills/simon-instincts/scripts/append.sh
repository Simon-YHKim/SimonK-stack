#!/usr/bin/env bash
# append.sh — interactive helper for appending a new entry to an instincts file.
#
# Usage:
#   bash append.sh mistakes        # append to mistakes-learned.md
#   bash append.sh patterns        # append to project-patterns.md
#   bash append.sh korean          # append to korean-context.md
#   bash append.sh tools           # append to tool-quirks.md
#
# With --title, --symptom, --cause, --fix flags you can pass data non-interactively:
#   bash append.sh mistakes --title "grep pattern leak" --symptom "..." --cause "..." --fix "..."
#
# Why a script instead of inline Edit calls:
# - consistent template (prevents forgetting a field)
# - timestamps auto-populated
# - sanity-checks that ~/.claude/instincts/ exists first

set -euo pipefail

INSTINCTS=~/.claude/instincts

case "${1:-}" in
  mistakes)  FILE="$INSTINCTS/mistakes-learned.md" ;;
  patterns)  FILE="$INSTINCTS/project-patterns.md" ;;
  korean)    FILE="$INSTINCTS/korean-context.md" ;;
  tools)     FILE="$INSTINCTS/tool-quirks.md" ;;
  "")        echo "Usage: $0 {mistakes|patterns|korean|tools} [--title T --symptom S --cause C --fix F]"; exit 1 ;;
  *)         echo "Unknown category: $1"; exit 1 ;;
esac
shift

mkdir -p "$INSTINCTS"
touch "$FILE"

TITLE=""
SYMPTOM=""
CAUSE=""
FIX=""
SOURCE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --title)    TITLE="$2"; shift 2 ;;
    --symptom)  SYMPTOM="$2"; shift 2 ;;
    --cause)    CAUSE="$2"; shift 2 ;;
    --fix)      FIX="$2"; shift 2 ;;
    --source)   SOURCE="$2"; shift 2 ;;
    *)          echo "Unknown flag: $1"; exit 1 ;;
  esac
done

# Interactive fallback for any missing fields
prompt_if_empty() {
  local var_name="$1" prompt="$2"
  if [ -z "${!var_name}" ]; then
    printf '%s: ' "$prompt" >&2
    read -r value
    printf -v "$var_name" '%s' "$value"
  fi
}

prompt_if_empty TITLE   "Title (one line)"
prompt_if_empty SYMPTOM "Symptom"
prompt_if_empty CAUSE   "Root cause (not surface cause)"
prompt_if_empty FIX     "Prevention / next-time action"
prompt_if_empty SOURCE  "Source (session / project / file)"

DATE=$(date -u +%Y-%m-%d)

cat >> "$FILE" <<EOF

### $DATE — $TITLE
- **증상**: $SYMPTOM
- **원인**: $CAUSE
- **예방책**: $FIX
- **출처**: $SOURCE
EOF

echo "✅ Appended to $FILE"
tail -7 "$FILE"
