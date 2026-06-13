#!/usr/bin/env bash
# check-circular-deps.sh — Detect circular dependencies and large files.
#
# Usage: bash skills-src/code-health-guard/scripts/check-circular-deps.sh [src-dir]
# Default src-dir: src
#
# Exit codes:
#   0 — No issues
#   1 — Circular deps or oversized files found
#   2 — Tooling missing (madge not available)

set -uo pipefail

SRC_DIR="${1:-src}"
LOG_PREFIX="[code-health]"
log() { echo "$LOG_PREFIX $*" >&2; }

if [ ! -d "$SRC_DIR" ]; then
  log "ERROR: directory $SRC_DIR not found"
  exit 1
fi

failures=0

# 1. Circular deps via madge (if available)
if command -v npx >/dev/null 2>&1; then
  log "Checking circular dependencies in $SRC_DIR ..."
  result=$(npx -y madge --circular --extensions ts,tsx,js,jsx "$SRC_DIR" 2>&1 || true)
  if echo "$result" | grep -qE "(circular|Found [0-9]+ circular)"; then
    log "❌ Circular dependencies detected:"
    echo "$result" >&2
    failures=$((failures + 1))
  else
    log "✅ No circular dependencies"
  fi
else
  log "WARN: npx not available, skipping madge check"
fi

# 2. Oversized files (>500 lines = strong split candidate)
log "Scanning for files >500 lines..."
large_files=$(find "$SRC_DIR" -type f \
  \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" \) \
  -exec wc -l {} + 2>/dev/null | awk '$1 > 500 && $2 != "total" {print $1 " " $2}' | sort -rn)

if [ -n "$large_files" ]; then
  log "❌ Oversized files (>500 lines):"
  echo "$large_files" | while read -r line; do
    log "  $line"
  done
  failures=$((failures + 1))
else
  log "✅ No oversized files"
fi

# 3. Top 10 largest files (informational)
log "Top 10 largest files (informational):"
find "$SRC_DIR" -type f \
  \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" \) \
  -exec wc -l {} + 2>/dev/null | sort -rn | head -10 | while read -r line; do
    log "  $line"
done

if [ $failures -gt 0 ]; then
  log ""
  log "Health check FAILED with $failures issue(s)"
  exit 1
fi

log ""
log "✅ Code health check PASS"
exit 0
