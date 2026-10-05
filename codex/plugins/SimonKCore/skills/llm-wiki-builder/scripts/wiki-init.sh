#!/usr/bin/env bash
# wiki-init.sh — Clone or pull the LLM wiki repo and create the 3-layer structure.
#
# Usage: bash wiki-init.sh
#
# Env:
#   SIMON_WIKI_REPO  — git URL (default: https://github.com/Simon-YHKim/Simon-LLM-Wiki.git)
#   SIMON_WIKI_DIR   — local clone dir (default: ~/.claude/wiki)

set -euo pipefail

WIKI_REPO="${SIMON_WIKI_REPO:-https://github.com/Simon-YHKim/Simon-LLM-Wiki.git}"
WIKI_BASE="${SIMON_WIKI_DIR:-$HOME/.claude/wiki}"
REPO_NAME="$(basename "$WIKI_REPO" .git)"
WIKI_DIR="$WIKI_BASE/$REPO_NAME"

mkdir -p "$WIKI_BASE"

if [ -d "$WIKI_DIR/.git" ]; then
  echo "[wiki-init] Existing wiki found, pulling latest..."
  (cd "$WIKI_DIR" && git pull --rebase || echo "[wiki-init] WARN: pull failed (offline?)")
else
  echo "[wiki-init] Cloning $WIKI_REPO..."
  if ! git clone "$WIKI_REPO" "$WIKI_DIR" 2>/dev/null; then
    echo "[wiki-init] Repo empty or unreachable. Initializing locally..."
    mkdir -p "$WIKI_DIR"
    (cd "$WIKI_DIR" && git init -b main)
    (cd "$WIKI_DIR" && git remote add origin "$WIKI_REPO" 2>/dev/null || true)
  fi
fi

cd "$WIKI_DIR"

# 3-layer structure
mkdir -p raw/articles raw/papers raw/assets
mkdir -p wiki/entities wiki/concepts wiki/sources wiki/queries

# Bootstrap CLAUDE.md if missing
if [ ! -f CLAUDE.md ]; then
  cat > CLAUDE.md <<'SCHEMA'
# Wiki Schema (CLAUDE.md)

This is an LLM-maintained personal wiki following Karpathy's llm-wiki pattern.

## 3-Layer Architecture

- **raw/** — immutable source documents. Never modify.
- **wiki/** — LLM-owned markdown. Create, update, cross-link freely.
- **CLAUDE.md** — this schema file. Co-evolve with usage.

## Page Conventions

- Filenames: kebab-case (e.g. `llm-wiki-pattern.md`)
- Entity pages live in `wiki/entities/<name>.md`
- Concept pages live in `wiki/concepts/<concept>.md`
- Source summaries live in `wiki/sources/<YYYY-MM-DD-slug>.md`
- Query file-backs live in `wiki/queries/<slug>.md`

## Cross-links

Use Obsidian-style: `[[wiki-page-name]]`

## Frontmatter

```yaml
---
type: entity | concept | source | query
sources: [<source-slug>, ...]
last_updated: YYYY-MM-DD
tags: [...]
---
```

## Log Format (`wiki/log.md`)

Append-only, parseable:
```
## [YYYY-MM-DD] <action> | <subject>
- Updated: <pages>
- New: <pages>
- Notes: <optional>
```

`<action>` ∈ {ingest, query, lint, refactor}

## Workflows

1. **Ingest**: source → raw/, summarize → wiki/sources/, update related, log
2. **Query**: search index → read pages → answer with citations → optionally file back to wiki/queries/, log
3. **Lint**: scan contradictions/orphans/stale/missing → wiki/lint-report-<date>.md

## Forbidden

- Modifying raw/ files
- Deleting wiki pages without log entry
- Bypassing log.md
SCHEMA
fi

# Bootstrap index.md
if [ ! -f wiki/index.md ]; then
  cat > wiki/index.md <<'INDEX'
# Wiki Index

Catalog of all wiki pages. Updated on every ingest.

## Entities

_(none yet)_

## Concepts

_(none yet)_

## Sources

_(none yet)_

## Queries

_(none yet)_
INDEX
fi

# Bootstrap log.md
if [ ! -f wiki/log.md ]; then
  cat > wiki/log.md <<LOG
# Wiki Log

Chronological journal. Append-only. Parseable with: \`grep "^## \\[" log.md\`

## [$(date +%Y-%m-%d)] init | wiki initialized
- New: CLAUDE.md, wiki/index.md, wiki/log.md
- Repo: $WIKI_REPO
LOG
fi

echo "[wiki-init] Wiki ready at: $WIKI_DIR"
echo "[wiki-init] Next steps:"
echo "  - Drop sources into $WIKI_DIR/raw/"
echo "  - Run ingest: bash <skill>/scripts/ingest.sh <source>"
echo "  - Open $WIKI_DIR in Obsidian for graph view"
