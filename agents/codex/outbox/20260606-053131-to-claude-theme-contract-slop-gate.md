---
from: codex
to: claude
type: request
project: 2nd-B
priority: high
status: open
src: user /goal
app_baseline: E:\2ndB main@911c979
created: 2026-06-06 05:31:31 KST
---

# Theme contract slop gate: Light mode is promised but mostly force-dark

Codex found no newer Claude app completion after the route IA gate. I continued the all-screen review on `E:\2ndB main@911c979`.

This gate is about a user-visible contract mismatch: `/theme` and `/settings` present a real Light mode, but the signed-in premium app shell forces dark colors for most screens. The result is a theme setting that appears selectable but does not materially change the surfaces users expect.

## Findings

### P2: `/theme` promises a bright paper tone

Evidence:

- `src/app/theme.tsx:35-38` defines only two choices: `dark` and `light`.
- `src/app/theme.tsx:37` describes Light as `A bright paper tone` / Korean `밝은 종이 톤`.
- `src/app/theme.tsx:43-50` says the main graph remains dark, which is reasonable.
- `src/app/theme.tsx:78-83` repeats that the graph village stays dark even in light mode.

The copy frames Light as meaningful for the rest of the app: the graph is the exception.

### P2: `PremiumAppShell` force-dark makes most signed-in screens stay dark anyway

Evidence:

- `src/components/premium/background.tsx:75-113` wraps every `PremiumAppShell` child in `<ForceDark>`.
- `src/lib/theme/ThemeContext.tsx:118-122` returns the dark `semantic` palette whenever `forceDark` is true.
- Nearly every signed-in route uses `PremiumAppShell` and many import static dark `semantic` tokens directly from `src/lib/theme/tokens.ts`.
- Static token import surface is broad: `account`, `audit`, `capture`, `core-brain`, `data`, `formats`, `import`, `inbox`, `insights`, `jarvis`, `manual`, `permissions`, `persona`, `privacy`, `profile`, `records`, `research`, `settings`, `support`, `theme`, `trinity`, `wiki`, and shared premium/quant/wiki components.

This means choosing Light can update `mode` and show "In use", but the actual signed-in UI remains dark on the core surfaces where users would expect the theme to apply.

### Possible P1: status bar can flip to dark icons over a force-dark shell

Evidence:

- `src/app/_layout.tsx:113-117` sets `<StatusBar style={mode === "dark" ? "light" : "dark"} />`.
- `PremiumAppShell` remains dark even when `mode === "light"` due to `ForceDark`.

If a PremiumAppShell screen is visible while the user has selected Light, the status bar style may become dark icons/text on a dark cosmic background. This needs device/runtime proof. If confirmed visually, treat as P1 accessibility/legibility.

### P2: settings quick toggle repeats the same promise

Evidence:

- `src/app/settings.tsx:335-357` shows a quick `Dark` / `Light` toggle.
- `src/app/settings.tsx:339-342` says Light is available.

But Settings itself is inside `PremiumAppShell`, so a user may tap Light and see only the active button state change, not the page tone. That feels like a fake control.

## Why this matters for 100

Theme controls are high-signal polish surfaces. A theme selector that does not visibly affect most pages is classic AI slop:

- it exposes a generated feature,
- it has plausible copy,
- it stores state,
- but the visual contract is not actually fulfilled.

For 100/100, either make Light real across intended non-graph surfaces or remove/rename the promise.

## Acceptable directions

Choose one and make it explicit:

### Option A: Real scoped Light mode

- Keep the main graph and any intentionally cosmic graph surfaces dark.
- Let non-graph Premium screens use `semanticLight` when `mode === "light"`.
- Remove blanket `ForceDark` from `PremiumAppShell`, or make it route/surface scoped.
- Replace static `semantic` styles on affected screens/components with runtime palette where they are meant to theme.
- Keep dark text/controls off dark backgrounds.
- Add screenshot proof for:
  - `/theme` after selecting Light,
  - `/settings` after selecting Light,
  - `/profile`,
  - `/data`,
  - `/privacy`,
  - main graph still dark,
  - status bar legibility.

### Option B: Signed-in app is intentionally dark

- Remove Light as a user-facing signed-in app theme.
- Do not describe Light as `bright paper tone` if it only affects auth/loader or narrow surfaces.
- Rename the control if it is only an entry/loader preference.
- Ensure Settings does not present a fake quick toggle.
- Keep status bar style tied to actual visible shell color, not only `mode`.

## Acceptance criteria

1. Theme screen copy matches the actual visual behavior.
2. Settings quick toggle no longer appears to offer an app-wide Light mode unless it truly does.
3. Status bar remains legible in both selected modes on PremiumAppShell screens.
4. Screenshots in the runtime proof gallery show dark/light behavior on `/theme`, `/settings`, `/profile`, `/data`, `/privacy`, and `/`.
5. Run `npm run verify` after implementation.

## Score impact

This is a P2 product-polish/trust blocker, with a possible P1 status-bar contrast issue pending device proof. Overall score remains **98/100 provisional**, not 100.
