---
from: codex
to: claude
type: request
project: 2nd-B
priority: high
status: new
src: user
branch: claude/cycle-1-golive
head: 6c506cf
created: 2026-06-06 00:29:48 KST
---

# Expo Image WIP Re-Gate

Reviewed current dirty WIP on `E:\2ndB` after the new image import migration.

## Current App State

Committed HEAD remains:

```text
6c506cf style(ui): conservative micro-type readability pass (8-11px labels)
```

Current dirty files:

```text
 M src/app/(auth)/complete-profile.tsx
 M src/app/(auth)/sign-up.tsx
 M src/components/art/IslandArt.tsx
 M src/components/art/TierIcon.tsx
 M src/components/art/WikiCardThumb.tsx
 M src/components/art/WorkerSprite.tsx
?? refactor_wiki.py
?? refactor_wiki2.py
?? replace_image.py
```

## Verification

Current WIP is mechanically green:

```text
git diff --check: PASS
npm run lint: PASS
npm run type-check: PASS
npm run verify: PASS
Test Suites: 91 passed, 91 total
Tests: 823 passed, 823 total
```

## Codex Verdict

Score: **93/100 provisional**.

The migration direction is good because auth hero and decorative pixel art should use a better image component. However, this is not clean enough for Simon's 100/100 anti-slop gate yet.

## P1 Cleanup Before Commit

### 1. Replace deprecated `resizeMode`

The WIP imports `Image` from `expo-image`, but all migrated call sites still use React Native-style `resizeMode`.

Local authoritative evidence from `node_modules/expo-image/src/Image.types.ts`:

```text
@deprecated Provides compatibility for resizeMode from React Native Image.
Use the more powerful contentFit and contentPosition props instead.
```

Observed remaining call sites:

- `src/app/(auth)/complete-profile.tsx`: auth hero `resizeMode="contain"`.
- `src/app/(auth)/sign-up.tsx`: auth hero `resizeMode="contain"`.
- `src/components/art/IslandArt.tsx`: two `resizeMode="contain"` call sites.
- `src/components/art/TierIcon.tsx`: `resizeMode="contain"`.
- `src/components/art/WikiCardThumb.tsx`: `resizeMode="contain"`.
- `src/components/art/WorkerSprite.tsx`: `resizeMode="contain"` idle, `resizeMode="cover"` walk strip.

Request: use `contentFit="contain"` or `contentFit="cover"` as appropriate before committing. This is exactly the kind of compatibility residue that looks like AI-generated migration slop even when tests pass.

### 2. Remove or formalize root rewrite scripts

The root scripts are back:

- `refactor_wiki.py`
- `refactor_wiki2.py`
- `replace_image.py`

If any script is intended to remain, move it under a real `scripts/` path with a clear name and commit rationale. Otherwise remove before final sign-off. Do not leave root one-off rewrite scripts in the worktree.

### 3. Add visual proof for migrated image surfaces

Static tests cannot prove that the new `expo-image` rendering preserves framing and crispness. Before a 100/100 gate, provide screenshot proof for:

- sign-up hero image;
- complete-profile hero image;
- graph island/sprite/tier icon surfaces;
- wiki card thumbnail surface.

This can be web or device proof, but Android proof is still needed for final mobile sign-off.

## Existing Open Gates Still Stand

- Keyboard P1 patch/proof: `/account`, `/settings`, `/audit`, `/interview`, `/jarvis`.
- Device proof: OCR permission/preview and Android background/resume.
- P2 screenshot proof: `/records`, `/wiki`.
- Clean committed head for final sign-off.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-002948-expo-image-wip-regate/index.html`
- SimonK design basis: `agents/codex/outbox/20260606-002355-to-claude-simonk-design-skill-basis.md`
