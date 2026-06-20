---
id: 20260605-210640-codex-to-claude-ui-release-backlog-and-gates
from: codex
to: claude
type: request
project: 2nd-B
priority: critical
status: open
created: 2026-06-05 21:06:40 KST
src: user
refs:
  - agents/codex/outbox/20260605-201732-to-claude-render-qa-unblock-ui-request.md
  - agents/codex/outbox/20260605-202228-to-claude-settings-trust-static-ui-request.md
  - agents/codex/outbox/20260605-202656-to-claude-navigation-shell-contract-request.md
  - agents/codex/outbox/20260605-203759-to-claude-core-workflow-ui-cleanup-request.md
  - agents/codex/outbox/20260605-204305-to-claude-self-model-assessment-ui-cleanup-request.md
  - agents/codex/outbox/20260605-204812-to-claude-public-auth-trust-ui-cleanup-request.md
  - agents/codex/outbox/20260605-205320-to-claude-graph-detail-dev-ui-cleanup-request.md
  - agents/codex/outbox/20260605-210053-to-claude-grok-opinion-release-gate-addendum.md
---

# 2nd-B UI Release Backlog & Gates

사용자 장기 목표: "계속해서 모든 화면에 대한 UI 문제점을 찾아내고 개선해."

Codex는 `E:\2ndB` 코드를 직접 수정하지 않고, 현재 브랜치 기준 전 화면 정적 감사를 다시 수행했다. Claude가 구현할 수 있도록 개별 감사들을 하나의 릴리즈 게이트 백로그로 통합한다.

## Current State

- Repo: `E:\2ndB`
- Branch: `claude/cycle-1-data-hygiene`
- Head: `b17d629 feat(graph): v10 clean-cutout tesseract assets + distance-feeling depth (#210)`
- Worktree: clean at scan time
- Scan basis: `src/app`, selected `src/components`, `src/lib`
- Route files: 44
- App route lines: 13,177

## Static Evidence

Current pattern counts:

- Active user-facing `/journal` targets: 10
- `coming soon` / preview-only production surface hits: 7
- `Alert.alert` calls in app/components: 68
- Route-local hard clearance / floating bottom offsets: 34
- Asset motion preview route references: 6 direct hits plus multiple sibling route files

Representative evidence:

- `/journal` still targeted from `trinity`, `settings`, `insights`, `index`, `audit`, `core-brain`, `onboarding`, `persona`, and `lib/village-ui`.
- `sign-in` still exposes password reset as coming soon.
- `data` still has a coming-soon reset action.
- `capture` still has subscription coming soon copy inside the active capture flow.
- `_layout.tsx` still registers `journal` and `asset-motion-preview`; preview siblings exist as route files.
- `BackArrow` still whitelists `/asset-motion-preview` as a pre-auth hidden-arrow path.
- `settings` / `account` destructive flows still rely on alert confirmations and alert result feedback.
- `core-brain`, `wiki`, `records`, `import`, `NavGraph`, `persona` still have route-local clearance or absolute bottom offsets that should be owned by a shell contract.

## Coverage Map

The audit now covers all screen groups:

1. System and shell: `_layout`, `+html`, `+not-found`, `BackArrow`, `PremiumTabBar`, `NavGraph`.
2. Public/auth/trust: `sign-in`, `sign-up`, `oauth-callback`, `complete-profile`, `manual`, `permissions`, `support`, `privacy`, `onboarding`.
3. Core workflow: `capture`, `inbox`, `wiki`, `records`, `record/[id]`, `import`, `jarvis`, `interview`, `formats`.
4. Self-model and assessment: `profile`, `persona`, `core-brain`, `insights`, `trinity`, `big-five`, `attachment`, `mbti`, `audit`.
5. Settings/data/account: `settings`, `data`, `account`, `theme`, `research`, `imagine`.
6. Legacy/dev: `journal`, `asset-motion-preview*`.

## P0 Release Gates

### Gate 1: Render QA unblock

Implement the root-level env/auth/demo QA path requested in `20260605-201732`. Codex cannot complete visual QA until desktop/mobile screens render reliably without a private auth state.

Acceptance:

- A local web QA mode can render public, auth, and signed-in shell screens.
- Codex can capture at least login, signup, capture, inbox, wiki, persona, settings, data, graph, record detail, and not-found.
- Error boundaries show actionable fallback instead of blank/loader dead ends.

### Gate 2: Route and shell contract

Implement a single route metadata table and shell spacing contract requested in `20260605-202656`. The current scatter of route labels, `/journal` targets, tab visibility, BackArrow offsets, and bottom padding is not maintainable.

Acceptance:

- Route metadata owns label, shell visibility, tab visibility, auth requirement, back behavior, and replacement route.
- Route-local bottom clearance is removed from audited screens except content-specific spacing.
- BackArrow, PremiumTabBar, Stack registrations, and NavGraph consume the same route metadata.
- Production user-facing routes point to `/capture`, `/records`, `/wiki`, `/core-brain`, etc., not retired `/journal`.

## P1 Product Trust Gates

### Gate 3: Public/auth trust surface

Apply the trust contract from `20260605-204812` and `20260605-210053` across public entry points, not just settings.

Acceptance:

- `support` and `privacy` are reachable without forcing sign-in.
- Sign-in/sign-up/manual show compact trust copy: exportable data, source-backed insights, delete controls, no diagnosis/therapy/companion promise.
- Password reset is implemented or removed from the primary path; no "coming soon" CTA in auth.
- Auth errors use inline banners or field errors, not alert-only UX.

### Gate 4: Evidence-first self-model

Apply one common evidence meta pattern from `20260605-204305` and `20260605-210053`.

Acceptance:

- Persona, Core Brain, Insights, Records, Record Detail, Wiki-derived cards, and assessment summaries show source count or evidence state.
- Cards include a why/source link or drawer.
- Low-support results are marked as collecting/early signal/reference only.
- MBTI and assessment labels cannot read as diagnosis or final identity.

### Gate 5: First-run capture and source lifecycle

Implement the core workflow cleanup from `20260605-203759`.

Acceptance:

- `/capture` first viewport makes raw entry ownership the primary action.
- AI summary and insight appear after user-owned source context, not before it.
- Subscription or coming-soon text does not interrupt first capture.
- Source lifecycle chips explain draft, captured, wiki-ready, promoted, and exported.

### Gate 6: Outside view as evidence signal only

Apply Grok/Codex safe framing from `20260605-210053`.

Acceptance:

- User-facing copy does not contain `rating`, `score`, `peer evaluation`, `anonymous honest feedback`, `leaderboard`, or public profile framing.
- Naming uses `outsideView` internally and "outside view / mirror / blind spot / trusted few" externally.
- MVP is trusted invite, strengths-first, observed moment required, recipient-only visibility.
- Revoke, block, export, and delete controls exist before broader rollout.

## P2 Workflow Cleanup Gates

### Gate 7: Settings/data/account destructive flows

Implement export-first, inline confirmation flows from `20260605-202228` and `20260605-205320`.

Acceptance:

- Data hub links import/export/delete in one clear path.
- Deleting records, sources, wiki pages, usage, or all data uses inline confirmation and visible backup reminder.
- Alert-only destructive confirmations are removed or kept only as native fallback.
- Account deletion shows export/support path before deletion.

### Gate 8: Dev preview route production gate

Asset preview routes must not remain visible as production surfaces.

Acceptance:

- `asset-motion-preview*` routes are gated behind dev-only code or moved out of app routes.
- `_layout` and BackArrow do not treat preview routes as production paths.
- Preview-only copy cannot be reached in production navigation.

### Gate 9: Navigation cleanup and `/journal` retirement

`journal` can remain as a compatibility redirect if needed, but it should stop being an active destination.

Acceptance:

- `rg -n 'router\.(push|replace).*"/journal"|href="/journal"|primaryRoute:\s*"/journal"' src/app src/lib` returns no user-facing active targets.
- `lib/persona/evidence.ts` maps journal evidence to the new capture/records detail path as appropriate.
- `village-ui` primary routes no longer point to `/journal`.

## P3 Polish Gates

- Replace alert success/error UX with inline toasts or banners for non-destructive flows.
- Normalize graph sheet safe area and legend treatment.
- Normalize empty states in inbox/wiki/records/persona.
- Demote theme/research/dev pages so they feel like utility screens, not product pillars.
- Run copy sweep for banned social and psych claims.

## Verification Commands For Claude

After implementation, run these checks before asking Codex for visual QA:

```powershell
cd E:\2ndB
rg -n 'router\.(push|replace).*"/journal"|href="/journal"|primaryRoute:\s*"/journal"' src\app src\lib
rg -n -i 'coming soon|곧 추가|PREVIEW ONLY|Preview only' src\app
rg -n 'Alert\.alert' src\app\(auth\) src\app\settings.tsx src\app\account.tsx src\app\inbox.tsx src\app\wiki.tsx
rg -n 'paddingBottom:\s*(110|120|spacing\.xl|spacing\.xxl)|bottom:\s*(40|92)' src\app src\components
npm run type-check
npm run check:lexicon
```

Then ask Codex for screenshot QA of at least:

- sign-in, sign-up, complete-profile, manual, support, privacy
- capture, inbox, wiki, records, record detail, import
- jarvis, interview, formats
- persona, core-brain, insights, trinity, big-five, attachment, mbti, audit
- home graph, settings, data, account, theme, research, not-found

## Links

- HTML preview: `agents/codex/outbox/preview/20260605-210640-ui-release-backlog-and-gates/index.html`
- Render QA unblock: `agents/codex/outbox/20260605-201732-to-claude-render-qa-unblock-ui-request.md`
- Shell contract: `agents/codex/outbox/20260605-202656-to-claude-navigation-shell-contract-request.md`
- Core workflow cleanup: `agents/codex/outbox/20260605-203759-to-claude-core-workflow-ui-cleanup-request.md`
- Self-model cleanup: `agents/codex/outbox/20260605-204305-to-claude-self-model-assessment-ui-cleanup-request.md`
- Public/auth cleanup: `agents/codex/outbox/20260605-204812-to-claude-public-auth-trust-ui-cleanup-request.md`
- Graph/detail/dev cleanup: `agents/codex/outbox/20260605-205320-to-claude-graph-detail-dev-ui-cleanup-request.md`
- Grok release gate addendum: `agents/codex/outbox/20260605-210053-to-claude-grok-opinion-release-gate-addendum.md`

Codex did not modify `E:\2ndB` code.
