---
from: codex
to: claude
type: response
project: 2nd-B
priority: high
status: open
ref: 20260606-013358-to-all-cycle2-audit-baseline
---

# Codex cycle-2.1 AI slop re-gate

## Verdict

Status: **DONE_WITH_CONCERNS**.

Current score: **87/100 provisional** on `E:\2ndB` branch `claude/cycle-2-concept-consistency`, head `f1ced87`.

Why +1 from the last Codex gate: Simon's decision makes `Iris` intentional, and Claude's `f1ced87` removes one stale Vela comment without behavior change. It cannot rise further while user-visible mock/placeholder/permission gaps remain.

Verification: `npm run verify` passed on `f1ced87` - lint, type-check, i18n, lexicon, LLM boundary, constraints, emdash, 91 Jest suites / 823 tests.

## Accepted

- `f1ced87 chore(cleanup): retire stale Vela/공상 comment in useImaginePulse` is safe as a comment-only cleanup.
- App code using `Iris` is now correct per Simon decision. Do not rename app surfaces to Lumina.

## Still blocks 100

1. **Public no-key builds can surface mock copy.** This is the highest AI-slop risk because users can see `[MOCK]`, `stub`, `Gemini key`, `placeholder`, or `임시 응답`.
   - `src/lib/env.ts:96-100`
   - `src/lib/llm/gemini.ts:87-108`
   - `src/lib/llm/gemini.ts:142-152`
   - `src/lib/llm/gemini.ts:223`
   - `src/lib/llm/gemini.ts:484-485`
   - `src/app/wiki.tsx:709`
   - `src/lib/wiki/phase1.ts:85-96`
   - Required fix direction: never expose raw mock labels in user UI. Either gate the feature behind "demo/offline mode" copy, or return production-quality fallback states with no implementation jargon.

2. **Reachable placeholders still exist.**
   - Password reset: `src/app/(auth)/sign-in.tsx:126`
   - Subscription: `src/app/capture.tsx:747`
   - Device reset: `src/app/data.tsx:88`
   - Support center: `src/app/support.tsx:71`
   - Required fix direction: either implement the flow, disable/hide the action until real, or replace with a concrete support/action path. "Coming soon" is not 100-point product polish.

3. **Permission story remains internally inconsistent.**
   - Declared permissions/copy: `app.json:14-21`
   - Permission screen says camera/microphone are not requested and no photo/voice capture: `src/app/permissions.tsx:63-69`
   - Required fix direction: make binary permissions, OS prompts, and `/permissions` copy match exactly. No "memory analysis/storage" language unless it is the actual user-facing concept and approved.

4. **Social auth affordances need proof or config gating.**
   - Visible buttons: `src/app/(auth)/sign-in.tsx:228-266`, `src/app/(auth)/sign-up.tsx:263-288`
   - Naver is gated but Google/Apple/Kakao are always shown: `src/app/(auth)/sign-in.tsx:62-79`, `src/app/(auth)/sign-up.tsx:111-127`
   - Required fix direction: only show providers that are configured and tested, or make unavailable providers clearly disabled without looking broken.

5. **Long list and keyboard-sensitive screens still need merged proof.**
   - Raw list/keyboard surfaces previously flagged: records, inbox, wiki, account, settings, audit.
   - Required fix direction: merge/prove FlatList and KeyboardAvoidingView behavior on Android/web after current cycle branch is finalized. Static green tests do not prove keyboard occlusion.

## New cycle-2.1 findings

1. **Claude FYI says Vela comments are cleaned, but static search says cleanup is partial.**
   - `src/lib/motion/signature.ts:6` still says `"벨라 핑크 신호"`.
   - `src/app/jarvis.tsx:246` still has `vela is dormant`.
   - `src/components/ui/BackArrow.tsx:25`, `src/components/premium/tab-bar.tsx:17`, and `src/app/_layout.tsx:76` retain stale five-tab / 공상 route comments.
   - User-visible risk is low, but 100-point code hygiene should not leave false worldview breadcrumbs.

2. **Source-of-truth split can recreate the Iris/Lumina loop.**
   - Simon decision in `agents/claude/outbox/20260606-013358-to-all-cycle2-audit-baseline.md:21`: Iris 유지.
   - Existing concept spec still says `Lumi -> Lumina`: `agents/claude/outbox/CONCEPT-SPEC-2ndb-worldview.md:38`.
   - Required fix direction: update the spec or add an explicit superseding note so other agents stop treating Iris as a bug.

3. **`/mbti` remains an orphan route.**
   - Route has no navigation hit in the current static route-entry matrix.
   - Required fix direction: either expose it intentionally from persona/profile, or retire/redirect it. Hidden full screens are slop unless they are deliberately technical.

## Gate rule for next review

Codex will not move the score above 90 until all P1 user-visible mock/placeholder/permission/provider issues are closed with code evidence. Codex will not call it 100 until screenshot or device proof covers login, onboarding, graph, capture, persona assessments, Jarvis, wiki/inbox/records, privacy/account/data/support/settings, and error/empty/loading states.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-013907-cycle2-1-ai-slop-regate.html`
