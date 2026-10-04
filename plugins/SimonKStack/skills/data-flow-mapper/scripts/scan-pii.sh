#!/usr/bin/env bash
# scan-pii.sh — Index candidate PII collection points across a codebase.
#
# Surfaces scanned: PII field keywords, SDK init, network calls,
# 3rd-party env keys, and platform permission declarations.
#
# Usage: bash skills/data-flow-mapper/scripts/scan-pii.sh [project-root]
# Default project-root: current directory
#
# Output: candidate hits to stderr, grouped by surface. This is an
# INDEX of where to look, not an automatic classification. A human
# must review and map results into data-flow.md.
#
# Exit codes:
#   0 — scan completed (hits or no hits)
#   1 — project root not found
#   2 — no search tool available (rg or grep)

set -uo pipefail

ROOT="${1:-.}"
LOG_PREFIX="[pii-scan]"
log() { echo "$LOG_PREFIX $*" >&2; }

if [ ! -d "$ROOT" ]; then
  log "ERROR: project root '$ROOT' not found"
  exit 1
fi

# Prefer ripgrep; fall back to grep -r.
if command -v rg >/dev/null 2>&1; then
  SEARCH() { rg -n -i --no-heading -g '!node_modules' -g '!.git' -g '!dist' -g '!build' -g '!.next' -e "$1" "$ROOT" 2>/dev/null; }
elif command -v grep >/dev/null 2>&1; then
  SEARCH() { grep -rniE --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=dist --exclude-dir=build --exclude-dir=.next "$1" "$ROOT" 2>/dev/null; }
else
  log "ERROR: neither rg nor grep available"
  exit 2
fi

section() {
  log ""
  log "================================================================"
  log "  $1"
  log "================================================================"
}

report() {
  local title="$1" pattern="$2"
  local hits
  hits="$(SEARCH "$pattern")"
  if [ -n "$hits" ]; then
    log "--- $title ---"
    echo "$hits" | head -60 >&2
  fi
}

# 1. PII field keywords (DB columns, form fields, payload keys)
section "1. PII FIELD KEYWORDS (DB columns / payload keys / form fields)"
report "identity"      'email|e-mail|이메일|phone|mobile|전화|휴대폰|\bname\b|fullname|이름'
report "demographics"  'birth|dob|생년월일|\bage\b|나이|gender|성별'
report "location"      'address|주소|postal|\bzip\b|location|\blat\b|\blng\b|gps|geo|위치|precise_location'
report "device/online" 'device_id|idfa|aaid|gaid|advertis|ip_address|user_agent|cookie'
report "sensitive"     'ssn|주민|passport|여권|health|건강|biometric|생체|card|payment|iban|결제'
report "media/contacts" 'photo|image|avatar|contacts|연락처'

# 2. SDK init (auto-collection sources)
section "2. SDK INIT (auto-collection: device id / IP / events)"
report "analytics/ad/crash/push SDK" \
  'firebase|crashlytics|analytics|admob|google-analytics|gtag|posthog|mixpanel|amplitude|sentry|appsflyer|adjust|facebook-sdk|react-native-fbsdk|messaging\(\)|getToken|requestTrackingAuthorization'

# 3. Network calls (where data leaves the app)
section "3. NETWORK CALLS (egress points — review target hosts)"
report "http clients & hosts" \
  'fetch\(|axios|XMLHttpRequest|https?://[a-z0-9.-]+'

# 4. 3rd-party env keys (processor identification)
section "4. ENV / CONFIG KEYS (3rd-party processors)"
for f in "$ROOT"/.env "$ROOT"/.env.* "$ROOT"/app.json "$ROOT"/app.config.* "$ROOT"/eas.json; do
  [ -f "$f" ] || continue
  log "--- keys in $(basename "$f") (values redacted) ---"
  # print key names only, never values
  grep -aoE '^[A-Za-z_][A-Za-z0-9_]*' "$f" 2>/dev/null | sort -u | head -80 >&2
done

# 5. Platform permission declarations
section "5. PLATFORM PERMISSIONS (potential PII sources)"
report "iOS/Android/RN permissions" \
  'NSCameraUsageDescription|NSLocationWhenInUseUsageDescription|NSLocationAlwaysUsageDescription|NSContactsUsageDescription|NSMicrophoneUsageDescription|NSPhotoLibraryUsageDescription|NSUserTrackingUsageDescription|ACCESS_FINE_LOCATION|ACCESS_COARSE_LOCATION|READ_CONTACTS|CAMERA|RECORD_AUDIO|READ_MEDIA_IMAGES|permissions'

log ""
log "================================================================"
log "Scan complete. This is a CANDIDATE index — review each hit by hand"
log "and map into data-flow.md (6-column inventory + risk list)."
log "Never trust auto-classification for legal/privacy artifacts."
log "================================================================"
exit 0
