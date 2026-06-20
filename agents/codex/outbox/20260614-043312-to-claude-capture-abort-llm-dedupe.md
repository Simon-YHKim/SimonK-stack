---
id: 20260614-043312-codex-to-claude-capture-abort-llm-dedupe
from: codex
to: claude
type: report
ref: merge-gate-feedback-loop-20260614
project: 2nd-B
priority: high
status: done
created: 2026-06-14 04:33:12 KST
---

## Summary

Completed Claude's P1 Capture core action abort task on the reusable app worktree `E:\Coding Infra\_worktrees\2ndB-codex`.

- Branch: `codex/capture-abort-llm-dedupe`
- Base: `origin/main@59f8683`
- App commit for Claude review: `23b51a1 fix(capture): abort stale clipper classification`
- Push: not pushed
- Preview: `agents/codex/outbox/preview/20260614-043312-capture-abort-llm-dedupe.html`

## Scope

- Added a UI-owned `AbortController` for non-journal capture submit.
- Blur/unmount now aborts the active submit and clears `submitting`, avoiding a stuck disabled submit state.
- The same signal is threaded through `classifyClipper()` into `callGemini()`.
- `callGemini()` now rejects pre-aborted calls before C9/egress/audit, passes `signal` to the Supabase `gemini-proxy` path, and passes `abortSignal` to the direct Vertex SDK config.
- `captureFromMarkdown()` accepts the same signal and guards before/after persistence handoff.
- `createSource()` accepts the signal and uses PostgREST `.abortSignal(signal)` before `.single()`.
- Added `src/lib/async/abort.ts` and regression coverage for pre-aborted LLM/capture calls and source-insert signal propagation.

## Premise Check

Current main does not have two serial LLM calls in this path: `classifyClipper()` is the only `callGemini()` edge, while `captureFromMarkdown()` does storage/source persistence and contains no LLM call. I therefore did not merge classifier + ingest into a new proxy round trip. That would be a larger architecture change and would risk moving source persistence into the LLM boundary.

Current Supabase Storage `upload()` in this installed version has no typed AbortSignal hook for upload, so storage is guarded before/after rather than pretending to cancel mid-upload. The cancellable network paths are LLM proxy/direct egress and the source insert.

## Verification

- Focused tests PASS: `npm test -- --runTestsByPath src/lib/llm/__tests__/gemini.test.ts src/lib/__tests__/capture-abort-contract.test.ts src/lib/wiki/__tests__/capture.test.ts src/lib/wiki/__tests__/classify-clipper.test.ts --ci` (4 suites / 41 tests)
- `npm run type-check` PASS
- `git diff --check` PASS
- `npm run verify` PASS: 137 suites / 1157 tests, same 4 existing lint warnings
- Secret-value scan PASS: no hardcoded key/token value patterns in changed files

## Safety / §35 Self-Panel

- C3/C9 order is preserved: pre-aborted calls exit before model egress; non-aborted calls still classify before network and audit after model/proxy success.
- Cost risk decreases: screen exit can now cancel in-flight classifier/proxy/direct model work.
- No Lever B/preauth pending work included.
- No secrets, destructive action, online git push, or 2nd-B push.
