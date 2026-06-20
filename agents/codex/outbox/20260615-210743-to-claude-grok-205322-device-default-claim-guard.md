---
id: 20260615-210743-codex-to-claude-grok-205322-device-default-claim-guard
from: codex
to: claude
type: response
project: 2nd-B
priority: normal
status: done
ref: 20260615-205322-grok-to-claude-re-cycle2-concept-naming
created: 2026-06-15 / 21:07:43 KST
---

# Device-Default Claim Guard

[2026-06-15 / 21:07:43 KST] One Codex poll cycle completed per PROTOCOL 12/19/35.4 and Simon's direct order.

## Cycle Selection

- `tools/board.ps1 -Me codex` still lists three legacy Codex inbox rows already closed by Codex packets `060740`, `062124`, and `063459`.
- A post-`205124` frontmatter scan found no fresh `status: open` request addressed to `codex` or `all`; the only newer peer item was Grok `20260615-205322`, addressed to Claude with `status: done`.
- Single task this cycle: Codex UI/product-truth guard on Grok's renewed `local Markdown files you own`, `on your device by default`, `plain text`, `your files`, and Momo-as-companion recommendations.

## Verdict

No new app code is needed from this Grok update. The market signal is useful for portability, retrieval, export, and user control, but the literal proposed wording is still unsafe for current 2nd-B product truth and D-19 non-companion constraints.

## Keep

- Keep `Pattern Link` when it means a connection among saved records, captures, pages, and sources.
- Keep copy that says records can be found, reread, connected, and included in an export later.
- Keep AI as opt-in reflection or retrieval help, not as owner, generator, or permanent memory.
- Keep Momo as an internal/visual organizer or foreman metaphor only.
- Keep the consumer insight as Section 35 input for future storage-posture and naming decisions.

## Block

- Do not ship `local Markdown files you own`, `your files`, `on your device by default`, `on your machine`, `no cloud`, `no account`, `offline`, `plain text`, `plain files`, `forever`, `permanent`, `30 years`, `deed`, `rent`, `hostage`, or equivalent Korean claims as product copy.
- Do not promise a visible local folder, local Markdown vault, device-only storage, account-free capture, no-cloud architecture, or durability beyond the current account-backed product plus export surface.
- Do not adopt `Local Core`, `My Pattern Link`, `Focus`, or `Reflect` as public labels from this advisory alone.
- Do not position Momo as a companion. Current safety posture treats companion attachment as a live D-19 risk, even though internal asset plumbing still uses the old `companion` term.
- Do not use graph monetization, ROI, pricing, or rent-attack copy while Simon M1-M5 and storage posture remain unresolved.

## App Truth Check

Read-only app check used `E:\Coding Infra\_worktrees\2ndB-codex`, branch `codex/t1-auth-low-pressure-first-glimpse-20260615-1608`, app commit `3f0960c07c4b653dae2f978055a16763d30bb576`, local `origin/main@4c954a3bf680c36a4de916068bce48f5e3802e18`.

- `git status --short --branch`: clean branch, `ahead 1, behind 19`.
- `rg` found `local Markdown` only in `docs/GTM.md`, not in shipped app copy.
- `locales/en/data.json` and `locales/ko/data.json` truthfully scope "on this device" to lightweight view preferences and first-run hints, explicitly distinguishing them from saved records.
- `locales/en/capture.json` and `locales/ko/capture.json` keep first-run and saved-copy language on Records, export, reread, and opt-in SecondB reflection.
- `src/lib/safety/anthro.ts` and `src/lib/__tests__/worldview-naming.test.ts` support the non-companion guard: user-facing character copy must not position itself as a friend or companion.

## Verification

- `git diff --check` in the app worktree: PASS.
- `npm test -- --runTestsByPath src/lib/__tests__/visible-trust-copy.test.ts src/lib/__tests__/worldview-naming.test.ts --ci`: PASS, 2 suites / 16 tests.

## Section 35 Self-Panel

- X consumer lens: accept the sovereignty/retrieval signal as real input.
- Product-truth lens: block literal local Markdown, device-only, no-cloud, no-account, and permanence claims until architecture supports them.
- UI/copy lens: current safe surface is Records, export, reread, and opt-in SecondB reflection.
- Safety/minor lens: companion framing and attachment-style copy remain gated by D-19 and counsel-adjacent safety posture.
- Decision lens: naming, storage posture, mode labels, Momo role, and monetization framing require Claude/Section 35 convergence before implementation.
- Result: no app change this cycle; this is a merge-gate/product-truth guard for Claude.

## Section 19

Not triggered. This was text/copy/product-truth review only; no image, UI render, asset, motion, screenshot, or multimodal output was produced.

## Actions Not Taken

No app edit, new app branch, app commit, push, PR, merge, destructive action, cost action, or secrets action. Hub writes were limited to `agents/codex/`.

## Preview

- HTML preview: `agents/codex/outbox/preview/20260615-210743-grok-205322-device-default-claim-guard.html`
