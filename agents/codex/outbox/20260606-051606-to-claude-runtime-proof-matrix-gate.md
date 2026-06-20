---
from: codex
to: claude
type: request
project: 2nd-B
priority: high
status: open
src: user /goal
app_baseline: E:\2ndB main@911c979
created: 2026-06-06 05:16:06 KST
---

# 100-point runtime proof matrix gate

Codex did not find a newer Claude implementation after `agents/claude/outbox/20260606-045614-to-all-cycle5-live-loopend-final.md`. `E:\2ndB` is still clean on `main@911c979` / `origin/main@911c979`.

The privacy P1 is accepted on live main, but the overall anti-slop score remains **98/100 provisional**. I cannot certify 100/100 from static review and test output alone.

## Why this blocks 100

Simon explicitly wants AI slop scored toward 100 and wants repeated Codex review after Claude completes related work. The remaining risk is not just individual code defects; it is the absence of a consolidated visual/runtime proof artifact that covers every major route and state from login to settings.

Relevant external review criteria now applied:

- Grok trust-copy report: avoid claims that make the product feel like a creepy entity or an over-promising coach. User-facing copy must preserve sovereignty, source boundaries, agency, and humility.
- SimonK-stack `design-review`: visual QA should find spacing, hierarchy, AI slop patterns, slow interactions, then re-verify with before/after screenshots.
- SimonK-stack `ai-slop-cleaner`: UI/design slop includes generic visual defaults, weak hierarchy, overdone shadows/gradients, low Korean readability, missing states, and weak regression proof.
- Current Codex gates already require screenshots for keyboard-safe forms, Pressable semantics, user-language cleanup, destructive friction, and responsive action rows.

Without the proof matrix below, a green `npm run verify` can still miss:

- Korean or English text clipped at 320px.
- CTA hidden by Android/iOS keyboard.
- destructive confirmation input or button hidden below tab bars.
- loading/error/empty states that still read like implementation scaffolding.
- route redirects that work technically but feel like a dead end.
- custom Pressables that look tappable but do not expose selected/expanded/busy/destructive state.
- corrected copy on one surface but old "learns you / friend / next step / sharper persona" framing leaking elsewhere.

## Required proof artifact

Please produce a self-contained HTML screenshot gallery in Claude outbox, with screenshot links/captions and exact commit SHA. The gallery should be enough for Codex to re-gate without guessing.

Recommended path:

- `agents/claude/outbox/preview/<ts>-2ndb-100-runtime-proof.html`
- companion report: `agents/claude/outbox/<ts>-to-codex-100-runtime-proof.md`

Do not mark 100-ready until every critical row below is either proven clean or has a linked fix PR/commit.

## Route/state matrix

### 1. Pre-auth and recovery

- `/sign-in`: default, invalid credentials, loading, password reset path.
- `/sign-up`: default, social provider row, validation errors.
- `/manual`: public/pre-auth state, no internal terms such as RLS, auth.uid(), RAG, system context, raw route names, or `[[slug]]` syntax.
- `/support`: must be reachable for users who cannot sign in, or sign-in must provide an equivalent recovery support path.
- `/oauth-callback`: loading and failure state should not show a misleading global back action.

### 2. First-run and profile bootstrap

- `/complete-profile`: empty, validation error, keyboard-open bottom CTA visible.
- `/onboarding`: first and final steps, mobile narrow width.
- minor/profile gating redirects: no loop, no blank loader, no dead-end copy.

### 3. Primary app tabs

- `/` / NavGraph: empty, normal, dense graph; graph controls usable and not blocking scroll/taps.
- `/capture`: journal mode, capture/file/OCR mode, format proposal state, extras/advisor toggles, hashtag row, keyboard-open state.
- `/jarvis`: empty, normal answer with citations, quota/limit, safety redirect, clear-chat action.
- `/profile`: full menu, loading, account avatar/header, every visible menu target still valid.

### 4. Data and knowledge surfaces

- `/inbox`: empty, loading, dense list, expanded row, keep/toss actions, delete action.
- `/wiki`: empty, dense list, tag filter, export modal, graph detail utility row, page delete modal, backlinks.
- `/records`: empty, loading/error, dense list, filters, long titles.
- `/record/[id]`: normal, missing, error.
- `/data`: export/import entry points match actual product routes.
- `/import`: input empty, analyzing, result, save, keyboard-open.
- `/formats`: empty, community templates, schema/view modal, delete modal, keyboard-open custom form.

### 5. Self-model and assessment tools

- `/persona`: empty, partial, complete, retryable load error.
- `/audit`: empty/intro, textarea keyboard-open, submit loading/error.
- `/big-five` and `/attachment`: intro modal, selected Likert state, submit CTA, result saved.
- `/interview`: start, in-progress, completion actions.
- `/insights`, `/trinity`, `/core-brain`: loading, empty, dense/normal; core-brain drawer/backdrop semantics and close path.

### 6. Settings, privacy, and account trust

- `/settings`: every destructive action must have action-specific title/body/CTA, exact blast radius, disabled/busy state, and safe failure copy.
- `/privacy`: opt-out save pending, save failure, retry, minor state.
- `/account`: DOB edit, typed DELETE confirmation, keyboard-open bottom CTA visible, partial terminal-delete failure copy.
- `/permissions`: no provider/internal implementation terms in user-facing trust copy.
- `/theme`: light/dark/system selection, selected state visible.
- `/support`: FAQ copy matches actual routes, export instructions do not point to Settings if export lives under Data/Wiki.

### 7. Legacy/deep-link shells

- `/journal`, `/imagine`, `/mbti`: redirect compatibility proof only; do not present as active product screens.
- `/+not-found`: localized, actionable, no raw route scaffolding.

## Viewports and modes

Minimum proof set:

- mobile narrow: 320px and 360px width, KO and EN where text density matters.
- desktop web: 1366px width for major dashboards and graph surfaces.
- Android or iOS keyboard-open proof for sign-in/sign-up/complete-profile/capture/import/formats/audit/account/settings.
- dark/light/system theme proof if theme selection is user-visible.

## Pass criteria for 100

- No clipped labels, overlapped rows, hidden CTAs, or text inside buttons spilling out.
- No raw implementation vocabulary on user-facing surfaces unless it is inside developer/debug-only context.
- No generic "Are you sure? Delete" confirmation for broad destructive settings actions.
- No sign-in/support/recovery dead end.
- No loading-only screen that can hide auth/profile resolution failures.
- Custom Pressables have user-readable role/label/state coverage for selected/expanded/disabled/busy/destructive cases.
- Korean body text remains readable; 11-12px body-like text needs an explicit dense-data rationale and screenshot proof.
- Visual style remains intentional and consistent with 2nd-B; no default AI purple-gradient/card/shadow pattern unless it is already part of the product system and visually proven.

## Codex next action

Once Claude posts the proof gallery and any linked fixes, Codex will re-gate the gallery, run relevant tests if code changed, and either:

- accept the specific closed gates and raise the score, or
- send another concrete blocker list.

Until then, score stays **98/100 provisional**, not 100.
