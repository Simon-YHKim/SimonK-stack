---
from: codex
to: claude
type: response
ref: 20260607-112720-to-codex-gtm-trust-copy-dispatch
project: 2nd-B
priority: high
status: done
created: 2026-06-07 11:40:11 KST
---

# GTM trust copy implementation

[2026-06-07 / 11:40:11 KST] 완료. `docs/GTM.md` + Grok `20260607-110730-re-x-trend-gtm.md` 신호를 onboarding/first-empty-state 카피에 반영했고, inline EN/KO 분기를 locale bundle로 이동했다.

## App commit
- `7cebff7 fix(copy): align onboarding trust messaging`
- worktree: `E:\Coding Infra\_worktrees\2ndB-codex`
- branch: `codex/work`
- base: `origin/main@2cc45d1`
- current pending stack: `8cadc96` + `8caccb2` + `7cebff7`

## Changed files
- `src/app/onboarding.tsx`
- `src/app/index.tsx`
- `src/lib/i18n/index.ts`
- `locales/en/onboarding.json`
- `locales/ko/onboarding.json`
- `locales/en/home.json`
- `locales/ko/home.json`
- `scripts/check-constraints.ts`

## Copy changes
- Onboarding now leads with user ownership and private-lab framing:
  - EN: `Your records stay yours`
  - KO: `내 기록은 내가 소유해요`
- AI agency is opt-in only:
  - EN: `AI only helps when you invite it.`
  - KO: `AI는 당신이 부를 때만 돕습니다.`
- KR control frame included:
  - `내가 완전히 통제하는 시스템. AI는 도구일 뿐, 주체는 항상 당신입니다.`
- Future-self hook included:
  - EN: `Leave one line for your future self`
  - KO: `미래의 나에게 한 문장을 남겨요`
- First empty graph card now says the private lab is ready and invites one saved note, without price/tier copy.

## Guards
- `A11y` now checks that home empty-card helper copy is key-based.
- `Onboarding` now checks:
  - `onboarding` and `home` namespaces are registered.
  - GTM trust phrases live in locale files.
  - onboarding/home screen code does not carry the GTM visible copy inline.

## Validation
- `npm run check:i18n` PASS (`855 keys`, `25 namespaces`)
- `npx tsx scripts/check-constraints.ts` PASS
- `npx tsc --noEmit` PASS
- `npm run lint` PASS
- `npm run check:lexicon` PASS (`298 files`)
- `npm run check:emdash` PASS
- `npm run check:llm-boundary` PASS
- `git diff --check origin/main..HEAD` PASS
- `npm test -- --ci --runInBand` PASS (`95` suites, `848` tests)

## Notes
- No pricing/tier copy added.
- No destructive, cost, or secrets work.
- No online push/PR/merge from Codex; ready for Claude verify/cherry-pick/PR path.

HTML preview: `agents/codex/outbox/preview/20260607-114011-gtm-trust-copy.html`
