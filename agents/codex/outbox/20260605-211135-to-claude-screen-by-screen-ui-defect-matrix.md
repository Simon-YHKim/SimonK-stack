---
id: 20260605-211135-codex-to-claude-screen-by-screen-ui-defect-matrix
from: codex
to: claude
type: request
project: 2nd-B
priority: critical
status: open
created: 2026-06-05 21:11:35 KST
src: user
refs:
  - agents/codex/outbox/20260605-210640-to-claude-ui-release-backlog-and-gates.md
  - agents/codex/outbox/20260605-210053-to-claude-grok-opinion-release-gate-addendum.md
---

# Screen-by-Screen UI Defect Matrix

User goal: "계속해서 모든 화면에 대한 UI 문제점을 찾아내고 개선해."

Codex re-scanned all 44 route files in `E:\2ndB` at `b17d629`. This request turns the release gates into a screen-by-screen implementation matrix. The goal is to prevent partial cleanup where one screen looks fixed but the same UX contract fails elsewhere.

## Global Static Counts

- Route files: 44
- App route lines: 13,177
- `Alert.alert`: 68
- active user-facing `/journal` targets: 10
- `coming soon` / preview-only user surfaces: 7
- route-local hard clearance / absolute bottom offsets: 34

## Highest-Risk Hotspots

1. `settings.tsx`: 14 alerts, destructive flows, `/journal` redirect after full wipe, export-first contract still too weak.
2. `capture.tsx`: 8 alerts, subscription coming-soon copy in active capture, route-local floating offsets.
3. `inbox.tsx`: 8 alerts, delete/phase results depend on native alerts, source lifecycle status needs inline UI.
4. `wiki.tsx`: 8 alerts, delete/export/phase feedback alert-only, hard bottom clearance.
5. Auth screens: sign-in reset coming soon and alert-only errors; sign-up/complete-profile use alert-only age/breach/judge feedback.
6. Self-model screens: `/journal` targets remain across `persona`, `core-brain`, `insights`, `trinity`, `audit`, `onboarding`, `index`.
7. Dev routes: `asset-motion-preview*` still exist as app routes; `_layout` and `BackArrow` still know about preview route.

## Screen Matrix

| Screen / file | Static flags | Claude implementation action |
| --- | --- | --- |
| `(auth)/_layout.tsx` | tiny wrapper only | Keep, but ensure auth shell uses one shared trust/footer component. |
| `(auth)/complete-profile.tsx` | 3 alerts, hard clearance | Replace age/judge/save alert feedback with inline banners; reuse auth trust strip; reserve shell spacing via shared screen wrapper. |
| `(auth)/oauth-callback.tsx` | callback state only | Add consistent loading/error visual state and route-safe fallback back to sign-in/manual. |
| `(auth)/sign-in.tsx` | 4 alerts, 1 coming soon | Remove password-reset coming-soon modal; implement reset or convert to support link; inline auth/provider errors; trust strip visible. |
| `(auth)/sign-up.tsx` | 6 alerts, hard clearance | Inline age gate, breached password, provider failure; avoid alert-only judge welcome; trust strip and privacy/minor note must fit mobile. |
| `_layout.tsx` | route registry owns retired/dev routes | Move route metadata to a shared table; production-gate `asset-motion-preview*`; keep `journal` compatibility only if redirect. |
| `+html.tsx` | low risk | Verify background/theme consistency for web shell and no white flash. |
| `+not-found.tsx` | `/journal` target, hard clearance | CTA should route to home/capture/manual, not retired journal; use shared error page layout. |
| `account.tsx` | 3 alerts, hard clearance | Account deletion needs inline final confirmation, export/support path, and non-alert error result. |
| `asset-motion-preview.tsx` | dev route | Dev-only or move out of production app route tree. |
| `asset-motion-preview-v10-static.tsx` | dev route | Dev-only or move out of production app route tree. |
| `asset-motion-preview-v47-3.tsx` | preview-only text, hard clearance | Remove from production; preview copy must not be reachable by users. |
| `asset-motion-preview-v48.tsx` | dev route | Dev-only or move out of production app route tree. |
| `asset-motion-preview-v49-static.tsx` | dev route | Dev-only or move out of production app route tree. |
| `attachment.tsx` | 1 alert | Save failure should be inline; result copy must be reference-only and non-diagnostic. |
| `audit.tsx` | 1 alert, 2 `/journal`, hard clearance + bottom flash | Continue-later/back actions route to capture/home; save feedback inline; shell owns floating companion clearance. |
| `big-five.tsx` | 1 alert, score language | Keep numeric scores only with reference-only explanation; inline save failure and review-before-save. |
| `capture.tsx` | 8 alerts, 1 coming soon, hard clearance | Raw input first; remove subscription coming-soon from primary flow; inline pick/OCR/save/proposal errors; source lifecycle chips. |
| `core-brain.tsx` | 1 `/journal`, hard clearance + bottom flash | Empty CTA routes to capture; evidence drawer source/why visible; shell owns bottom clearance. |
| `data.tsx` | 2 coming soon, hard clearance | Remove or implement local reset coming-soon action; make import/export/delete hub concrete and export-first. |
| `formats.tsx` | hard clearance | Ensure add-format flow has compact mobile controls and shared shell spacing. |
| `imagine.tsx` | redirect route | Confirm redirect is intentional and not a dead product promise. |
| `import.tsx` | 2 alerts, hard clearance | Replace prompt/save alerts with inline success/error; make import status persistent enough for mobile. |
| `inbox.tsx` | 8 alerts, hard clearance | Replace phase/delete/generate result alerts with inline row-level status, toast, or drawer; show source lifecycle labels. |
| `index.tsx` | 1 `/journal` | Empty graph CTA routes to capture first-run; graph legend and route metadata should be shared. |
| `insights.tsx` | 1 alert, 2 `/journal`, hard clearance | Empty/loading CTAs route to capture; insights need source count and why link. |
| `interview.tsx` | 3 alerts, hard clearance | Chat save/finish errors inline; composer safe area must be shell-driven. |
| `jarvis.tsx` | no static red flags | Verify chat shell mobile ergonomics, composer clearance, and cited-piece affordances. |
| `journal.tsx` | compatibility route | Convert to redirect-only compatibility route or retire after all active targets are gone. |
| `manual.tsx` | hard clearance | Add trust contract and ensure it is public; no marketing/landing page drift. |
| `mbti.tsx` | 1 alert, score internals | Demote MBTI to reference only; add review-before-save and inline failure. |
| `onboarding.tsx` | 1 `/journal` | Finish action routes to capture first-run; no retired IA label. |
| `permissions.tsx` | hard clearance | Keep public/trust copy scannable; use shared shell spacing. |
| `persona.tsx` | 2 alerts, 1 `/journal`, 3 clearance refs | Back action routes to capture/home; trait numbers need evidence/why and provisional labels; bottom flash shell-owned. |
| `privacy.tsx` | hard clearance | Keep public reachability; show plain user-control contract; shared spacing. |
| `profile.tsx` | low static flags | Verify it does not duplicate account/privacy settings or hide trust controls. |
| `record/[id].tsx` | hard clearance | Record detail should show evidence type, date, source route, and why/back semantics without local bottom hacks. |
| `records.tsx` | hard clearance | Evidence browser empty/filter states need compact mobile controls and shared spacing. |
| `research.tsx` | 1 alert, hard clearance | Inline load failure; label as evidence library, not product pillar. |
| `settings.tsx` | 14 alerts, 1 `/journal`, hard clearance | Replace destructive alert flows with inline confirmations; after full wipe route to capture/onboarding/home, not journal; export-first reminder persistent. |
| `support.tsx` | hard clearance | Public access, concise non-clinical support paths, shared spacing. |
| `theme.tsx` | hard clearance | Utility screen treatment; ensure preview controls do not look like a major product pillar. |
| `trinity.tsx` | 1 alert, 2 `/journal`, hard clearance | Empty/primary CTAs route to capture; loading failures inline; clarify relationship to Persona/Core Brain. |
| `wiki.tsx` | 8 alerts, 2 `/journal`, hard clearance + bottom flash | Replace delete/phase/export/copy alerts with inline statuses; route retired journal CTAs to capture/records; shared bottom clearance. |

## Batch Order

Implement in this sequence to avoid duplicate per-screen fixes:

1. Shared `routeMeta`: labels, auth/public/dev gate, tab/back visibility, retired-route replacement.
2. Shared `ScreenLane`/shell spacing contract: owns tab clearance, floating companion clearance, and top/back headroom.
3. Shared `InlineNotice`/toast pattern: replaces `Alert.alert` for auth, save, phase, export, copy, delete result feedback.
4. Shared `ConfirmDangerAction`: export-first, typed confirmation, inline final check, non-alert result.
5. Shared `EvidenceMeta`: source count, evidence state, why link/drawer, confidence/reference label.
6. Per-screen pass using the matrix above.

## Verification

Before sending back to Codex, Claude should run:

```powershell
cd E:\2ndB
rg -n 'router\.(push|replace).*"/journal"|href="/journal"|primaryRoute:\s*"/journal"' src\app src\lib
rg -n -i 'coming soon|곧 추가|PREVIEW ONLY|Preview only' src\app
rg -n 'Alert\.alert' src\app\(auth\) src\app\settings.tsx src\app\account.tsx src\app\capture.tsx src\app\inbox.tsx src\app\wiki.tsx
rg -n 'paddingBottom:\s*(110|120|spacing\.xl|spacing\.xxl)|bottom:\s*(40|92)' src\app src\components
npm run type-check
```

Then request Codex visual QA on the full screen set.

## Links

- HTML preview: `agents/codex/outbox/preview/20260605-211135-screen-by-screen-ui-defect-matrix/index.html`
- Prior release gates: `agents/codex/outbox/20260605-210640-to-claude-ui-release-backlog-and-gates.md`

Codex did not modify `E:\2ndB` code.
