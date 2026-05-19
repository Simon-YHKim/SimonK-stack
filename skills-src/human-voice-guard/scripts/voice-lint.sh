#!/usr/bin/env bash
# voice-lint.sh — grep-based anti-LLM voice linter.
#
# Reads optional STYLE.md "어휘 금지" list; scans target paths for known LLM tells.
# Exit 1 on any hit so CI can fail.
#
# Usage:
#   bash voice-lint.sh [target_path ...]   # defaults to current dir
#
# Env:
#   STYLE_FILE   path to STYLE.md (default: ./STYLE.md)
#   STRICT=1     also fail on warnings (em-dash overuse, emoji density)

set -u

STYLE_FILE="${STYLE_FILE:-./STYLE.md}"
STRICT="${STRICT:-0}"

# Built-in LLM tells (always checked; extend via STYLE.md "어휘 금지" section)
BUILTIN_KO=(
  "혁신적"
  "강력한"
  "원활한"
  "직관적"
  "최적화된"
  "도와드립니다"
  "제공해 드립니다"
  "여러분의 소중한"
)
BUILTIN_EN=(
  "leverage"
  "robust"
  "seamless"
  "delve"
  "In conclusion"
  "It's worth noting"
  "I hope this helps"
)

# Extend with STYLE.md user list if present
EXTRA=()
if [ -f "$STYLE_FILE" ]; then
  # Parse the "어휘 금지 목록" section — bullet items only.
  while IFS= read -r line; do
    [ -n "$line" ] && EXTRA+=("$line")
  done < <(awk '
    /^## 어휘 금지/ {flag=1; next}
    /^## / {flag=0}
    flag && /^- / {sub(/^- /,""); print}
  ' "$STYLE_FILE")
fi

ALL=("${BUILTIN_KO[@]}" "${BUILTIN_EN[@]}" "${EXTRA[@]}")

TARGETS=("$@")
[ ${#TARGETS[@]} -eq 0 ] && TARGETS=(.)

HITS=0
for pat in "${ALL[@]}"; do
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    echo "[voice-lint] tell: '$pat' -> $line"
    HITS=$((HITS+1))
  done < <(grep -rIn --exclude-dir=.git --exclude-dir=node_modules \
            --include='*.md' --include='*.txt' \
            -F -- "$pat" "${TARGETS[@]}" 2>/dev/null)
done

# Em-dash overuse (warning unless STRICT)
EM_HITS=$(grep -rIn --exclude-dir=.git --exclude-dir=node_modules \
           --include='*.md' --include='*.txt' \
           -F -- "—" "${TARGETS[@]}" 2>/dev/null | wc -l | tr -d ' ')
if [ "$EM_HITS" -gt 20 ]; then
  echo "[voice-lint] WARN: $EM_HITS em-dashes — consider rewriting some as commas/parentheses"
  [ "$STRICT" = "1" ] && HITS=$((HITS+1))
fi

if [ "$HITS" -eq 0 ]; then
  echo "[voice-lint] OK — no LLM tells found"
  exit 0
fi

echo "[voice-lint] $HITS hit(s)"
exit 1
