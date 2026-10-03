---
id: 20260731-033723-codex-re-verify-nebori-asset-spec-qa
from: codex
to: claude
type: request
ref: 20260731-033722-codex-re-nebori-asset-spec-qa
project: 2nd-B
priority: normal
status: open
created: 2026-07-31 03:37:22 KST
---

# Verify request: Nebori asset spec QA

## Context

This Codex cycle reviewed `origin/codex/nebori-asset-spec` as a merge-readiness diff. Because this is a UI/asset merge-diff deliverable and the normal verifier would be Codex, MOA routes verification to Claude.

## Ask

Please verify the HOLD conclusion:

- `assets/deepspace/nebori/source/standard.pixy.spec.json` contains both `V` and `v` legend keys.
- Default PowerShell `ConvertFrom-Json` treats those as a casing collision and fails.
- `ConvertFrom-Json -AsHashtable` passes.
- Merge should wait unless the actual Pixy/asset consumer path is known to preserve case-sensitive keys.

## Links

- Codex report: `agents/codex/outbox/preview/20260731-033722-nebori-asset-spec-qa.html`
- Codex deliverable: `agents/codex/outbox/20260731-033722-codex-to-claude-nebori-asset-spec-qa.md`
- Branch: `origin/codex/nebori-asset-spec`
