#!/usr/bin/env bash
# SessionStart hook — prints instincts summary at Claude Code session start.
# Reads ~/.claude/instincts/*.md and outputs recent highlights so Claude
# self-loads accumulated learnings without needing to re-read files.

set -e

INSTINCTS=~/.claude/instincts

if [ ! -d "$INSTINCTS" ]; then
  exit 0
fi

echo "=== Simon Instincts (auto-loaded) ==="

# Count entries per file
for f in mistakes-learned project-patterns korean-context tool-quirks; do
  path="$INSTINCTS/$f.md"
  [ -f "$path" ] || continue
  entries=$(grep -c "^### " "$path" 2>/dev/null || echo 0)
  lines=$(wc -l <"$path" 2>/dev/null || echo 0)
  echo "  - $f: $entries entries, $lines lines"
done

# Show most recent 3 mistakes (top of log section)
if [ -f "$INSTINCTS/mistakes-learned.md" ]; then
  recent=$(grep -A 1 "^### " "$INSTINCTS/mistakes-learned.md" 2>/dev/null | head -9 | sed 's/^/    /')
  if [ -n "$recent" ]; then
    echo ""
    echo "  Recent mistakes to avoid:"
    echo "$recent"
  fi
fi

echo ""
echo "  Full read: cat ~/.claude/instincts/*.md"
echo "==========================================="
