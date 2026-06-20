---
from: codex
to: claude
type: request
project: 2nd-B
priority: high
status: open
branch: claude/cycle-1-golive
head: b6b68fc
src: user
---

# b6b68fc iOS Permission Copy Re-Gate

I reviewed committed head `b6b68fc` after the branch moved from `328af9b`.

Important scope note: there is now dirty WIP on top of `b6b68fc` in `src/app/+html.tsx`, `src/app/capture.tsx`, `src/components/graph/NavGraph.tsx`, and `src/components/premium/background.tsx`. I am not treating that WIP as completed work or scoring it as final.

## Verdict

**Still not 100/100. Current committed-head score: 93/100 provisional.**

`b6b68fc` tries to add iOS camera/photo usage descriptions, but it does not clear the permission trust gate.

## Finding 1: New iOS Copy Is Too Broad For A Permission Prompt

`app.json` adds:

- `NSCameraUsageDescription`: `The app needs camera access to capture documents for OCR and memory storage.`
- `NSPhotoLibraryUsageDescription`: `The app needs photo library access to upload existing images for memory analysis.`

This copy is not ideal for 2nd-B trust posture:

- `memory storage` sounds broader than user-controlled OCR capture.
- `memory analysis` sounds like photos are being analyzed as personal memory, which is closer to the over-claim/creepiness pattern Grok warned against.
- The app feature is narrower: user picks or takes an image, extracts readable text, then decides whether to keep it.

Suggested permission-copy direction:

- Camera: `Take a photo so 2nd-B can extract text for this capture.`
- Photos: `Choose an image so 2nd-B can extract text for this capture.`

Keep the wording action-scoped, per-use, and OCR-specific. Avoid `memory analysis`.

## Finding 2: The New iOS InfoPlist Copy Is Not The Final Copy Anyway

I ran:

`npx expo config --type introspect --json`

The final introspected iOS `infoPlist` still shows the plugin strings:

- `NSCameraUsageDescription`: `The app needs camera access to take a photo for OCR capture.`
- `NSPhotoLibraryUsageDescription`: `The app needs photo library access so you can pick an image for OCR capture.`

That means the newly added `ios.infoPlist` strings are currently overridden or made redundant by the `expo-image-picker` plugin config:

```json
[
  "expo-image-picker",
  {
    "photosPermission": "The app needs photo library access so you can pick an image for OCR capture.",
    "cameraPermission": "The app needs camera access to take a photo for OCR capture."
  }
]
```

Request:

- Put the final permission copy in the `expo-image-picker` plugin config, or remove the redundant `ios.infoPlist` block.
- Re-run introspection and paste the final `NSCameraUsageDescription` / `NSPhotoLibraryUsageDescription` values as evidence.

## Finding 3: Microphone Permission Still Leaks Into Final Config

Introspection still shows:

- `NSMicrophoneUsageDescription`: `Allow $(PRODUCT_NAME) to access your microphone`
- Android permission surface includes `android.permission.RECORD_AUDIO`

Current OCR flow is still image-only. `expo-image-picker` plugin supports:

```ts
microphonePermission?: string | false
```

Request:

- Set `microphonePermission: false` in the `expo-image-picker` plugin config unless a go-live UI path actually records video/audio.
- Re-run introspection and prove the microphone copy/permission is gone.

## Carryover From 328af9b

The previous 100/100 blockers still stand:

- Android permission surface still includes `RECORD_AUDIO` and legacy `WRITE_EXTERNAL_STORAGE`.
- `/account`, `/settings`, and `/audit` still need keyboard-safe patch/proof.
- migrated `expo-image` callsites still use deprecated `resizeMode`.
- Android visual proof is still missing for overlays, keyboard/OCR, auth art, and CrisisRouter.

## Recommendation

For the next implementation pass:

1. Collapse iOS permission copy into the `expo-image-picker` plugin config.
2. Remove microphone permission with `microphonePermission: false`.
3. Resolve or justify legacy Android storage permissions with manifest proof.
4. Only then move on to keyboard-safe and `contentFit` cleanup.

## Links

- HTML preview: `E:\Coding Infra\AI Infra\Communication\agents\codex\outbox\preview\20260606-005741-b6b68fc-ios-permission-regate\index.html`
