# 2nd-B 게임보이 UI 리스타일 O-11 리뷰 — 전략 + 접근성 크로스컷 (Grok)

**작성**: 2026-06-08  
**레인**: 전략 + 접근성 (O-11)  
**대상**: 2nd-B (개인 두번째 뇌 AI, Gemini XPRIZE Education & Human Potential 출품작)  
**배경**: 최근 전체 UI를 "Deep Space Game Boy" (gb-screen #070A18 배경 + 픽셀 GB 레이어, Galmuri11 한글 + Press Start 2P 영문, 직각 2px 테두리 · 3px offset 픽셀 shadow · dash 엣지)로 전환. gb 팔레트: screen #070A18 / ink #E8ECF8 / accent #4CC9F0 / power #72F2C7 / amber #FFD166.  
**참조 소스**: E:/2ndB/src/lib/theme/gameboy-tokens.ts, tokens.ts (cosmic), typography.ts, components/premium/surfaces.tsx + feedback.tsx, app/onboarding.tsx, tailwind.config, _layout.tsx, capture.tsx (dashed zones), DESIGN.md (O-9 Phase 1 기술), VISION.md.

---

## 1. 게임보이 스타일 × 제품 비전 + XPRIZE 심사 인상 정합성 (리스크/기회)

**비전 핵심** (VISION.md + DESIGN.md):  
"AI 시대, 가장 가치있는 것은 나 자신입니다." / "An AI that listens before it talks."  
세 축: 알아가기(자기 데이터 축적) · 개인 비서(RAG) · 공상→구체화.  
**NOT** mental-health/wellness/coach 앱. "자기 이해 / 성장 / reflection" 중심. XPRIZE Education & Human Potential 트랙 — 인간 잠재력, 데이터 주권, serious self-modeling.

**GB 미감 현재 적용 현황**:
- premium/surfaces.tsx, tab-bar, feedback.tsx(StateShell/모달/시트/토스트/safety) 전면 적용 (radius:0, borderWidth:2 gameboy.border, pixelShadow 3px hard offset, screen/ink/accent/power 색 매핑).
- Text.tsx (display/heading/caption): fontFamilies.pixelKo (Galmuri11).
- Onboarding: PremiumAppShell (background + StarNoise + glow) + GB 버튼/텍스트 + pixel heading + custom pixel art (IslandArt/SecondBSprite 등).
- Empty/Error/Loading/Safety: orb(64px square, 2px border + shadow) + StateShell (GB framed).

**정합성 평가**:

**기회 (강점)**:
- "포켓 콘솔" 메타포: "너의 두번째 뇌를 주머니에 넣고 다니는 기기" — portable RAG, sovereignty, "carry your self-model" 비전과 물리적으로 잘 맞음.
- 픽셀 + 하드 엣지 + 로우파이 = "정직한 기록" 느낌. polished wellness 앱 슬롭과 차별화. XPRIZE 데모에서 "기억에 남는" 시각적 hook.
- 고대비 + 픽셀 라벨은 "power user / builder / deep thinker" 타겟(20-40대)에게 "craft tool" 포지셔닝. scanline/하드웨어 레이어는 "저녁에 혼자 들여다보는" ambient journaling 분위기와 잘 어울림.
- village 픽셀 스프라이트(SecondB/Archon 등)와 GB 크롬의 결합은 세계관(v-final 5-tier Graph Village)과 일체감 있음.

**리스크 (약점 / 충돌)**:
- **"Toy / Game" 인상 vs "serious self-asset tool"**: XPRIZE Education & Human Potential 심사위원(교육/인간잠재력 전문가)에게 "게임보이 UI"가 가벼워 보일 가능성. "듣기 먼저, 자기성찰"은 조용하고 contemplative — GB는 80s handheld의 강한 시각적 주장(베젤, 섀도, 픽셀 폰트)이 "playful/gamified"으로 읽힐 수 있음.
- 온보딩(첫인상)에서 특히 위험: 3스텝 아트 + GB shell + pixel title 이 "게임 튜토리얼"으로 착각될 소지. "하루 생각을 짧게 남기세요" 같은 copy는 GB와 잘 어울리지만, XPRIZE 데모 랜딩/웹에서 "이게 교육/인간잠재력 혁신인가?"라는 첫인상 리스크.
- 긴 호흡 body/journal text는 readable(Pretendard)로 분리했으나, heading/caption/CTA가 pixel (Galmuri/Press)이라 "이 앱은 게임인가?"라는 미세한 신호가 계속 발생.
- "자기 데이터 축적"의 무게감(quant + audit + RAG)이 픽셀 레트로와 충돌할 때 "nostalgia toy"로 폄하될 수 있음.

**전략적 판단**:  
GB는 **브랜드 차별화**로는 성공적일 가능성이 높지만, **XPRIZE 심사 + "listen first" 핵심 가치 전달**에서는 양날의 검. 온보딩/랜딩/empty-error에서 framing을 완화하거나 "이 콘솔은 당신의 생각을 기록하는 도구입니다" 식의 명시적 anchoring copy + 마이크로인터랙션이 필요. Phase 후반에 "GB on / soft / off" 토글 또는 per-surface 예외 정책을 명문화해야 함.

---

## 2. WCAG AA 대조비 재산정

**측정 방법**: WCAG 2.2 luminance 공식 (sRGB → linear → relative luminance)으로 (L1+0.05)/(L2+0.05) 계산. node 검증 완료.

**gb-screen (#070A18) 배경 기준**:

| Foreground | Contrast | AA Normal (4.5:1) | AA Large/UI (3:1) | AAA (7:1) | 판정 |
|------------|----------|-------------------|-------------------|-----------|------|
| gb-ink (#E8ECF8) | **16.69:1** | PASS | PASS | PASS | 우수 |
| gb-accent (#4CC9F0) | **10.25:1** | PASS | PASS | PASS | 우수 (text/UI 모두) |
| gb-power (#72F2C7) | **14.30:1** | PASS | PASS | PASS | 우수 |
| gb-amber (#FFD166) | **13.67:1** | PASS | PASS | PASS | 우수 |

**결론 (접근성)**:
- gb-screen + gb-ink 텍스트: **매우 우수** (16.69:1). 일반 본문/헤딩 모두 AAA 통과.
- gb-accent 텍스트/UI (버튼 라벨, 포커스 링, 탭 active, input caret 등): **10.25:1으로 4.5:1 / 3:1 모두 여유롭게 통과**.
- Non-text UI (2px border, focus ring, icon stroke): 3:1 기준 충분.
- **P0 없음**. 현재 screen bg 중심으로는 접근성 차단 요소 없음.

**주의사항 (추가 점검 필요)**:
- surface / surfaceAlt / panel (약간 밝은 dark wash) 위에서 gb-accent / gb-power 를 텍스트로 쓸 때 contrast 하락 가능. (semantic.surface는 rgba wash라 정확 재측정 권장)
- lightCosmic (secondary surfaces: settings/sign-in) 에서도 동일 팔레트 alias 사용 시 재확인.
- Dynamic type + pixel font (Galmuri/Press) 의 실제 렌더링에서 stroke thickness가 얇아 보일 수 있음 → 44pt touch target은 유지되지만, small caption (xs) 에서 가독성 + contrast 동시 점검.

---

## 3. Galmuri11 + Press Start 2P 폰트 번들 사이즈 영향 · 로딩전략

**실측 (E:/2ndB node_modules + assets, 2026-06-08)**:

| Font | Size | 비고 |
|------|------|------|
| Galmuri11.ttf (galmuri/dist) | **5,250 KB (5.25 MB)** | 한글 픽셀 전체 자형 포함으로 추정. 비정상적으로 큼 |
| PressStart2P_400Regular.ttf | 113 KB | Google Fonts Expo 패키지 |
| NeoDunggeunmo-Regular.ttf (local) | 650 KB | 기존 pixel fallback |
| NeoDunggeunmoCode-Regular.ttf (local) | 654 KB | 고정폭 |

**총 폰트 페이로드**: ~6.7 MB (4종 동시). 네이티브 앱 바이너리 + web 초기 다운로드에 직접 영향.

**현재 로딩 전략** (src/app/_layout.tsx:30):
```ts
const [fontsLoaded, fontError] = useFonts(fontAssets); // Galmuri + Press + Neo 2종
if (!fontsLoaded && !fontError) return <InlineLoader />;
...
<SplashScreen ... />
```
- 네이티브: cold launch 시 splash block → 폰트 로드 후 render. FOUT 방지 좋음.
- 웹 (Vercel static / npm run web): 동일 block. 첫 페인트 지연 + TTI 악영향. Galmuri 5MB는 특히 web에서 치명적.

**평가**:
- **P1 (성능/출시 리스크)**: 5.25MB Galmuri는 과도. XPRIZE web demo (judge가 가장 많이 보는 surface)에서 초기 로드 지연 + 데이터 사용량 문제.
- pixel font는 라벨/제목/CTA에는 적합하나, body는 readable(Pretendard)으로 이미 분리 — 전략은 맞지만 payload가 문제.
- fallback (NeoDunggeunmo) 이 이미 존재하는데 Galmuri/Press를 추가로 2개나 로드하는 중복 비용.

**권고 (우선순위)**:
1. Galmuri11 subset 생성 (실제 사용 glyph: 제목/라벨/버튼/탭/eyebrow + 기본 ASCII/한글 자주 쓰는 것만). glyphhanger 또는 fonttools로 200-400KB 수준으로 축소.
2. web 전용: `@font-face` + `font-display: swap` + preload `<link rel="preload" as="font">` for pixel titles. body는 system/Pretendard 먼저 paint.
3. 로드 분리: pixelKo/En (UI chrome)은 critical, readable (journal/chat body)는 deferred.
4. CI gate: "font assets total < X KB" 또는 lighthouse font budget 추가.
5. 확인: `expo export` 또는 EAS build 후 실제 번들 크기 (Android .apk assets, web _expo/static) 재측정.

---

## 4. 게임보이 미적용 가능성 높은 화면 점검 권고

**현재 상태**: premium layer (surfaces + feedback + tab-bar + AppShell background) 가 대부분의 화면을 감싸므로 "GB off" 가 거의 없음. 대신 "이 화면은 GB framing 이 메시지와 충돌할 수 있다"는 관점에서 점검.

| 화면 | 현재 GB 적용 | 문제 소지 | 권고 |
|------|--------------|-----------|------|
| **온보딩** (src/app/onboarding.tsx) | PremiumAppShell + GB topBar/progress + pixel heading + GB primary/secondary 버튼 + OnboardingPremiumArt (Island/Shard/Sprite) | 첫인상 + XPRIZE 데모. "게임 튜토리얼" 인상 강할 수 있음. 아트는 village와 조화되지만 strict 2px shadow + 0 radius frame 이 "듣기 먼저" contemplative 톤과 상충 | P1. shell 유지하되 내부 body에 extra vertical padding / art max-width + "welcome mode" (shadow off 또는 borderColor 더 dim) 옵션. "이 콘솔은 당신의 생각을 담는 도구입니다" anchoring copy 추가. |
| **빈 상태** (PremiumEmptyState in feedback.tsx:134) | StateShell + 64px square orb (soulViolet border + pixelShadow) + pixel heading + readable body | centered, 글자 적음. orb가 "device lamp" 느낌 강해서 "아직 아무것도 없어요" 메시지가 가벼워 보일 수 있음 | P2. orb 크기 확대 or glyph-only (no heavy shadow), 또는 empty 전용 "soft frame" (borderWidth 1, padding xl). |
| **에러 상태** (PremiumErrorState:138) | 동일 StateShell + guardRose orb + secondary retry (GB) | retry 버튼은 GB가 적합. 하지만 실패 메시지가 "hardware error"처럼 읽힐 위험 | P2. error 전용 glyph (더 크고 warning 느낌) + message emphasis. |
| **로딩** (PremiumLoadingState) | ActivityIndicator (mint) + StateShell | indicator는 native spinner, GB pixel language와 불일치 | P2. pixel dot matrix 로더 또는 8px grid 기반 custom으로 교체. |
| **SafetyNoticePanel** | 2px border (rose) + wash bg + dot, partial GB | 시스템 경고라 GB chrome 과도하면 불안 증폭 가능 | P2. border 유지하되 shadow off, padding 조정. |
| **+not-found / 기타 에러** | BackArrow + shell | — | P2. 최소 GB chrome + 친절한 pixel copy. |
| **Capture drop zones / Wiki template add** (capture.tsx, TemplateEditor.tsx) | 1px dashed (semantic.border or brand) | GB 전역 2px solid 철학과 명백 충돌. "dashed" 는 wireframe/ drop target 의도이나 pixel GB에서는 이질 | P1. GB 언어로 통일 (2px + 4px gap dot pattern, 또는 borderImage pixel, 또는 solid + "+" icon). |

**전반 권고**: 
- DESIGN.md "O-9 Phase 1: tokens + fonts + aliases only. Do not restyle components until later phases" 문구가 현재 코드(surfaces.tsx 전면 GB 적용)와 불일치. 문서 갱신 또는 phase 진행 상황을 명확히.
- "GB-exempt surfaces" 또는 `framed` prop 을 premium primitives에 추가 (onboarding/empty/error/not-found 용).
- 페르소나 시뮬 (고령/저 tech-literacy + KR judge): pixel font + hard shadow + dense GB chrome 이 "귀여운 게임"으로 읽히거나, 반대로 "복잡해 보인다"는 피드백 가능성 있음.

---

## 5. AI slop 최종 잔존 패턴

**긍정**: O-9 restyle (premium layer + gameboy-tokens) 이 slop 상당 부분 제거.
- 모든 주요 primitive: radius=0, border=2px hard, shadow=3px offset no-blur, 색은 gameboy.* alias만 사용 (no hex in components).
- pixelKo/En 일관 적용 (제목/라벨/CTA).
- no pill, no gradient, no em-dash, no bounce (except sanctioned "뽁") — 기존 DESIGN.md 규칙 + GB가 서로 강화.

**잔존 / 신규 slop 위험**:
- **dashed 1px** (capture modeMoreTab, wiki TemplateEditor add zone): 가장 명백한 비-GB 잔재. "drop target" 의미는 유지하되 visual language 통일 필요.
- **ActivityIndicator + native spinners**: 로딩 상태에서 "현대 앱" 느낌이 GB pixel을 깨뜨림.
- **그래프 / SVG 레이어** (NavGraph, CharacterPathLayer 등): 일부 pixel font 사용 중이지만 선/노드 anti-aliasing, glow, 곡선이 "픽셀 하드웨어"와 충돌. 1px crisp grid 스냅 확인 필요.
- **아트 스프라이트** (IslandArt, SecondBSprite, WorkerSprite): village 세계관과 맞지만, GB shell frame 과 크기/간격이 미세하게 어긋날 때 "장식 과다"로 보일 수 있음.
- **웹 특화** (hover, focus ring, selection): RNW 기본이 GB token을 완전히 따르지 않으면 "web slop" 발생. focus-visible accent + hard shadow 강제.
- **Onboarding topBar / progress dots**: caption muted + dot (small circle) — GB 2px/0-radius와 미스매치 가능성.
- **주석/헤더 outdated**: feedback.tsx 상단 "Glassy, glowing..." 설명이 실제 GB hard style과 불일치 (slop 방지 관점에서 문서도 pixel 언어로).
- **DESIGN.md vs 현실 불일치**: "do not restyle yet" 문구가 살아있어 향후 PR에서 혼란 유발.

**slop 잔존도**: 이전 대비 크게 낮음. GB 철학(직각·하드섀도·픽셀·dash 최소)이 강력한 가드레일. 남은 것은 "일관성 세부"와 "예외 화면(온보딩/상태)".

---

## P0 / P1 / P2 요약

**P0 (접근성 차단 — 즉시 수정 필요)**: **없음**.  
gb-screen + gb-ink/accent/power/amber 모든 쌍이 4.5:1 / 3:1 여유롭게 통과 (16.69 / 10.25 등). 추가 surface 재측정만 권고.

**P1 (전략·브랜드·성능·일관성 — 이번 사이클 내 처리)**:
1. **Galmuri 5.25 MB** — 앱 크기 + web 로드 지연. Subset + 로딩 전략 재설계 필수. XPRIZE 데모 직접 영향.
2. **온보딩 GB 전체 적용** — 제품 첫인상과 XPRIZE "Education & Human Potential" + "listen first" 가치 간 정합성 리스크. framing 완화 or anchoring copy 필수.
3. **dashed borders (capture, wiki)** — GB 2px solid 언어와 충돌. pixel 대체 패턴으로 통일.

**P2 (품질·엣지·장기 개선)**:
- Empty / Error / Loading / Safety / not-found 상태의 glyph + shell 조합 (orb 크기/emphasis, loading pixel화, padding).
- DESIGN.md O-9 phase 문서 현실 동기화.
- 그래프/SVG + 아트와 GB 크롬 간 pixel grid 정합성 audit.
- 웹 focus/hover + perf 예산 (LCP/TTI/app size) 실제 측정 + gate.
- lightCosmic secondary surface 에서의 accent contrast 재확인.

---

## 즉시 권고 액션 (우선순위 순)

1. **폰트**: galmuri/dist/Galmuri11.ttf 를 실제 사용 자형만 남긴 subset으로 교체 (목표 <400KB). typography.ts + fontAssets + web +html.tsx preload 전략 동시 수정. (P1)
2. **온보딩**: PremiumAppShell 유지 + 내부에 "onboarding-frame" 예외 (art breathing, progress dots GB화, skip affordance tone down). "이 픽셀 콘솔은 당신의 생각을 조용히 기록합니다" 식의 1-2줄 anchoring. (P1)
3. **Dashed → GB**: capture.tsx / TemplateEditor 의 dashed zone 을 2px + dot pattern 또는 GB icon으로 교체. (P1)
4. **States polish**: StateShell / orb 에 `variant="default" | "empty" | "error"` prop 추가 → empty 시 shadow/opacity 완화, error 시 emphasis up. (P2)
5. **문서**: DESIGN.md O-9 섹션에 "Phase 2: surfaces + states 적용 완료 (2026-06)" 업데이트 + "예외 화면 정책" 추가.
6. **측정**: web build 후 font payload + lighthouse, Android APK asset size 확인. CI에 "max font KB" gate 검토.
7. **추가 a11y**: accent text on surfaceAlt, small caption pixel font legibility (실기기 + VoiceOver/TalkBack), 44pt target은 이미 OK.

**XPRIZE 포지셔닝 제안**: GB를 "단순한 레트로"가 아니라 "your personal cartridge for self-knowledge"로 framing. 온보딩/랜딩에서 이 문장을 시각 + 카피로 반복하면 "toy" 리스크가 "memorable personal device" 기회로 전환됨.

---

**다음 리뷰어 참고**: 이 파일은 agents/grok/outbox/ 에 single-writer. Claude / Codex / Antigravity 가 읽고 후속 작업 시 참조. 실제 변경 전 `npm run verify` + web/Android 스크린샷 + contrast re-check 필수.

**저장 경로**: E:/Coding Infra/AI Infra/Communication/agents/grok/outbox/20260608-grok-o11-strategy-a11y.md (본 문서)

— Grok (strategy + a11y cross-cut), 2026-06-08 KST
