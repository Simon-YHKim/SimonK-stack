---
id: 20260606-095933-codex-theme-native-persistence-truth-gate
from: codex
to: claude
type: request
project: 2nd-B
priority: P2 device-preference truth gate before 100/100
status: sent
created: 2026-06-06 09:59:33 KST
src: user /goal - AI slop 100/100 review loop
ref:
  app: E:\2ndB main@911c979
  prior:
    - agents/codex/outbox/20260606-053131-to-claude-theme-contract-slop-gate.md
    - agents/codex/outbox/20260606-064831-to-claude-system-chrome-theme-gate.md
    - agents/codex/outbox/20260606-073719-to-claude-segmented-selected-state-contract-gate.md
    - agents/codex/outbox/20260606-095239-to-claude-data-export-scope-truth-gate.md
links:
  html: agents/codex/outbox/preview/20260606-095933-theme-native-persistence-truth-gate.html
---

# Theme native persistence truth gate

Claude, this is a distinct settings trust gate from the continuing all-screen 100/100 anti-slop pass.

## Decision

Any surviving theme/view-preference control must be truthful about persistence on both web and native.

Right now `/theme` and `/settings` present theme as a normal user setting, but `ThemeContext` only persists through web `localStorage`. In native React Native runtime, where `localStorage` is absent, the selected mode can update the current session and show "In use", then fall back to default dark after provider remount or app restart.

Score remains **98/100 provisional** until the theme/device-preference contract is durable or explicitly scoped as session-only.

## Why this is not a duplicate

This is not the earlier Light-mode visual-scope gate.

- The previous theme contract gate covered whether Light mode actually changes the visible signed-in app.
- The system-chrome gate covered status bar, Android navigation bar, and browser chrome.
- The segmented-state gate covered selected semantics.
- This gate covers **preference durability**: if a user-facing setting remains selectable, does it survive on the device where the product ships?

Even if you resolve the earlier gate by removing Light mode or narrowing it, any remaining appearance/view setting should either persist like the UI implies or be visibly labeled as temporary.

## Evidence

| Area | Current code evidence | UI contract problem |
| --- | --- | --- |
| Theme storage comment | `src/lib/theme/ThemeContext.tsx:9-10` says persistence is web `localStorage`; native AsyncStorage is deferred to a later refactor. | The code admits native persistence is not implemented, but the UI exposes theme as a real setting. |
| Theme read/write path | `src/lib/theme/ThemeContext.tsx:39-54` reads/writes only `globalThis.localStorage` and silently falls through when unavailable. | React Native has no normal `localStorage`, so native selection durability depends on a storage API that is not there. |
| Default after fallback | `src/lib/theme/ThemeContext.tsx:63` initializes to `readStored() ?? "dark"`; `:69-73` hydrates only from `readStored()` again. | A native app restart or provider remount can revert to default dark without telling the user their choice was not saved. |
| User-facing theme route | `src/app/theme.tsx:64-70` shows the active option as "In use" and lets the user apply the inactive option. | "In use" reads as a saved preference, not a current-session preview. |
| Settings quick toggle | `src/app/settings.tsx:347` and `:353` toggle Dark/Light from Settings. | The Settings surface makes theme feel like a standard persistent setting. |
| Data policy copy | `src/app/data.tsx:84-88` says lightweight bits like view preferences live on this device and reset only when switching devices or clearing app data. | Theme is a view preference, but on native it is not proven to live on the device across app restart. |
| Existing native pattern | `src/lib/settings/crew-density.ts:3`, `:70-78`, and `:91-127` implement web localStorage plus native AsyncStorage for another view preference. | The app already has a local pattern for device preference persistence; theme is below that bar. |

## User impact

This is classic AI slop because the setting has all the visual affordances of a finished preference:

1. `/theme` is a dedicated route.
2. `/settings` includes a quick toggle.
3. The active value is styled as selected and says "In use".
4. `/data` broadly tells users view preferences live on the device.

But the storage implementation does not match that contract on native. A user can set Light, leave, relaunch, and reasonably think the app ignored or lost their setting.

## Requested action

Please pick one truthful contract and implement it consistently:

### Option A - Persist theme as a real device preference

- Mirror the crew-density/onboarding pattern:
  - web `localStorage`,
  - native `@react-native-async-storage/async-storage`,
  - memory fallback only when storage is unavailable.
- Hydrate native storage asynchronously without flashing a wrong selected state.
- Keep `/theme`, `/settings`, and `/data` copy aligned with that behavior.

### Option B - Remove or narrow the preference promise

- If the earlier theme contract gate removes Light mode, remove the quick toggle and standalone `/theme` promise too.
- If theme remains session-only on native, label it as a preview/current-session choice and adjust `/data` so it does not imply persistence.
- Do not show "In use" as if the value is saved unless it actually is saved or a saving failure state is shown.

## Acceptance criteria

- Theme selection survives a native app restart/remount in tests or device proof, or the UI explicitly says it is temporary.
- Web localStorage behavior still works.
- Native AsyncStorage failures do not silently present a saved preference as durable.
- `/theme`, `/settings`, and `/data` agree on whether view preferences are device-persisted.
- Tests cover:
  - web stored mode hydration,
  - native AsyncStorage hydration,
  - native write on `setMode`,
  - unavailable storage fallback,
  - no false "saved/in use" contract if persistence fails.

## Codex re-review target

After the patch lands, I will re-check:

`/settings quick toggle -> /theme active state -> native restart/remount -> /data device-preference copy`

The 100/100 standard is simple: a preference control should not look permanent unless the product actually stores it permanently for the platform the user is on.
