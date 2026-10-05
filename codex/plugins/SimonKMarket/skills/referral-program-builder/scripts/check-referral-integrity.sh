#!/usr/bin/env bash
# Read-only PostgreSQL integrity scan for the referral-schema.sql tables.
# Connection comes only from libpq environment / pgpass. Never pass a password
# in argv, print raw referral rows, or source a .env file here.
set -euo pipefail

if (($# != 0)); then
  printf 'usage: set PGHOST, PGDATABASE, PGUSER (and safe libpq auth), then run this script with no arguments\n' >&2
  exit 2
fi
for required in PGHOST PGDATABASE PGUSER; do
  if [[ -z "${!required:-}" ]]; then
    printf 'missing required connection setting: %s\n' "$required" >&2
    exit 2
  fi
done
if ! command -v psql >/dev/null 2>&1; then
  printf 'psql not found; no database query was run\n' >&2
  exit 2
fi

# -X ignores .psqlrc; -w never prompts; ON_ERROR_STOP fails closed. BEGIN READ
# ONLY makes the scan non-mutating even if the login role has write privileges.
if ! results="$(psql -X -w -qAt -v ON_ERROR_STOP=1 <<'SQL'
BEGIN READ ONLY;
SELECT 'self_referral' || '|' || COUNT(*)::text
FROM referrals WHERE referrer_id = referred_id
UNION ALL
SELECT 'duplicate_idempotency_key' || '|' || COALESCE(SUM(n - 1), 0)::text
FROM (
  SELECT COUNT(*) AS n FROM reward_ledger
  GROUP BY idempotency_key HAVING COUNT(*) > 1
) duplicates
UNION ALL
SELECT 'ledger_role_mismatch' || '|' || COUNT(*)::text
FROM reward_ledger l
LEFT JOIN referrals r ON r.id = l.referral_id
WHERE r.id IS NULL OR l.role NOT IN ('referrer', 'referred')
   OR (l.role = 'referrer' AND l.user_id <> r.referrer_id)
   OR (l.role = 'referred' AND l.user_id <> r.referred_id)
UNION ALL
SELECT 'grant_outside_rewarded_state' || '|' || COUNT(*)::text
FROM reward_ledger l
JOIN referrals r ON r.id = l.referral_id
WHERE l.state = 'granted' AND r.status NOT IN ('rewarded', 'clawed_back');
COMMIT;
SQL
)"; then
  printf 'integrity scan failed; database state is unknown\n' >&2
  exit 2
fi

violations=0
rows=0
declare -A seen=()
while IFS='|' read -r check count; do
  case "$check" in
    self_referral|duplicate_idempotency_key|ledger_role_mismatch|grant_outside_rewarded_state) ;;
    *) printf 'unexpected scan output; result is unknown\n' >&2; exit 2 ;;
  esac
  if [[ -n "${seen[$check]:-}" ]]; then
    printf 'duplicate scan output; result is unknown\n' >&2
    exit 2
  fi
  seen[$check]=1
  if [[ ! "$count" =~ ^[0-9]+$ ]]; then
    printf 'non-numeric scan output; result is unknown\n' >&2
    exit 2
  fi
  printf '%s=%s\n' "$check" "$count"
  ((rows += 1))
  if ((count > 0)); then ((violations += count)); fi
done <<< "$results"

if ((rows != 4)) || [[ -z "${seen[self_referral]:-}" || -z "${seen[duplicate_idempotency_key]:-}" \
  || -z "${seen[ledger_role_mismatch]:-}" || -z "${seen[grant_outside_rewarded_state]:-}" ]]; then
  printf 'incomplete scan output; result is unknown\n' >&2
  exit 2
fi
if ((violations > 0)); then
  printf 'integrity violations=%s\n' "$violations" >&2
  exit 1
fi
printf 'integrity checks passed (read-only)\n'
