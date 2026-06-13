#!/usr/bin/env bash
# tdd-guard-check.sh — Block commits that change source without corresponding tests.
#
# Usage: bash skills-src/simon-tdd/scripts/tdd-guard-check.sh
# Exit codes:
#   0 — All source changes have corresponding test changes
#   1 — TDD violation: source changed without test
#   2 — No staged changes (nothing to check)
#
# Integrate as pre-commit hook for hard enforcement.

set -uo pipefail

LOG_PREFIX="[tdd-guard]"
log() { echo "$LOG_PREFIX $*" >&2; }

# Get staged files
staged=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null)

if [ -z "$staged" ]; then
  log "No staged changes."
  exit 2
fi

# Source file patterns (extend as needed)
is_source() {
  case "$1" in
    *.ts|*.tsx|*.js|*.jsx|*.py|*.go|*.rs|*.rb|*.java|*.kt|*.swift) return 0 ;;
    *) return 1 ;;
  esac
}

# Test file patterns
is_test() {
  case "$1" in
    *.test.*|*.spec.*|test_*.py|*_test.py|*_test.go|*.test.ts|*.test.tsx) return 0 ;;
    */tests/*|*/test/*|*/__tests__/*|*/spec/*) return 0 ;;
    *) return 1 ;;
  esac
}

# Skip patterns (docs, configs, etc.)
is_skip() {
  case "$1" in
    *.md|*.json|*.yml|*.yaml|*.toml|*.txt|*.lock|*.gitignore|*.env*) return 0 ;;
    package.json|tsconfig.json|*.config.*) return 0 ;;
    *) return 1 ;;
  esac
}

violations=()
test_changed=false

while IFS= read -r file; do
  [ -z "$file" ] && continue
  is_skip "$file" && continue
  if is_test "$file"; then
    test_changed=true
    continue
  fi
  if is_source "$file"; then
    # Check: does this source file have a corresponding test file in staging?
    base=$(basename "$file")
    name="${base%.*}"
    ext="${base##*.}"
    # Look for matching test in staged files
    found=false
    while IFS= read -r staged_file; do
      [ -z "$staged_file" ] && continue
      sb=$(basename "$staged_file")
      case "$sb" in
        "${name}.test.${ext}"|"${name}.spec.${ext}"|"test_${name}.py"|"${name}_test.py"|"${name}_test.go")
          found=true; break ;;
      esac
      # Also match by directory: same dir + tests/ subdir
      sd=$(dirname "$staged_file")
      fd=$(dirname "$file")
      if [ "$sd" = "$fd/tests" ] || [ "$sd" = "$fd/__tests__" ]; then
        found=true; break
      fi
    done <<< "$staged"
    if [ "$found" = "false" ]; then
      violations+=("$file")
    fi
  fi
done <<< "$staged"

if [ ${#violations[@]} -eq 0 ]; then
  log "✅ TDD Guard PASS — all source changes have tests."
  exit 0
fi

log "❌ TDD Guard FAIL — source changes without corresponding tests:"
for v in "${violations[@]}"; do
  log "  - $v"
done
log ""
log "Add test files to the same commit, or use --no-verify to bypass (not recommended)."
exit 1
