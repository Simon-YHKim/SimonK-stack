#!/usr/bin/env bash
# incident-log.sh — solo on-call incident timeline logger.
# Records T0 + SEV on start, appends timestamped notes during response,
# and seeds a postmortem draft on close. No secrets, no network. Pure local files.
#
# Usage:
#   incident-log.sh "<title>" <SEV>     # start a new incident (SEV = SEV1..SEV4 or 1..4)
#   incident-log.sh --note "<text>"     # append a timestamped note to the active incident
#   incident-log.sh --close             # close active incident, seed postmortem draft
#   incident-log.sh --status            # show active incident + recent notes
#
# Files (relative to git root, fallback to CWD):
#   docs/incidents/.active                       # pointer to the active incident log
#   docs/incidents/LOG-<date>-<slug>.md          # live timeline
#   docs/incidents/INCIDENT-<date>-<slug>.md     # postmortem draft (on --close)

set -eu

# --- locate base dir (git root, else CWD) ---
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
INC_DIR="$ROOT/docs/incidents"
ACTIVE="$INC_DIR/.active"
mkdir -p "$INC_DIR"

# --- timestamp helpers (KST display, naming uses local date) ---
now_kst() {
  # Prefer explicit KST; fall back to local time if TZ unsupported.
  TZ="Asia/Seoul" date "+%Y-%m-%d %H:%M" 2>/dev/null || date "+%Y-%m-%d %H:%M"
}
date_tag() {
  TZ="Asia/Seoul" date "+%Y%m%d" 2>/dev/null || date "+%Y%m%d"
}

slugify() {
  # lowercase, spaces/punct -> dash, trim, cap length
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9가-힣]+/-/g; s/^-+//; s/-+$//' \
    | cut -c1-40
}

require_active() {
  if [ ! -f "$ACTIVE" ]; then
    echo "no active incident. start one: incident-log.sh \"<title>\" <SEV>" >&2
    exit 1
  fi
  LOG_FILE="$(cat "$ACTIVE")"
  if [ ! -f "$LOG_FILE" ]; then
    echo "active pointer is stale ($LOG_FILE missing). remove $ACTIVE and restart." >&2
    exit 1
  fi
}

cmd="${1:-}"

case "$cmd" in
  ""|-h|--help)
    sed -n '2,20p' "$0"
    exit 0
    ;;

  --note)
    note="${2:-}"
    [ -n "$note" ] || { echo "usage: incident-log.sh --note \"<text>\"" >&2; exit 1; }
    require_active
    printf '| %s | %s |\n' "$(now_kst)" "$note" >> "$LOG_FILE"
    echo "logged: $note"
    ;;

  --status)
    require_active
    echo "ACTIVE: $LOG_FILE"
    echo "--- recent ---"
    tail -n 8 "$LOG_FILE"
    ;;

  --close)
    require_active
    base="$(basename "$LOG_FILE")"           # LOG-<date>-<slug>.md
    rest="${base#LOG-}"                       # <date>-<slug>.md
    pm_file="$INC_DIR/INCIDENT-${rest}"
    {
      echo "# Postmortem — (fill title)"
      echo
      echo "> seeded from $base on $(now_kst) KST. Fill root cause + action items."
      echo
      echo "## Timeline"
      echo
      echo "| 시각(KST) | 사건 |"
      echo "|---|---|"
      grep -E '^\| ' "$LOG_FILE" | grep -v -E '^\| *시각' | grep -v -E '^\|---' || true
      echo
      echo "## Root cause"
      echo
      echo "(unknown — investigate)"
      echo
      echo "## Action items (min 1)"
      echo
      echo "| 액션 | 분류(예방/탐지/완화) | 기한 |"
      echo "|---|---|---|"
      echo "|  |  |  |"
    } > "$pm_file"
    printf '| %s | 인시던트 종료 (close) |\n' "$(now_kst)" >> "$LOG_FILE"
    rm -f "$ACTIVE"
    echo "closed. postmortem draft: $pm_file"
    echo "next: flesh out root cause + action items, then hand to /retro."
    ;;

  --*)
    echo "unknown flag: $cmd (see --help)" >&2
    exit 1
    ;;

  *)
    # start a new incident
    title="$cmd"
    sev_raw="${2:-}"
    [ -n "$sev_raw" ] || { echo "usage: incident-log.sh \"<title>\" <SEV1..SEV4>" >&2; exit 1; }
    # normalize SEV
    case "$sev_raw" in
      1|SEV1|sev1) sev="SEV1" ;;
      2|SEV2|sev2) sev="SEV2" ;;
      3|SEV3|sev3) sev="SEV3" ;;
      4|SEV4|sev4) sev="SEV4" ;;
      *) echo "SEV must be 1..4 or SEV1..SEV4 (got: $sev_raw)" >&2; exit 1 ;;
    esac

    if [ -f "$ACTIVE" ]; then
      echo "an incident is already active: $(cat "$ACTIVE")" >&2
      echo "close it first (incident-log.sh --close) or remove $ACTIVE." >&2
      exit 1
    fi

    slug="$(slugify "$title")"
    [ -n "$slug" ] || slug="incident"
    log_file="$INC_DIR/LOG-$(date_tag)-${slug}.md"
    t0="$(now_kst)"
    {
      echo "# Incident log — $title"
      echo
      echo "- SEV: $sev"
      echo "- T0 (감지): $t0 KST"
      echo
      echo "| 시각(KST) | 무엇을 했나 / 관찰 |"
      echo "|---|---|"
      printf '| %s | 감지 (T0), %s 판정 |\n' "$t0" "$sev"
    } > "$log_file"
    printf '%s' "$log_file" > "$ACTIVE"
    echo "started $sev: $log_file"
    echo "log steps with: incident-log.sh --note \"...\"  | close with: --close"
    ;;
esac
