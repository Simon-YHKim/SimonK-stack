# 2nd-B Review Cycle 2 (post-15-PR main) — confirmed in-lane fix list

## CONFIRMED (REAL + in-lane) — 46
- [P1][integration-regression] Missing Stack.Screen registration for /profile primary tab
  file: E:/2ndB/src/app/_layout.tsx:48-82
  evidence: /profile is listed in PRIMARY_TAB_PATHS (E:/2ndB/src/lib/nav/tabs.ts:50), registered in PremiumTabBar as a tab destination (E:/2ndB/src/components/premium/tab-bar.tsx:35), and is navigated to from settings (E:/2ndB/src/app/settings.tsx). However, it is not registered as <Stack.Screen name="profile" /> in the Stack, while journal (also a redirect) IS registered at line 51. This breaks the /profile navigation from the tab bar and from settings.
  fix: Add <Stack.Screen name="profile" /> after line 72 (after <Stack.Screen name="import" />) to explicitly register the profile route in the navigation stack, matching the pattern used for journal and other redirect routes.
  verify: REAL (Based on my thorough analysis of the codebase, here's my verdict:  **VERDICT=REAL inLane=yes**)
- [P2][integration-regression] Missing Stack.Screen registration for /imagine redirect route
  file: E:/2ndB/src/app/_layout.tsx:48-82
  evidence: imagine.tsx (E:/2ndB/src/app/imagine.tsx) is a redirect stub that redirects to /secondb with divergent mode, exactly like journal.tsx which IS registered at line 51. The comment at line 78 acknowledges "/imagine is now a redirect into Divergent mode" but does not register it. The BackArrow component has a label entry for /imagine at E:/2ndB/src/components/ui/BackArrow.tsx:43, indicating the route should be navigable. This creates an inconsistency with how journal is handled.
  fix: Add <Stack.Screen name="imagine" /> to the Stack.Screen list in _layout.tsx to match the pattern used for journal. Insert it after line 51 (after <Stack.Screen name="journal" />) for consistency, or after <Stack.Screen name="import" /> at line 72.
  verify: REAL (Looking at the evidence:  1. **imagine.tsx** - Confirmed redirect stub redirecting to `/secondb?mode=divergent`, with comment "公想 is no longer a place — it is SecondB's Divergent chat mode.")
- [P0][routing-ia] Missing Stack.Screen registration for /onboarding route
  file: E:/2ndB/src/app/_layout.tsx:49-81
  evidence: The root _layout.tsx registers 28 Stack.Screen entries but omits 'onboarding'. However, E:/2ndB/src/app/index.tsx:308 redirects unauthenticated users to /onboarding: `if (!onboardingComplete) return <Redirect href="/onboarding" />;`. The route file exists (E:/2ndB/src/app/onboarding.tsx) and is a full functional screen, not a redirect stub.
  fix: Add `<Stack.Screen name="onboarding" />` to the Stack.Screen list in _layout.tsx (around line 59, after plans)
  verify: REAL (VERDICT=REAL inLane=yes  The onboarding route is actively redirected to at E:/2ndB/src/app/index.tsx:308 (`if (!onboardingComplete) return <Redirect href="/onboarding" />;`), and the full functional screen exists at E:/2ndB/src/app/onboarding.tsx with navigation logic and UI. However, E:/2ndB/src/ap)
- [P0][routing-ia] Missing Stack.Screen registration for /profile route
  file: E:/2ndB/src/app/_layout.tsx:49-81
  evidence: E:/2ndB/src/app/settings.tsx:350 calls `router.push("/profile")` when the Profile button is pressed, but /profile is not registered in Stack.Screen. The route file exists (E:/2ndB/src/app/profile.tsx) and is a functional profile hub screen.
  fix: Add `<Stack.Screen name="profile" />` to the Stack.Screen list in _layout.tsx
  verify: REAL (Looking at the evidence systematically:  **_layout.tsx review (lines 49-81):** The Stack.Screen registrations show routes for: index, (auth), journal, audit, persona, capture, inbox, formats, secondb, jarvis, plans, wiki, manual, big-five, insights, attachment, permissions, research, trinity, mbti, )
- [P0][routing-ia] Missing Stack.Screen registration for /theme route
  file: E:/2ndB/src/app/_layout.tsx:49-81
  evidence: E:/2ndB/src/app/settings.tsx:368 calls `router.push("/theme")` when the Theme button is pressed, but /theme is not registered in Stack.Screen. The route file exists (E:/2ndB/src/app/theme.tsx) and is a functional screen for dark/light mode selection.
  fix: Add `<Stack.Screen name="theme" />` to the Stack.Screen list in _layout.tsx
  verify: REAL (VERDICT=REAL inLane=yes  settings.tsx:368 calls `router.push("/theme")` but `/theme` is absent from the Stack.Screen list in _layout.tsx:49-81. The route file E:/2ndB/src/app/theme.tsx exists with a valid ThemeScreen export, but there is no `<Stack.Screen name="theme" />` registered in the navigatio)
- [P0][routing-ia] Missing Stack.Screen registration for /data and /support routes
  file: E:/2ndB/src/app/_layout.tsx:49-81
  evidence: E:/2ndB/src/app/settings.tsx has router.push calls at lines 374 and 386 for `/data` and `/support` respectively, but neither route is registered in Stack.Screen. Both route files exist (data.tsx, support.tsx) as functional screens. These are part of the A-to-Z Phase 12 settings navigation.
  fix: Add `<Stack.Screen name="data" />` and `<Stack.Screen name="support" />` to the Stack.Screen list in _layout.tsx
  verify: REAL (VERDICT=REAL inLane=yes  Both `/data` and `/support` routes are actively pushed to in settings.tsx (lines 374, 386) and their handler files exist as functional screens (data.tsx, support.tsx), but neither is registered with `<Stack.Screen>` in _layout.tsx:49-81. The fix requires adding two registrat)
- [P0][routing-ia] Missing Stack.Screen registration for /esm route
  file: E:/2ndB/src/app/_layout.tsx:49-81
  evidence: E:/2ndB/src/app/profile.tsx:38 includes `/esm` in the hub routes: `{ key: "esm", route: "/esm" }`. This route is clickable from the profile hub (line 161: `router.push(item.route)`), but /esm is not registered in Stack.Screen. The route file exists (esm.tsx) as a functional Experience Sampling Method check-in screen.
  fix: Add `<Stack.Screen name="esm" />` to the Stack.Screen list in _layout.tsx
  verify: REAL (VERDICT=REAL inLane=yes  E:/2ndB/src/app/_layout.tsx:49-81 has no `<Stack.Screen name="esm" />` entry. The route exists in profile.tsx:38 (`{ key: "esm", route: "/esm" }`) and the esm.tsx screen file is present and functional, but Stack.Screen registration is missing.)
- [P1][i18n-coherence] Hardcoded tier display names bypass i18n in conversation.ts
  file: E:/2ndB/src/lib/chat/conversation.ts:112-117
  evidence: TIER_DISPLAY constant hardcodes 'Free', 'Plus', 'Pro' as English-only strings. These are embedded in BLOCKED_HINT messages on lines 122 and 126 that are shown to users in both English and Korean locales. The Korean BLOCKED_HINT uses the hardcoded English tier names, leaving tier names untranslated in user-facing upgrade prompts.
  fix: Move tier display names to secondb.json locale files (add keys like 'tier.free', 'tier.plus', 'tier.pro') and update TIER_DISPLAY to reference t() instead of hardcoded strings. Alternatively, use a mapping function that looks up tier names from the i18n system.
  verify: REAL (VERDICT=REAL inLane=yes  Korean UI embeds English tier names from hardcoded TIER_DISPLAY constant (lines 112-117) directly into locale message template at line 126: `${TIER_DISPLAY[upgrade]} 플랜으로 업그레이드하면`. The hint is shown verbatim to users (secondb.tsx:204), breaking i18n coherence.)
- [P1][i18n-coherence] SecondB screen contains large blocks of hardcoded English/Korean text in speech/eyebrow props
  file: E:/2ndB/src/app/secondb.tsx:252-270
  evidence: Lines 252, 260-262, 264-266, 268-269 contain hardcoded user-facing strings in nested ternaries: (1) eyebrow='06. 세컨비 대화'/'06. SecondB chat'; (2) speech for sending state with 'I'm reading the pieces that matter.'/'참고한 조각들을 읽어오는 중이에요.'; (3) speech for divergent mode; (4) speech for analytic mode. These strings are not in secondb.json and bypass the i18n system.
  fix: Add keys to secondb.json for: 'eyebrow', 'speech.sending', 'speech.divergent', 'speech.analytic'. Update secondb.tsx lines 252 and 258-270 to use t() calls instead of inline ternaries. Verify both en/ko locale files have matching keys.
  verify: REAL (VERDICT=REAL inLane=yes  Lines 252 and 258-270 contain hardcoded locale ternaries ("06. 세컨비 대화"/"06. SecondB chat" and four speech variants) that bypass i18n; these strings are absent from locales/en/ko/secondb.json and should use t() like lines 253-254 demonstrate.)
- [P2][i18n-coherence] Usage panel in SecondB contains hardcoded action button strings with inline locale ternaries
  file: E:/2ndB/src/app/secondb.tsx:275-310
  evidence: Lines 275, 291, 295, 305-309 contain hardcoded English/Korean strings in locale ternaries: 'Today'/'오늘' (line 275), 'View plans'/'플랜 보기' (lines 291, 295), 'Clear chat'/'대화 비우기' (lines 305, 309). Also hardcoded accessibility labels and hints on lines 292, 306. These action strings appear throughout the user interface but are not internationalized via locale files.
  fix: Add keys to secondb.json: 'usage.today', 'usage.viewPlans', 'usage.viewPlansHint', 'usage.clearChat', 'usage.clearChatHint'. Update all hardcoded ternaries in the usagePanel section to use t() calls. This improves maintainability and ensures consistency with the i18n system.
  verify: REAL (VERDICT=REAL inLane=yes  Lines 275, 291-292, 295, 305-306, 309 in secondb.tsx contain hardcoded "Today"/"오늘", "View plans"/"플랜 보기", "Clear chat"/"대화 비우기" with inline locale ternaries instead of t() calls; component imports useTranslation and uses t() elsewhere (lines 253, 376, 491, etc.) but not in )
- [P2][i18n-coherence] QUICK_ACTIONS array contains hardcoded English/Korean strings not in locale files
  file: E:/2ndB/src/app/secondb.tsx:41-47
  evidence: QUICK_ACTIONS constant (lines 41-47) defines 5 quick-action chips with hardcoded en/ko properties: 'Next step'/'다음 한 걸음', 'Divergent mode'/'공상 모드로', 'Save to wiki'/'지식 창고에 저장', etc. Each action also has a prompt field with hardcoded English/Korean strings. These are user-facing UI elements not managed by the i18n system.
  fix: Move QUICK_ACTIONS to secondb.json under a nested 'quickActions' key with an array structure, or create separate locale keys for each action label and prompt. Update the component to load these strings from t() instead of hardcoding them. This allows for easier localization and maintenance.
  verify: REAL (VERDICT=REAL inLane=yes Hardcoded QUICK_ACTIONS array at E:/2ndB/src/app/secondb.tsx:41-47 contains en/ko strings ("Next step"/"다음 한 걸음", etc.) and nested prompts not defined in E:/2ndB/locales/{en,ko}/secondb.json; component renders them directly without i18n at lines 470-483.)
- [P1][ux-flow-gaps] Send button not disabled when daily AI limit is reached
  file: E:/2ndB/src/app/secondb.tsx:231
  evidence: Line 231: `const canSend = draft.trim().length > 0 && !sending;` checks only if draft is not empty and not currently sending. It does NOT check if `usedToday >= limit`. When a returning free user hits their 5-message daily limit, they can still click the Send button. The LLM call fails server-side (bumpChatUsageIfUnderCap throws ChatLimitExceededError), and the user sees the blocked hint (lines 203-205). However, the UI should prevent the attempt entirely by disabling the button when `usedToday !== null && usedToday >= limit`.
  fix: Modify line 231 to: `const canSend = draft.trim().length > 0 && !sending && (usedToday === null || usedToday < limit);`
  verify: REAL (VERDICT=REAL inLane=yes Line 231 `const canSend = draft.trim().length > 0 && !sending;` lacks the limit check — the button remains clickable when `usedToday >= limit`, relying on server-side rejection instead of UI prevention.)
- [P2][ux-flow-gaps] Missing error recovery hint when Core Brain load fails
  file: E:/2ndB/src/app/core-brain.tsx:150-161
  evidence: Lines 150-161 show error state with two buttons: "Try again" and "Start with SecondB". However, the error message (lines 146-148) only says "connection wobbled" without suggesting why (RLS, timeout, token refresh). For a non-technical senior user or first-time user, they won't know if they should retry, check internet, or try later. The secondary button routes to /secondb, but a user with zero pieces will immediately hit the empty chat state, creating confusion about the intended flow.
  fix: Add context-specific guidance: (1) Include 'Check your internet connection' in error message, (2) Add timestamp of last successful load so user can see if it's been down, (3) Consider routing to /home instead of /secondb if user has no pieces yet.
  verify: REAL (VERDICT=REAL inLane=yes  Error message (lines 145-149) only says "connection wobbled" with no diagnostic hints or internet check prompt; secondary button routes to `/secondb` unconditionally without checking user piece count, creating confusion for zero-piece users who immediately hit empty state. F)
- [P2][ux-flow-gaps] Empty state in /secondb when entering with fromNode parameter but no pieces
  file: E:/2ndB/src/app/secondb.tsx:365-378
  evidence: Lines 365-378 show empty chat state when `turns.length === 0`. User can reach /secondb from graph node (fromNode param at line 96) but if they have zero saved pieces, the wiki snapshot exported to buildPersona will be minimal. Line 375 shows generic 'empty' message, but doesn't explain that the chat will be more useful once they save their first piece (unlike /capture which explicitly says 'Leave a first piece'). The UX is asymmetric: /capture's empty state invites action, but /secondb's doesn't.
  fix: When no pieces exist, show a contextual empty state: (1) Check if usedToday < limit (they haven't hit the cap), (2) Show message like 'SecondB will be more helpful once you save your first piece' with a link to /capture, (3) Offer to continue to /secondb anyway if they want to explore it empty.
  verify: REAL (VERDICT=REAL inLane=yes  The empty state message at `/secondb.tsx:375-376` shows `t("empty")` which is "Start a conversation. Try: \"What patterns show up across my captures this month?\"" — this assumes the user has captured pieces. The code at line 365 checks only `turns.length === 0` (no chat tur)
- [P3][ux-flow-gaps] First-time user can dismiss empty graph card but has no alternative entry point visible
  file: E:/2ndB/src/app/index.tsx:361-433
  evidence: Lines 417-430 show the 'I'll look around first' button that dismisses the empty graph card. This allows first-time users to explore without saving a piece. However, once dismissed, the card won't show again (persisted via emptyGraphDismissed at line 186). The only visible CTA after dismissal is the 'Today's center' ribbon at lines 453-474, which routes to /core-brain. For a user with zero pieces, core-brain shows its own empty state (core-brain.tsx:168-195) with 'Leave today's piece' CTA. The path is: dismiss card → explore graph (nothing to see) → today's center → empty core → finally capture. The UX should either (A) not let dismissal persist, or (B) surface a sticky 'Create first note' affordance after dismissal.
  fix: Either: (1) Make empty card dismissal session-only (clear on app restart), OR (2) After dismissing, show a subtle persistent 'New note' FAB or bottom sheet when user is idle on the graph for >30 seconds.
  verify: REAL (VERDICT=REAL inLane=yes  The empty card dismissal is permanently persisted (empty-card.ts:41-48 to localStorage/AsyncStorage), and after dismissal the only visible entry point on the graph screen is the "Today's center" ribbon (index.tsx:453-474), which routes to core-brain where another empty state)
- [P3][ux-flow-gaps] onboarding.tsx allows skipping to graph without any data, no incentive to save first piece
  file: E:/2ndB/src/app/onboarding.tsx:108-111,155-162
  evidence: Lines 108-111: finishToGraph() skips onboarding and goes to /. Lines 155-162: both last-step button options (primary 'Save my first note' and secondary 'Skip and look around') let user escape onboarding. A user can complete all 3 onboarding slides (which teach the value of saving pieces) and then choose to skip. They land on the empty graph with the dismissible empty-graph-card (index.tsx). The consequence: zero friction to reach a dead-end (empty graph, no pieces, confusing next step). For non-technical seniors, this is particularly bad.
  fix: On the final onboarding step, make the primary button more prominent and secondary button less visible. Consider: (1) Remove skip button on last slide, (2) Auto-focus the primary CTA, (3) Add micro-copy 'One sentence is enough to start' to lower the activation energy for the primary path.
  verify: REAL (VERDICT=REAL inLane=yes Final onboarding slide allows escape via secondary "Skip and look around" button (E:/2ndB/src/app/onboarding.tsx:155-162) that calls finishToGraph(), marking onboarding complete and leaving user on empty graph with only dismissible empty-card friction. UX-only fix (button pro)
- [P1][data-truth] "Notify me" button claims notification signup without backend integration
  file: E:/2ndB/src/app/plans.tsx:94
  evidence: The button is labeled t('notify') = 'Notify me at launch' with hint t('notifyHint') = 'We will let you know when Plus is ready'. However, the onPress handler only executes setNotified(true), setting local component state. There is no API call to register the notification preference, no email collection, no backend persistence, and no integration with any notification system. The notified state variable is not persisted beyond the current app session.
  fix: Either (1) implement full notification system with email collection and backend persistence via Supabase, or (2) replace the button with honest copy saying 'Coming soon' or 'Checking availability' that doesn't claim notification functionality. The current implementation should not use the word 'Notify' since the feature does not exist.
  verify: REAL (Perfect. I have enough information to make my verdict.  **VERDICT=REAL inLane=yes**)
- [P1][dead-code-hygiene] Orphaned worker asset pack: /workers/ directory
  file: public/assets/2ndb-production-premium-v1/workers/
  evidence: Grep found 0 references to '2ndb-production-premium-v1/workers/' in src/ (excluding workers-redraw-v1). All worker assets loaded from /workers-redraw-v1/ in src/components/art/WorkerSprite.tsx:24-40.
  fix: Delete public/assets/2ndb-production-premium-v1/workers/ directory (14 PNG files: archi_premium_*.png, gadi_premium_*.png, lulu_premium_*.png, lumi_premium_*.png, momo_premium_*.png, secondb_premium_*.png, vela_premium_*.png). Keep workers-redraw-v1 which is the current production pack.
  verify: REAL (Perfect. My verification is complete. Let me provide the verdict:  VERDICT=REAL inLane=yes)
- [P1][dead-code-hygiene] Orphaned worker asset pack: /workers-sharp/ directory
  file: public/assets/2ndb-production-premium-v1/workers-sharp/
  evidence: Grep found 0 references to 'workers-sharp' anywhere in src/. WorkerSprite.tsx uses only workers-redraw-v1.
  fix: Delete public/assets/2ndb-production-premium-v1/workers-sharp/ directory (14 PNG files). This is an alternative render pass that was never integrated.
  verify: REAL (VERDICT=REAL inLane=yes Workers-sharp directory contains 14 PNG files with identical filenames to workers-redraw-v1; zero code references exist across the entire codebase (grep confirms). WorkerSprite.tsx (lines 24-29, 35-40) exclusively imports from workers-redraw-v1, never workers-sharp. This is a)
- [P2][dead-code-hygiene] Unused SVG companion state sprites in cosmic-pixel-v3-soulcore
  file: public/assets/cosmic-pixel-v3-soulcore/companions/sprites/
  evidence: Only idle poses imported in src/lib/assets/soulcore-v3.ts:21-25 (archon_idle, relia_idle, lumen_idle, foreman_momo_idle, iris_idle). Grep found 0 references to archon_build, archon_highlight, archon_linking, relia_carry, relia_guide, lumen_illuminate, iris_curate, etc. or any sprite_sheet.svg files.
  fix: Delete 26 unused SVG files: all archon_*.svg except idle (6 files), all relia_*.svg except idle (6 files), all lumen_*.svg except idle (7 files), all foreman_momo_*.svg except idle (7 files). Comments in soulcore-v3.ts note these are 'not yet mounted'—they appear to be reserved for future animation states but currently unused.
  verify: REAL (VERDICT=REAL inLane=yes  The 30 non-idle SVG companion sprites genuinely exist unused in public/assets/cosmic-pixel-v3-soulcore/companions/sprites/ (archon, relia, lumen, foreman_momo, iris subdirectories), with only idle variants imported in src/lib/assets/soulcore-v3.ts:21-25 and zero grep referen)
- [P2][dead-code-hygiene] Unused PNG size variants in cosmic-pixel-v3-soulcore/final-candidate-v45
  file: public/assets/cosmic-pixel-v3-soulcore/final-candidate-v45/tier1_soul_core/
  evidence: Only soul_core_256.png is referenced in src/lib/assets/soulcore-v3.ts:116 and src/components/art/SoulcoreFinalArt.tsx:27. Grep found 0 references to soul_core_96.png, soul_core_128.png, soul_core_384.png, or soul_core_preview512.png.
  fix: Delete 4 unused PNG files: soul_core_96.png, soul_core_128.png, soul_core_384.png, soul_core_preview512.png from tier1_soul_core/. Also delete unused 96px and preview variants from tier2_pattern_cores/: bond_core_96.png, bond_core_preview384.png, growth_core_96.png, growth_core_preview384.png, muse_core_96.png, muse_core_preview384.png, narrative_core_96.png, narrative_core_preview384.png, wisdom_core_96.png, wisdom_core_preview384.png (20 files total).
  verify: REAL (Perfect. Let me summarize my findings with a final verification of the actual situation:  **Files confirmed to exist on disk:**)
- [P2][dead-code-hygiene] Unused size variants in cosmic-pixel-v4-tesseract-v49 (app_128 and app_96 directories)
  file: public/assets/cosmic-pixel-v4-tesseract-v49/app_128/ and app_96/
  evidence: Only app_256/ files are referenced in src/components/art/SoulcoreFinalArt.tsx:72-77, 107-115, 140, 143. Grep found 0 references to v49_128, v49_96, or @4x anywhere in src/.
  fix: Delete entire app_128/ directory (10 PNG files) and app_96/ directory (10 PNG files) from cosmic-pixel-v4-tesseract-v49. Also delete pattern_link/pattern-link-crystal-conduit-tile-v47-3@4x.png (only v47-3.png is used at line 143).
  verify: REAL (VERDICT=REAL inLane=yes  E:/2ndB/src/components/art/SoulcoreFinalArt.tsx:143 confirms only pattern-link-crystal-conduit-tile-v47-3.png is used (not @4x), and lines 71-115 confirm all v49 code references are app_256 only. Zero references to app_128, app_96, or @4x found in entire src/. The manifest.j)
- [P1][monetization-coherence] Deprecated soma tier still exposed in EXPO_PUBLIC_FORCE_TIER enum
  file: E:/2ndB/src/lib/env.ts:53
  evidence: Line 53 includes 'soma' in the .enum(['off', 'free', 'soma', 'cortex', 'brain']) declaration for EXPO_PUBLIC_FORCE_TIER test override. Per D-09 deprecation, soma should never appear as a valid option in released code, even for testing, since it risks accidental exposure.
  fix: Remove 'soma' from the enum, leaving only ['off', 'free', 'cortex', 'brain']. Update line 49 comment to remove reference to soma as a test option. This prevents accidental misuse of the deprecated tier in test/release builds.
  verify: REAL (VERDICT=REAL inLane=yes  Line 53 of E:/2ndB/src/lib/env.ts includes "soma" in the EXPO_PUBLIC_FORCE_TIER enum despite explicit D-09 deprecation comments (E:/2ndB/src/lib/chat/limits.ts:39 and conversation.ts:109-110 state "deprecated soma must never reach the UI"). This creates test-override exposur)
- [P1][monetization-coherence] EXPO_PUBLIC_FORCE_TIER comment mentions deprecated soma tier
  file: E:/2ndB/src/lib/env.ts:49
  evidence: Line 49 comment says '"soma" | "cortex" | "free": pin everyone to that tier to test a specific paywall boundary'. Since soma is deprecated and not a live launch tier, it should not be listed as a standard test option.
  fix: Update comment to read '"cortex" | "free": pin everyone to that tier to test a specific paywall boundary.' This clarifies that only current tiers are available for testing.
  verify: REAL (VERDICT=REAL inLane=yes  Reason: E:/2ndB/src/app/plans.tsx:5 confirms "soma is a deprecated alias of Plus (D-09)" — soma must remain in the env.ts enum for legacy user backwards compatibility, but the line 49 comment lists it as a standard test option, which is incoherent. Comment should reference o)
- [P2][monetization-coherence] File header comment in conversation.ts lists 'Soma 30' as active tier
  file: E:/2ndB/src/lib/chat/conversation.ts:4
  evidence: Line 4 comment says '2. Check the tier limit (free 5, Soma 30, Cortex 80, Brain 250).' The capitalized 'Soma' implies it is a current tier, when it is actually deprecated. Should use tier names consistently with the launch tier display names (Free/Plus/Pro) or internal enum names.
  fix: Update comment to '2. Check the tier limit (free 5, Plus 80, Pro 250).' This reflects the actual launch tier names and removes reference to the deprecated soma enum value.
  verify: REAL (VERDICT=REAL inLane=yes  The comment at E:/2ndB/src/lib/chat/conversation.ts:4 mentions "Soma 30", but entitlements.ts:7 and limits.ts:39-41 confirm Soma is deprecated ("enum kept for legacy rows"). The display tier names are Free/Plus/Pro per plans.tsx:1 and line 26 mapping. Comment should use curr)
- [P2][monetization-coherence] Tier hierarchy comment in entitlements.ts includes deprecated soma
  file: E:/2ndB/src/lib/progression/entitlements.ts:2
  evidence: Line 2 comment says 'Stepped unlock: brain > cortex > soma > free.' This lists soma as if it were a current tier in the hierarchy. The comment should clarify the current (live launch) tier ordering or note that soma is legacy-only.
  fix: Update comment to 'Stepped unlock: brain > cortex > free. (soma is deprecated legacy tier, kept for backward-compat with existing users.)' This clarifies the tier hierarchy while documenting why soma appears in the SubscriptionTier type.
  verify: REAL (VERDICT=REAL inLane=yes The comment at entitlements.ts:2 lists "brain > cortex > soma > free" without clarifying deprecation status, while plans.tsx:22-23 confirms soma is deprecated: "soma is a deprecated alias of Plus (D-09), so a legacy soma user still sees Plus highlighted as current." A one-lin)
- [P0][accessibility] Usage panel button touch target below 44px minimum
  file: E:/2ndB/src/app/secondb.tsx:286-297
  evidence: The 'View plans' Pressable button in the usage panel has hitSlop={4} (8px total extra touch area) but no paddingVertical on the Pressable itself. The contained Text is variant='caption' (14px font). Calculated touch target is approximately 22px, well below the 44px minimum recommended by WCAG 2.5.5 and Apple/Google accessibility guidelines.
  fix: Add minHeight={44} or paddingVertical={spacing.md} to the Pressable style to meet the 44px minimum touch target. Alternatively, increase hitSlop to 18+ to reach 44px.
  verify: REAL (VERDICT=REAL inLane=yes  The 'View plans' button at E:/2ndB/src/app/secondb.tsx:286-297 has no minHeight or paddingVertical on the Pressable itself—only marginTop:4 and hitSlop:4. With variant="caption" (14px font), the touch target is approximately 16.8-19.6px (text height) + 8px (hitSlop expansion)
- [P0][accessibility] Clear chat button touch target below 44px minimum
  file: E:/2ndB/src/app/secondb.tsx:300-311
  evidence: The 'Clear chat' Pressable button has the same touch target issue: hitSlop={4}, no paddingVertical, Text variant='caption' (14px). Calculated touch target is approximately 22px, well below the 44px minimum.
  fix: Add minHeight={44} or paddingVertical={spacing.md} to the Pressable style. This affects the usage panel CTA that directs users to /plans when the daily limit is reached, a critical accessibility moment.
  verify: REAL (VERDICT=REAL inLane=yes  The "Clear chat" Pressable at secondb.tsx:300-311 has hitSlop={4} with no padding and Text variant="caption" (14px), yielding a ~22px touch target. Adding minHeight={44} or paddingVertical to the Pressable style remedies it without requiring approvals.)
- [P1][accessibility] Plan tier cards lack accessibilityRole despite having labels
  file: E:/2ndB/src/app/plans.tsx:50-84
  evidence: The tier cards (free/plus/pro) have accessibilityLabel on the View container (line 56: `accessibilityLabel={`${t(`tiers.${key}.name`)} ${t(`tiers.${key}.price`)}`}`) but no accessibilityRole. The cards are not interactive (no onPress), so screen readers may incorrectly suggest they are buttons or interactive regions.
  fix: Either: (1) remove the accessibilityLabel if cards are purely visual containers, OR (2) add accessibilityRole='text' or accessibilityRole='region' to clarify they are display elements, not interactive controls.
  verify: REAL (VERDICT=REAL inLane=yes E:/2ndB/src/app/plans.tsx:53-56 — The tier card View has `accessibilityLabel` but no `accessibilityRole`, causing potential screen reader misinterpretation. Add `accessibilityRole="group"` or `accessibilityRole="region"` to clarify non-interactive intent.)
- [P1][accessibility] Current plan badge state not exposed to accessibility tree
  file: E:/2ndB/src/app/plans.tsx:62-66
  evidence: The 'current' badge (line 62-66) indicating which tier the user is on is rendered as visual-only text with no accessibility semantics. Screen reader users won't know that one card represents their current plan. The parent card at line 53 should expose this state.
  fix: Add accessibilityState={{checked: isCurrent}} to the card View (line 53), or add an accessibilityLabel specifically for the badge like `{isCurrent ? '(Current plan)' : ''}` and prepend it to the card's label. This follows ARIA patterns for indicating selected/checked state.
  verify: REAL (VERDICT=REAL inLane=yes  The accessibilityLabel on line 56 does not include the `isCurrent` state. Screen reader users will hear "Plus $9.99/month" but not know this is their current plan. The badge text at lines 62–66 has no accessibility role/state to expose it to the accessibility tree. Fix: upda)
- [P2][accessibility] Back button touch target may be below 44px minimum
  file: E:/2ndB/src/app/plans.tsx:100-108
  evidence: The back button has hitSlop={6} (12px total extra) and padding={spacing.sm} (8px), with Text variant='caption' (14px font). Calculated minimum touch target is 30-38px depending on line height, possibly below the 44px guideline. The inline style shows hitSlop but no explicit minHeight.
  fix: Add minHeight={44} to the Pressable style to guarantee accessibility compliance, or increase hitSlop to {15}+ to compensate.
  verify: REAL (Based on my analysis of the code:  **Calculation:**)
- [P2][accessibility] SceneHero swipeable stage lacks accessibility context for gesture support
  file: E:/2ndB/src/components/premium/SceneHero.tsx:195
  evidence: The stage View with swipe handlers (line 195: `<View style={styles.stage} {...(hasSwipe ? swipeResponder.panHandlers : {})}>`) has no accessibilityRole or accessibilityHint to indicate to screen reader users that the area supports swipe gestures. Users with accessibility needs won't discover this interaction pattern.
  fix: When hasSwipe is true, add accessibilityRole='button' and accessibilityHint={locale === 'ko' ? '왼쪽 또는 오른쪽으로 밀어서 전환합니다' : 'Swipe left or right to navigate'} to the stage View. This informs screen reader users of the gesture support.
  verify: REAL (VERDICT=REAL inLane=yes  E:/2ndB/src/components/premium/SceneHero.tsx:195 has no `accessibilityRole`, `accessibilityHint`, or `accessible` prop on the stage View. When `hasSwipe` is true (line 103), the swipeResponder.panHandlers are applied (line 195) but screen reader users receive no indication o)
- [P1][error-handling] Unguarded async/await in wiki.tsx handleRefresh leaves spinner spinning on error
  file: E:/2ndB/src/app/wiki.tsx:261-266
  evidence: The handleRefresh function calls `await load(userId, activeTags)` without try-catch wrapping. If load() throws an error, setRefreshing(false) on line 265 will never execute, leaving the refresh spinner in a permanent loading state. The error is silently swallowed with no user feedback.
  fix: Wrap the load call in try-catch: `try { await load(userId, activeTags); } catch (e) { console.warn(...); } finally { setRefreshing(false); }` so the spinner stops regardless of success/failure.
  verify: REAL (VERDICT=REAL inLane=yes  The handleRefresh function at E:/2ndB/src/app/wiki.tsx:261-266 lacks error handling. If load() throws (e.g., from listWikiPages), setRefreshing(false) on line 265 never executes, leaving the spinner spinning. Contrast with confirmDeletePage (line 289) and handleRunPhase1OnPa)
- [P1][error-handling] Unchecked type cast in chat/usage.ts bumpChatUsageIfUnderCap assumes RPC returns number
  file: E:/2ndB/src/lib/chat/usage.ts:71
  evidence: Line 71 returns `data as number` after an RPC call with no validation. If the Supabase RPC returns null, undefined, or a malformed value, the cast to `number` succeeds at compile time but data is not actually a number at runtime. This breaks the sendChatMessage flow silently and could corrupt chat usage tracking.
  fix: Replace `return data as number;` with `return typeof data === 'number' ? data : 0;` or add a runtime assertion: `if (typeof data !== 'number') throw new Error('invalid_response');`
  verify: REAL (Based on my analysis of the code:  **VERDICT=REAL inLane=yes**)
- [P2][error-handling] Multiple unsafe as-unknown-as type escapes in gemini.ts bypass type safety
  file: E:/2ndB/src/lib/llm/gemini.ts:236,269,396,424
  evidence: Lines 236, 269, 396, 424 use `as unknown as T` to force-cast the LLM response text. If the response format is incorrect or the mock response doesn't match the expected type, TypeScript's type system is bypassed and callers receive incorrectly typed data. Example: line 269 casts mock text as `unknown as T` which could be string when callers expect a structured object.
  fix: Remove the double-cast and use proper type guards: validate response shape before returning, or use `const result = data as GeminiResult<T>; if (!isValidResult(result)) throw ...;` to catch malformed responses.
  verify: REAL (VERDICT=REAL inLane=yes  The code has unsafe double-cast `as unknown as T` patterns on lines 236, 269, 396, and 424 in E:/2ndB/src/lib/llm/gemini.ts. Most critical is line 269 (mock path), where a hardcoded string is force-cast to the caller's requested type T without any runtime validation. When ca)
- [P2][error-handling] Swallowed promise rejection in capture.tsx silent error on streak load
  file: E:/2ndB/src/app/capture.tsx:370-378
  evidence: Lines 370-378 call `Promise.all([...])` with `.catch(() => {})` - a silent swallowing of errors. If listRecentRecords or countRecordsByKind fail, the streak and journal-usage-count state remain stale/outdated without any user notification or retry mechanism. The next journal entry won't have correct metadata.
  fix: Replace empty catch with: `.catch((e) => { console.warn('[capture] streak refresh failed', e); setRecentDates([]); setJournalCount(0); })` so stale state is reset instead of persisted.
  verify: REAL (**VERDICT=REAL inLane=yes**  The empty catch handler at capture.tsx:378 silently swallows `listRecentRecords` and `countRecordsByKind` failures after a successful journal save, leaving streak/count state stale. Compare with lines 205-206: the identical Promise.all call in the initial useEffect has p)
- [P2][brand-naming] Stale documentation referencing retired 'Jarvis' feature
  file: E:/2ndB/src/components/graph/NavGraph.tsx:6
  evidence: Header comment says "Tier 1 (centre, 1 node)     2nd Brain — user profile. Bubble has\n                               a Jarvis quick-launch icon." But line 220 notes bubbleAction was removed in 2026-05-28 user directive and the chat entry moved to a floating button.
  fix: Update header comment to reflect actual current design: "Tier 1 (centre, 1 node)     Soul Core — user profile. Floating chat button in bottom-right." Remove reference to "Jarvis quick-launch icon."
  verify: REAL (VERDICT=REAL inLane=yes  The header comment at lines 5-6 still references "a Jarvis quick-launch icon" but the CENTER_NODE definition at lines 220-222 explicitly notes "bubbleAction removed (2026-05-28 user directive): the chat entry moved out of the bubble to a floating button." Additionally, lines)
- [P2][brand-naming] Stale documentation describing removed bubbleAction configuration
  file: E:/2ndB/src/components/graph/NavGraph.tsx:27-28
  evidence: Comment block documents "Core tier-1 node (bubbleAction: 'jarvis'): bubble shows a 💬 icon that opens /secondb. Primary action: open /persona." But this feature was removed per line 220's user directive comment. bubbleAction is no longer used on CENTER_NODE.
  fix: Remove or update the documentation block (lines 22-28) to reflect the current design where CENTER_NODE has no bubbleAction and chat is handled via floating FAB button at screen bottom-right.
  verify: REAL (VERDICT=REAL inLane=yes  **Reason:** The comment block at lines 27-28 documents "Core tier-1 node (bubbleAction: 'jarvis')" with a 💬 icon opening /secondb, but the CENTER_NODE object at line 216 explicitly states "bubbleAction removed (2026-05-28 user directive)" and the node has no bubbleAction pr)
- [P1][brand-naming] Type definition includes unused 'jarvis' value
  file: E:/2ndB/src/components/graph/NavGraph.tsx:151
  evidence: NavNode interface defines bubbleAction?: "jarvis" | "upload", but "jarvis" is never used anywhere (search confirms no references outside this file). Only "upload" is actually assigned to any node. This dead code supports a removed feature.
  fix: Remove "jarvis" from the type union: change `bubbleAction?: "jarvis" | "upload";` to `bubbleAction?: "upload";` to reflect the actual feature set after bubbleAction was removed from CENTER_NODE.
  verify: REAL (VERDICT=REAL inLane=yes  **Reason:** Line 151 defines `bubbleAction?: "jarvis" | "upload";` but "jarvis" is never assigned (only "knowledge" node has `bubbleAction: "upload"` at line 185) and never referenced in logic. Lines 220-222 confirm bubbleAction was removed from CENTER_NODE on 2026-05-28, le)
- [P2][brand-naming] Stale motion documentation referencing retired character Vela
  file: E:/2ndB/src/lib/motion/signature.ts:6
  evidence: Header documentation says "3) 공상 / Imagine     \"벨라 핑크 신호\"  — a soft pink presence pulse" but Vela is retired. Line 73 shows IMAGINE_MOTION.accent uses "secondb", not "vela". Code comment on line 73 confirms: "Vela retired; legacy imagine motion is dormant (공상 → Divergent)"
  fix: Update line 6 comment to: "3) 공상 / Imagine     \"세컨비 신호\"  — a soft presence pulse (legacy motion, dormant since 공상 → Divergent mode)" to accurately reflect the current implementation.
  verify: REAL (VERDICT=REAL inLane=yes  **Reason:** Line 6 documentation claims `"벨라 핑크 신호"` (Vela Pink Signal), but line 73 confirms accent is `"secondb"` with explicit comment `"Vela retired; legacy imagine motion is dormant"`. Header doc is stale and contradicts the actual implementation. Fix requires updating )
- [P1][consistency-guard] Loading State Inconsistency: Raw ActivityIndicator Instead of PremiumLoadingState
  file: E:/2ndB/src/app/research.tsx:112-115
  evidence: research.tsx wraps raw ActivityIndicator (line 114) in a View with styles.center for data loading. However, the same screen uses PremiumLoadingState for auth loading (line 72). This pattern repeats across records.tsx, insights.tsx, inbox.tsx, interview.tsx where raw ActivityIndicator is used for data loading while PremiumLoadingState is used for auth loading. PremiumLoadingState provides a consistent premium design wrapper with proper spacing and layout (StateShell with padding, gap, centered alignment), while raw ActivityIndicator lacks this visual hierarchy.
  fix: Replace raw ActivityIndicator usage in data loading states with PremiumLoadingState component. For research.tsx line 112-115, change to: `{loading ? (<PremiumAppShell><View style={styles.center}><PremiumLoadingState message={t('loading')} /></View></PremiumAppShell>) : ...}`. Apply the same pattern to records.tsx lines 159-166 and 242-248, insights.tsx lines 88-95, and inbox.tsx lines 632-635.
  verify: REAL (VERDICT=REAL inLane=yes research.tsx:114 uses raw ActivityIndicator for data loading while line 72 uses PremiumLoadingState for auth; same inconsistency in insights.tsx:92 vs 79 and inbox.tsx:634 vs 587. PremiumLoadingState wraps ActivityIndicator in StateShell with padding, centered alignment, and )
- [P1][consistency-guard] Modal Style Divergence from Premium Design System
  file: E:/2ndB/src/app/secondb.tsx:501-545
  evidence: secondb.tsx uses raw React Native Modal (lines 501-545) with custom styles that diverge from the premium design system. The custom modalBackdrop (line 655) and modalCard (line 662) styles use semantic.surface and semantic.border (dynamic colors) instead of the premium glassy rgba colors. Specifically, modalCard is missing: (1) elevation: 24 for the glassy depth effect, (2) borderColor 'rgba(167,139,250,0.42)' for the premium glow, (3) backgroundColor 'rgba(7,10,24,0.98)' for the dark glassy look. Compare to PremiumModal in surfaces.tsx (lines 181-192) which has proper glass panel styling with borderColor rgba(167,139,250,0.42) and elevation:24. Same issue in core-brain.tsx line 323 which uses raw Modal.
  fix: Replace raw Modal with PremiumModal component from @/components/premium. For secondb.tsx: change `<Modal visible={introOpen} ...>` (lines 501-545) to `<PremiumModal visible={introOpen} onClose={() => setIntroOpen(false)} accessibilityLabel={...}>` and move the inner content into the children prop. Remove custom modal styles from StyleSheet. Apply same fix to core-brain.tsx line 323 for the evidence drawer modal.
  verify: REAL (VERDICT=REAL inLane=yes  The modalCard in secondb.tsx:501-545 uses semantic.surface and semantic.border (lines 663-664) instead of the glassy rgba colors defined in PremiumModal (feedback.tsx:187-188). The secondb.tsx modalCard also lacks elevation:24. PremiumModal is exported but not imported in se)
- [P2][consistency-guard] Inconsistent Loading State Wrapping in Inbox Screen
  file: E:/2ndB/src/app/inbox.tsx:312-318
  evidence: inbox.tsx has three different loading state renderings: (1) auth loading uses PremiumLoadingState with proper StateShell styling (line 587), (2) row-level body loading uses raw ActivityIndicator (line 313) with no container styling, (3) list-level loading uses raw ActivityIndicator in a View with styles.center (lines 632-635). This creates visual inconsistency where individual row spinners appear different from full-screen loading states. The row-level spinner on line 313 is especially unpolished as it has no surrounding padding or container styling.
  fix: For row-level loading (line 313), wrap the ActivityIndicator consistently: replace `{body === undefined ? (<ActivityIndicator color={semantic.brand} />) : ...}` with a smaller, styled loading indicator component or use PremiumLoadingState with size adjustments. Alternatively, create a consistent inline loader component (similar to InlineLoader in E:/2ndB/src/components/ui/InlineLoader.tsx) for row-level states.
  verify: REAL (VERDICT=REAL inLane=yes  Row-level body loading at line 313 is a bare `<ActivityIndicator color={semantic.brand} />` with zero container styling, while list-level loading at line 632-635 wraps it in `<View style={styles.center}>` with paddingVertical+alignItems, and auth loading at line 587 uses ful)
- [P2][consistency-guard] Cross-Screen Loading Pattern: Auth vs Data Loading States
  file: E:/2ndB/src/app/insights.tsx:75-95
  evidence: insights.tsx shows the pattern repeated across premium screens: authLoading shows full-screen PremiumLoadingState (line 79) while data loading shows raw ActivityIndicator in View/styles.center (line 92). This two-tier inconsistency (PremiumLoadingState for auth, raw ActivityIndicator for data) affects: records.tsx, research.tsx, insights.tsx, inbox.tsx. The auth loading pattern uses proper premium styling while data loading falls back to raw components. This visual inconsistency is especially visible when screens transition between these states.
  fix: Standardize all full-screen loading states to use PremiumLoadingState. For data loading in insights.tsx lines 88-95, use PremiumLoadingState with an appropriate message (t('loading')) instead of raw ActivityIndicator. Apply to all screens showing this pattern.
  verify: REAL (VERDICT=REAL inLane=yes  The inconsistency is confirmed at E:/2ndB/src/app/insights.tsx:75-95. Lines 75-82 return `PremiumLoadingState` for authLoading, while lines 88-95 return raw `ActivityIndicator` for data loading. Same pattern verified in research.tsx (lines 68-75 vs 112-115) and inbox.tsx (li)
- [P2][consistency-guard] Hardcoded Eyebrow Props Ignored in SceneHero Components
  file: E:/2ndB/src/app/plans.tsx:40-47
  evidence: SceneHero component (src/components/premium/SceneHero.tsx lines 76-78) explicitly ignores eyebrow and subtitle props with `void eyebrow; void subtitle;` per 2026-06-02 directive. However, many screens still pass eyebrow to SceneHero: plans.tsx line 41, account.tsx line 182, capture.tsx line 542, and others. While this doesn't break visually (the props are just ignored), it creates dead code and confusion. Callers believe they are customizing the hero header when they aren't. The eyebrow parameter should either be removed from the API or documented as deprecated.
  fix: Remove eyebrow and subtitle parameters from SceneHero prop interface to match the implementation. Update all callers (plans.tsx, account.tsx, capture.tsx, etc.) to remove these unused props. Alternatively, if keeping them for API compatibility, add a TypeScript comment documenting they are deprecated and ignored.
  verify: REAL (VERDICT=REAL inLane=yes  The SceneHero component at E:/2ndB/src/components/premium/SceneHero.tsx:77-78 explicitly ignores eyebrow and subtitle props with `void eyebrow; void subtitle;` per the 2026-06-02 directive (comment at line 75-76), yet 26 screens across the codebase actively pass these props )
- [P3][consistency-guard] Inconsistent Modal Styling: Secondary Buttons in secondb.tsx
  file: E:/2ndB/src/app/secondb.tsx:682-683
  evidence: secondb.tsx defines custom modalBtn styles where modalBtnSecondary has `backgroundColor: 'transparent'` (line 683) with no border. Other premium surfaces use PremiumButton with variant='secondary' which has proper styling: `borderColor: 'rgba(141,152,184,0.56)'`, `backgroundColor: 'rgba(141,152,184,0.08)'`. The raw transparent button in secondb modal (line 529) lacks visual affordance compared to premium secondary buttons elsewhere. This is a subtle consistency issue in button styling within modals.
  fix: When migrating secondb modal to PremiumModal, use PremiumButton components with variant='secondary' and variant='primary' instead of custom styled Pressable buttons. This ensures modal buttons match the rest of the app's button system.
  verify: REAL (VERDICT=REAL inLane=yes  E:/2ndB/src/app/secondb.tsx:683 defines `modalBtnSecondary: { backgroundColor: "transparent" }` (no border), applied to intro modal dismiss button at line 524. This lacks the visual affordance of PremiumButton variant='secondary' which has `borderColor: "rgba(141,152,184,0.5)

## UNCLEAR (verify inconclusive — manual check, NOT auto-dropped) — 0
(none)

## OUT-OF-LANE (Simon/legal/PG/safety or other-AI lane) — 1
- [P2][ux-flow-gaps] "Notify me" button on /plans screen has no backend integration
  file: E:/2ndB/src/app/plans.tsx:94
  evidence: Line 94: `onPress={() => setNotified(true)}` only changes local component state. The `notified` variable is useState (line 35), so it resets to false on page reload. No API call is made, no email/push notification preference is persisted. User sees "Thanks. We will reach out at launch" (notified.json) but the app never records this preference. When a free user hits the daily AI limit and is directed to /plans (secondb.tsx:287-298), they think clicking "Notify me" means they'll get alerted about Plus launch, but nothing is actually recorded.
  fix: Implement backend notification preference storage: (1) Add API endpoint to persist notification preference to DB, (2) Call API in the onPress handler with proper error handling, (3) Show toast confirmation, (4) Optionally disable button after clicking to prevent duplicates.
  verify: n/a 

## finder null dims (schema fail, not clean): none
