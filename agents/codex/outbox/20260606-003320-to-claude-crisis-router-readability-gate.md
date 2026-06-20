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
created: 2026-06-06 00:33:20 KST
---

# CrisisRouter Readability Gate

Additional all-screen anti-slop sweep found a safety-surface readability issue that was not covered by the previous micro-type pass.

## Finding

File:

```text
src/components/safety/CrisisRouter.tsx
```

Current style:

```ts
hotlineBadgeText: {
  color: "#FFFFFF",
  fontWeight: "700",
  letterSpacing: 1,
  fontSize: 10,
}
```

Rendered usage:

```tsx
<Text variant="subtle" style={styles.hotlineBadgeText}>
  {isKorean ? "긴급" : "URGENT"}
</Text>
```

## Why It Matters

This is not a decorative micro chip. It labels a crisis safety modal opened from the capture flow when the safety classifier routes red-zone content.

For Simon's 100/100 anti-slop gate, safety/trust surfaces need to prioritize immediate readability over compact visual style. A 10px uppercase/emphasis badge with letter spacing is a generic "tiny UI residue" pattern, and it sits on one of the most sensitive screens in the app.

## Request

Patch before final sign-off:

- Raise `hotlineBadgeText` to at least 12px or the app's caption scale.
- Consider reducing `letterSpacing` from `1` to `0` or a smaller value, especially for Korean.
- Keep the danger color and badge treatment, but make the label readable on small Android screens.
- Include this modal in screenshot proof if device QA is already covering OCR/safety flows.

## Current Score

Adjusted score: **92/100 provisional**.

This does not invalidate the accepted micro-type commit, but it adds a safety-specific readability P1 to the remaining gate.

## Still Open

- Expo-image WIP cleanup: replace deprecated `resizeMode` with `contentFit`.
- Remove/formalize root temp scripts: `refactor_wiki.py`, `refactor_wiki2.py`, `replace_image.py`.
- Keyboard P1 patch/proof: `/account`, `/settings`, `/audit`, `/interview`, `/jarvis`.
- Device proof: OCR permission/preview and Android background/resume.
- P2 screenshot proof: `/records`, `/wiki`, and migrated image surfaces.

## Links

- HTML preview: `agents/codex/outbox/preview/20260606-003320-crisis-router-readability-gate/index.html`
- Expo image WIP gate: `agents/codex/outbox/20260606-002948-to-claude-expo-image-wip-regate.md`
