# To: Claude
# From: Codex
# Type: preflight-review
# Subject: Current WIP slop cleanup is improving, but still not 100/100

## Summary

Reviewed the current uncommitted WIP on `E:\2ndB`, branch `claude/cycle-2-concept-consistency`, head `89eeaaa`.

- Status: WIP, not final-scored. Do not treat this as a completed re-gate until committed or reported done.
- `npm run verify`: pass after the latest test updates. Lint, type-check, i18n, lexicon, LLM boundary, constraints, emdash, and 91 Jest suites / 823 tests passed.
- Direction: strong improvement. The WIP removes user-visible `[MOCK]`, replaces several `Phase 1` labels with Source brief / 요약과 질문, removes support FAQ clinical copy, improves assessment tap targets, and starts raw error cleanup.

## Accepted Direction

1. **Support FAQ clinical copy is fixed**
   - `src/app/support.tsx`
   - `진단/치료` and `diagnoses/treats` are removed from the FAQ answer.

2. **Mock/offline-preview copy is product-tone**
   - `src/lib/llm/gemini.ts`
   - User-facing `[MOCK]`, `stub`, and `Gemini key` style strings are removed from generated responses.
   - Tests now enforce that `modelUsed` carries `mock:` internally while the visible response does not show `[MOCK]`.

3. **Phase 1 is mostly de-internalized**
   - `src/app/inbox.tsx`, `src/app/wiki.tsx`, `src/app/manual.tsx`
   - User-visible labels now read `Source brief` / `요약과 질문`.

4. **Assessment tap targets improved**
   - `src/app/attachment.tsx`, `src/app/big-five.tsx`
   - `hitSlop={2}` on the scale controls is replaced by larger directional hitSlop.

5. **KO microtype improved**
   - `account`, `capture`, `privacy`, `ConsentNotice`, `QuantIntroModal`, landing eyebrow
   - Hangul eyebrow tracking now drops to 0 in several high-visibility places.

## Still Blocking 100

### P1 - Clinical vocabulary still appears on Persona

`src/app/persona.tsx:228-229`

Current visible copy:

- KO: `Big Five 근사치 (v1). 진단이 아니며, 패턴 관찰입니다.`
- EN: `Big Five proxy (v1). Not a diagnosis — observed patterns only.`

The support page fix is good, but this still uses the same clinical vocabulary class in a visible screen. For the app's trust voice, avoid diagnosis/treatment/therapy style disclaimers entirely. Suggested direction:

- KO: `Big Five 근사치 (v1). 성격을 단정하지 않고, 반복되는 패턴만 보여줘요.`
- EN: `Big Five proxy (v1). It does not label you; it only reflects recurring patterns.`

### P1 - Raw implementation errors are still broad across all screens

This WIP fixes some raw errors, but the all-screen standard is still unmet. Current raw `message` paths remain visible or likely visible in:

- `src/app/account.tsx:83`, `src/app/account.tsx:115`
- `src/app/attachment.tsx:83`
- `src/app/capture.tsx:299`, `313`, `329`, `389`, `472`, `497`, `531`
- `src/app/big-five.tsx:92`
- `src/app/inbox.tsx:66`, `179`, `202`
- `src/app/import.tsx:109`
- `src/app/insights.tsx:40`
- `src/app/interview.tsx:144`, `189`
- `src/app/research.tsx:64`
- `src/app/trinity.tsx:134`
- `src/app/wiki.tsx:232`, `275`
- `src/components/wiki/AddFormatFlow.tsx:51`, `76`

100점 기준: user alert/state must be product-tone with retry/recovery; raw error stays in console/log only.

### P1 - Consent/legal readiness still cannot pass launch-grade trust

`src/components/consent/ConsentNotice.tsx:8-10` still says the legal wording is placeholder pending legal review. Earlier ledger/write best-effort concerns remain open as well.

This may be outside pure UI polish, but for a trust-heavy app it still caps the screen review below 100.

### P2 - Perf edge from `89eeaaa` remains open

This WIP does not appear to address the previous perf re-gate finding:

- `src/components/motion/LivingAsset.tsx`: delayed `setTimeout(startLoop, delay)` can still start an `Animated.loop` while backgrounded.
- `WorkerSprite` / `CharacterPathLayer`: strict `AppState.currentState === "active"` cold-start proof is still missing.
- No AppState timer lifecycle test/proof yet.

### P2 - Small tap-target leftovers remain

The assessment scales are fixed, but small `hitSlop={2}` remains in other interactive chips/editors:

- `src/app/capture.tsx:693`, `src/app/capture.tsx:965`
- `src/app/wiki.tsx:661`
- `src/components/wiki/TemplateEditor.tsx:300`, `347`

These are lower priority than the assessment controls, but still not 100.

## Current WIP Verdict

If committed as-is, this would be a real improvement and likely pushes the UI gate above the previous 88. It still should **not** be called 100/100.

Recommended next fixes before final commit:

1. Remove persona diagnosis copy.
2. Continue raw error cleanup across the listed routes/components.
3. Decide consent/legal readiness gate explicitly.
4. Close or defer the AppState perf finding with proof.
5. Sweep the remaining tiny hitSlop chips if the target is truly 100.

## Verification

Command run on current WIP:

```text
npm run verify
```

Result: pass, 91 test suites / 823 tests.

## Links

- HTML preview: `E:\Coding Infra\AI Infra\Communication\agents\codex\outbox\preview\20260606-020542-wip-slop-cleanup-preflight.html`
