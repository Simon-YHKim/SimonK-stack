---
name: social-graphic
description: >
  Use when the user wants social media or marketing graphics generated — SNS·마케팅 그래픽을
  Gemini 이미지 생성으로 만든다 — 트리거 "카드뉴스", "인스타 이미지", "포스터 만들어", "SNS 그래픽",
  "스토리 이미지", 또는 /social-graphic. Produces 인스타 1:1(1080x1080)·4:5(1080x1350)·스토리 9:16,
  카드뉴스 시리즈, 포스터를 지원한다. 브랜드 토큰(색·폰트·로고)이 있으면 주입해 일관성을 유지하고, 없으면
  /design-consultation 을 먼저 권유한다. AI-slop 방지(모노톤 3색 이내·Inter 금지·과잉장식 금지)를
  프롬프트에 강제한다.
version: 1.0.0
author: simon-stack
allowed-tools: Read, Write, Bash, AskUserQuestion
---

# /social-graphic

인스타그램·스토리·카드뉴스·포스터 같은 SNS/마케팅 그래픽을 Gemini 이미지 생성으로 만든다. 브랜드 일관성과 AI-slop 방지를 프롬프트 단계에서 강제하고, `scripts/gen_graphic.mjs` 로 실제 PNG 를 생성한다.

## When to use

트리거:
- Korean: 카드뉴스, 인스타 이미지, 인스타 카드, 포스터 만들어, SNS 그래픽, 스토리 이미지, 썸네일 만들어
- English: instagram graphic, card news, make a poster, social media image, story graphic
- Slash: `/social-graphic`

## Boundaries

- 디자인 시스템(색·폰트·톤) 자체를 **정의**하는 작업이 아니다 → 그건 `/design-consultation` · `/simon-design-first`. 이 skill 은 이미 정해진(또는 즉석에서 받은) 브랜드를 **그래픽으로 출력**한다.
- HTML/CSS 페이지가 아니라 **래스터 이미지(PNG)** 를 만든다. 웹페이지는 `/design-html`.
- 영상/모션이 아니다 → `remotion-best-practices`.

## 비율 프리셋

| 용도 | 비율 | 픽셀 | `--aspect` |
|---|---|---|---|
| 인스타 정사각 / 프로필 카드 | 1:1 | 1080x1080 | `1:1` |
| 인스타 피드(세로, 권장) / 카드뉴스 | 4:5 | 1080x1350 | `4:5` |
| 스토리 / 릴스 커버 | 9:16 | 1080x1920 | `9:16` |

포스터는 용도에 따라 4:5 또는 9:16 선택(인쇄용 별도 비율이 필요하면 사용자에게 확인).

## Workflow

### Step 1. 용도·비율·브랜드 파악

`AskUserQuestion` 으로 한 번에 확인(이미 메시지에 있으면 생략):

1. **용도/플랫폼** — 인스타 피드 / 스토리 / 카드뉴스(몇 장) / 포스터
2. **비율** — 위 프리셋에서 선택
3. **핵심 메시지 한 줄** — 그래픽이 전달할 단 하나의 문장(정보 밀도 규칙: 화면당 메시지 1개)
4. **브랜드 토큰** — 색(accent/text/bg) · 폰트 · 로고 파일 경로

브랜드 토큰 처리:
- `DESIGN.md` · `tokens.ts` · `design-system.html` 등이 프로젝트에 있으면 **Read 해서 색/폰트를 그대로 주입**한다.
- 아무 브랜드 정보가 없으면: "브랜드 색·폰트가 정해져 있나요? 없으면 `/design-consultation` 으로 먼저 정하길 권합니다. 일단 진행하려면 모노톤 기본값(차분한 neutral + accent 1색)으로 만들까요?" 라고 물어 사용자 결정을 받는다.

### Step 2. 브랜드 일관 프롬프트 작성 (AI-slop 방지 강제)

프롬프트에 다음을 **반드시 명시**한다:

- **모노톤 3색 이내** — accent + text + bg. 4색 이상 multi-color 금지.
- **폰트** — 한국어는 Pretendard 계열, 영문은 Inter 금지(AI 티). 텍스트가 들어가면 폰트 톤을 명시.
- **과잉장식 금지** — 이모지 아이콘, glassmorphism, 과한 gradient(purple→pink), 둥근 카드+좌측 컬러보더 금지.
- **한 메시지 + 한 그래픽** — 화면당 핵심 문장 1개. 설명 텍스트로 메우지 말 것.
- **여백 존중** — 인스타 안전영역(상하단 UI 가림) 고려, 핵심은 중앙 60%.

카드뉴스 시리즈는 장마다 프롬프트를 만들되 **공통 스타일 문장(색·폰트·레이아웃·여백)을 모든 장에 동일하게 반복**해 톤을 묶는다. 표지/본문/마무리 역할을 구분한다.

프롬프트 골격 예:
```
<주제> 인스타 <용도> 그래픽. 핵심 메시지: "<한 줄>".
스타일: 모노톤 — 배경 <bg hex>, 텍스트 <text hex>, 액센트 <accent hex> 단 1색.
폰트 톤: <Pretendard 계열 / 지정 폰트>, 깔끔한 산세리프. 과잉장식 없음, 이모지 없음, gradient 없음.
레이아웃: 중앙 정렬 큰 타이포, 넉넉한 여백, 안전영역 고려.
```

### Step 3. 생성 — scripts/gen_graphic.mjs 실행

```bash
node "<skill_dir>/scripts/gen_graphic.mjs" \
  --prompt "<Step 2 프롬프트>" \
  --aspect 4:5 \
  --out "<프로젝트>/assets/social/launch_card.png"
```

옵션:
- `--n 3` — 같은 프롬프트로 변형 N장(파일명에 `-1`, `-2` 접미사). 표지 시안 비교용.
- `--out` 미지정 시 cwd 에 `social-graphic-<timestamp>.png` 로 저장.

환경 변수 `GEMINI_API_KEY`(없으면 `GOOGLE_API_KEY`) 필요. 스크립트가 키/SDK 누락 시 설치·설정 안내를 출력하니 그대로 사용자에게 전달한다.

### Step 4. 사용자 확인 → 반복

생성된 PNG 경로를 사용자에게 보여주고(`SendUserFile` 가능하면 활용):

- 문구 수정 → 프롬프트의 메시지만 교체 후 재생성
- 톤/색 수정 → 스타일 문장 교체 후 재생성
- 카드뉴스 추가 장 → 공통 스타일 유지하며 장별 프롬프트 추가

"이대로 확정할까요, 아니면 어디를 바꿀까요?" 로 닫는다. 사용자가 멈추라 할 때까지 시안 → 피드백 루프를 돈다.

## Anti-patterns

- 브랜드 정보 없이 화려한 multi-color 그래픽을 임의 생성
- 한 장에 메시지·정보 여러 개를 욱여넣기(정보 밀도 위반)
- Inter 폰트, 이모지 아이콘, 과한 gradient 사용
- 사용자 확인 없이 N장을 무한 생성해 토큰·쿼터 낭비
- 모델 ID 를 본문에 하드코딩한 채 방치 — 최신 이미지 모델로 교체 필요 시 스크립트 상단 상수만 수정

## Operational notes

- 외부 의존: Node 18+, `@google/genai`, 그리고 `GEMINI_API_KEY` 또는 `GOOGLE_API_KEY`.
- 모델 ID 는 `scripts/gen_graphic.mjs` 상단 `MODEL` 상수에서 한 곳만 교체한다(주석으로 명시).
- 실패 시: 어느 단계(키 누락 / SDK 미설치 / 응답에 이미지 없음)에서 막혔는지 명시하고 사용자 결정을 받는다.
- 유료 API 호출이므로 변형 장수(`--n`)는 보수적으로. 확인 후 늘린다.

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
