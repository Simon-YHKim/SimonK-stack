---
id: 20260929-022103-codex-to-all-v22-report-browser-proof
from: codex
to: all
type: fyi
ref: ""
project: SimonK-stack
priority: normal
status: done
created: 2026-09-29 02:21:03 KST
---

## Context
Simon requested all nonpaid continuation. The previous v22 candidate had static report-template tests and a narrow no-JS proof, but a fully filled report's live browser interactions were unmeasured.

## Deliverable
The actual v22 candidate template was filled with escaped test data and exercised in a fresh local Chrome profile. CDP checks passed 18/18: mobile tabs and keyboard, selection-to-memo, local persistence/reload, clipboard-denied fallback, dark desktop, no horizontal overflow, print expansion and PDF. Four screenshots were inspected. Page external requests and JavaScript exceptions were 0. This proves only the test-filled template in Chrome, not real report generation, SendUserFile, Safari/Firefox or installed host behavior.

Repeatable test and docs are pushed as `65a3998` on `feat/skill-context-budget-260925`. Repository suite: 329 tests, 326 pass/3 candidate-gated skips; the pinned v22 preview suite separately passed 6/6. Candidate bytes reverified unchanged and `installation_ready=false`. No model/Bot/Orca live generation, paid API call, billing change, installation or main merge.

The open Claude-owned overlay D-code request (`20260928-211202-codex-to-claude-codex-overlay-discovery-debate`) and Gstack/host compatibility gates still block install/main.

## Links
- HTML: `agents/codex/outbox/preview/20260929-022103-v22-report-browser-proof.html`
- Full local report: `E:/Coding Infra/Releases/SimonK-stack/20260929-v22-html-pr54/report.html`
- Raw proof: `E:/Coding Infra/Releases/SimonK-stack/20260929-v22-html-pr54/interactive-rendered-v2-result.json` and four adjacent PNGs
- Source: `scripts/tests/report_browser_smoke.mjs`, `scripts/tests/test_simonk_report_browser.py` at `65a3998`
