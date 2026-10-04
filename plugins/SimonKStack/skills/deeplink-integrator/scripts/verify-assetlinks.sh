#!/usr/bin/env bash
# Verify an Android App Links assetlinks.json is hosted and validates.
# Usage: ./verify-assetlinks.sh <domain> <package-name>
#   ./verify-assetlinks.sh app.example.com com.example.myapp
set -euo pipefail

DOMAIN="${1:?usage: verify-assetlinks.sh <domain> <package-name>}"
PKG="${2:?usage: verify-assetlinks.sh <domain> <package-name>}"
URL="https://${DOMAIN}/.well-known/assetlinks.json"

echo "→ GET ${URL}"
STATUS="$(curl -sS -o /tmp/assetlinks.json -w '%{http_code}' "${URL}")"
FAIL=0
[ "${STATUS}" = "200" ] && echo "  [ok] HTTP 200" || { echo "  [FAIL] HTTP ${STATUS}"; FAIL=1; }

if command -v jq >/dev/null 2>&1; then
  jq -e --arg p "${PKG}" \
    '[.[] | select(.target.package_name==$p) | .target.sha256_cert_fingerprints[]?] | length > 0' \
    /tmp/assetlinks.json >/dev/null 2>&1 \
    && echo "  [ok] sha256 fingerprints present for ${PKG}" \
    || { echo "  [FAIL] no sha256 fingerprints for ${PKG} — link verification will fail"; FAIL=1; }
else
  echo "  [info] install jq for structural checks; raw body at /tmp/assetlinks.json"
fi

# Authoritative check via Google's Digital Asset Links API (mirrors what Android does).
API="https://digitalassetlinks.googleapis.com/v1/assetlinks:check"
QS="source.web.site=https://${DOMAIN}&relation=delegate_permission/common.handle_all_urls"
QS="${QS}&target.android_app.package_name=${PKG}"
echo "→ Google Digital Asset Links check"
RESP="$(curl -sS "${API}?${QS}" || true)"
if printf '%s' "${RESP}" | grep -q '"linked": true'; then
  echo "  [ok] Google API reports linked: true"
else
  echo "  [FAIL] Google API did not confirm the link. Response:"
  printf '%s\n' "${RESP}" | sed 's/^/    /'
  echo "  → most common cause: SHA-256 fingerprint mismatch (add debug + release + Play app-signing keys)."
  FAIL=1
fi

echo "  [tip] on-device check:"
echo "        adb shell am start -a android.intent.action.VIEW -d \"https://${DOMAIN}/post/123\""
echo "        (opens the app directly if verified; shows a chooser if not)"
exit "${FAIL}"
