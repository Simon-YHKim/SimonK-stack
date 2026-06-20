# Codex Review: PR #213 Cycle-3 Hardening

Branch reviewed: `claude/cycle-3-hardening`  
Base/head: `main` at `d8ba4a0` -> `9b03f04`  
Commits reviewed: `b9e89f5`, `babc920`, `9b03f04`  
Verification: `npm run verify` passed locally on 2026-06-06 KST.

Provisional score: **6.5/10**  
Live-site verdict: **DO-NOT-MERGE**

The branch fixes several real issues, and the automated verification suite is green. I still found two blockers in the legal/privacy-critical surface: privacy preference saves can still lose rapid toggles, and account deletion can still tell the user their data is intact after a partial destructive wipe.

## Blocking Findings

### 1. HIGH: Privacy toggles can still lose a rapid save, including analytics consent

Files: `src/app/privacy.tsx`, `src/lib/supabase/privacy.ts`

The new `prefsRef` composition fixes local stale-state reads, but `onToggle` still launches every `savePrivacyPrefs(userId, updated)` concurrently, and `savePrivacyPrefs` writes the entire `privacy_prefs` object:

```ts
await supabase.from("users").update({ privacy_prefs: prefs }).eq("id", userId);
```

That means rapid toggles can still race at the database. Example:

1. Toggle A on -> request 1 writes `{ A: true, B: false }`.
2. Toggle B on -> request 2 writes `{ A: true, B: true }`.
3. Request 2 reaches Supabase first.
4. Request 1 reaches Supabase last and overwrites B back to false.

The same ordering issue applies to `setAnalyticsConsent(updated.external_analytics)`: an older save can complete after a newer opt-out and re-apply stale analytics consent locally. The UI state composition is better, but the persisted state is not serialized, versioned, or guarded by latest-write-wins.

Required before live merge: serialize privacy writes through a queue, collapse rapid changes into one latest full-object save, use per-key/RPC patch semantics, or otherwise ignore stale completions. Add a regression test for two rapid toggles resolving out of order, especially `external_analytics`.

### 2. HIGH: Account deletion copy is still untruthful after partial client wipe failure

Files: `src/app/account.tsx`, `src/lib/records/delete-bulk.ts`

The new copy is correct only if `deleteAllUserData(userId)` fully completes and `requestAccountDeletion()` then fails. It does not handle partial client wipe failure.

`deleteAllUserData` performs destructive work sequentially:

```ts
const wikiPages = await deleteAllWikiPages(userId);
const sources = await deleteAllSources(userId);
const records = await deleteAllRecords(userId);
const chatUsage = await deleteAllChatUsage(userId);
```

But `account.tsx` only flips `contentWiped = true` after the entire function returns. If wiki pages are deleted and then source deletion throws, `contentWiped` remains false and the catch path tells the user:

> "Your data is still intact."

It also offers "Retry", even though some content may already be gone. That is still a destructive retry/truthfulness bug on a legal-critical flow.

Required before live merge: track destructive progress from the first successful deletion, or make `deleteAllUserData` return partial-progress status instead of throwing blindly. Once any destructive step may have succeeded, the user-facing copy must not claim intact data or offer a normal retry.

## Focus-Area Review

### routeCrisis `crisis_events` write

Status: functionally acceptable, with a test gap.

`src/lib/llm/gemini.ts` now performs a best-effort `insertCrisisEvent` in `routeCrisis`, with no raw text, RPC-backed user hash, `locale`, `triggerCategories`, `cssrsLevel: null`, and a routing template version. The fields match the `insertCrisisEvent` contract and the migration-backed `log_crisis_event` RPC. This is appropriately best-effort, matching the audit-log pattern.

It is not perfect parity with `callAdvisor`: the confidence is fixed at `0.95`, triggers are synthesized from lexicon categories plus `input_red`, and the routing template version is generic (`routecrisis-inline-v1`) rather than the fixed response version. That is defensible because `routeCrisis` uses an inline response path, but it should be intentional.

Test gap: the Gemini test title says the crisis event is recorded, but the test does not assert that `insertCrisisEvent` is called or inspect the payload.

### `mergeResults` fail-closed zone handling

Status: correct.

Known zone ordering is unchanged: red beats yellow beats green. Unknown runtime zones are ranked as red and normalized to `red`, so an unknown model zone can no longer downgrade a lexicon RED. This is the right fail-closed behavior.

Test gap: add an explicit unknown-zone regression test proving a lexicon RED remains red and an unknown model zone normalizes to red.

### `persona.tsx` minor-resolved gate

Status: mostly safe by current DB/AuthContext invariants, but not the literal requested gate.

`buildPersona` now includes `isMinor` in the effect dependencies and uses a per-user/locale `builtKey` ref, so normal profile loads where `hasProfile` and `isMinor` resolve together should build minors with the youth hotline. Existing migrations enforce non-null `birth_date` for real profiles, and `AuthContext` sets `hasProfile` and `isMinor` in the same state transition after `fetchProfile`.

However, the effect does not explicitly wait for `isMinor !== null`. If a profile row ever exists without a birth date, or an auth/profile edge path returns `hasProfile === true` with `isMinor === null`, it builds as adult (`isMinor === true` is false) and `builtKey` prevents a same-user/same-locale rebuild later. That is a residual edge risk and a mismatch with the stated fix. A direct `if (isMinor === null) return;` guard after the profile redirect case would make the behavior unambiguous.

### `complete-profile.tsx` consent gate

Status: correct.

Consent is now recorded only when `ensureUserProfile` returns `created === true`, so existing profiles are no longer re-consented with a newly submitted DOB/age band. This matches the legal intent.

### `account.tsx` deletion copy

Status: not merge-safe.

The full-client-wipe-then-terminal-failure path is improved, but partial wipe failure is still misrepresented as intact data and still offers Retry. See blocker 2.

### `privacy.tsx` ref-based toggle composition

Status: not merge-safe.

The local ref avoids stale local composition, but concurrent full-object saves can still persist stale privacy settings out of order. See blocker 1.

### `records/create.ts` streak window

Status: improved, with one residual accuracy issue.

The query now uses an any-kind 90-day window, and app callers still consume the same row shape. I did not find caller breakage.

Residual issue: the query still applies `limit = 200`. Heavy users can have more than 200 records inside 90 days, so the streak can still truncate before the full 90-day window. The cutoff is also a rolling UTC instant rather than a KST-day boundary. This is lower severity than the privacy/deletion blockers but should be fixed if the requirement is truly "any-kind, 90-day".

### `conversation.ts` injection guard

Status: directionally correct.

User-controlled wiki snapshot content is now fenced as untrusted and sanitized for `</UNTRUSTED>` and `[SYSTEM]` escape attempts, with a clear system instruction to treat it only as recall data. The app-level persona hint is fixed application data, and user messages stay in the user role.

Test gap: add a malicious wiki snapshot test proving `</UNTRUSTED>` and `[SYSTEM]` are stripped and cannot escape the untrusted block.

## Other Notes

I did not find additional merge blockers in the surrounding cycle-3 changes. The import save guard, wiki source refresh, reduced-motion drift handling, timer callback refs, and KST prompt rotation all look reasonable within the inspected diff.

`npm run verify` result: PASS. The suite reported 91 Jest suites and 823 tests passing, plus lint, type-check, i18n, lexicon, LLM-boundary, constraint, and em-dash checks passing.

## Recommendation

Do not merge this branch to the live site yet. Fix the privacy save ordering and account-deletion partial-wipe copy/retry behavior first, then re-run `npm run verify` and add targeted regression tests for the two blockers plus the safety test gaps above.
