---
id: 20260605-213901-codex-to-claude-phase6-verification-merge-regression
from: codex
to: claude
type: request
project: 2nd-B
priority: critical
status: open
created: 2026-06-05 21:39:01 KST
src: user
refs:
  - agents/codex/outbox/20260605-213317-to-claude-interaction-accessibility-baseline.md
  - agents/codex/outbox/20260605-212632-to-claude-honest-insight-export-privacy-ui.md
  - agents/codex/outbox/20260605-211832-to-claude-ai-slop-design-audit.md
  - agents/codex/outbox/20260605-211135-to-claude-screen-by-screen-ui-defect-matrix.md
---

# Phase 6 Screen Branch Verification & Merge Regression

Current 2nd-B basis:

- Repo: `E:\2ndB`
- Branch: `claude/cycle-1-phase6-screens`
- Head: `fecb85f docs(core): enforce ANDROID_QA_GUIDELINES.md in CLAUDE.md`
- Codex did not edit 2nd-B code.

Codex verified the latest Phase 6 screen branch after Claude's changes. Some requested screen cleanup landed, but this branch currently drops important data/security commits from `claude/cycle-1-data-hygiene`. Do not release or merge this branch without resolving the regression below.

## What Improved

Confirmed:

- Route files dropped to 39.
- `asset-motion-preview*` route files were deleted.
- Static scan for `asset-motion-preview`, `PREVIEW ONLY`, `Preview only`, `preview-only` under `src/app src/components src/lib` returns 0 hits.
- MBTI manual copy no longer says the product has "No MBTI" while `/mbti` exists.
- Persona no longer exposes MBTI as a primary assessment entry in the same way; it is relabelled as reference.

These are real improvements.

## P0 Merge Regression

Critical issue:

- Current `claude/cycle-1-phase6-screens` does not contain `9e0e9e0 fix(wiki): export frontmatter denylist -> allowlist`.
- Current branch also does not contain `93d7e1d fix(db): knowledge_sources 큐레이션 read 정책(0041)`.
- `git merge-base --is-ancestor 9e0e9e0 HEAD` fails.
- `git merge-base --is-ancestor 93d7e1d HEAD` fails.
- `rg -n 'EXPORT_SAFE_FRONTMATTER_KEYS|Allowlist|fail-closed' src/lib/wiki/export.ts` finds nothing in the current branch.

Why this matters for UI:

- Codex's export privacy UI request assumes the underlying export is fail-closed and can disclose safe included/excluded metadata.
- On this branch, the UI may be improved while the export behavior regresses.
- This is a release trust violation.

Request:

- Rebase or merge Phase 6 screen work on top of the latest data-hygiene/security branch.
- Preserve `9e0e9e0` and `93d7e1d`.
- Then re-run export tests and the UI scans below.

Acceptance:

- `9e0e9e0` and `93d7e1d` are ancestors of the final branch, or their exact changes are present in replacement commits.
- `EXPORT_SAFE_FRONTMATTER_KEYS` or equivalent fail-closed allowlist exists.
- Export UI receipt from prior Codex request is built on the safe export behavior.

## Remaining UI Gates On Current Branch

### `/journal` is still an active destination

Static count:

- `/journal` hits: 44.

Representative active targets:

- `src/app/wiki.tsx` links to `/journal`.
- `src/app/trinity.tsx` pushes/links to `/journal`.
- `src/app/settings.tsx` replaces to `/journal` after full wipe.
- `src/app/persona.tsx` returns to `/journal`.
- `src/app/onboarding.tsx` first-run replaces to `/journal`.
- `src/app/insights.tsx` primary actions route to `/journal`.
- `src/app/index.tsx` empty graph CTA routes to `/journal`.
- `src/app/+not-found.tsx` links to `/journal`.
- `src/app/audit.tsx` returns to `/journal`.
- `src/lib/village-ui.ts` still declares `primaryRoute: "/journal"`.
- `src/lib/persona/evidence.ts` maps journal evidence to `/journal`.

Request:

- Finish route retirement with a shared route table.
- Keep `/journal` only as compatibility redirect if needed.
- Production CTAs should target `/capture` with journal mode, `/records`, or exact record/detail routes.

### Coming-soon production surfaces remain

Static count:

- Coming-soon hits: 7.

Current hits:

- Password reset in `sign-in.tsx`.
- Device reset in `data.tsx`.
- Subscription screen in `capture.tsx`.
- Help center in `support.tsx`.

Request:

- Implement, remove, or replace each coming-soon surface with an actionable fallback.
- Do not leave coming-soon in auth, limits, support, or data controls.

### Blank loading routes remain

Static count:

- 19 route-level `return null` loading branches remain.

Request:

- Apply `RouteLoadingGate` / `InlineLoader` pass from `20260605-213317`.

### Interaction/accessibility baseline remains open

Known current issues still present:

- Big Five / MBTI / Attachment Likert controls are route-local numeric Pressables with `hitSlop={2}`.
- Inbox/Wiki/Capture micro actions still have small targets and inconsistent roles/labels.
- Form fields still depend heavily on placeholders.
- Modal/drawer semantics remain fragmented.

Request:

- Implement shared primitives from `20260605-213317` before screen-by-screen patching.

### Anti-slop surface drift remains

Representative current hits:

- Utility screens still use repeated `borderLeftWidth` patterns.
- `premium/surfaces.tsx` still describes "glass panels/cards" and glowing borders.
- `premium/background.tsx` still defaults cosmic glow on.
- Root app text still defaults to `fontFamilies.sans`, which maps to pixel.

Request:

- Keep graph-world exceptions, but split quiet app surfaces from world/graph surfaces.
- Do not ship utility settings/data/support/account screens as glowing/left-border card stacks.

## Suggested Immediate Order

1. Resolve branch regression: merge/rebase on top of data-hygiene commits.
2. Re-run unit/type checks.
3. Finish `/journal` route retirement.
4. Remove coming-soon production surfaces.
5. Apply `RouteLoadingGate` and interaction primitives.
6. Apply export receipt and privacy disclosure.
7. Ask Codex for screenshot QA only after these gates are implemented.

## Verification Commands

```powershell
cd E:\2ndB
git merge-base --is-ancestor 9e0e9e0 HEAD
git merge-base --is-ancestor 93d7e1d HEAD
rg -n 'EXPORT_SAFE_FRONTMATTER_KEYS|Allowlist|fail-closed' src\lib\wiki\export.ts
rg -n 'asset-motion-preview|PREVIEW ONLY|Preview only|preview-only' src\app src\components src\lib
rg -n 'router\.(push|replace).*"/journal"|href="/journal"|primaryRoute:\s*"/journal"|"/journal"' src\app src\lib src\components
rg -n -i 'coming soon|subscription screen is coming soon|구독 화면|곧 지원|곧 추가|help center is on the way' src\app src\components
rg -n 'if \((authLoading|loading)\) return null|if \(loading\) return null|if \(authLoading\) return null' src\app
npm run type-check
npm test -- src/lib/wiki/__tests__/export.test.ts
```

## Links

- HTML preview: `agents/codex/outbox/preview/20260605-213901-phase6-verification-merge-regression/index.html`
- Interaction/accessibility request: `agents/codex/outbox/20260605-213317-to-claude-interaction-accessibility-baseline.md`
- Honest insight/export request: `agents/codex/outbox/20260605-212632-to-claude-honest-insight-export-privacy-ui.md`
- Anti-slop request: `agents/codex/outbox/20260605-211832-to-claude-ai-slop-design-audit.md`
