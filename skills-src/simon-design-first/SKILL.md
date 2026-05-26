---
name: simon-design-first
description: "Use when the user asks for design, UI, landing page, or website work—triggers \"디자인 만들어줘\", \"UI 만들어줘\", \"랜딩페이지\", \"design this\", \"build a landing page\". Produces a diagnostic (audience/purpose/tone) + 3-5 reference URLs + font options with Google Fonts links, then gets user's direction choice BEFORE any code. Blocks AI from jumping to HTML/CSS. Prevents AI slop (Inter font, pure black, emoji icons, multi-color). Mandatory proxy before /design-consultation, /design-html, /design-shotgun, stitch-design-flow."
allowed-tools: Read, Write, Edit, WebFetch
version: 1.0.0
author: simon-stack
---

# simon-design-first

디자인 작업 전 **반드시** 진단 → 레퍼런스 → 방향 확정을 거치게 강제하는 프록시 skill.

## 발동 조건

사용자 메시지에 다음이 포함되면 즉시 이 skill이 먼저 돈다:

- "디자인 만들어줘", "UI 만들어줘", "랜딩페이지", "웹사이트 만들어줘"
- "design this", "build a landing page", "make a website"
- `/design-consultation`, `/design-html`, `/design-shotgun` 호출 전

## Workflow — 반드시 이 순서

### Step 1. 진단 (사용자에게 질문)

절대 건너뛰지 않는다. 다음 3가지를 확인:

1. **누가 볼 사이트인가?** — 개발자 / 일반 사용자 / 기업 고객 / 투자자
2. **목적은?** — 제품 소개 / 판매 / 문서 / 포트폴리오 / 커뮤니티
3. **톤·분위기는?** — 프로페셔널 / 친근 / 프리미엄 / 실험적 / 미니멀

사용자가 "알아서 해"라고 하면 → 최소한 1번(누가 볼 사이트)만 확정하고 진행.

### Step 2. 레퍼런스 추천 (URL 필수)

유사 제품·톤의 사이트 3-5개를 **반드시 접속 가능한 URL과 함께** 제시.

형식 예시:

| # | 사이트 | 참고 포인트 | URL |
|---|---|---|---|
| 1 | Linear | 미니멀 다크, 모노톤 | https://linear.app |
| 2 | Vercel | 개발자 도구 미니멀 | https://vercel.com |

탐색용 사이트도 함께 제공:
- https://dribbble.com
- https://www.awwwards.com
- https://www.lapa.ninja
- https://21st.dev (UI 구성요소 + AI 에이전트 호환)
- https://uxsnaps.com (실제 앱 UI/UX 분석, 한국 멘탈 헬스 앱 케이스 포함)
- https://styles.refero.design (URL → DESIGN.md 자동 추출)
- https://transitions.dev (CSS 트랜지션 즉시 복붙)
- https://pencil.dev (IDE 캔버스 → 코드)
- https://fontofweb.com (AI 폰트/디자인 영감 피드)

상세 카탈로그 + DESIGN.md 6단계 워크플로우: [references/design-md-workflow.md](references/design-md-workflow.md)

### Step 3. 폰트 선택권

Google Fonts 미리보기 URL 포함한 후보 3-5개 + AI 추천 1개.

형식:

| 폰트 | 특징 | 미리보기 |
|---|---|---|
| Pretendard | 한국어 최적화 | https://cactus.tistory.com/306 |
| Plus Jakarta Sans | 모던 | https://fonts.google.com/specimen/Plus+Jakarta+Sans |
| Space Grotesk | 기술적 | https://fonts.google.com/specimen/Space+Grotesk |

### Step 3.5. AI Trope Detection (사전 차단)

레퍼런스 추천 직후, 사용자에게 다음 안티패턴을 명시하여 동의 받음:

| AI Slop | 대안 |
|---|---|
| Inter 폰트 (어디서나 보임) | Pretendard / Geist / Plus Jakarta Sans |
| pure black `#000` 배경 | tinted neutral (`#0d0f1a` 같은 violet/blue tint) |
| 이모지를 아이콘 대용 | 텍스트 라벨 또는 SVG icon (Iconify Solar) |
| 과한 gradient (특히 purple→pink) | 단색 또는 미묘한 tint |
| 둥근 카드 + 좌측 컬러 보더 | 단순 1px border 또는 shadow only |
| 모든 것이 가운데 정렬 | 의도적 비대칭, asymmetric grid |
| Bouncy/elastic easing | ease-out 또는 cubic-bezier(0.16, 1, 0.3, 1) |

상세 detection list와 anti-pattern 갤러리: [references/design-chapters.md](references/design-chapters.md)

**자동 검수 옵션** — 코드 작성 후 `impeccable.style` 에 URL 제출 → 24 AI slop 패턴 자동 탐지 + UX 평가. 상세: [references/design-md-workflow.md § Part 4](references/design-md-workflow.md)

### Step 4. 사용자 방향 확정

"이 느낌으로 갈까요?" 또는 "다른 레퍼런스 보여줄까요?" 물어본다.

사용자 응답:
- 특정 방향 선택 → 그 방향으로 진행
- "알아서 해" → AI가 추천 방향으로 진행
- "다른 것" → Step 2부터 재시작

### Step 4.5. Accessibility Quick Check

방향 확정 시 다음 체크리스트가 충족되는지 확인 (하위 skill에 전달):

- [ ] Text/background contrast WCAG AA (4.5:1 normal text, 3:1 large text)
- [ ] Focus state 명시 (keyboard navigation 가능)
- [ ] Interactive 요소는 44×44px 최소 (mobile tap target)
- [ ] Loading/error/empty/disabled state 모두 디자인됨
- [ ] Semantic HTML (`<button>`, `<nav>`, `<main>`, alt text)
- [ ] Reduced-motion 대응 (`prefers-reduced-motion`)

### Step 5. 하위 skill 위임 — 디자인 라이프사이클 7 skill 전체 chain

방향 확정 후, 사용자가 어떤 단계 (plan / 디자인 결정 / 시안 / 코드 / 폴리시)에 있느냐에 따라 분기:

**A. 플랜 / 디자인 결정 단계** (코드 작성 전)
- 디자인 시스템 정의·DESIGN.md 산출 → `/design-consultation`
- 플랜 모드에서 시안 평가 → `/plan-design-review` (0~10점 + "10점이 되려면" feedback)
- AI 변형 탐색·비교 보드·피드백 수렴 → `/design-shotgun`

**B. 외부 시안 도구**
- Google Stitch / 시각 AI 도구용 프롬프트 생성 → `stitch-design-flow`

**C. 코드 생성 단계**
- production HTML/CSS 변환 (Pretext-native, 30KB 무의존) → `/design-html`

**D. 라이브 사이트 폴리시 단계** (코드 배포 후)
- 시각 QA — spacing/hierarchy/AI slop 탐지 + 원자 commit 자동 폴리시 → `/design-review`

→ 전체 디자인 라이프사이클 **7 skill** (simon-design-first 본인 + 위 6개) 가 빠짐없이 chain 통과. 어느 한 단계에서 진입하든 simon-design-first 가 entry · 나머지 위임은 단계별로.

**호출 순서 권장 예시** (zero-to-one 디자인):
```
simon-design-first (진단·레퍼런스·방향)
  → /design-consultation (DESIGN.md)
  → /plan-design-review (계획 검토)
  → /design-shotgun (변형 탐색)        ← 사용자 비교·피드백
  → stitch-design-flow (외부 시안)     ← 선택적
  → /design-html (production 코드)
  → /design-review (배포 후 폴리시)
```

### Step 5.5. 시나리오별 chain 가지치기 (chain bloat 방지)

시나리오마다 필수 chain 이 다르다. 모든 7 skill 을 매번 다 돌리지 말고 시나리오로 가지치기:

| 시나리오 | 필수 chain | 선택 chain | Skip |
|---|---|---|---|
| **Zero-to-one** (새 디자인) | simon-design-first → /design-consultation → /plan-design-review → /design-html → /design-review | /design-shotgun, stitch-design-flow | — |
| **Existing 페이지 refactor** (이미 존재) | simon-design-first → **/plan-design-review (기존 페이지 0-10 audit)** → /design-consultation (필요 시 DESIGN.md 갱신) → /design-html → /design-review | /design-shotgun | stitch-design-flow |
| **라이브 사이트 폴리시** (배포 후 작은 fix) | simon-design-first → /design-review | — | /design-consultation, /plan-design-review, /design-shotgun, stitch-design-flow, /design-html |
| **변형 탐색 only** (방향 미정) | simon-design-first → /design-shotgun | (선택 후 시나리오 1 or 2 로 전환) | 나머지 |
| **외부 시안 도구만** (Stitch 사용) | simon-design-first → stitch-design-flow → /design-html | /design-review | /plan-design-review, /design-shotgun |

**핵심 원칙 2가지**:

1. **plan-design-review 는 코드 작성 전 plan 평가뿐 아니라 *기존 페이지 사전 audit* 으로도 활용** — refactor 시나리오에서 진입점. 0-10 점수가 "10점이 되려면" 사양으로 변환되어 design-consultation / design-html 입력이 됨.
2. **design-html 산출 후엔 자동 design-review 폴리시 단계** — design-html 의 description 은 upstream (plan-design-review, design-shotgun) 만 명시하지만, simon-design-first 가 hub 로서 후속 design-review 를 강제. 이 단계 없이는 AI slop 잔존 위험.

## AI Slop 방지 3원칙 (실행 시 반드시 적용)

하위 skill로 넘길 때 이 원칙을 명시적으로 전달:

1. **불필요한 것 제거** — 이모지 아이콘, 장식, 과잉 요소 금지
2. **모노톤 색상** — 전체 UI 색상 3개 이내 (accent + text + bg)
3. **레퍼런스에서 착안** — 확정된 방향 유지, 자체 방향 X

### 금지 폰트·색상

- **Inter** (AI 생성 티 남) → 한국어 **Pretendard**, 영문 대안 산세리프
- **pure black/gray** → tinted neutrals (약간 violet/blue tint)
- **4색 이상 multi-color**
- **bounce/elastic easing**

## Anti-patterns

- ❌ 진단 없이 바로 코드 작성
- ❌ 레퍼런스 없이 "모던한 디자인" 같은 막연한 방향으로 진행
- ❌ 링크 없는 폰트/레퍼런스 추천
- ❌ 사용자가 방향 결정하기 전에 HTML 생성
- ❌ AI slop 3원칙 무시

## Korean context

한국어 프로젝트는 기본적으로:
- 폰트: Pretendard Variable (CDN)
- `word-break: keep-all` 필수
- 한국 사용자 대상이면 레퍼런스에 한국 사이트(Toss, Liner, Wrtn 등)도 포함

## Escape hatch

사용자가 명시적으로 "레퍼런스 스킵하고 바로 만들어"라고 지시하면 이 skill을 스킵 가능.
하지만 나중에 "AI 티 난다"고 지적받을 가능성 높음을 경고할 것.
