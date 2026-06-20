# O-11 Code Quality Adversarial Review

Range reviewed: `6d4adb1..32ee865` (`#266` parent through current `main`)
Current head: `32ee865 docs(orders): O-10 design overhaul complete; O-11 4-AI review launched`

## Gate

**FAIL**

No P0 crash regression found, and TypeScript/lint/Jest pass. Gate fails on a P1 shared UI regression: caller `style` props are now applied before base component styles in the premium surface layer, so existing per-screen overrides can be silently overwritten.

## Verification

- `git log --oneline -20`: reviewed; current head is `32ee865`, #266 is `6ae837c`, #266 parent is `6d4adb1`.
- `npm run type-check`: PASS.
- `npm run lint`: PASS.
- `npm test -- --ci`: PASS, 103 suites / 888 tests.
- Target tests: `gameboy-tokens`, `tabs`, `card-insights`: PASS, 13 tests.
- `git diff --check 6d4adb1..32ee865`: FAIL on docs whitespace only (`ORDERS.md`).

## P0

None.

## P1

1. `src/components/premium/surfaces.tsx:78` / `src/components/premium/surfaces.tsx:207` / `src/components/premium/surfaces.tsx:293` / `src/components/premium/surfaces.tsx:382` - Shared surface components now put caller `style` before base styles. This reverses the previous contract where callers could override panel/button/input styles. Concrete fallout:
   - `PremiumPanel` puts `style` before `styles.panel`, so `PremiumCard style={styles.savedPanel}` custom `backgroundColor`, `borderColor`, `borderRadius`, and `padding` can be overwritten by the base panel. Example caller styles are at `src/app/capture.tsx:1264` and `src/app/capture.tsx:1271`.
   - `PremiumButton` puts `style` before `styles.btn`, so `PremiumCTA`'s `styles.cta` padding at `src/components/premium/surfaces.tsx:329` / `src/components/premium/surfaces.tsx:479` is overwritten by `styles.btn.paddingVertical` at `src/components/premium/surfaces.tsx:459`.
   - `PremiumInput`/`PremiumTextarea` now place caller style before `styles.inputFrame` / focus styles, preventing caller-level frame/background/border overrides. This is a regression from the pre-#266 ordering.

## P2

1. `src/lib/motion/pixel-physical.ts:12` - `pixelStackTransition` enforces `animationDuration: 100` and reduced-motion `0`, but it does not implement or expose the requested `steps(3/4)` or explicit linear easing from `ORDERS.md:140` / `ORDERS.md:233`. Button press does use `Easing.linear` at `src/components/premium/surfaces.tsx:223`, but stack transitions rely on the navigator animation curve.

2. `src/lib/motion/pixel-physical.ts:8` - No direct unit test covers `pixelMotionDuration` / `pixelStackTransition`, especially reduced-motion behavior. Existing motion tests cover `prefersReducedMotion`, not this new wrapper.

3. `src/components/graph/NavGraph.tsx:315` - `NodeGlow` now creates three inline halo views per rendered node. This is probably acceptable at current LOD, but it is untested and private inside `NavGraph`, so ring count, alpha falloff, and tier scaling can regress without a focused test.

4. `src/lib/nav/tabs.ts:15` - `PROFILE_CHILD_PATHS` / `isProfileChildPath` are tested at `src/lib/nav/__tests__/tabs.test.ts:8`, but unused by runtime code. `BackArrow` and tab clearance still key only off `isPrimaryTabPath` (`src/components/ui/BackArrow.tsx:80`). The test locks the constant, not the intended profile-child integration.

5. `src/app/index.tsx:349` - `overviewCardSignals(dataNodes)` is recomputed on every Landing render instead of memoized. The pure helper has good unit coverage, but the UI integration for recent/sparse card copy is not covered.

6. `ORDERS.md:131`, `ORDERS.md:436`, `ORDERS.md:868`, `ORDERS.md:1170`, `ORDERS.md:1377` - `git diff --check` fails on trailing whitespace / final blank line in docs. Not a runtime issue, but it is a hygiene gate failure if whitespace checks are enforced.

## Checks Requested

- TypeScript errors / `any`: no type errors. Diff added no new `any`, `as unknown`, or `as never` casts under `src`.
- Render-heavy work: no new heavy algorithmic work found in #266-#276. Existing `NavGraph` render-time `Animated.add(new Animated.Value(baseX), ...)` pattern predates #266.
- `pixel-physical` steps/easing: duration and reduced-motion are present; stack step/linear easing is not implemented.
- `Animated.Value` / `useNativeDriver`: no #251-style regression found. `AnimatedLine` remains JS-driven for SVG props (`useNativeDriver:false` at `src/components/graph/NavGraph.tsx:848`, `src/components/graph/NavGraph.tsx:1173`, `src/components/graph/NavGraph.tsx:1368`). New native-driver usage is limited to transform/opacity-compatible `AnimatedPressable` press motion.
- Coverage gaps: `gameboy-tokens` and `tabs` have basic tests; `NodeGlow`, `pixel-physical`, premium surface style merge order, and card UI integration do not.
