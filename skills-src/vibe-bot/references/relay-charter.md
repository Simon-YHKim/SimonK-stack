# Grok Bot organization — 2026-09-24

User-supplied source: `grok-bot-org-overview-2026-09-24.md`.
SHA-256: `3dbaba9585ecf01cdef216dae0eb74b367f4ac10e3d0e4bd8b2e83c9c8592dd3`.
This supersedes the 09-20 charter for new tasks. It is an organization snapshot,
not live access, billing, account, scheduling or delivery verification.
The exact 19 identities, six team IDs and memberships live in `bots.json`.
Do not copy this reference into a cloud profile or change routines without a task.

## Coordinator, delivery and ownership

Simon owns decisions/approval. The current /vibe host writes task sheets and
verifies returns; it need not be Claude Code. Aurelius Middleman / Relay is the
cloud post office, not a second model/budget coordinator.

Relay alone reads new coordinator tasks in:

- shared hub: `E:/Coding Infra/AI Infra/Communication/bots/relay/inbox/`;
- 2ndB: `E:/2ndB/.bots/relay/inbox/`.

Results return to the corresponding `relay/outbox/<nonce>.result.md` with the
exact nonce on the first line. Preserve specialist identity in the task and
metadata; do not publish to specialist inboxes. For other projects use only their
explicitly authorized bus; do not infer that every task belongs to 2ndB.
Relay passes the unchanged deliverable to specialists or an existing team.
A claimed or delegated task is not completed. Retain claims and original tasks;
an interrupted claim requires lookup, not replacement or duplicate execution.
Status records nonce, task, owner, state, time and result. Unconfirmed replies
stay pending; preserve source attribution and never invent a specialist response.

## Choose the owner

| Work | Owner |
| --- | --- |
| Play Console / App Store Connect / EAS | play-console / apple-dev / eas |
| GitHub, Supabase and development dashboards | dev-infra |
| GA4, Firebase, Clarity and event validation | analytics |
| AdMob units, fill and monetization checks | admob |
| Screen/device QA | qa (Cassius StillBroken) |
| Credential names, presence and expiry only | keys |
| Documentation and changelog | docs |
| Mail triage / store review drafts / content drafts | public-mail / store-reviews / marketing |
| Evidence research / ads preparation / lead drafts / subscription inventory | research / ads / leads / subs |
| Game proposals / shared work records | game / worklog |
| Unclassified task or team handoff | relay |

The legacy `web-qa` mapping is unverified; no dedicated profile was found in the
snapshot. Ask Relay to clarify within an authorized task, not as an automatic
probe. Do not silently equate it with Cassius. Sebastian Research's profile
description was empty; its broader scope is inferred, not fully verified.
The six existing teams are release, customer, launch-check, game-studio,
maintenance and growth. Each includes Relay, with at most six members.
Use their exact roster name/ID in the target; the builder has no `--team` switch.

## Free reversible preparation and hard stops

Within the user's actual task authority, prepare free reversible drafts and
scoped handoffs without asking repeatedly. A reported standing preference for
free accounts/profiles is not credential, signup, billing or data-sharing consent.
CLI/API/MCP-capable work stays in /vibe. App code belongs to the coding LLM:
Bots propose only; for 2ndB use `E:/2ndB/docs/drafts/`, for another project use its
approved draft location. Never commit, merge or edit app source through a Bot.

Stop for payment, advertising ON, store submission/release, deletion, public
posting, external email/messages, cancellation/refund/payment-method or permission
changes. Login/2FA needs Simon. Never include secret values in chat, logs or results.
Internal handoffs still need authorization for that exact dispatched task.
Use the central guarded adapter; neither a copied draft nor a routine bypasses it.

After two reported wakes (about 20 minutes), at most one authorized reminder;
if still unanswered on the next wake, mark blocked with owner/time/evidence.
No third reminder, new nonce, automatic resend or daemon. Reported wake timing
is not proof that a scheduler is installed or currently running.

## Shared environment, worklog and QA

All bots share one Linux box, tools, files and browser logins. Separate windows
or desktops do not isolate credentials, costs or data. Coordinate console scope
and batch login blockers; do not count nineteen independent security boundaries.

Before authorized work, read `/workspace/worklog/workbooks/_common.md` and the
owner's workbook. Append work events to `/workspace/worklog/YYYY-MM-DD.md`.
Tacitus is reported to check every two hours and summarize daily at 23:56 KST.
Weekly lessons exist as a policy; Monday 08:37 is Relay-reported, not file-verified.
Do not create or change these routines merely because this reference lists them.

Android QA is reported installed with a shared Pixel 6/API 34 emulator using TCG;
start it only for authorized QA and stop it afterward. No macOS/iOS simulator is
established. TestFlight device checks remain on Simon's phone.
Separate code evidence, build logs and observed console state; one does not prove
the others. Current login/device/runtime state remains unknown until observed.
