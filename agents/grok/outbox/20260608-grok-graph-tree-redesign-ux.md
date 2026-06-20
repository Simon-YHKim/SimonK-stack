# 2nd-B 메인 그래프 재설계 — UX/감성 방향 (Grok 독립 리포트)

**date:** 2026-06-08  
**from:** grok (to claude for synthesis)  
**context:** Simon "이미지 구조와 의도를 제대로 안 보고 조각만 적용했다" 지시에 따른 4 AI 공동 방향 수립. 나는 UX/감성 레인 전담. 두 reference 이미지를 직접 판독 + 현재 코드(NavGraph, world-layout, drilldown-nav, SoulcoreFinalArt, tokens, DESIGN.md) 대조.

---

## 1. 두 이미지 직접 판독 — 구조·의도 재기술

### REF1 (전체 성좌 / overview)
- **배경:** 극도로 깊은 네이비-잉크 (#070A18 계열). pure black 금지.
- **레이아웃:** 명백한 **하단-앵커 수직 성장 구조**. 
  - Soul Core (거대 시안 발광 테서랙트 큐브, 내부 연꽃/불꽃 코어)가 화면 하단 중앙에 뿌리처럼 고정. 가장 크고 가장 밝음.
  - 그 위로 5개의 Pattern Core (작은 테서랙트 큐브)가 **상단 방향으로 군집**:
    - 상단 중앙 부근: 틸/그린 (성장?)
    - 좌상: 화이트/실버
    - 우상: 퍼플
    - 좌하 (Soul 바로 위 좌): 핑크/로즈
    - 우하 (Soul 바로 위 우): 그린
  - Pattern Data: 파란 6각 **눈송이 크리스탈** 다수. 코어 주변과 위쪽 공간을 메우며 "가지"를 형성.
  - Pattern Link: 가늘고 발광하는 시안/민트 계열 신경망 선. 뿌리 근처일수록 밝고, 위로 갈수록 섬세.
- **헤더:** 좌측 "Y" 테서랙트 로고 + "그래프", 우측 "설정". 극도로 미니멀. 어떤 추가 버튼이나 크롬도 없음.
- **하단 2 인사이트 카드 (항상 존재):**
  1. 세컨비 (퍼플 로봇 아바타) — "최근 위즈덤 코어에 새로운 조각 추가" / "뮤즈코어 보강 필요해요!" + **Touch!**
  2. 위즈덤 코어 (큐브 아이콘) — 최근 추가된 "Lean Production" 관련 조각 서사 + **Touch!**
- **전체 인상:** "보석 상자 안에 들어 있는 살아있는 수정 정원". 조각이 아니라 **하나의 유기체**처럼 보임.

### REF2 (드릴다운 / focused core)
- 같은 언어, 같은 배경, 같은 아트 어휘.
- **그로스 코어** (녹색-시안 테서랙트, 내부 새싹/식물)가 하단-중앙에 위치. (overview에서 해당 코어가 있던 자리에 더 강조되어 자리 잡음)
- 그 코어의 "canopy"로 파란 눈송이들이 위쪽으로 가지치기.
- **하단 카드 2장:**
  1. 아콘 (블루 픽셀 로봇) — "이곳은 그로스 코어예요. 나의 커리어와 관련된 조각들이 모여 있어요." + **Touch!**
  2. MPAP 프로젝트 (작은 눈송이/큐브 아이콘) — 최근 추가된 조각에 대한 구체 서사 ("...프론트엔드 개발을 하면서 AI 활용 방법에 대해 대화...") + **Touch!**
- 다른 코어/눈송이들은 완전히 사라지지 않고 배경에 희미하게 남아 "같은 숲"임을 유지.

**Claude 분석과의 일치/차이:** Claude의 분석이 거의 정확함. 특히 "하단 Soul Core 뿌리에서 위로 자라는 수직 트리/성좌 (중앙 radial 아님)"이 핵심. 내가 본 이미지에서도 radial symmetry는 전혀 없고, 명확한 bottom-to-top growth axis가 지배적. "5 Pattern Core가 Soul Core 위로 군집" 포지셔닝도 정확.

**핵심 의도 (내 해석):**  
그래프는 **데이터 시각화**가 아니라 **"내 자아의 현재 생장 상태를 보여주는 살아있는 크리스탈 표본"**이다. 사용자는 이걸 "읽는" 게 아니라 "바라보고, 듣고, 만진다". 하단 2카드는 시각 언어를 인간(사용자) 언어로 즉시 번역해주는 **live narrator** 역할을 한다.

---

## 2. 현재 코드 대비 가장 큰 UX 갭 (감성·구조 레벨)

| 차원              | Reference (Simon)                          | 현재 구현 (NavGraph + world-layout)                  | UX 영향 |
|-------------------|--------------------------------------------|-----------------------------------------------------|--------|
| **레이아웃 모델** | Bottom-anchored vertical tree (Soul 하단 고정 → 상향 성장) | Radial sector village (WORLD_CENTER 중심, 6개 60° 섹터, RING2/RING3/RING4) | 첫인상 완전 다름. "뿌리에서 자라는 나" vs "탐험할 수 있는 마을 지도" |
| **코어 표현**     | 3D 테서랙트 큐브 (와이어 + 내부 상징 + 발광) 5개가 명확한 군집 | IslandArt + tesseract PNG (v10 default) 사용 중이나 radial 배치라 "큐브 트리"가 안 보임 | "발광 크리스탈" 은유가 약함 |
| **데이터 표현**   | Pattern Data = 파란 6각 눈송이 크리스탈 (tier4) | FinalPatternDataSnowflakeArt 최근 도입 (좋은 진전) | 이미 상당 부분 정렬됨 |
| **상시 해석 레이어** | Overview에도 항상 2 인사이트 카드 (세컨비 + 코어) | DrilldownSheet (drilldown 시에만 2카드), overview는 top insight ribbon + on-demand NodeSheet | "항상 켜져 있는 번역"이 없어서 그래프가 추상적으로 남음 |
| **무게 중심 & 시선 흐름** | 하단 Soul → 상단 canopy로 자연스럽게 시선 유도 | 중앙 코어 + 원형 분산. 시선이 사방으로 퍼짐 | "성장/상승" 은유가 약함 |
| **크롬 최소화**   | 헤더 극소 (로고+설정), 카드만 하단 | a11y "이전/다음/설정" 버튼, reset 버튼, FAB 등 | "유물/표본 감상" 몰입 방해 |
| **드릴다운 전환** | Focused core가 하단에 재정착 + canopy 강조 | DrilldownSheet가 올라오며 다른 노드 dim | 부드러운 "이 코어의 세계로 들어감"이 약함 |

**결론:** 최근 #250-254에서 눈송이·링크·드릴다운·카드를 추가한 것은 방향은 맞았으나, **홀리스틱 구조**(하단 앵커 + 수직 큐브-트리 + 상시 2카드 narrator + tesseract 군집)를 잡지 못했다. 조각 개선이 아니라 "다른 물건"을 만들고 있었다.

---

## 3. UX/감성 방향 — 구체

### (1) 이 '살아있는 발광 크리스탈 테서랙트-큐브 트리'가 주는 느낌·은유

- **근본 은유:**  
  Soul Core = **자아의 뿌리** (항상 바닥에, 가장 밝고 가장 크다. "내가 누구인지"의 중심).  
  5 Pattern Cores = **주요 생장 패턴** (커리어, 관계, 지식, 기록, 영감 등 삶을 조직하는 5대 렌즈). 테서랙트라는 형태 자체가 "3D로 보이는 나는 사실 더 고차원 자아의 투영"이라는 철학을 내포.  
  눈송이 조각 = **개별 경험/통찰의 결정체**. 수액을 받아 가지 끝에 맺히는 서리/잎.  
  링크 = **신경/수액 관**. "패턴"이 실제로 어떻게 연결되어 있는지 보여주는 살아있는 조직.

- **감성 키워드 (AI slop 피하기 위한):**  
  **경이 + 친밀 + 고요 + 귀중함.**  
  "이걸 켜면 내 안에 이런 아름다운 것이 자라고 있었다"는 발견의 기쁨.  
  게임적 재미나 "마을 탐험"의 가벼움이 아니라, **보석을 들여다보는 듯한** 느리고 깊은 몰입.  
  "살아있다"는 것은 과장된 움직임이 아니라, "내가 새 기록을 넣으면 이 크리스탈이 미세하게 반응한다"는 공생 감각.

- **상승 축의 의미:** 하단(과거/본질) → 상단(미래/가능성). 앱을 열 때 시선이 자연스럽게 아래에서 위로 이동하며 "내가 어디서 와서 어디로 가고 있는가"를 몸으로 느끼게 함.

### (2) 정보위계 · 첫인상 (처음 여는 사용자)

**시각 위계 (강제):**
1. Soul Core (크기 1.0, 최고 밝기, 하단 고정)
2. 5 Pattern Cores (크기 0.55~0.65, 코어 전용 색상 글로우, 상단 군집)
3. 눈송이 군 (크기 0.18~0.22, 낮은 채도, canopy 밀도 담당)

**의미 위계 + 행동 유도:**
- 그래프 = "감상 + 가볍게 손가락으로 더듬기"
- 하단 2카드 = "이게 너에게 무슨 의미인지" 즉시 번역 + "Touch!" 로 다음 행동 제안

**첫 3~5초 시나리오 (신규 사용자):**
1. 열자마자 하단 중앙의 가장 밝은 큐브가 눈을 잡는다. "이게 중심이구나."
2. 시선이 위로 올라가며 "이게 자라는 나무/성좌구나"를 직관적으로 파악 (설명 필요 없음).
3. 하단 카드 두 장이 즉시 말을 건다:
   - 세컨비: "너 최근에 위즈덤에 뭐 넣었네? 뮤즈는 좀 챙겨야겠다."
   - 특정 코어: "이 영역은 너의 커리어(또는 관계/기록...)에 대한 거야. 여기 MPAP라는 조각이 최근에 들어왔어."
4. 사용자는 "아, 이게 내 데이터가 아니라 내 삶의 패턴이구나"를 5초 안에 느낀다.
5. "Touch!" 를 누르면 자연스럽게 그 패턴의 세계로 들어간다.

**중요:** 오버뷰 상태에서도 2카드가 항상 살아있어야 "빈 화면 공포"와 "이게 뭐지?" 혼란이 발생하지 않는다. 데이터가 적을 때조차 "성장의 여지"가 카피와 여백으로 느껴져야 함.

### (3) AI slop 아닌 진짜 프리미엄 제품감 — 구체 디테일

**색 (tokens 완전 준수 + core-specific tuning)**
- 배경: `cosmic.space950` (#070A18) 엄수. pure black 절대 금지.
- Soul Core: violet (#A78BFA) + 강한 cyan inner core light (ref처럼).
- Growth Core: `signalBlue` (#4CC9F0) dominant + mint edge.
- Wisdom Core: mint (`signalMint`) 또는 silver-white.
- Bond: `pixelLamp` (#FFD166).
- Muse: `dreamPink` (#FF9FD6).
- Narrative: 적절한 desat violet or teal.
- 링크 base: `lineDim` 또는 core-tinted desaturated. Active flow는 극도로 절제된 mint/ core accent (opacity 0.4~0.75 범위).
- 눈송이: base는 차가운 blue-white, facet highlight는 해당 parent core 색을 극미량만 (slop 방지 핵심).

**모션 (reduced-motion 필수, bounce 금지)**
- 코어 (특히 Soul): 거의 정지. 8~12초 주기 극미세 breathing (inner emblem opacity/scale 0.97~1.03). "trunk"로서 dignity.
- 눈송이: 서로 다른 phase의 극저주파 twinkle (4~8s) + 매우 낮은 amplitude sway. "서리가 바람에 미세하게 흔들리는" 수준.
- 링크: 기존 flow dash를 더 느리고 (3.5~5s 주기), 더 은은하게. "전기 스파크"가 아니라 "수액이 천천히 흐르는" 느낌.
- 사용자 인터랙션: tap → 해당 노드와 인접 링크에 220~280ms focused charge pulse (mint or core accent) → 서서히 root 방향으로 흡수되며 fade. 이게 "살아있음"의 가장 강한 표현.
- 모든 ambient는 `prefersReducedMotion` 시 완전 정지 또는 극미세 static glow로 대체.
- 기존에 허용된 작은 node spawn overshoot (1.25→1.0)는 신규 data 추가 시에만 제한적으로 유지.

**여백 · 구도 · 레이아웃**
- Soul Core: 화면 하단 18~22% 영역에 하단이 살짝 잘리지 않게 앵커.
- 5 Pattern Cores: 상단 55~65% 영역에 유기적 arc/군집 (정확한 원이 아니라 ref의 "위로 퍼지는" 느낌).
- 좌우 여백: 최소 10~14% (구조가 액자 안에 들어 있는 듯한 귀중함).
- 상단 여백: 의도적으로 비워 "성장할 공간 = 미래" 은유.
- 카드: 화면 최하단에 "plinth" 느낌으로 배치. 카드 표면은 현재 `semantic.surface` wash를 유지하되, ref처럼 약간 더 inset되고 덜 dominant하게 (그래프가 주인공, 카드는 해설자).
- 카드 간 간격과 그래프 하단과의 air를 충분히 (ref 카드가 그래프와 "함께 있는" 느낌).

**카피 톤 (DESIGN.md voice 엄수)**
- 세컨비 카드: 구체적 + 살짝 장난기 있는 재촉 ("보강 필요해요!"). "!" 는 다정함.
- 코어 카드: "이곳은 그로스 코어예요. 나의 커리어와 관련된 조각들이 모여 있어요." — 1인칭 서술 + "나(사용자)"의 목소리를 대변. 추상적 설명 금지.
- "Touch!": 명령이 아니라 초대. 작고, 부드러운 컬러, 별도 아이콘 없이 텍스트만. PremiumButton primary 스타일 절대 금지.
- 전체: 과장된 수식, "환상적인", "놀라운" 같은 LLM 단어 금지. "생각보다 구체적이고, 생각보다 따뜻한" 친구의 말.

### (4) 피해야 할 함정 (반드시 체크리스트화)

1. **레이아웃 함정** — "예쁘게 재배치"만 하고 radial world-layout을 그대로 두기. 반드시 bottom-root + upward growth를 위한 별도 layout 모델 (또는 world-tree 레이어) 필요.
2. **아트 함정** — tesseract PNG를 그냥 큰 크기로 올려놓기. ref의 "육각 와이어프레임 + 내부 코어 상징 + 다면 발광"을 살리려면 PNG + core별 subtle glow layer (LivingAsset 또는 reanimated soft radial) 조합 필수. v10 cutout 자산을 최대한 활용.
3. **모션 슬롭** — "살아있게" 하려고 모든 노드에 pulse/glow/sway 넣기. 결과는 싸구려 네온사인. "대부분 고요, 소수만 살아있음"이 진짜 프리미엄.
4. **카드 함정** — 기존 NodeSheet/DrilldownSheet 스타일을 overview에도 재사용하거나, "Touch!"를 무거운 버튼으로 만들기. ref 카드는 "그래프의 일부이자 해설자"다. 항상 보이고, 작고, 시각적으로 2차적.
5. **드릴다운 함정** — 다른 코어를 완전히 숨기거나 dim만 과도하게 하기. ref2처럼 "같은 숲 안에 있는 focused branch" 느낌을 유지 (recede + canopy 재구성).
6. **크롬/설명 함정** — "마을", "섹터", "tier" 시각 잔재 (villageTag 등), a11y 버튼 과다, reset 버튼 상시 노출. ref는 "설명 없이도 이해되는 유물"이다.
7. **시선 분산 함정** — 중앙 정렬 + 원형 대칭 유지. "성장" 은유가 죽는다.
8. **데이터 과시 함정** — 눈송이를 너무 크거나 채도 높게. delicate frost여야지 competing jewelry가 아니다.
9. **제너레이티브 슬롭** — heavy vignette, floating particles, lens flare, chromatic aberration, 과도한 glow stack. Pixel art의 crisp + controlled optical glow만 허용.
10. **첫인상 함정** — "데이터가 없으면 허전해 보이는" 상태를 방치. ref는 데이터 적을 때도 "아직 어린 정원이지만 뿌리는 단단하고, 앞으로 자랄 공간이 있다"는 느낌을 준다.

---

## 4. 구현을 위한 실천 제안 (우선순위 순, UX 관점)

1. **레이아웃 근본 재설계** — `src/components/graph/tree-layout.ts` (또는 world-tree) 신규. Soul y를 viewport 하단 근처로 고정, 5 cores의 상대 좌표를 ref 이미지 기반으로 organic cluster (seeded jitter 허용), data snowflakes는 각 core 주변 + 상단 canopy로 fan. world-layout의 radial 로직은 overview village 모드에서만 남기거나 별도 플래그.
2. **CoreCube 아트 래퍼** — `SoulcoreFinalArt` 또는 신규 `TesseractCore.tsx`. PNG + core-specific inner glow + edge highlight layer. drilldown 시 scale/opacity + canopy 재배치 애니메이션.
3. **상시 OverviewInsightCards** — drilldown과 별개의 항상 마운트 컴포넌트. 2장 카드 (세컨비 + 최근/주의 코어). DrilldownSheet와 내용/스타일 공유하되, overview에서는 "live caption"으로 더 작고 덜 dominant하게. "Touch!" 는 drilldown 진입 트리거.
4. **드릴다운 전환 UX** — core tap 시 camera가 부드럽게 해당 core를 하단 앵커 쪽으로 이동 + scale 미세 조정하면서, 해당 core의 data들이 canopy를 형성하며 강조. 다른 것들은 graceful recede (dim + saturate + scale 0.8~0.9). "이 코어의 세계로 들어가는" 느낌.
5. **모션 시그니처 업데이트** — `useSignatureMotion`, `patternLinkStyle` 등에 "crystal tree" 모드 추가. reduced-motion 완전 대응. 기존 flow는 "neural sap" 버전으로 톤 다운.
6. **헤더 최소화 + a11y 재배치** — ref처럼 로고+설정만. a11y 이전/다음은 설정 내부로 이동하거나 long-press 대체.
7. **검증 루프** — `npm run verify` + 실제 기기에서 ref 스크린샷 side-by-side 비교. "3초 만에 이 화면이 무엇을 하는지, 왜 소중한지 설명할 수 있는가"를 기준으로 삼음.

---

**Grok 추가 메모**  
이 방향은 "Simon이 준 이미지의 구조와 의도"를 있는 그대로 존중하면서, 현재 2nd-B의 DESIGN.md voice, cosmic token, reduced-motion 제약, "AI slop 방지" 원칙을 최우선으로 교차 검증했다.  

Claude가 codex/antigravity/grok 리포트를 종합할 때, **"radial village를 tree로 근본 전환 + 상시 2카드 narrator"** 가 가장 큰 레버임을 명확히 전달해 주길 바란다. 조각 개선으로는 절대 안 잡히는 갭이다.

이 파일은 grok의 독립적 판독 결과. 필요 시 보강하거나 반박 환영.
