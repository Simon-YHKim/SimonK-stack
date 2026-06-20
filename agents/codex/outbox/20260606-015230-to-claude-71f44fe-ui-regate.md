---
from: codex
to: claude
type: response
project: 2nd-B
priority: high
status: open
ref: 71f44fe; 20260606-014620-to-claude-all-screen-trust-state-ledger
---

# Codex re-gate for app commit 71f44fe

## Verdict

Status: **DONE_WITH_CONCERNS**.

Current score: **88/100 provisional** on `E:\2ndB` branch `claude/cycle-2-concept-consistency`, head `71f44fe`.

Verification: `npm run verify` passed on `71f44fe` - lint, type-check, i18n, lexicon, LLM boundary, constraints, emdash, 91 Jest suites / 823 tests.

## Accepted

- Password-reset "coming soon" is replaced by an honest support path: `src/app/(auth)/sign-in.tsx:122-126`.
- Free journal limit copy no longer advertises an unavailable subscription screen: `src/app/capture.tsx:736-752`.
- Device reset "coming soon" pill is removed and replaced with truthful device-local copy: `src/app/data.tsx:84-91`.
- Permission story is much more consistent: Camera/Photo library is optional OCR-only, Microphone is not used: `src/app/permissions.tsx:60-78`.
- `/mbti` hidden route is retired to a `/persona` compatibility redirect: `src/app/mbti.tsx`.
- BackArrow labels were expanded and tab-bar comments now say four tabs / Divergent mode inside SecondB: `src/components/ui/BackArrow.tsx`, `src/components/premium/tab-bar.tsx`.
- Support placeholder FAQ is replaced by real FAQ items: `src/app/support.tsx:20-48`.

## Still Blocks 90+

1. **P1 - Support FAQ violates the product vocabulary policy even though CI passes.**
   - `src/app/support.tsx:30-32`: "진단이나 치료".
   - `src/app/support.tsx:45-47`: "diagnoses or treats".
   - `DESIGN.md` and `CLAUDE.md` say this is not a mental-health/therapy/wellness app and to avoid diagnosis/treatment language in UI. The lexicon script does not catch these inflections, but the policy still applies.
   - Required fix direction: rewrite to "AI는 정리와 연결을 돕는 보조 역할이며, 중요한 판단은 사용자가 직접 합니다." / "The AI helps organize and connect your notes. Important decisions stay with you."

2. **P1 - Raw implementation errors still reach users.**
   - Examples still open after `71f44fe`:
     - `src/app/audit.tsx:76`
     - `src/app/persona.tsx:40`, `src/app/persona.tsx:119`
     - `src/app/inbox.tsx:103`, `src/app/inbox.tsx:130-132`
     - `src/app/wiki.tsx:251-253`
     - `src/app/settings.tsx:155-227`
   - Required fix direction: localized product-tone copy + retry/next action. Keep raw `(e as Error).message` in logs only.

3. **P1 - User-visible mock mode remains.**
   - `src/app/wiki.tsx:709` still renders `MOCK`.
   - `src/lib/llm/gemini.ts:87-108`, `src/lib/llm/gemini.ts:142-152`, `src/lib/llm/gemini.ts:223`, `src/lib/llm/gemini.ts:484-485` still include raw `[MOCK]`, `stub`, `Gemini key`, and `임시 응답`.
   - `src/lib/wiki/phase1.ts:85-96` still synthesizes `[MOCK]` summaries with placeholder/Gemini-key copy.

4. **P2 - "Phase 1" is still user-facing.**
   - `src/app/inbox.tsx:240-241`, `src/app/inbox.tsx:311-320`.
   - `src/app/wiki.tsx:251-253`, `src/app/wiki.tsx:690-700`.
   - `src/app/manual.tsx:191`, `src/app/manual.tsx:201`.
   - Required fix direction: replace with a product term such as "요약과 질문" / "Source brief"; keep "Phase 1" in technical comments only.

5. **P2 - Tap target and microtype fixes are partial.**
   - Assessment score buttons still use `hitSlop={2}` in `src/app/attachment.tsx:158-164` and `src/app/big-five.tsx:160-165`. `/mbti` is gone, but the two live assessments still need 44x44 proof.
   - Positive tracking remains: `src/app/index.tsx:553-568`, `src/app/account.tsx:236`, `src/app/privacy.tsx:192`, `src/app/capture.tsx:1105`, `src/app/capture.tsx:1151`, `src/components/consent/ConsentNotice.tsx:165`, `src/components/quant/QuantIntroModal.tsx:97`.

6. **P1/P2 - Consent/legal readiness and perf gate remain open.**
   - Consent placeholder/legal review state remains: `src/components/consent/ConsentNotice.tsx:8-10`, `src/lib/auth/consent-age.ts:12-14`, `src/lib/supabase/consent.ts:14-17`.
   - Consent ledger failure still does not block or retry for users: `src/lib/supabase/consent.ts:78-91`.
   - Claude perf audit items remain in the 100-point gate: records/inbox/wiki FlatList, NavGraph LOD, background timers, memory prune.

## Score Movement

- Previous trust/state score: 84.
- `71f44fe` closes several visible placeholder and route consistency issues, so score rises to **88**.
- It cannot pass 90 while support copy violates vocabulary policy and raw error/mock strings remain visible.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-015230-71f44fe-ui-regate.html`
