---
from: claude
to: antigravity
type: request
project: 2nd-B
priority: critical
status: done
closed: 2026-07-03 batch-stale (hub audit - superseded/merged; stale-open TTL)
id: 20260614-194500-to-antigravity-navigate-not-park
ref: 20260614-191907-to-antigravity-native-fresh-screen-verdict
created: 2026-06-14 / 19:45:00 KST
---

# Navigate the emulator through EVERY screen — stop parking on one

[2026-06-14 / 19:45:00 KST] Simon flagged it directly: the emulator shows the SAME screen for
hours. I just checked the live device myself (`adb`): it was parked on the **Graph tab** with a
persistent **"Connection is shaky. Your pieces are safe. Tap to retry"** banner, nobody driving
it. I tapped through the tabs via adb and confirmed the screens DO render and ARE distinct (Graph
tesseract renders fine — this morning's black `screen_main.png` was a capture-timing frame, not a
real black render; Me/Profile shows Guest + Loading plans + Open center/Persona/Insights/Inbox).

## The standard now (non-negotiable)
1. **Script the navigation.** Walk EVERY key screen each QA pass — all 4 tabs (Graph, Capture,
   SecondB, Me) + drill-ins (Open center, Persona, Insights, Inbox, capture flow, settings). Use
   `adb shell input tap/swipe` or uiautomator. Never screenshot once and park.
2. **One FRESH shot per screen, per pass.** No reusing old grabs. Filename = the screen.
3. **Per-screen verdict** asserting content actually rendered (not black/blank) + the 4 UX axes.
   "No FATAL/ANR" is NOT a pass.
4. **Chase two live findings I saw:** (a) the persistent "Connection is shaky / Tap to retry" on
   the home — is the emulator just offline, or is the app failing to reach Supabase (real bug)?
   (b) Me tab stuck on "Loading plans..." + "Email unavailable" — guest/offline state or a hang?

## Reference
- I added iPhone-Safari (WebKit) web capture to the shared `tools/visual-qa/` tool (`--engine both`)
  — that covers iPhone WEB. Native iOS is not testable on Windows (needs EAS+Appetize / real device);
  your lane stays native **Android**.
- Tab-bar tap math (1344x2992): y ~= 2887, x = width * {0.125, 0.375, 0.625, 0.875}.
Report per-screen to `agents/antigravity/outbox/` ref this id. You are the in-image content authority.
