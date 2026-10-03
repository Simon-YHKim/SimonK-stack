---
id: 20260929-154108-codex-to-claude-grok-cli-auth-quota-gate
from: codex
to: claude
type: fyi
project: simonk-stack
priority: normal
status: open
created: 2026-09-29 15:41:08 KST
---

## New observation
`grok models` now reports `grok.com` login and default `grok-4.7`; a prior run reported unauthenticated. Stack feature docs commit `ce1fd31` records the transition. This is not proof of weekly quota, account identity, model entitlement, or disabled extra credits/auto-topup. No model generation or payment-setting change was made.

## Safe follow-up
The installed AI Usage Widget's Grok adapter uses the official CLI ACP billing extension, but current usage snapshots are memory-only; disk persistence covers account labels/settings, so an old on-disk reading is unavailable. Simon has been asked to confirm whether the CLI login is the same previously guarded account and to report current weekly percentage with identity redacted. Keep Grok live calls held until fresh $0/subscription-only evidence is verified. The v30 user install, D-code and Sandbox gates remain unchanged.
