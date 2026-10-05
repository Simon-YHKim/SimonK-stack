#!/usr/bin/env bash
# scan-retention.sh — Index retention/purge-relevant surfaces across a codebase.
#
# Surfaces scanned: timestamp/lifecycle columns, existing TTL/cron config,
# backup config, object-storage lifecycle rules, and hard-delete call sites.
#
# Usage: bash skills/data-retention-planner/scripts/scan-retention.sh [project-root]
# Default project-root: current directory
#
# Output: candidate hits to stderr, grouped by surface. This is an INDEX of
# where retention logic lives (or is missing), NOT an automatic classification.
# A human must map each hit into retention-classes.json.
#
# Exit codes:
#   0 — scan completed (hits or no hits)
#   1 — project root not found
#   2 — no search tool available (rg or grep)

set -uo pipefail

ROOT="${1:-.}"
LOG_PREFIX="[retention-scan]"
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
  else
    log "--- $title --- (no hits)"
  fi
}

# 1. Lifecycle timestamp columns — the hooks a purge job needs.
section "1. LIFECYCLE TIMESTAMP COLUMNS (what a purge job filters on)"
report "creation"     'created_at|inserted_at|createdAt|created_on|생성일'
report "soft-delete"  'deleted_at|deletedAt|is_deleted|removed_at|soft_delete|archived_at'
report "expiry/TTL"   'expires_at|expiresAt|expire_at|ttl|valid_until|expiry|만료'
report "last-seen"    'last_seen|last_active|lastLogin|last_login|휴면|dormant'

# 2. Existing TTL / scheduled purge logic.
section "2. EXISTING TTL / CRON PURGE LOGIC (don't duplicate; review correctness)"
report "scheduler"    'pg_cron|cron\(|schedule:|crontab|cron_schedule|cloud scheduler|vercel.*cron|node-cron'
report "purge calls"  '\bpurge\b|\bprune\b|cleanup|reap|sweep|expire|retention|setTTL|createTTLIndex|expireAfterSeconds'

# 3. Hard-delete call sites — must be gated behind soft-delete + grace.
section "3. HARD-DELETE CALL SITES (must sit behind soft-delete + grace)"
report "raw deletes"  'DELETE FROM|\.delete\(|\.destroy\(|\.remove\(|deleteMany|drop\(|truncate'

# 4. Backup configuration — must align with retention windows.
section "4. BACKUP CONFIG (retention window must be aligned to shortest class)"
report "backup config" 'backup|pg_dump|snapshot|retention.*day|backup_retention|wal|pitr|point.in.time'

# 5. Object-storage lifecycle rules.
section "5. OBJECT-STORAGE LIFECYCLE (S3 / R2 / GCS expiry rules)"
report "storage lifecycle" 'lifecycle|LifecycleConfiguration|s3.*expire|r2.*lifecycle|gcs.*lifecycle|object.*expir|presigned'

# 6. Legal-retention markers — must be split into their own class.
section "6. LEGAL-RETENTION MARKERS (split into legal_txn class, expire independently)"
report "legal records" 'invoice|receipt|payment|transaction|결제|거래|영수증|세금계산서|tax|order_history|거래기록'

# 7. Env / config keys (scheduler + service-role secrets — names only).
section "7. ENV / CONFIG KEYS (scheduler & service-role — values redacted)"
for f in "$ROOT"/.env "$ROOT"/.env.* "$ROOT"/app.json "$ROOT"/app.config.* "$ROOT"/eas.json; do
  [ -f "$f" ] || continue
  log "--- keys in $(basename "$f") (values redacted) ---"
  grep -aoE '^[A-Za-z_][A-Za-z0-9_]*' "$f" 2>/dev/null | sort -u | head -80 >&2
done

log ""
log "================================================================"
log "Scan complete. This is a CANDIDATE index — map each hit into"
log "retention-classes.json by hand, then run gen-purge-plan.mjs."
log "Reminder: timestamp columns missing = a class that CANNOT be purged."
log "Never trust auto-classification for legal/privacy artifacts."
log "================================================================"
exit 0
