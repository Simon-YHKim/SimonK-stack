#!/usr/bin/env bash
# audit-img-tags.sh — scan a Next.js project for <img> tags that should be next/image.
#
# Usage: bash audit-img-tags.sh [path=.]
#
# Why: <img> tags skip next/image's automatic lazy loading, format conversion
# (WebP/AVIF), and width/height enforcement. Missing width/height causes CLS
# (layout shift), which tanks Core Web Vitals.
#
# What the script reports:
#   1. count of <img> tags per file
#   2. suggested next/image replacement snippet
#   3. files using raw <img> tags sorted by severity

set -euo pipefail

ROOT="${1:-.}"
cd "$ROOT"

if [ ! -f package.json ]; then
  echo "⚠️  No package.json found at $ROOT — is this a Node project?"
  exit 1
fi

if ! grep -q '"next"' package.json; then
  echo "⚠️  This doesn't look like a Next.js project (no 'next' in package.json)"
  exit 1
fi

echo "=== next/image audit — $ROOT ==="
echo

# Find all <img> tags in .tsx/.jsx/.ts/.js files under src/ app/ pages/ components/
FILES=$(find src app pages components 2>/dev/null -type f \( -name "*.tsx" -o -name "*.jsx" -o -name "*.ts" -o -name "*.js" \) 2>/dev/null || true)

if [ -z "$FILES" ]; then
  echo "No component source files found in standard directories."
  exit 0
fi

TOTAL=0
FILES_WITH_IMG=0

while IFS= read -r file; do
  count=$(grep -c '<img\b' "$file" 2>/dev/null || echo 0)
  if [ "$count" -gt 0 ]; then
    TOTAL=$((TOTAL + count))
    FILES_WITH_IMG=$((FILES_WITH_IMG + 1))
    printf '%4d  %s\n' "$count" "$file"
  fi
done <<< "$FILES" | sort -rn

echo
echo "=== Summary ==="
echo "  files with raw <img>: $FILES_WITH_IMG"
echo "  total <img> occurrences: $TOTAL"

if [ "$TOTAL" -eq 0 ]; then
  echo
  echo "✅ No raw <img> tags found. Good Core Web Vitals hygiene."
  exit 0
fi

cat <<'TIPS'

=== Replacement guidance ===

Replace each <img> with next/image:

  // Before
  <img src="/hero.jpg" alt="Hero" />

  // After
  import Image from 'next/image';
  <Image
    src="/hero.jpg"
    alt="Hero"
    width={1200}              // Required, prevents CLS
    height={630}              // Required, prevents CLS
    priority                  // Only for above-the-fold images
    sizes="(max-width: 768px) 100vw, 50vw"
    placeholder="blur"        // Optional, requires blurDataURL for /public assets
  />

Key rules:
  - width+height are required (or use `fill` inside a sized parent)
  - `priority` only on images visible on first paint (LCP candidates)
  - `sizes` tells Next which variant to serve at each breakpoint
  - For remote images, add the domain to next.config.js `images.remotePatterns`

Run `npm run build` after each batch and check bundle diff.
TIPS
