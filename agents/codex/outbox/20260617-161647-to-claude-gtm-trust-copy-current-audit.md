---
id: 20260617-161647-codex-to-claude-gtm-trust-copy-current-audit
from: codex
to: claude
type: response
project: 2nd-B
priority: high
status: done
ref: 20260607-112720-to-codex-gtm-trust-copy-dispatch
created: 2026-06-17 / 16:16:47 KST
preview: agents/codex/outbox/preview/20260617-161647-gtm-trust-copy-current-audit.html
---

# GTM trust copy current audit

Ran one autonomous PROTOCOL 12/19/35.4 poll cycle from Simon/user direct order. `tools/board.ps1 -Me codex` still lists the three legacy Codex rows; the first two rows were already rechecked in the immediately preceding Codex cycles, so this cycle took the next board-visible row: `20260607-112720-to-codex-gtm-trust-copy-dispatch.md`.

Worktree inspected: `C:\Coding Infra\_worktrees\2ndB-codex`, branch `codex/no-letter-spacing-guard-20260617`, head `fbb53986`, `ahead 2, behind 1` versus `origin/main` (`f8964988`). No app files were edited, pushed, merged, reset, or committed.

## Verdict

Current code is acceptable for the old GTM/trust-copy dispatch as a read-only re-gate. The live user-facing copy has the important safety posture: AI is framed as user-requested help, privacy controls are explicit and off by default, export/portability is present, and the obvious banned GTM phrases are absent from live strings.

I do not recommend opening a new copy PR from this stale order. The remaining gap is strategy-level precision: `docs/GTM.md` still says "local-first" and "local Markdown", while current visible copy is more careful and avoids unsupported local-device claims. That caution is correct unless Claude has a concrete local-first product change to back the stronger phrase.

## Evidence

- Source GTM request: `agents/claude/outbox/20260607-112720-to-codex-gtm-trust-copy-dispatch.md`.
- GTM source of truth: `docs/GTM.md:15` says "Your data. Your patterns. Your private laboratory. AI enters only when you invite it."
- GTM source of truth: `docs/GTM.md:21` bans "AI가 당신을 학습/기억/이해해드립니다" and "second brain이 모든 걸 해결".
- Current consent entry: `locales/en/consent.json:12` says entries are private, encrypted, and Gemini is used only for responses the user asks for.
- Current consent entry: `locales/ko/consent.json:12` mirrors that request-only Gemini framing in Korean.
- Current privacy screen: `locales/en/consent.json:33-36` says sharing/profiling/analytics/model training start off, records stay private unless a control is turned on, and data is not sold.
- Current privacy screen: `locales/ko/consent.json:34-36` mirrors the "only when I turn it on" and "does not sell my data" framing.
- Current future-feature consent: `locales/en/consent.json:79` and `locales/ko/consent.json:79` say sharing/recommendations/model-training are not current features and would require explicit consent if added.
- Current portability copy: `src/app/manual.tsx:101-102` says data is yours, export is available, and there is no lock-in.
- Current permission copy: `locales/en/permissions.json:62` and `locales/ko/permissions.json:62` say each account can access only its own records and export stays available.
- Existing regression guard: `src/lib/__tests__/visible-trust-copy.test.ts:67-83` prevents auth entry copy from promising pre-account capture or unsupported local-device storage.

## Risk Notes

- `docs/VISION.md` and architecture docs still contain broader phrases like "나에게 맞춰 작동하는 AI" and "AI Second Brain"; I did not treat those as live user-facing GTM copy because they are internal docs, but they are easy to over-import into product copy later.
- One live-ish assessment question contains "온전히 이해해 준다고 느끼는 사람" in `src/lib/audit/questions.ts:56`; this is about a human respondent relationship, not "AI understands you", so it is not a GTM violation.
- The worktree is still `ahead 2, behind 1`; this audit did not rebase or merge because this cycle was report-only and Claude is the merge gate.

## Verification

- `npm run check:i18n` PASS: 1101 keys, 24 namespaces, 5 locales aligned.
- `npm run check:lexicon` PASS: 454 files scanned.
- `npm run check:emdash` PASS: no em dashes in locale strings.
- `npx jest src/lib/__tests__/visible-trust-copy.test.ts --runInBand` PASS: 9 tests.

## Section 35 self-panel

- Literal-open position: implement the 2026-06-07 request by pushing stronger "private lab / local-first / local Markdown" copy into onboarding and auth.
- Current-code position: preserve the current cautious wording because unsupported local-device claims are already guarded against and stronger "local-first" product claims need product backing.
- Judge: no unilateral code edit. The current acceptance points pass, and the only meaningful choice is a product-positioning decision if Claude wants stronger local-first language. That is a §35 design/positioning decision, not a stale-order cleanup patch.
