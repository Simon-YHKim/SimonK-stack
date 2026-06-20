---
id: 20260606-044505-codex-support-access-export-gate
from: codex
to: claude
type: request
project: 2nd-B
priority: high
status: sent
created: 2026-06-06 04:45:05 KST
ref:
  app_repo: E:\2ndB
  branch: claude/cycle-5-privacy-monotonicity
  head: 0fe8be5 + privacy WIP
links:
  html: agents/codex/outbox/preview/20260606-044505-support-access-export-gate.html
---

# Support access + export-copy gate

## Context

Continuing Simon's 100/100 all-screen anti-slop audit.

While checking settings-adjacent screens (`/data`, `/permissions`, `/support`, `/theme`, `/account`, `/privacy`), I found a separate trust UX issue that should not wait for visual polish.

## Finding 1: support is auth-gated

Evidence:

- `src/app/support.tsx:52` reads `userId`.
- `src/app/support.tsx:64` redirects unauthenticated users to `/sign-in`.
- `src/app/profile.tsx:82` and `src/app/settings.tsx:331` expose Support only inside authenticated app surfaces.
- `src/app/(auth)/sign-in.tsx:135-138` password reset shows a support email inside an Alert, but no direct mail action and no route to a public support surface.

Why this matters:

The users who most need support are often pre-auth or blocked-auth users:

- cannot sign in
- forgot password
- social provider misconfigured
- account deletion/recovery confusion
- email/password not working

Right now the complete support page is behind the same gate that may be failing them. That is a support dead end.

Acceptance:

- Make a minimal support/contact route available pre-auth, or split `/support` so contact/SLA/password-help content is public while account-specific support stays auth-aware.
- Add a direct mail action from the sign-in forgot-password flow, not just an email string inside an Alert.
- Keep privacy-sensitive account details out of the public route.

## Finding 2: Support FAQ points to the wrong export location

Evidence:

- `src/app/support.tsx:42`: "Use Export in Settings to download your data as a file anytime."
- `src/app/data.tsx:64-70`: Export routes to `/wiki` with label "Export from the store".
- `src/app/settings.tsx:317`: Settings only says export before deleting; there is no export action in settings.
- `src/app/wiki.tsx:302`, `488`: actual export lives on the wiki/store screen.

Why this matters:

This is small but very visible. A user trying to back up data before deletion gets told to use Settings, then lands in a danger-zone hub without the export action. That is exactly the kind of UI slop Simon is trying to eliminate.

Acceptance:

- Update Support FAQ to point to the actual export path: `/data` -> `/wiki`, or direct `/wiki` if that is the product decision.
- Prefer one product term across screens: "store", "knowledge store", or "wiki", not a mix that makes export feel hidden.
- If Settings remains the data hub, add an explicit "Export" button there or make the FAQ say "Data management" instead of Settings.

## Score impact

This is P2 trust UX, not a P0/P1 crash.

It still blocks 100/100 because support and export are recovery paths. Recovery paths must be clearer than the happy path.

