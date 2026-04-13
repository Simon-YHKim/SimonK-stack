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

# Count entries per file.
# Count all ### headings; template placeholders (### YYYY-MM-DD style)
# are filtered out only from the recent-mistakes display below.
for f in mistakes-learned project-patterns korean-context tool-quirks; do
  path="$INSTINCTS/$f.md"
  [ -f "$path" ] || continue
  # Use grep | wc -l instead of grep -c to avoid the dual-output quirk
  # where grep -c prints "0" and exits 1, then `|| echo 0` prints
  # another "0" concatenated.
  entries=$(grep -c "^### " "$path" 2>/dev/null | tr -d ' \n')
  [ -z "$entries" ] && entries=0
  # Exclude the "### YYYY-..." placeholder from mistakes-learned count.
  if [ "$f" = "mistakes-learned" ]; then
    placeholder=$(grep -c "^### YYYY" "$path" 2>/dev/null | tr -d ' \n')
    [ -z "$placeholder" ] && placeholder=0
    entries=$((entries - placeholder))
  fi
  lines=$(wc -l <"$path" 2>/dev/null | tr -d ' \n')
  [ -z "$lines" ] && lines=0
  printf '  - %-18s %s entries, %s lines\n' "$f:" "$entries" "$lines"
done

# Show most recent 3 real mistakes (exclude template placeholder).
# Match dated entries only (### 20xx-...).
if [ -f "$INSTINCTS/mistakes-learned.md" ]; then
  recent=$(awk '
    /^### [0-9]/ { count++; show=1; if (count>3) exit }
    show { print "    " $0 }
    /^### [0-9]/ { next }
    /^- \*\*증상\*\*/ && show { show=0 }
  ' "$INSTINCTS/mistakes-learned.md" 2>/dev/null)

  if [ -n "$recent" ]; then
    echo ""
    echo "  Recent mistakes to avoid:"
    echo "$recent"
  fi
fi

echo ""
echo "  Full read: cat ~/.claude/instincts/*.md"
echo "==========================================="
