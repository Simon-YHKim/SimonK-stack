#!/usr/bin/env bash
# check-spec.sh — Validate a spec.md is implementation-ready (deterministic, no LLM).
#
# Checks:
#   1. Required BLOCKER sections exist AND have non-empty body:
#      문제 / 대상 사용자 / 성공 기준 / 범위(In Scope) / 수용 기준
#   2. Counts remaining `OPEN:` markers (unresolved questions).
#   3. Reports declared status (draft|ready) and whether it is consistent.
#
# Usage: bash scripts/check-spec.sh <path-to-spec.md>
#
# Exit codes:
#   0 — All BLOCKER sections filled AND zero OPEN markers (ready for handoff)
#   1 — Missing/empty BLOCKER section OR unresolved OPEN markers (resume interview)
#   2 — File not found / unreadable

set -uo pipefail

LOG_PREFIX="[spec]"
log() { printf '%s %s\n' "$LOG_PREFIX" "$*" >&2; }

SPEC_FILE="${1:-}"

if [ -z "$SPEC_FILE" ]; then
  log "ERROR: usage: bash scripts/check-spec.sh <path-to-spec.md>"
  exit 2
fi

if [ ! -f "$SPEC_FILE" ]; then
  log "ERROR: file not found: $SPEC_FILE"
  exit 2
fi

if [ ! -r "$SPEC_FILE" ]; then
  log "ERROR: file not readable: $SPEC_FILE"
  exit 2
fi

# --- helper: extract the *real* body lines of a markdown section by heading
# keyword. Matches a heading line whose text contains the keyword, then collects
# every line until the next heading (any level) or EOF, and strips lines that
# carry no author content so an untouched template counts as empty:
#   - blank lines and HTML comments
#   - blockquote instruction lines (> ...)
#   - markdown table header/separator rows (|---|, | 상황 | 기대 동작 |)
#   - unfilled angle-bracket placeholders, optionally inside a list/table cell
#     e.g. "- <동작 1>", "| 빈 입력 | <> |", "<지금 무엇이...>"
#   - bare TODO/TBD markers
section_body() {
  local keyword="$1"
  awk -v kw="$keyword" '
    BEGIN { inside = 0 }
    /^#{1,6}[[:space:]]/ {
      if (inside) { inside = 0 }      # next heading closes the section
      if (index($0, kw) > 0) { inside = 1; next }
    }
    inside == 1 { print }
  ' "$SPEC_FILE" \
    | sed -E 's/<!--.*-->//' \
    | grep -vE '^[[:space:]]*$' \
    | grep -vE '^[[:space:]]*>' \
    | grep -vE '^[[:space:]]*\|?[[:space:]]*[-:|[:space:]]+\|?[[:space:]]*$' \
    | grep -ivE '^[[:space:]]*(TODO|TBD|N/?A)[[:space:]]*$' \
    | placeholder_strip
}

# Remove lines whose only non-decoration content is an unfilled <...>
# placeholder. A line counts as a placeholder (no real author content) if,
# after stripping list bullets, numbering, table pipes/cells, inline bold
# labels, key-labels, and the <...> placeholders themselves, nothing
# substantive remains. Examples that are treated as EMPTY:
#   "- <동작 1>"
#   "- 1차 사용자: <누가, 어떤 상황에서>"   (label + placeholder value)
#   "| 빈 입력 | <> |"                       (table cell with placeholder)
#   "1. **Given** <상태> **When** <행동> ..." (scenario skeleton, all <>)
# Examples that are KEPT (real content):
#   "- 1차 사용자: 로그인한 일반 사용자"
#   "사용자가 본 항목을 다시 찾으려면 매번 검색해야 한다."
placeholder_strip() {
  awk '
    {
      line = $0
      # drop leading list/number markers
      sub(/^[[:space:]]*([-*+]|[0-9]+\.)[[:space:]]*/, "", line)
      # drop table pipes -> spaces so cells are evaluated together
      gsub(/\|/, " ", line)
      # drop inline bold labels like **Given** / **When** / **Then**
      gsub(/\*\*[^*]*\*\*/, " ", line)
      # remove every <...> placeholder token
      gsub(/<[^>]*>/, "", line)
      # remove "key:" label fragments whose value (now) is empty. A label is
      # word-ish text ending in a colon; once its placeholder value is gone,
      # the dangling "label:" carries no author content.
      gsub(/[^:[:space:]][^:]*:[[:space:]]*/, " ", line)
      # if what remains is only whitespace/punctuation, no real content existed
      probe = line
      gsub(/[[:space:]:;.,()\/\-]/, "", probe)
      if (probe == "") next
      print $0
    }
  '
}

section_nonempty() {
  local keyword="$1"
  local body
  body="$(section_body "$keyword")"
  [ -n "$body" ]
}

failures=0

# --- 1. BLOCKER sections (heading-keyword : human label) ---
# Keyword is matched against the heading text (handles "## 1. 문제" etc.).
declare -a KEYS=("문제" "대상 사용자" "성공 기준" "In Scope" "수용 기준")
declare -a LABELS=("1. 문제" "2. 대상 사용자" "3. 성공 기준" "4. 범위 (In Scope)" "6. 수용 기준 (Given-When-Then)")

log "Validating $SPEC_FILE"
log "--- BLOCKER sections ---"
for i in "${!KEYS[@]}"; do
  key="${KEYS[$i]}"
  label="${LABELS[$i]}"
  if section_nonempty "$key"; then
    log "  OK    $label"
  else
    log "  EMPTY $label  <- fill before handoff"
    failures=$((failures + 1))
  fi
done

# --- 2. OPEN markers ---
open_count=$(grep -cE '(^|[[:space:]])OPEN:' "$SPEC_FILE" 2>/dev/null || true)
open_count=${open_count:-0}
log "--- Unresolved questions ---"
if [ "$open_count" -gt 0 ]; then
  log "  $open_count OPEN: marker(s) remaining"
  grep -nE '(^|[[:space:]])OPEN:' "$SPEC_FILE" 2>/dev/null | while IFS= read -r line; do
    log "    $line"
  done
  failures=$((failures + 1))
else
  log "  0 OPEN markers"
fi

# --- 3. Declared status consistency (informational) ---
declared_status=$(grep -iE '^\-?[[:space:]]*상태[[:space:]]*:' "$SPEC_FILE" 2>/dev/null | head -1 | sed -E 's/.*상태[[:space:]]*:[[:space:]]*//' | tr -d '\r' | awk '{print $1}')
declared_status=${declared_status:-unknown}
log "--- Declared status ---"
log "  status: $declared_status"
if [ "$declared_status" = "ready" ] && [ "$failures" -gt 0 ]; then
  log "  WARNING: status=ready but $failures issue(s) found — downgrade to draft"
fi

log ""
if [ "$failures" -gt 0 ]; then
  log "RESULT: NOT ready — $failures issue group(s). Resume the spec interview."
  exit 1
fi

log "RESULT: ready — all BLOCKER sections filled, no OPEN markers. Hand off to dev-orchestrator."
exit 0
