---
name: slides
description: >
  Use when the user wants to build a presentation deck as a single self-contained
  HTML file — triggers "슬라이드 만들어", "발표자료 만들어", "피치덱 만들어", "프레젠테이션 만들어",
  "pitch deck", "slide deck", "presentation slides", "html slides", or /slides.
  Produces a zero-dependency 16:9 HTML deck (one file, embedded CSS+JS, no build,
  no npm, no reveal.js) using the 3-visual-style-preview-then-pick flow — generate
  three single-slide style previews first, the user picks one, then the whole deck
  is rendered in that tone. Includes keyboard nav (arrows/space/F/Esc), print-to-PDF
  via CSS @page landscape, Pretendard for Korean, density caps, and anti-slop rules
  (no emoji bullets, monotone tinted-neutral palette, max 3 colors). Different from
  /design-html (general one-off pages) and /design-shotgun (design variant
  exploration) — this is specifically presentation decks.
version: 1.0.0
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - AskUserQuestion
compatibility: [claude-code]
---

# /slides

단일 HTML 파일 = 전체 덱. 빌드·npm·reveal.js 의존성 0. 섹션 하나가 슬라이드 하나.
16:9 고정, 임베디드 CSS/JS, 키보드 내비, 브라우저 print 로 PDF.

## When to use / boundaries

쓸 때:
- "슬라이드/발표자료/피치덱/프레젠테이션 만들어", "pitch deck", "slide deck", "html slides", `/slides`
- 발표·리뷰·제안용 산출물을 **브라우저에서 넘기며** 보여주고 PDF 로 내보내야 할 때
- `app-dev-orchestrator` / `office-hours` 산출 요약을 덱으로 만들 때

쓰지 말 것 (다른 skill 로):
| 요청 | 올바른 skill |
|---|---|
| 일반 1회성 HTML 리포트/스펙 | `/design-html`, `html-default-output` |
| 디자인 variant 여러 개 탐색·비교 | `/design-shotgun` |
| 디자인 시스템/토큰 정립 | `design-system-keeper` |
| 실제 .pptx 파일 생성 (python-pptx) | `office-docs` |
| 텍스트 어투 다듬기 | `human-voice-guard` |

이 skill 은 **HTML 덱 전용**. .pptx 가 필요하면 `office-docs` 로 위임.

## 선행 체크

```bash
# 출력 폴더 준비 + 한글 폰트 전략 결정 (Pretendard CDN 사용 여부)
OUT="${SLIDES_OUT:-./slides}"; mkdir -p "$OUT"
echo "OUT=$OUT"
# Chromium 계열 존재 확인 (헤드리스 PDF 자동화에 필요; 없으면 수동 print 안내)
for b in chrome chromium chromium-browser msedge "/c/Program Files/Google/Chrome/Application/chrome.exe" "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"; do
  command -v "$b" >/dev/null 2>&1 && { echo "BROWSER=$b"; break; }
done
```

브라우저가 안 잡히면 자동 PDF 는 건너뛰고 "브라우저에서 Ctrl+P → 대상: PDF 저장" 으로 안내한다.

## Workflow

### 1. 콘텐츠 인테이크 (질문은 한 번에)

발표 내용을 받되 모르면 `AskUserQuestion` 으로 묶어서 1회만 묻는다:
- 청중 (투자자 / 경영진 / 개발자 / 일반) — 정보 밀도·전문용어 수위 결정
- 목적 (설득·투자유치 / 현황보고 / 교육 / 제품소개)
- 분량 목표 (5·10·15·20장)
- 언어 (한국어 / 영어 / 혼용)

콘텐츠를 **섹션 트리**로 먼저 정리한다 (슬라이드 1장 = 1 메시지). 표지·목차·본문 N·마무리.

### 2. 3-style preview → pick (필수, show-don't-tell)

전체 덱을 만들기 전에 **단 한 장(표지+대표 본문 1장)** 을 3가지 톤으로 만들어 사용자가 고르게 한다.
바로 전체를 만들지 않는다 (`simon-design-first` show-don't-tell 패턴).

3가지 기본 프리셋 (모두 monotone tinted-neutral, accent 1색):

| 스타일 | accent | 분위기 | 적합 |
|---|---|---|---|
| **A. Editorial** | `#3b3a52` (ink violet) | 차분·문서형, 큰 여백 | 경영진·보고 |
| **B. Keynote** | `#2563eb` (calm blue) | 대비 강·큰 타이포 | 투자자·발표 |
| **C. Mono-tech** | `#0f766e` (teal) | 그리드·모노스페이스 라벨 | 개발자·기술 |

미리보기 생성 후 사용자에게 보여주는 방법:

```bash
# 3개 프리뷰를 한 파일에 담아 한 번에 비교 (각 .preview 블록 = 한 스타일 한 슬라이드)
"$BROWSER" "$OUT/style-preview.html" 2>/dev/null || echo "브라우저에서 $OUT/style-preview.html 열기"
```

```text
A / B / C 중 어떤 톤으로 갈까요? (또는 accent 색·폰트 바꿔서 다시 보여드릴까요?)
```

사용자가 "알아서" 하면 청중 기준으로 자동 선택(보고=A, 투자=B, 기술=C)하고 한 줄 고지한다.

### 3. 선택된 톤으로 전체 덱 렌더

아래 스켈레톤에 토큰(accent·폰트)만 주입하고, 섹션을 `<section class="slide">` 로 펼친다.
밀도 규칙(아래)을 각 슬라이드에 적용. 한 파일로 `$OUT/deck.html` 저장.

### 4. 검증 (열기 + print preview)

```bash
# 1) 슬라이드 수 = 의도한 분량인지
grep -c '<section class="slide"' "$OUT/deck.html"
# 2) 브라우저에서 키보드 내비 확인 (→/←/Space/F/Esc)
"$BROWSER" "$OUT/deck.html" 2>/dev/null || echo "브라우저에서 $OUT/deck.html 열기 → 화살표로 넘기기 확인"
# 3) 헤드리스 PDF (가로 A4, 배경 인쇄 포함). 브라우저 있을 때만.
"$BROWSER" --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$OUT/deck.pdf" "file://$(pwd)/$OUT/deck.html" 2>/dev/null \
  && echo "PDF=$OUT/deck.pdf" || echo "수동: 브라우저 Ctrl+P → 가로 → 배경그래픽 ON → PDF 저장"
```

확인 체크리스트:
- [ ] 첫 슬라이드가 16:9 안에 꽉 차고 잘리지 않음
- [ ] →/Space 다음, ←/Backspace 이전, F 풀스크린, Esc 종료, 숫자+Enter 점프 동작
- [ ] print preview 에서 한 슬라이드 = 한 페이지 (분할/공백 페이지 없음)
- [ ] 한글이 Pretendard 로 렌더 (네모/폴백 폰트 아님)

## 덱 스켈레톤 (복붙용)

토큰은 `:root` 의 `--accent` / 폰트만 교체. 슬라이드는 `<section class="slide">` 추가로 늘린다.

```html
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Deck</title>
<link rel="stylesheet" as="style" crossorigin
  href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<style>
:root{
  --accent:#2563eb;          /* 선택된 스타일의 accent 1색 */
  --bg:#f7f7fb; --surface:#ffffff;
  --text:#1b1b29;            /* pure black 금지 — violet tint */
  --muted:#6b6a83;
  --slide-w:1280px; --slide-h:720px;   /* 16:9 */
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:var(--bg);
  font-family:Pretendard,system-ui,-apple-system,"Segoe UI",sans-serif;
  color:var(--text);-webkit-font-smoothing:antialiased}
.deck{height:100%}
.slide{
  position:absolute;inset:0;display:none;
  width:var(--slide-w);height:var(--slide-h);
  margin:auto;left:0;right:0;top:0;bottom:0;
  padding:72px 88px;background:var(--surface);
  flex-direction:column;justify-content:center;gap:24px;
  /* 화면이 작으면 비율 유지하며 축소 */
  transform-origin:center center;
}
.slide.active{display:flex}
.slide h1{font-size:64px;font-weight:800;line-height:1.1;letter-spacing:-.02em}
.slide h2{font-size:40px;font-weight:700;line-height:1.2;letter-spacing:-.01em}
.kicker{font-size:18px;font-weight:600;color:var(--accent);
  text-transform:uppercase;letter-spacing:.08em}
.slide p,.slide li{font-size:24px;line-height:1.5;color:var(--text)}
.slide ul{list-style:none;display:flex;flex-direction:column;gap:14px}
.slide li{position:relative;padding-left:28px}
.slide li::before{content:"";position:absolute;left:0;top:.62em;
  width:10px;height:2px;background:var(--accent)}  /* 대시 마커, 이모지 금지 */
.cover{justify-content:flex-end}
.cover h1{font-size:80px}
.cover .meta{color:var(--muted);font-size:20px;margin-top:8px}
.rule{height:3px;width:64px;background:var(--accent);border:0;margin:4px 0}
.pageno{position:absolute;right:40px;bottom:28px;color:var(--muted);
  font-size:14px;font-variant-numeric:tabular-nums}
.progress{position:fixed;top:0;left:0;height:3px;background:var(--accent);
  width:0;transition:width .25s ease;z-index:10}
/* 화면 맞춤: 슬라이드를 뷰포트에 letterbox 스케일 */
@media (max-aspect-ratio:1280/720){.slide{transform:scale(calc(100vw/1280))}}
@media (min-aspect-ratio:1280/720){.slide{transform:scale(calc(100vh/720))}}
/* ===== 인쇄: 슬라이드 = 페이지, 가로 ===== */
@page{size:1280px 720px;margin:0}
@media print{
  html,body{background:#fff;height:auto}
  .progress,.pageno{display:none}
  .slide{position:static!important;display:flex!important;
    transform:none!important;page-break-after:always;break-after:page;
    box-shadow:none;width:1280px;height:720px;margin:0}
  /* 배경/accent 가 인쇄에 남도록 */
  *{-webkit-print-color-adjust:exact;print-color-adjust:exact}
}
</style>
</head>
<body>
<div class="progress" id="prog"></div>
<div class="deck" id="deck">

  <section class="slide cover active">
    <span class="kicker">2026 · Simon Kim</span>
    <h1>발표 제목</h1>
    <div class="meta">부제 · 발표자 · 날짜</div>
  </section>

  <section class="slide">
    <span class="kicker">목차</span>
    <h2>오늘 다룰 내용</h2>
    <hr class="rule">
    <ul>
      <li>문제 정의</li>
      <li>접근 방법</li>
      <li>결과와 다음 단계</li>
    </ul>
  </section>

  <section class="slide">
    <span class="kicker">01 · 문제</span>
    <h2>핵심 메시지 한 줄</h2>
    <hr class="rule">
    <p>슬라이드 1장 = 1 메시지. 본문은 근거 3개 이내.</p>
    <ul>
      <li>근거 또는 데이터 포인트</li>
      <li>근거 또는 데이터 포인트</li>
    </ul>
  </section>

</div>

<script>
(function(){
  const slides=[...document.querySelectorAll('.slide')];
  let i=slides.findIndex(s=>s.classList.contains('active'));
  if(i<0)i=0;
  const prog=document.getElementById('prog');
  let jump='';
  function render(){
    slides.forEach((s,n)=>s.classList.toggle('active',n===i));
    prog.style.width=((i+1)/slides.length*100)+'%';
    const cur=slides[i];
    let pn=cur.querySelector('.pageno');
    if(!pn){pn=document.createElement('div');pn.className='pageno';cur.appendChild(pn);}
    pn.textContent=(i+1)+' / '+slides.length;
    location.hash=i+1;
  }
  function go(d){i=Math.max(0,Math.min(slides.length-1,i+d));render();}
  document.addEventListener('keydown',e=>{
    if(['ArrowRight',' ','PageDown'].includes(e.key)){e.preventDefault();go(1);}
    else if(['ArrowLeft','Backspace','PageUp'].includes(e.key)){e.preventDefault();go(-1);}
    else if(e.key==='Home'){i=0;render();}
    else if(e.key==='End'){i=slides.length-1;render();}
    else if(e.key==='f'||e.key==='F'){document.fullscreenElement
      ?document.exitFullscreen():document.documentElement.requestFullscreen();}
    else if(e.key==='Escape'&&document.fullscreenElement){document.exitFullscreen();}
    else if(/[0-9]/.test(e.key)){jump+=e.key;}
    else if(e.key==='Enter'&&jump){i=Math.min(slides.length-1,Math.max(0,(+jump)-1));jump='';render();}
  });
  // 클릭/탭: 오른쪽 절반 다음, 왼쪽 절반 이전
  document.addEventListener('click',e=>{
    if(e.target.closest('a'))return;
    (e.clientX > innerWidth/2)?go(1):go(-1);
  });
  const h=parseInt(location.hash.slice(1),10);
  if(h){i=Math.min(slides.length-1,Math.max(0,h-1));}
  render();
})();
</script>
</body>
</html>
```

## 콘텐츠 밀도 규칙 (정보위계 / no-overload)

| 항목 | 상한 | 비고 |
|---|---|---|
| 슬라이드당 메시지 | 1 | 제목이 곧 결론(assertion-evidence) |
| 본문 bullet | ≤ 5 | 6개↑면 슬라이드 분리 |
| bullet당 단어 | 한국어 ≤ 14자 / 영어 ≤ 9 words | 문장 통째로 금지 |
| 텍스트 위계 단계 | 3 (kicker → h2 → body) | 4단계↑면 과밀 |
| 본문 폰트 | ≥ 24px | 뒤에서 읽힘 보장 |
| 표 행 | ≤ 6 | 초과 시 강조행만 |

발표는 "읽는 문서"가 아니다. 말로 할 내용은 발표자 노트(`<!-- note: ... -->` 주석)로 빼고 슬라이드엔 키워드만.

## Anti-slop (반드시 준수)

- **이모지 불릿 금지** — `🚀 ✅ 💡` 같은 아이콘 불릿 쓰지 않는다. 대시(`–`) 마커만.
- **모노톤 팔레트** — accent 1색 + text + bg, 총 3색 이내. multi-color 금지.
- **pure black/gray 금지** — `#000`/`#888` 대신 violet-tinted neutral (`--text:#1b1b29`).
- **Inter 금지** — 영문도 Pretendard 또는 중립 산세리프. 한글은 Pretendard 기본.
- **bounce/elastic 전환 금지** — 부드러운 cut 또는 fade. 즉각 cut 도 OK, 튕김은 금지.
- **장식 요소 금지** — 의미 없는 도형·그라데이션·드롭섀도 남발 금지. 여백으로 위계.
- **버전 접미사 난립 금지** — `final/v2/candidate` 파일 혼재 금지. `deck.html` 하나로.
- 표지 외 모든 슬라이드는 **제목이 주장(결론)** 이어야 한다 ("매출 현황" X → "Q2 매출 32% 성장" O).

## Anti-patterns (하지 말 것)

- reveal.js / Spectacle / Marp / Slidev 등 **외부 런타임 도입** — 이 skill 은 zero-dep 가 핵심. 끌어오지 말 것.
- CDN JS 프레임워크 `<script src>` 추가 — 폰트 CSS 1개(Pretendard) 외 외부 의존 금지.
- 3-style preview 건너뛰고 바로 전체 덱 생성 — show-don't-tell 위반.
- `transform:scale` 빼고 고정 1280px → 작은 화면에서 스크롤 발생.
- `@page` / print-color-adjust 누락 → PDF 에서 accent·배경 날아감.
- 한 슬라이드에 문단 통째 → 밀도 규칙 위반(청중 이탈).
- `git add -A` 로 `style-preview.html`·`deck.pdf` 까지 휩쓸어 커밋 (명시 경로만 stage).

## 실패 시

- 브라우저 미탐지 → 자동 PDF 생략, "Ctrl+P → 가로 → 배경그래픽 ON → PDF 저장" 안내.
- Pretendard CDN 차단(오프라인) → `font-family` 를 `system-ui` 폴백으로 두고 한 줄 고지.
- 분량 초과(슬라이드 30장↑) → 섹션을 덱 2개로 분할 제안.

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
