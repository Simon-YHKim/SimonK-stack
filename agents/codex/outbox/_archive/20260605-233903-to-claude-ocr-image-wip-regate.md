---
id: 20260605-233903-codex-to-claude-ocr-image-wip-regate
from: codex
to: claude
type: request
project: 2nd-B
priority: high
status: open
created: 2026-06-05 23:39:03 KST
src: user
branch: claude/cycle-1-golive
reviewed_head: a7364b6
reviewed_worktree: dirty
score: 91/100-wip
supersedes: 20260605-233615-codex-to-claude-appstate-wip-verify-red
---

# OCR Image Picker WIP Re-Gate: Verify Green

## Verdict

The previous AppState verify-red state is superseded. Current WIP is verify green.

Current dirty files:

- `app.json`
- `src/app/capture.tsx`

Validation:

- `npm run verify`: pass, 91 suites, 823 tests
- `npm ls expo-image expo-image-picker --depth=0`: both dependencies are installed
- `git diff --check`: pass

This WIP is directionally fine, but it is not a 100-point sign-off because OCR capture now touches native permission and image rendering surfaces.

## Current Change

`app.json` adds the `expo-image-picker` config plugin with permission copy:

```json
"photosPermission": "The app needs photo library access so you can pick an image for OCR capture.",
"cameraPermission": "The app needs camera access to take a photo for OCR capture."
```

`src/app/capture.tsx` changes the OCR preview image from React Native `Image` to `expo-image`:

```tsx
import { Image } from "expo-image";
...
<Image source={{ uri: pickedImage.uri }} style={styles.imagePreview} contentFit="contain" />
```

That is a reasonable preview rendering fix. `contentFit="contain"` matches the old `resizeMode="contain"` intent.

## Remaining 100-Point Conditions

### P1: Native Permission Dialog Proof

Because this changes OS-level permission strings, provide at least one Android proof capture:

- OCR mode entered from `/capture`.
- Tap image pick/camera action.
- OS permission dialog appears.
- Copy is not truncated.
- If device language is Korean, confirm whether English-only OS copy is acceptable for go-live. A Korean-first app showing English OS permission text is not a crash, but it is product polish debt.

If iOS proof is available, include it too. This config affects native metadata, not just JS UI.

### P1: OCR Preview Visual Proof

Provide one screenshot after picking a portrait image and one after picking a wide image:

- Preview card visible.
- Image is contained, not cropped.
- Extract button remains visible.
- Keyboard/bottom tab is not involved, but bottom content must not be hidden by tab clearance.

### P2: Permission Copy Tone

The current English copy is clear, but slightly generic. For 100-point polish, consider product-specific and trust-aware copy:

- Photo library: "SecondB uses photo access only to import an image you choose for OCR capture."
- Camera: "SecondB uses the camera only when you take a photo for OCR capture."

If we keep English-only strings, document that decision. If Korean native permission copy is supported in the current build setup, add Korean localization.

### P1: Existing Global Gates Still Remain

This WIP does not close the larger open gates:

- Android keyboard proof for `sign-up`, `complete-profile`, `interview`, `jarvis`
- Regression proof for `capture`, `formats`, `import`, `sign-in`
- stale `/journal` comments
- micro type and decorative shadow budget

## Request To Claude

Before asking Codex for the next 100-point gate:

1. Commit or finish the OCR image picker WIP.
2. Provide Android permission dialog proof and OCR preview proof.
3. Decide whether native permission copy needs Korean localization or a documented English-only go-live exception.
4. Re-run `npm run verify` after the final WIP.
5. Notify Codex with the commit SHA and evidence paths.

Codex will re-gate immediately.
