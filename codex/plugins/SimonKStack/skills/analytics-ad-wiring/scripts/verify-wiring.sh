#!/usr/bin/env bash
# verify-wiring.sh — analytics-ad-wiring 4대 불변식 정적 검사.
#
# Usage: bash skills/analytics-ad-wiring/scripts/verify-wiring.sh [src-dir]
# Default src-dir: src
#
# 검사 항목:
#   I1 동의 게이트   — 트래커/광고 init·스니펫이 consent 게이트 뒤에 있는지(휴리스틱)
#   I2 fail-open     — 측정/광고 ID env 를 non-null 단언(!)·throw 로 강제하지 않는지
#   I3 택소노미 일치 — track() 인자가 인라인 리터럴이 아니라 상수 import 인지(휴리스틱)
#   하드코딩         — 측정/광고 ID 리터럴이 소스에 박혀 있지 않은지
#   테스트 ID 분리   — 운영 광고 단위 ID 가 개발 폴백 자리에 노출되지 않는지
#
# Exit codes:
#   0 — 통과
#   1 — 불변식 위반 발견
#   2 — 입력 디렉터리 없음

set -uo pipefail

SRC_DIR="${1:-src}"
LOG="[wiring]"
log() { echo "$LOG $*" >&2; }

if [ ! -d "$SRC_DIR" ]; then
  log "ERROR: directory '$SRC_DIR' not found"
  exit 2
fi

if command -v rg >/dev/null 2>&1; then SEARCH="rg -n"; else SEARCH="grep -rn"; fi
EXT_FILTER='--glob=*.{ts,tsx,js,jsx,html,vue,svelte}'
# grep fallback 은 확장자 필터 미지원 — 전체 스캔
grep_src() { if command -v rg >/dev/null 2>&1; then rg -n "$EXT_FILTER" "$@" "$SRC_DIR"; else grep -rn "$@" "$SRC_DIR"; fi; }

fail=0

# ── 하드코딩 ID 검사 ────────────────────────────────
log "[hardcode] 측정/광고 ID 리터럴 검사..."
# GA4: G-XXXXXXXXXX  /  AdSense: ca-pub-16자리  /  AdMob: ca-app-pub-…
HARD=$(grep_src -e 'G-[A-Z0-9]\{10\}' -e 'ca-pub-[0-9]\{16\}' -e 'ca-app-pub-[0-9]' 2>/dev/null \
  | grep -v -e '3940256099942544' -e 'example' -e 'env.example' || true)
if [ -n "$HARD" ]; then
  log "❌ 하드코딩된 측정/광고 ID 의심 (env 주입으로 옮길 것):"
  echo "$HARD" | head -20 >&2
  fail=$((fail + 1))
else
  log "✅ 하드코딩 ID 없음 (테스트 ID 제외)"
fi

# ── I2 fail-open: env non-null 단언 / throw ─────────
log "[I2] env non-null 단언(!) / throw 강제 검사..."
BANG=$(grep_src -e 'process\.env\.[A-Z0-9_]*!' -e 'process\.env\.[A-Z0-9_]*\.[a-z]' 2>/dev/null \
  | grep -iE 'GA4|ANALYTICS|ADSENSE|ADMOB|CLARITY|FIREBASE|GTAG|MEASUREMENT' || true)
if [ -n "$BANG" ]; then
  log "❌ analytics/ad env 에 non-null 단언/직접 접근 — 누락 시 크래시 위험 (fail-open 위반):"
  echo "$BANG" | head -20 >&2
  fail=$((fail + 1))
else
  log "✅ analytics/ad env non-null 단언 없음"
fi

# ── I1 동의 게이트: consent 참조 존재 ───────────────
log "[I1] consent 게이트 참조 존재 검사..."
CONSENT=$(grep_src -i -e 'consent' 2>/dev/null | grep -iE 'granted|gate|consent' || true)
TRACK_CALLS=$(grep_src -e '\.track(' -e 'logEvent(' -e 'gtag(' -e 'injectAnalytics' -e 'injectAds' 2>/dev/null || true)
if [ -n "$TRACK_CALLS" ] && [ -z "$CONSENT" ]; then
  log "❌ 트래커/광고 호출은 있는데 consent 참조가 전혀 없음 — 동의 게이트 누락(I1):"
  echo "$TRACK_CALLS" | head -10 >&2
  fail=$((fail + 1))
elif [ -n "$TRACK_CALLS" ]; then
  log "✅ consent 참조 존재 (게이트 연결 수동 확인 권장)"
else
  log "ℹ️  트래커/광고 호출 미발견 (배선 전이거나 다른 경로)"
fi

# ── I3 택소노미: 인라인 이벤트명 리터럴 ─────────────
log "[I3] track() 인라인 이벤트명 리터럴 검사..."
INLINE=$(grep_src -e "\.track(['\"]" -e "logEvent(['\"]" 2>/dev/null || true)
if [ -n "$INLINE" ]; then
  log "⚠️  track()/logEvent() 에 인라인 문자열 이벤트명 — 택소노미 상수 import 권장(I3):"
  echo "$INLINE" | head -20 >&2
  # 경고만. 강제 실패는 아님(상수 파일 자체일 수 있음).
else
  log "✅ 인라인 이벤트명 리터럴 없음"
fi

# ── 테스트 ID 분리: 운영 단위가 개발 폴백에 노출 ────
log "[test-id] 개발 폴백에 운영 광고 단위 노출 검사..."
# 같은 줄에 운영 광고 단위 ID(테스트 publisher 3940256099942544 제외) + dev/test 키워드가 동시에 있으면 의심.
PROD_FALLBACK=$(grep_src -e 'ca-app-pub-[0-9]\{16\}/' 2>/dev/null \
  | grep -v '3940256099942544' | grep -iE '\b(test|dev|fallback)\b' || true)
if [ -n "$PROD_FALLBACK" ]; then
  log "⚠️  운영 광고 단위 ID 가 테스트/개발 경로 근처에 노출됨 — 분리 확인:"
  echo "$PROD_FALLBACK" | head -10 >&2
else
  log "✅ 테스트/운영 광고 ID 분리 정상"
fi

echo "" >&2
if [ "$fail" -gt 0 ]; then
  log "❌ wiring 검증 실패 — $fail 개 불변식 위반"
  exit 1
fi
log "✅ wiring 검증 통과 (경고는 위 로그에서 수동 확인)"
exit 0
