#!/usr/bin/env bash
# generate-prompts.sh — read DESIGN.md, emit Stitch prompts (A/B/C × screens).
#
# Usage: bash generate-prompts.sh [path/to/DESIGN.md]
#
# Outputs to docs/design/stitch-prompts-<YYYY-MM-DD>.md and also prints to stdout.
#
# This script is intentionally simple — bash + grep + awk. It does NOT call
# any API or MCP. It is pure text transformation. If parsing fails on a
# non-standard DESIGN.md, fall back to manually applying the template from
# references/prompt-template.md.

set -euo pipefail

DESIGN_MD="${1:-DESIGN.md}"

if [ ! -f "$DESIGN_MD" ]; then
  echo "ERROR: $DESIGN_MD not found. Run /design-consultation first to create it." >&2
  exit 1
fi

# -----------------------------------------------------------------------------
# Extract the six brand inputs.
# The parser looks for canonical headings; if your DESIGN.md uses different
# structure, edit the regexes below or fall back to manual template use.
# -----------------------------------------------------------------------------

extract_section() {
  local heading="$1"
  awk -v h="$heading" '
    $0 ~ "^##+ +" h { flag=1; next }
    flag && /^##+ / { flag=0 }
    flag && NF { print }
  ' "$DESIGN_MD" | head -20
}

PRODUCT=$(grep -m1 -iE "^# " "$DESIGN_MD" | sed 's/^# *//' || echo "Untitled Product")
PITCH=$(extract_section "한 줄|pitch|tagline|one.?liner" | head -1)
AUDIENCE=$(extract_section "target|타깃|audience|user" | head -1)
TONE=$(extract_section "tone|톤|mood|vibe" | head -1)
COLORS=$(extract_section "color|컬러|palette" | head -3)
FONTS=$(extract_section "typograph|폰트|font" | head -3)
SCREENS=$(extract_section "screen|화면|page|route" | head -5)

# Default fallbacks if parsing came up empty
: "${PITCH:=<one-line product pitch>}"
: "${AUDIENCE:=<target users>}"
: "${TONE:=modern, minimal}"
: "${COLORS:=primary #000, accent #0070F3}"
: "${FONTS:=Inter body, Satoshi display}"
: "${SCREENS:=landing, dashboard, detail}"

OUT_DIR="docs/design"
OUT_FILE="$OUT_DIR/stitch-prompts-$(date +%Y-%m-%d).md"
mkdir -p "$OUT_DIR"

# -----------------------------------------------------------------------------
# Write the three variants per screen.
# -----------------------------------------------------------------------------

emit_prompt() {
  local variant="$1"     # A / B / C
  local label="$2"       # Safe / Bold / Wild
  local reference="$3"   # style reference
  local screen="$4"
  cat <<EOF

### Variant $variant — $label ($screen)

\`\`\`
Design a $screen for $PRODUCT.
Pitch: $PITCH
Target users: $AUDIENCE
Tone: $TONE (leaning $label)
Colors: $COLORS
Typography: $FONTS

Constraints:
- Mobile-first, 375px viewport baseline
- WCAG AA contrast
- Korean + English copy (한/영 병기) if target is Korean
- No stock photography — illustrations or abstract shapes only
- Max 3 typography weights per screen

Style reference: $reference
\`\`\`

EOF
}

{
  echo "# Stitch Prompts — $PRODUCT"
  echo
  echo "Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "Source: $DESIGN_MD"
  echo
  echo "Paste **one prompt at a time** into https://stitch.withgoogle.com. Batching confuses the parser."
  echo "After each output, save the image as \`docs/design/stitch-output-<variant>-<screen>.png\`."
  echo
  echo "---"

  # Split SCREENS into individual screens (comma or newline separated)
  echo "$SCREENS" | tr ',\n' '\n' | sed 's/^ *//; s/ *$//' | grep -v '^$' | while read -r screen; do
    echo
    echo "## Screen: $screen"
    emit_prompt A "Safe"  "Stripe, Linear, Vercel"        "$screen"
    emit_prompt B "Bold"  "Figma, Notion, Arc"            "$screen"
    emit_prompt C "Wild"  "Raycast, Rauno Freiberg demos" "$screen"
  done

  echo "---"
  echo
  echo "Next: run \`/design-shotgun\` once you have 3+ images saved."
} | tee "$OUT_FILE"

echo
echo "✅ Saved: $OUT_FILE"
