# Design Chapters — claude-design-system-prompt 차용

> 출처: github.com/Trystan-SA/claude-design-system-prompt (20장 디자인 시스템)
> 거기서 핵심만 추출 + AI Slop 방지를 위한 자체 anti-pattern 추가.

## Contents

1. [20장 인덱스](#20장-인덱스)
2. [핵심 원칙 정리](#핵심-원칙-정리)
3. [Interaction State 커버리지](#interaction-state-커버리지)
4. [AI Trope Detection 상세](#ai-trope-detection-상세)
5. [Anti-pattern 갤러리](#anti-pattern-갤러리)
6. [폰트·색·간격 가이드](#폰트색간격-가이드)

---

## 20장 인덱스

| # | 장 | 핵심 |
|---|---|---|
| 1 | Identity | 디자이너 정체성, AI 클리셰 거부 |
| 2 | Workflow | discovery → aesthetic → wireframe → prototype → polish |
| 3 | Discovery | 사용자·목적·제약 인터뷰 |
| 4 | Context | 비즈니스 도메인 이해 |
| 5 | Content | 콘텐츠 우선, 디자인은 콘텐츠를 위해 |
| 6 | Aesthetics | 의도적 미감, 트렌드 추종 X |
| 7 | Hierarchy | scale·color·weight·spacing으로 위계 |
| 8 | Typography | type system, font pairing, modular scale |
| 9 | Color | OKLCH 색공간, tinted neutrals, dark mode |
| 10 | Accessibility | WCAG, 키보드, 스크린리더 |
| 11 | Interaction | 모든 state 명시 (default/hover/active/disabled/loading/error) |
| 12 | Simplicity | "정당화 못 하는 요소는 삭제" |
| 13 | System Thinking | 일관된 system, 일회용 디자인 X |
| 14 | Medium Respect | 웹은 웹답게, 앱은 앱답게 |
| 15 | User Understanding | 사용자 mental model 따라가기 |
| 16 | Quality | 마무리 1%, 5% 까지 신경 |
| 17 | Output | 완성된 코드 전달, 플레이스홀더 X |
| 18 | Collaboration | 디자이너·개발자·사용자 협업 |
| 19 | IP Boundaries | 저작권·라이선스 존중 |
| 20 | Skills | 14 procedural skills (kickoff, aesthetic, wireframes, decks, prototypes...) |

---

## 핵심 원칙 정리

### 1. "모든 요소는 존재 이유가 있어야 한다"

장식적 요소 금지. 각 요소는 다음 중 하나를 충족:
- 정보 전달 (텍스트, 데이터)
- 행동 유도 (버튼, 링크)
- 상태 표시 (loading, error)
- 위계 표현 (heading, divider)

미충족 = 삭제

### 2. "위계는 4가지로만"

- Scale (크기)
- Color (색)
- Weight (두께)
- Spacing (여백)

이 4가지로 모든 위계 표현. shadow·border·gradient 추가 사용은 장식 영역.

### 3. "모든 interaction state 명시"

버튼 하나도 8개 state:
- default
- hover
- active (pressed)
- focus (keyboard)
- disabled
- loading
- error
- success

빠지면 reactive UI가 깨진다.

### 4. "OKLCH로 색 정의"

```css
/* ❌ HSL/RGB는 perceptual uniform 아님 */
--blue: hsl(220, 80%, 50%);

/* ✅ OKLCH는 perceptual uniform */
--blue: oklch(60% 0.15 240);
```

이유: 다크모드 변환 시 HSL은 lightness가 visual lightness와 안 맞음.

### 5. "Tinted neutrals"

pure black/gray 금지. 항상 약간의 tint:

```css
/* ❌ */
--bg: #000;
--text: #888;

/* ✅ */
--bg: oklch(15% 0.02 270);   /* 약간 violet */
--text: oklch(70% 0.02 270);
```

---

## Interaction State 커버리지

### 모든 컴포넌트가 가져야 할 state

| 컴포넌트 | 필수 state |
|---|---|
| Button | default, hover, active, focus, disabled, loading |
| Input | default, focus, filled, error, disabled, readonly |
| Link | default, hover, visited, focus, active |
| Card | default, hover (clickable일 때), selected |
| Modal | opening, open, closing |
| Form | pristine, dirty, valid, invalid, submitting, submitted, error |
| List | empty, loading, loaded, error, refreshing |

### Empty/Loading/Error 디자인

페이지/컴포넌트마다 4개 state 필수:
1. **Initial loading** — skeleton screen
2. **Empty** — "결과가 없습니다" + 다음 액션 제안
3. **Error** — 친절한 메시지 + retry 버튼
4. **Success / Filled** — 정상 콘텐츠

빠뜨리는 게 가장 흔한 AI 디자인 실패.

---

## AI Trope Detection 상세

### Trope 1: Inter 폰트

증상: heading부터 body까지 전부 Inter
대안:
- 한국어: Pretendard Variable (https://github.com/orioncactus/pretendard)
- 영문 모던: Geist (https://vercel.com/font), Plus Jakarta Sans
- 코드: JetBrains Mono, IBM Plex Mono

### Trope 2: Purple→Pink Gradient

증상: hero 배경에 `linear-gradient(135deg, #8b5cf6, #ec4899)`
이유: AI 학습 데이터에 너무 많이 등장
대안: 단색 + 미묘한 tint, 또는 실제 사진/일러스트

### Trope 3: 이모지 아이콘

증상: 카드 헤더에 🚀⚡🎨 같은 이모지
이유: SVG 아이콘 만들기 귀찮아서 AI가 fallback
대안: Iconify Solar (https://iconify.design), Lucide, Heroicons

### Trope 4: 둥근 카드 + 좌측 컬러 보더

```
┌─━━━━━━━━━━━━━━━━━━━━┐
┃  Title              │
┃  Description        │
└──────────────────────┘
```

증상: `border-left: 4px solid <color>; border-radius: 12px`
이유: bootstrap 시대 alert 패턴, 이제 진부함
대안: 단순 1px border, 또는 미묘한 background tint

### Trope 5: "모든 것이 가운데 정렬"

증상: hero, feature card, footer 전부 `text-align: center`
이유: 안전한 default
대안: 의도적 비대칭. hero left-aligned + 우측에 image, asymmetric grid

### Trope 6: Bouncy/Elastic Easing

증상: `cubic-bezier(0.68, -0.55, 0.265, 1.55)` (overshoot)
이유: 2015년 Material Design 시대 trend
대안: `cubic-bezier(0.16, 1, 0.3, 1)` (smooth ease-out), 또는 `ease`

### Trope 7: Glassmorphism 남용

증상: 모든 카드에 `backdrop-filter: blur(20px)` + 반투명
이유: 2020 trend
대안: 의도적으로 한 곳만 (nav 같은 floating 요소)

### Trope 8: "느낌 위주" copy

증상: "Reimagine your workflow", "Transform the way you work" 같은 의미 없는 카피
대안: 구체적 benefit. "5초 안에 보고서 생성", "월 1만건 처리"

---

## Anti-pattern 갤러리

### Anti-pattern: Hierarchy 없는 텍스트

```html
<!-- ❌ 모든 텍스트가 같은 weight, size -->
<div>Title</div>
<div>Subtitle</div>
<div>Body text</div>

<!-- ✅ Scale + Weight 위계 -->
<h1 class="text-4xl font-bold">Title</h1>
<h2 class="text-xl font-medium text-gray-600">Subtitle</h2>
<p class="text-base">Body text</p>
```

### Anti-pattern: Hover만 있고 focus 없음

```css
/* ❌ keyboard 사용자 제외 */
.btn:hover { background: blue; }

/* ✅ */
.btn:hover, .btn:focus-visible { background: blue; }
.btn:focus-visible { outline: 2px solid currentColor; }
```

### Anti-pattern: 색만으로 정보 전달

```html
<!-- ❌ 색맹 사용자에게 전달 안 됨 -->
<span style="color:red">Error</span>

<!-- ✅ 색 + icon + text -->
<span style="color:red" role="alert">
  ⚠ Error: <strong>Invalid email</strong>
</span>
```

### Anti-pattern: Loading state 없음

```jsx
// ❌
{data && <List items={data} />}

// ✅ 4 state 모두
{isLoading && <Skeleton />}
{error && <ErrorMessage onRetry={refetch} />}
{data?.length === 0 && <Empty />}
{data?.length > 0 && <List items={data} />}
```

---

## 폰트·색·간격 가이드

### 폰트 페어링

| 용도 | 한국어 우선 | 영문 우선 |
|---|---|---|
| Heading + Body | Pretendard 700 + 400 | Geist 700 + 400 |
| Display + Body | Pretendard 800 + Pretendard 400 | Plus Jakarta 800 + Inter 400 (드물게) |
| Code | JetBrains Mono | JetBrains Mono / IBM Plex Mono |
| Display + Pixel | Galmuri11 + Pretendard | Press Start 2P + Geist |

### 모듈러 스케일 (1.25 ratio)

```
text-xs    12px
text-sm    14px
text-base  16px  ← body default
text-lg    20px
text-xl    25px
text-2xl   31px
text-3xl   39px
text-4xl   49px  ← hero
```

### Spacing 시스템 (4px grid)

```
0   1px  4px  8px  12px  16px  24px  32px  48px  64px  96px  128px
```

홀수 값 (`5px`, `7px`) 사용 금지. 항상 4px 배수.

### Color palette 최대 3개

```
--color-bg        # 배경
--color-text      # 본문
--color-accent    # 강조 (CTA, 링크)
```

추가 색은:
- `--color-success/warning/error` (의미 색)
- `--color-text-muted` (보조 텍스트, --color-text의 lightness만 다른 변형)

5개 이상의 brand color = 디자인 무너짐.

---

## 출처 및 참고

- claude-design-system-prompt: github.com/Trystan-SA/claude-design-system-prompt
- Impeccable: github.com/pbakaus/impeccable
- Refactoring UI: refactoringui.com (책)
- Practical Typography: practicaltypography.com
