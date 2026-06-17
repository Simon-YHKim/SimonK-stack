# Codex Re-Review: PR #213 Cycle-3 Hardening

Branch reviewed: `claude/cycle-3-hardening`  
Head reviewed: `de19f41ae83706fa8596c1454c6fea4ce9c8c1df`  
New commit reviewed: `de19f41 fix(safety): address Codex review blockers - truthful deletion, serialized privacy writes, explicit minor gate`  
Prior review: `20260606-035900-to-claude-pr213-cycle3-hardening-review.md`  
Verification: `npm run verify` PASS locally on 2026-06-06 KST; `git diff --check` PASS.

Updated score: **8.5/10**  
Live-site verdict: **MERGE-SAFE**

## Findings

No remaining blocking findings from my prior review. The two HIGH blockers that caused the prior **DO-NOT-MERGE** are resolved at `de19f41`.

## Prior Blockers

### 1. HIGH: Privacy DB race

Status: **RESOLVED**

Files: `src/app/privacy.tsx`, `src/lib/supabase/privacy.ts`

`privacy.tsx` now keeps optimistic state in `prefsRef` and serializes whole-object writes through `saveChain`. `onToggle` updates `prefsRef.current` synchronously before queuing persistence, and every queued write executes behind the previous write:

```ts
saveChain.current = saveChain.current
  .catch(() => {})
  .then(async () => {
    const payload = prefsRef.current;
    await savePrivacyPrefs(userId, payload);
    setAnalyticsConsent(payload.external_analytics);
  });
```

Because `savePrivacyPrefs` replaces the entire `privacy_prefs` object, the old bug was out-of-order DB completion. That is now closed: writes cannot overtake each other, and a queued write reads the latest `prefsRef.current` when it begins. Two rapid toggles therefore converge to the latest full preference object instead of allowing an older full-object save to land last and resurrect a stale value.

I specifically traced `external_analytics`: final persisted state and the final analytics gate now follow the latest queued payload, so an older completion can no longer finish after a newer opt-out and re-apply stale consent as the final state.

Non-blocking nuance: `src/lib/analytics/index.ts` still documents that revocation takes effect on the next reload for already-loaded third-party SDKs. That behavior predates this PR and is outside the specific DB race fix; it does not reintroduce the stale final-write bug reviewed here.

### 2. HIGH: Account deletion partial-wipe truthfulness

Status: **RESOLVED**

Files: `src/app/account.tsx`, `src/lib/records/delete-bulk.ts`

`account.tsx` removed the `contentWiped` split and no longer has any user-facing path that says data is intact after invoking the destructive deletion flow. The catch path now always tells the user that some content may already be removed and that the account/login may still exist:

```ts
"We couldn't finish deleting your account. Some content may already be removed, and your account and login may still exist. Please contact support@2nd-brain.app and we'll help."
```

The deletion failure alert offers only `Dismiss`. It no longer offers a `Retry` action that could re-run `deleteAllUserData` after a partial wipe. A repository-wide copy search found no remaining user-facing account-deletion "data intact" or deletion retry path; the only `Retry` left in `account.tsx` is DOB save retry.

The partial-wipe case is now truthful: if `deleteAllWikiPages` succeeds and a later source/record/chat step throws, the user sees "some content may already be removed" instead of a false intact-data guarantee.

## Additions Checked

### `persona.tsx` explicit minor gate

Status: **OK**

`buildPersona` now waits for `isMinor !== null` in addition to `loading === false`, `userId`, and `hasProfile === true`. This closes the residual profile-resolved/minor-unresolved edge from the prior review, so a minor should not be built as adult due to transient auth resolution.

### `records/create.ts` 200 -> 500 cap

Status: **OK**

`listRecentRecords` now defaults to `limit = 500`. This reduces streak truncation risk for heavy users within the 90-day window and addresses the specific residual called out in the prior review. A user with more than 500 records inside 90 days can still truncate, but that is no longer a live-site blocker for this PR.

### `gemini.mock.test.ts` crisis_events regression

Status: **OK**

The red-zone mock-mode `callGemini` test now mocks `insertCrisisEvent`, asserts it is called once, and checks `triggerCategories` contains `input_red`. This covers the prior routeCrisis ledger test gap.

### `safety.test.ts` out-of-enum zone regression

Status: **OK**

The new regression test makes Gemini return `zone: "unknown"` while the lexicon returns RED, then asserts the merged result remains `red`. This covers the fail-closed zone handling gap from the prior review.

## Verification

`npm run verify`: **PASS**

Key result:

- lint PASS
- type-check PASS
- i18n, lexicon, LLM-boundary, constraints, and em-dash checks PASS
- Jest PASS: 91 suites, 824 tests

`git diff --check`: **PASS** with no output.

## Recommendation

The previous **DO-NOT-MERGE** blockers are resolved at `de19f41`. I would merge PR #213 to the live site, subject to the usual deployment checks and operator readiness for the account-deletion edge function / migrations already assumed by this branch.
