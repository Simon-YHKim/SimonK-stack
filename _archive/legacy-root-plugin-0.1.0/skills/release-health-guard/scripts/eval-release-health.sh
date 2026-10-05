#!/usr/bin/env bash
# eval-release-health.sh — Release health gate for mobile (EAS) releases.
#
# Evaluates a candidate release against the previous one across three gates:
#   1. Absolute thresholds (crash-free sessions/users, ANR rate)
#   2. Regression vs previous release (did this build make things worse?)
#   3. Sample sufficiency (don't block on noise from low traffic)
#
# Inputs are JSON blobs (one per release). No secrets here — the caller
# fetches metrics from Sentry/Crashlytics using env-based auth and passes
# the resulting numbers in. This script does NO network I/O.
#
# Usage:
#   bash eval-release-health.sh \
#     --current  '{"version":"1.4.0","crash_free_sessions":99.2,"crash_free_users":99.6,"anr_rate":0.30,"sessions":8200}' \
#     --previous '{"version":"1.3.0","crash_free_sessions":99.7,"crash_free_users":99.8,"anr_rate":0.22,"sessions":15400}' \
#     [--min-cf-sessions 99.0] [--warn-cf-sessions 99.5] [--min-cf-users 99.5] \
#     [--max-anr 0.47] [--max-regress 0.3] [--min-sessions 1000]
#
# JSON fields (numbers, percentages as plain numbers e.g. 99.2 not 0.992):
#   version, crash_free_sessions, crash_free_users, anr_rate, sessions
#   --previous may be omitted/empty for a first release (regression gate skipped).
#
# Exit codes (verdict):
#   0  PASS  — safe to expand rollout
#   10 WARN  — hold expansion, investigate
#   20 BLOCK — stop/freeze rollout (absolute or regression breach)
#   30 HOLD  — insufficient sample, re-evaluate later (NOT a block)
#   2  usage/parse error
#
# Verdict is advice. Any rollout-control command is the user's decision.

set -uo pipefail

CUR_JSON="" PREV_JSON=""
MIN_CF_SESSIONS=99.0
WARN_CF_SESSIONS=99.5
MIN_CF_USERS=99.5
MAX_ANR=0.47
MAX_REGRESS=0.3
MIN_SESSIONS=1000

log() { echo "[release-health] $*" >&2; }

while [ $# -gt 0 ]; do
  case "$1" in
    --current)          CUR_JSON="${2:-}"; shift 2 ;;
    --previous)         PREV_JSON="${2:-}"; shift 2 ;;
    --min-cf-sessions)  MIN_CF_SESSIONS="${2:-}"; shift 2 ;;
    --warn-cf-sessions) WARN_CF_SESSIONS="${2:-}"; shift 2 ;;
    --min-cf-users)     MIN_CF_USERS="${2:-}"; shift 2 ;;
    --max-anr)          MAX_ANR="${2:-}"; shift 2 ;;
    --max-regress)      MAX_REGRESS="${2:-}"; shift 2 ;;
    --min-sessions)     MIN_SESSIONS="${2:-}"; shift 2 ;;
    -h|--help)          grep -E '^#( |$)' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) log "ERROR: unknown arg '$1'"; exit 2 ;;
  esac
done

if [ -z "$CUR_JSON" ]; then
  log "ERROR: --current JSON is required"
  exit 2
fi

# Extract a numeric field from a JSON blob. Uses jq if present, else a
# portable grep fallback (no nested objects expected here).
field() {
  local json="$1" key="$2"
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$json" | jq -r --arg k "$key" '.[$k] // empty' 2>/dev/null
  else
    printf '%s' "$json" \
      | grep -oE "\"$key\"[[:space:]]*:[[:space:]]*\"?[-0-9.]+\"?" \
      | head -1 \
      | grep -oE '[-0-9.]+' | head -1
  fi
}
str_field() {
  local json="$1" key="$2"
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$json" | jq -r --arg k "$key" '.[$k] // empty' 2>/dev/null
  else
    printf '%s' "$json" \
      | grep -oE "\"$key\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" \
      | head -1 | sed -E 's/.*:[[:space:]]*"([^"]*)"/\1/'
  fi
}

# float compare: cmp A OP B  → echo 1 if true else 0. OP in < > <= >= ==
cmp() {
  awk -v a="$1" -v op="$2" -v b="$3" 'BEGIN{
    if (a=="" || b=="") { print 0; exit }
    if (op=="<")  print (a<b)?1:0;
    else if (op==">")  print (a>b)?1:0;
    else if (op=="<=") print (a<=b)?1:0;
    else if (op==">=") print (a>=b)?1:0;
    else print (a==b)?1:0;
  }'
}
sub() { awk -v a="$1" -v b="$2" 'BEGIN{ printf "%.3f", a-b }'; }

CUR_VER=$(str_field "$CUR_JSON" version)
CUR_CFS=$(field "$CUR_JSON" crash_free_sessions)
CUR_CFU=$(field "$CUR_JSON" crash_free_users)
CUR_ANR=$(field "$CUR_JSON" anr_rate)
CUR_SES=$(field "$CUR_JSON" sessions)

if [ -z "$CUR_CFS" ] || [ -z "$CUR_SES" ]; then
  log "ERROR: --current must include crash_free_sessions and sessions"
  exit 2
fi

HAS_PREV=0
if [ -n "$PREV_JSON" ]; then
  HAS_PREV=1
  PREV_VER=$(str_field "$PREV_JSON" version)
  PREV_CFS=$(field "$PREV_JSON" crash_free_sessions)
fi

log "================================================================"
log "  RELEASE HEALTH GATE"
log "================================================================"
log "current : ${CUR_VER:-?}  crash-free sessions=${CUR_CFS}%  users=${CUR_CFU:-n/a}%  anr=${CUR_ANR:-n/a}%  sessions=${CUR_SES}"
[ "$HAS_PREV" -eq 1 ] && log "previous: ${PREV_VER:-?}  crash-free sessions=${PREV_CFS:-n/a}%"
log "thresholds: cf-sessions block<${MIN_CF_SESSIONS} warn<${WARN_CF_SESSIONS} | cf-users<${MIN_CF_USERS} | anr>${MAX_ANR} | regress>=${MAX_REGRESS}pp | min-sessions=${MIN_SESSIONS}"
log "----------------------------------------------------------------"

VERDICT="PASS"
REASONS=()
note() { REASONS+=("$1"); }
escalate() { # only ever raises severity
  case "$1" in
    HOLD)  [ "$VERDICT" = "PASS" ] && VERDICT="HOLD" ;;
    WARN)  { [ "$VERDICT" = "PASS" ] || [ "$VERDICT" = "HOLD" ]; } && VERDICT="WARN" ;;
    BLOCK) VERDICT="BLOCK" ;;
  esac
}

# Gate 3 first: sample sufficiency. If under-sampled, we never auto-BLOCK.
UNDER_SAMPLED=0
if [ "$(cmp "$CUR_SES" "<" "$MIN_SESSIONS")" = "1" ]; then
  UNDER_SAMPLED=1
  note "표본 부족: sessions=${CUR_SES} < ${MIN_SESSIONS} → 절대/회귀 위반은 BLOCK 대신 보류 처리"
  escalate HOLD
fi

# Gate 1: absolute thresholds
if [ "$(cmp "$CUR_CFS" "<" "$MIN_CF_SESSIONS")" = "1" ]; then
  note "crash-free sessions ${CUR_CFS}% < block 임계 ${MIN_CF_SESSIONS}%"
  [ "$UNDER_SAMPLED" -eq 1 ] && escalate HOLD || escalate BLOCK
elif [ "$(cmp "$CUR_CFS" "<" "$WARN_CF_SESSIONS")" = "1" ]; then
  note "crash-free sessions ${CUR_CFS}% < warn 임계 ${WARN_CF_SESSIONS}%"
  escalate WARN
fi

if [ -n "$CUR_CFU" ] && [ "$(cmp "$CUR_CFU" "<" "$MIN_CF_USERS")" = "1" ]; then
  note "crash-free users ${CUR_CFU}% < ${MIN_CF_USERS}%"
  escalate WARN
fi

if [ -n "$CUR_ANR" ] && [ "$(cmp "$CUR_ANR" ">" "$MAX_ANR")" = "1" ]; then
  note "ANR rate ${CUR_ANR}% > ${MAX_ANR}% (Play 나쁜 동작 임계)"
  [ "$UNDER_SAMPLED" -eq 1 ] && escalate HOLD || escalate BLOCK
fi

# Gate 2: regression vs previous (crash-free sessions drop)
if [ "$HAS_PREV" -eq 1 ] && [ -n "${PREV_CFS:-}" ]; then
  DROP=$(sub "$PREV_CFS" "$CUR_CFS")   # previous - current ; positive = got worse
  if [ "$(cmp "$DROP" ">=" "$MAX_REGRESS")" = "1" ]; then
    note "회귀: crash-free sessions ${PREV_CFS}% → ${CUR_CFS}% (${DROP}pp 하락 ≥ ${MAX_REGRESS}pp)"
    [ "$UNDER_SAMPLED" -eq 1 ] && escalate HOLD || escalate BLOCK
  fi
fi

if [ ${#REASONS[@]} -eq 0 ]; then
  note "모든 게이트 통과 — 다음 단계(%)로 확대 가능"
fi

log "VERDICT: $VERDICT"
for r in "${REASONS[@]}"; do log "  - $r"; done
log "----------------------------------------------------------------"
case "$VERDICT" in
  BLOCK) log "ACTION: staged rollout 확대 중단/동결 권고. top crash 분류(OOM/ANR/네이티브) 후 incident-runbook." ;;
  WARN)  log "ACTION: 확대 보류. 표본 더 쌓고 top crash 조사." ;;
  HOLD)  log "ACTION: 표본 부족 — 자동 차단 금지. 세션 쌓이면 재평가." ;;
  PASS)  log "ACTION: 다음 rollout 단계로 확대 OK." ;;
esac
log "NOTE: 판정은 제안. 어떤 롤아웃 제어 명령도 사용자 confirm 후 실행."
log "================================================================"

case "$VERDICT" in
  PASS)  exit 0 ;;
  WARN)  exit 10 ;;
  BLOCK) exit 20 ;;
  HOLD)  exit 30 ;;
esac
