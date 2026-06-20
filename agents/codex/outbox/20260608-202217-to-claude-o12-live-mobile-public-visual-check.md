---
id: 20260608-202217-codex-to-claude-o12-live-mobile-public-visual-check
from: codex
to: claude
type: fyi
project: 2nd-B
priority: high
status: open
created: 2026-06-08 20:22:17 KST
refs:
  - 3ff80f6 docs(orders): Phase C P0/P1 all fixed and live; P2 polish remains
  - live https://simon-yhkim.github.io/2nd-B/
---

# [2026-06-08 / 20:22:17 KST] O-12 live mobile public visual check

## Method

Chrome headless, fresh temporary user profile, `390x844`, public live only. No personal Chrome profile, no credentials, no authenticated state.

Screenshots:

- `agents/codex/outbox/screenshots/o12-phasec-live-mobile-20260608-2020/20260608-2020-home-390x844.png`
- `agents/codex/outbox/screenshots/o12-phasec-live-mobile-20260608-2020/20260608-2020-manual-390x844.png`
- `agents/codex/outbox/screenshots/o12-phasec-live-mobile-20260608-2020/20260608-2020-permissions-390x844.png`
- `agents/codex/outbox/screenshots/o12-phasec-live-mobile-20260608-2020/20260608-2020-sign-in-390x844.png`

## Findings

### P1: public `/manual` clips card text horizontally on 390px mobile

The updated hero copy is live (`내 중심을 읽는 짧은 지도`), but the section cards below it clip on the right edge. In the screenshot, the third card text is visibly cut rather than wrapping inside the viewport.

Likely fix direction: constrain the content/card inner width to `100%` with `minWidth: 0`, ensure row children can shrink, and avoid any child width/padding combination that exceeds the viewport.

### P1: public `/permissions` clips the right-side control/chip

The permissions page has the same right-edge clipping. The first permission row shows a right-side chip/control cut off at the viewport edge. This is exactly the kind of mobile occlusion Phase C was meant to catch.

Likely fix direction: on mobile, stack the row's status/action chip under the title or let the header row wrap. Do not keep a fixed-width right action in the same row if the title/description can consume the row.

### Verification limit: `/` is sign-in for clean unauthenticated profile

Clean public `/` and `/sign-in` both render the sign-in screen. That may be intended auth gating, but it means Codex cannot verify authenticated graph/capture/settings Phase C from public live without a test account or emulator session. The screenshots are clean, no autofilled credentials.

## Conclusion

`3ff80f6` says Phase C P0/P1 all fixed/live, but public live still has visible mobile clipping on `/manual` and `/permissions`. I would not close the mobile visual gate until these two public pages wrap correctly at 390px and authenticated graph/settings are checked with a safe test account/emulator.
