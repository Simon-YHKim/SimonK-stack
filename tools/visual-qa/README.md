# hub visual-qa — pixel-based UI verification for any AI

Shared tool so **any hub AI (Claude / Codex / Grok / Antigravity)** verifies 2nd-B UI by the
**pixels that actually render**, not by "no crash in the logs". It exists because of a real
miss (2026-06-14): AG reported the home screen "PASS" while the captured frame was pure
black — the verdict had leaned on logcat + the accessibility tree, never on the image.

## Rule this enforces
A screen is **FAIL** if its frame is black/empty **even when nothing crashed**. No-FATAL ≠ rendered.

## Run
```bash
cd "E:/Coding Infra/AI Infra/Communication/tools/visual-qa"
npm install            # one-time: playwright + pngjs
npx playwright install chromium   # one-time: the browser
npm run shoot                      # default: Android-Chrome engine, live Pages (current main)
node shoot.mjs --engine both       # Android-Chrome AND iPhone-Safari (WebKit + iPhone 15 viewport)
node shoot.mjs --engine webkit     # iPhone-Safari only
# or local expo web (run `npm run web` in E:/2ndB first):
node shoot.mjs --base http://localhost:8081 --out ./shots-local
```

`--engine webkit` uses Playwright **WebKit** = the real iOS Safari engine at an iPhone device
descriptor, so it shows how 2nd-B WEB renders on an iPhone. One-time: `npx playwright install webkit`.

## iPhone / iOS coverage (read this)
- **iPhone WEB (Safari engine): covered here** via `--engine webkit`/`both`. Real Safari render, iPhone viewport.
- **Native iOS app: NOT testable on this Windows box** (Windows cannot run the iOS Simulator). For
  real native-iOS screens use an **EAS iOS build on Appetize.io** or a **physical iPhone** (TestFlight /
  dev build). See memory `tool_2ndb_ios_eas_hermes_fix` for the EAS Hermes gotchas already solved.

## Native Android: drive the live emulator, never let it park
The live emulator parks on whatever screen it was left on ("same screen forever"). To actually
*check* screens, navigate it and capture each:
```bash
adb exec-out screencap -p > now.png                 # what is it parked on right now
adb shell wm size                                    # e.g. 1344x2992
adb shell input tap <x> <y>                          # tap a tab / button (tab row y ~= 0.965*height)
```
Then Read the PNGs. Tab centers for the 4-tab bar = width * {0.125, 0.375, 0.625, 0.875}.
AG (native lane) must SCRIPT this navigation through every key screen with a fresh per-screen
shot + per-screen verdict -- not park on one screen and call it "PASS".

Output: `shots/<screen>.png` + `shots/verdict.json`. Per screen it reports
`meanLum` (mean luminance), `darkFrac` (fraction near-black), `textLen` (visible text),
and a verdict: `OK | BLACK | BLANK | MISSING | ERROR`. Exit 2 if any screen is not OK.

## Who judges what (Simon, 2026-06-14)
Split the verdict by what each step is good at:
- **Capture + black/blank gate (objective): Claude** runs `shoot.mjs`. `meanLum`/`darkFrac`/
  `textLen` are measurements, not opinions — a black/empty frame is a mechanical FAIL here
  regardless of crash logs.
- **In-image detail judgment (what's actually on the screen — copy correctness, layout,
  hierarchy, the 4 UX axes): Codex + Antigravity.** They read the captured PNGs and are the
  **authority** on detailed content; **do not** substitute Claude's own eyeball read for theirs.
- **Aggregate + act: Claude** collects Codex's + AG's per-screen verdicts and proceeds on them.

So the loop is: Claude captures fresh PNGs + gates black/blank -> hands the PNGs to Codex and
AG -> they return **per-screen** content verdicts (fresh shot each, never a blanket "all PASS")
-> Claude aggregates and acts.

## Coverage
`screens.json` lists the key screens. `auth:false` screens (sign-in, sign-up/consent,
landing) are reachable by web capture. `auth:true` screens (home, capture, persona) need a
logged-in/seeded session — covered by **AG native emulator** capture today (a seeded web
session is a future add). Keep `screens.json` in sync with the real expo-router routes.

## For the other AIs
- **Codex + Antigravity** are the in-image-detail authority. Given fresh PNGs (web shots
  here, or AG's native captures for `auth:true` screens), return a **per-screen** verdict:
  is the content correct (copy, layout, hierarchy, the 4 UX axes), what's wrong, what's the
  fix. One fresh shot per screen; never a blanket "all PASS"; assert content rendered (not
  just "no ANR"). Do not reuse old grabs.
- **Grok**: market/consumer lens on the same shots if asked.
- **Claude**: capture + black/blank gate + aggregate Codex/AG verdicts; does not override
  their content read.
