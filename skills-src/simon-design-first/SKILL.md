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
- https://21st.dev (UI 구성요소)

### Step 3. 폰트 선택권

Google Fonts 미리보기 URL 포함한 후보 3-5개 + AI 추천 1개.

형식:

| 폰트 | 특징 | 미리보기 |
|---|---|---|
| Pretendard | 한국어 최적화 | https://cactus.tistory.com/306 |
| Plus Jakarta Sans | 모던 | https://fonts.google.com/specimen/Plus+Jakarta+Sans |
| Space Grotesk | 기술적 | https://fonts.google.com/specimen/Space+Grotesk |

### Step 4. 사용자 방향 확정

"이 느낌으로 갈까요?" 또는 "다른 레퍼런스 보여줄까요?" 물어본다.

사용자 응답:
- 특정 방향 선택 → 그 방향으로 진행
- "알아서 해" → AI가 추천 방향으로 진행
- "다른 것" → Step 2부터 재시작

### Step 5. 하위 skill 위임

방향 확정 후 실제 작업은 하위 skill에 위임:
- 디자인 시스템 정의 → `/design-consultation`
- Stitch 프롬프트 생성 → `stitch-design-flow`
- HTML 코드 생성 → `/design-html`
- 변형 탐색 → `/design-shotgun`

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
