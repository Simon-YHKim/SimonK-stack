#!/usr/bin/env bash
# iap-configure.sh — Cross-platform runner for the IAP product builder.
#
# Validates a product manifest and emits a localized price plan. Pure logic,
# no network. Delegates to iap-build.mjs (Node, no dependencies).
#
# Usage:
#   bash iap-configure.sh <manifest.json>          # validate + write plan.json
#   bash iap-configure.sh <manifest.json> --check  # validate only
#   bash iap-configure.sh <manifest.json> --table  # also print a review table
#
# Exit codes:
#   0  valid
#   1  validation error
#   2  usage / missing Node
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="${1:-}"
shift || true

if [ -z "${MANIFEST}" ]; then
  echo "usage: bash iap-configure.sh <manifest.json> [--check] [--table]" >&2
  exit 2
fi
if [ ! -f "${MANIFEST}" ]; then
  echo "[error] manifest not found: ${MANIFEST}" >&2
  exit 2
fi
if ! command -v node >/dev/null 2>&1; then
  echo "[error] node not found on PATH — install Node 18+ to run the builder" >&2
  exit 2
fi

ARGS=("$@")
if printf '%s\n' "${ARGS[@]:-}" | grep -q -- '--check'; then
  node "${HERE}/iap-build.mjs" "${MANIFEST}" "${ARGS[@]}"
  exit $?
fi

# Default: write the plan next to the manifest as <name>.plan.json.
OUT="${MANIFEST%.json}.plan.json"
if node "${HERE}/iap-build.mjs" "${MANIFEST}" "${ARGS[@]}" > "${OUT}"; then
  echo "[ok] price plan written → ${OUT}" >&2
  exit 0
else
  rc=$?
  rm -f "${OUT}"
  exit "${rc}"
fi
