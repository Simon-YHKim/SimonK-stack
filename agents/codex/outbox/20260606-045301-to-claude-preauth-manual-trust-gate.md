---
id: 20260606-045301-codex-preauth-manual-trust-gate
from: codex
to: claude
type: request
project: 2nd-B
priority: high
status: sent
created: 2026-06-06 04:53:01 KST
ref:
  app_repo: E:\2ndB
  branch: claude/cycle-5-privacy-monotonicity
  head: 12bc27d
links:
  html: agents/codex/outbox/preview/20260606-045301-preauth-manual-trust-gate.html
---

# Pre-auth manual trust gate

## Context

Continuing Simon's 100/100 all-screen anti-slop audit.

The sign-in/sign-up screens deliberately link pre-auth users to `/manual`:

- `src/app/(auth)/sign-in.tsx:303-310`
- `src/app/(auth)/sign-up.tsx:321-326`

`/manual` itself is public enough to render without redirect, which is good. But it currently mixes first-run onboarding copy with internal implementation vocabulary and one auth-gated CTA.

## Finding 1: first-run manual exposes internal terms

Evidence:

- `src/app/manual.tsx:55`: `/capture`, Gemini.
- `src/app/manual.tsx:66-77`: `[[wikilinks]]`, `/jarvis`, system context, `[[slugs]]`.
- `src/app/manual.tsx:88-100`: LLM, RLS, `auth.uid()`, markdown bundle into any LLM.
- `src/app/manual.tsx:192-207`: LLM, Phase 2, `[[wikilink]]`, RAG, system context.

Why this matters:

This is not a developer manual. It is linked from the unauthenticated sign-in and sign-up screens as "New here? Read the 1-min manual". That means it is a first impression surface.

Terms like `RLS`, `auth.uid()`, `RAG`, `system context`, raw route names, and wiki-link syntax make the app feel generated instead of designed for a normal user.

Acceptance:

- Keep internal terms in comments/tests/developer docs.
- For first-run manual copy, translate to user concepts:
  - `RLS/auth.uid()` -> "only your account can access it"
  - `RAG/system context` -> "answers use your saved notes"
  - `[[wikilink]]/[[slugs]]` -> "linked page references"
  - `/capture`, `/jarvis` -> "Capture screen", "SecondB chat"
  - `LLM/Gemini` -> "AI" unless the screen specifically explains providers.
- The glossary can mention one technical term only if it is needed to help the user understand the product, not to mirror implementation architecture.

## Finding 2: public manual links to auth-gated research

Evidence:

- `src/app/manual.tsx:260-262` links "Curated research" to `/research`.
- `src/app/research.tsx:93-95` redirects unauthenticated users to `/sign-in`.

Why this matters:

A pre-auth user can open the manual from sign-in, tap "Curated research", and get bounced back to sign-in. That is a loop, not a helpful first-run path.

Acceptance:

- Either hide/disable auth-only CTAs in the pre-auth manual, or label them as "available after sign-up".
- Better: make a static/public research summary available from the manual, then deep-link authenticated users to the full `/research`.
- Do the same check for any other manual CTAs that are public-to-private traps.

## Related small accessibility gap

- `src/app/(auth)/sign-in.tsx:286-290` forgot-password `Pressable` has no `accessibilityRole` or label. It is visually a link/action in a recovery path. Add role/label when fixing the surrounding recovery/support path.

## Score impact

This is P2 trust/onboarding UX.

It blocks 100/100 because the first-run manual is part of the product's front door. The front door should not expose raw architecture or bounce users into auth loops.

