#!/usr/bin/env bash
# Verify an iOS Universal Links AASA file is hosted correctly.
# Usage: ./verify-aasa.sh <domain> [expected-appID]
#   ./verify-aasa.sh app.example.com TEAMID.com.example.myapp
set -euo pipefail

DOMAIN="${1:?usage: verify-aasa.sh <domain> [appID]}"
APPID="${2:-}"
URL="https://${DOMAIN}/.well-known/apple-app-site-association"

echo "→ GET ${URL}"
# -L would follow redirects; AASA must be served WITHOUT redirects, so we do NOT pass -L.
HEADERS="$(curl -sS -D - -o /tmp/aasa.json "${URL}")"
STATUS="$(printf '%s' "${HEADERS}" | awk 'NR==1{print $2}')"
CTYPE="$(printf '%s' "${HEADERS}" | tr -d '\r' | awk -F': ' 'tolower($1)=="content-type"{print $2}')"

FAIL=0
[ "${STATUS}" = "200" ] && echo "  [ok] HTTP 200" || { echo "  [FAIL] HTTP ${STATUS} (expected 200, no redirect)"; FAIL=1; }
case "${CTYPE}" in
  application/json*|application/pkcs7-mime*) echo "  [ok] Content-Type: ${CTYPE}" ;;
  *) echo "  [WARN] Content-Type: ${CTYPE:-<none>} (Apple expects application/json)";;
esac

if command -v jq >/dev/null 2>&1; then
  jq -e '.applinks.details' /tmp/aasa.json >/dev/null 2>&1 \
    && echo "  [ok] applinks.details present" \
    || { echo "  [FAIL] no applinks.details — malformed AASA"; FAIL=1; }
  if [ -n "${APPID}" ]; then
    jq -e --arg a "${APPID}" '[.applinks.details[].appID] | index($a)' /tmp/aasa.json >/dev/null 2>&1 \
      && echo "  [ok] appID ${APPID} listed" \
      || { echo "  [FAIL] appID ${APPID} NOT found"; FAIL=1; }
  fi
else
  echo "  [info] install jq for structural checks; raw body at /tmp/aasa.json"
fi

echo "  [note] real iOS devices read Apple's CDN cache (app-site-association.cdn-apple.com);"
echo "         changes can lag — reinstall the app to force a refresh."
exit "${FAIL}"
