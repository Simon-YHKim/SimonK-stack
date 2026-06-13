---
name: design-system-page
description: >
  Use when the user wants a full design-system catalog page or a printable
  brand book from an existing design source — triggers "디자인 시스템 만들어",
  "브랜드 북 만들어", "스타일 가이드 페이지", "design system page",
  "brand book pdf", "style guide html", or /design-system-page. Reads
  design.md / DESIGN.md (or a user-supplied brand reference), extracts tokens
  (color, type, spacing, radius, shadow), then writes a self-contained
  design-system.html (palette swatches, type scale, spacing ramp, component
  gallery, logo/icon grid) with inline CSS + inline SVG and a Google Fonts CDN
  link — zero build. Finally renders an A4 brand-book PDF via headless chromium
  (chrome/edge --headless --print-to-pdf). Different from /simon-design-first
  (intake interview) and /design-html (one-off page) — this produces a
  reference catalog plus a printable book from tokens that already exist.
version: 1.1.0
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
compatibility: [claude-code]
---

# design-system-page

기존 디자인 소스(`design.md` / `DESIGN.md`)나 사용자가 준 브랜드 reference 에서
**토큰을 추출 → design-system.html 카탈로그 → A4 brand-book PDF** 까지
한 번에 뽑아낸다. 빌드 도구 없음(zero build): 인라인 CSS/SVG + Google Fonts CDN.
PDF 는 헤드리스 크로미움 print-to-pdf 로 렌더.

## When to use / boundaries

쓰는 경우:
- 프로젝트에 이미 `design.md`/`DESIGN.md` 가 있고, 팀·외주·인쇄용으로 보여줄
  **시각 카탈로그 1장 + 인쇄용 책자**가 필요할 때
- 토큰(색·폰트·간격)이 코드 곳곳에 흩어져 있어 한곳에 모아 보고 싶을 때
- `founder-context` 의 `design.md` 산출 직후, 그 토큰을 시각화하고 싶을 때

쓰지 않는 경우 (다른 skill 로):
- 디자인 방향이 아직 없다 → `simon-design-first` (진단·레퍼런스·방향 먼저)
- 토큰을 처음 정하고 영속화·드리프트 감시 → `design-system-keeper`
- 랜딩/제품 페이지 1장 production HTML → `/design-html`
- 데이터/config 스키마 일관성 → `consistency-guard`

전제: **토큰이 이미 존재**해야 한다. 없으면 이 skill 은 멈추고
`simon-design-first` 로 보낸다 (아래 1단계 참조).

## 선행 체크 (precheck)

```bash
# 1) 디자인 소스 탐색 — 우선순위: design.md > DESIGN.md > docs/DESIGN.md
SRC=""
for f in design.md DESIGN.md docs/design.md docs/DESIGN.md .design-system/system.md; do
  [ -f "$f" ] && SRC="$f" && break
done
[ -n "$SRC" ] && echo "SOURCE_OK: $SRC" || echo "NO_SOURCE — run simon-design-first first, or pass a brand reference"

# 2) 헤드리스 브라우저 1개라도 있는지 (PDF 렌더용)
#    Windows: full path 필요 (PATH 에 없음). Linux/mac: chromium / google-chrome.
CHROME=""
for c in \
  "/c/Program Files/Google/Chrome/Application/chrome.exe" \
  "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
  "$(command -v google-chrome 2>/dev/null)" \
  "$(command -v chromium 2>/dev/null)"; do
  [ -x "$c" ] && CHROME="$c" && break
done
[ -n "$CHROME" ] && echo "BROWSER_OK: $CHROME" || echo "NO_BROWSER — HTML still works; PDF step will be skipped"
```

소스도 없고 reference 도 못 받으면 진행하지 말 것. 브라우저가 없으면
HTML 은 만들되 PDF 단계는 건너뛰고 "수동 인쇄(Ctrl+P → PDF)" 안내.

> Windows 경로는 Bash 에서 `/c/Program Files/...` (forward slash) 로 쓴다.
> PowerShell 에서는 `& "C:\Program Files\Google\Chrome\Application\chrome.exe"`.

## Workflow

### 1. 소스 확정 + 토큰 추출

`design.md` (founder-context 포맷) 에서 뽑는 토큰 매핑:

| design.md 섹션 | 추출 토큰 | HTML 에서 쓰임 |
|---|---|---|
| `## Palette` 표 (Accent/Text/Background) | `--accent`, `--text`, `--bg` | 스와치, 본문, 배경 |
| `## Fonts` (한국어/영문/제목용) | `--font-ko`, `--font-en`, `--font-display` | 타입 스케일, `<link>` |
| `## Tone` (한 단어) | `tone` 라벨 | 표지·헤더 카피 |
| `## References` (URL 3-5) | reference 링크 | 부록 페이지 |
| `## 금지` / `## Approved 패턴` | do/don't 리스트 | 가이드라인 페이지 |

design.md 에 **없는** 토큰(spacing/radius/shadow)은 다음 기본 ramp 로 채우고
"기본값 적용 — design.md 에 추가 권장" 이라고 표시한다:

```
spacing: 4 8 12 16 24 32 48 64 96   (px, 4px base scale)
radius:  4 8 12 16 999(pill)
shadow:  sm  0 1px 2px rgba(15,14,26,.06)
         md  0 4px 12px rgba(15,14,26,.10)
         lg  0 12px 32px rgba(15,14,26,.14)
type:    12 14 16 18 24 32 48 64     (px, 1.25 modular scale)
```

코드에 흩어진 색을 역추출할 때 (소스가 thin 할 경우):

```bash
# 컴포넌트/CSS 에서 실제 사용된 hex 색 상위 빈도 — design.md 누락 보강용
grep -rhoiE '#[0-9a-f]{6}\b' src app components styles 2>/dev/null \
  | tr 'A-F' 'a-f' | sort | uniq -c | sort -rn | head -12
```

### 2. design-system.html 작성 (인라인, zero build)

규칙:
- **단일 파일**. 외부 의존은 Google Fonts `<link>` 하나만. JS 없음.
- 색은 모두 `:root` CSS 변수로. 본문에서 hex 직접 쓰지 않음.
- 아이콘은 **인라인 SVG** (이모지 금지 — 전역 CLAUDE.md AI-slop 규칙).
- `@media print` + `@page { size: A4; margin: 14mm }` 로 인쇄 레이아웃 동시 지원.
- 섹션 순서: 표지 → 팔레트 → 타입 스케일 → 간격/radius/shadow → 컴포넌트
  갤러리(버튼·인풋·카드·뱃지) → 로고/아이콘 그리드 → do/don't → reference 부록.

스캐폴드 (이 골격을 토큰으로 채운다):

```html
<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>Design System — {{PROJECT}}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<!-- 한국어: Pretendard CDN (Google Fonts 미제공) -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<style>
  :root{
    --accent:#5B4FE0; --text:#1A1830; --bg:#FBFAFF;   /* design.md Palette */
    --font-ko:'Pretendard',sans-serif;
    --font-en:'Plus Jakarta Sans',sans-serif;
    --r-md:12px; --sh-md:0 4px 12px rgba(15,14,26,.10);
    --sp-4:16px; --sp-6:32px;
  }
  *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--text);
    font-family:var(--font-ko);line-height:1.6}
  .page{max-width:880px;margin:0 auto;padding:var(--sp-6)}
  .swatch{display:inline-flex;flex-direction:column;gap:8px;margin:8px}
  .swatch i{display:block;width:120px;height:80px;border-radius:var(--r-md);
    box-shadow:var(--sh-md)}
  .btn{font:600 16px var(--font-en);padding:10px 20px;border-radius:var(--r-md);
    border:0;background:var(--accent);color:#fff;cursor:pointer}
  .card{padding:24px;border-radius:var(--r-md);background:#fff;
    box-shadow:var(--sh-md)}
  @page{size:A4;margin:14mm}
  @media print{ .page{max-width:none;padding:0} a{color:inherit} }
</style></head>
<body>
<section class="page">
  <h1>{{PROJECT}} Design System</h1>
  <p>Tone: {{TONE}} · Generated {{DATE}}</p>

  <h2>Palette</h2>
  <div class="swatch"><i style="background:var(--accent)"></i><code>--accent #5B4FE0</code></div>
  <div class="swatch"><i style="background:var(--text)"></i><code>--text #1A1830</code></div>
  <div class="swatch"><i style="background:var(--bg);border:1px solid #eee"></i><code>--bg #FBFAFF</code></div>

  <h2>Type scale</h2>
  <p style="font-size:48px">48 / Display</p>
  <p style="font-size:24px">24 / Heading</p>
  <p style="font-size:16px">16 / Body 본문 한글 혼용</p>

  <h2>Components</h2>
  <button class="btn">Primary</button>
  <div class="card" style="margin-top:16px">카드 컴포넌트 — shadow md, radius md</div>

  <h2>Iconography (inline SVG)</h2>
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    stroke-width="2"><path d="M5 12l5 5 9-11"/></svg>
</body></html>
```

한국어 본문에는 `word-break: keep-all` 를 추가한다 (전역 규칙).

### 3. A4 brand-book PDF 렌더 (headless print-to-pdf)

Bash (Git Bash, Windows) — 절대경로 사용:

```bash
CHROME="/c/Program Files/Google/Chrome/Application/chrome.exe"   # precheck 결과로 치환
OUT="$(pwd)/design-system.pdf"
IN="file:///$(pwd | sed 's#^/c#C:#')/design-system.html"        # file:// URI

"$CHROME" --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$OUT" "$IN"

[ -f "$OUT" ] && echo "PDF_OK: $OUT ($(wc -c < "$OUT") bytes)" || echo "PDF_FAIL"
```

PowerShell 동등 명령:

```powershell
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$in  = "file:///" + ((Resolve-Path .\design-system.html).Path -replace '\\','/')
$out = (Join-Path (Get-Location) 'design-system.pdf')
& $chrome --headless --disable-gpu --no-pdf-header-footer "--print-to-pdf=$out" $in
```

플래그 메모:
- `--no-pdf-header-footer` — URL/날짜 머리말·꼬리말 제거 (브랜드 북엔 불필요).
- 머리말이 필요하면 빼고 `--print-to-pdf-no-header` 는 쓰지 말 것 (deprecated).
- 한국어 폰트(Pretendard)는 CDN 에서 로드되므로 **네트워크 필요**. 오프라인이면
  Pretendard 를 로컬 woff2 로 받아 `@font-face` 인라인 (`base64` 권장).
- 외부 폰트 로드 경쟁이 의심되면 `--virtual-time-budget=4000` 로 렌더 대기.

브라우저별 차이:

| 브라우저 | print-to-pdf | 비고 |
|---|---|---|
| Chrome (stable) | O | 1순위. `--headless=new` 도 가능 |
| Edge (msedge.exe) | O | 동일 플래그. Chrome 없을 때 fallback |
| Chromium (Linux) | O | `chromium`/`chromium-browser` |
| Firefox | X | print-to-pdf 미지원 → 사용 금지 |

### 4. 보고

- 생성 파일 절대경로 (HTML, PDF), PDF 바이트 크기.
- design.md 에서 **누락되어 기본값으로 채운 토큰** 목록 (spacing/radius/shadow 등).
- 다음 행동 제안: 누락 토큰을 `design.md` 에 역기입할지 1회 확인.

## 검증 (verification)

```bash
# 1) HTML 이 self-contained 인지 — 로컬 상대경로 의존 0건이어야 함
grep -nE '(src|href)="\.?/' design-system.html && echo "WARN: local dep found" \
  || echo "SELF_CONTAINED_OK"

# 2) 색은 변수로만 — 본문(:root 밖)에 raw hex 가 섞이지 않았는지 스폿체크
grep -nE '#[0-9a-fA-F]{6}' design-system.html | grep -v ':root' | head

# 3) PDF 가 실제로 생성됐고 비어있지 않은지
[ -s design-system.pdf ] && echo "PDF non-empty: $(wc -c < design-system.pdf) bytes" \
  || echo "PDF MISSING/EMPTY"

# 4) 눈 검증 — HTML 을 브라우저로 열어 A4 인쇄 미리보기 확인
#    (Windows) start design-system.html   (mac) open ...   (linux) xdg-open ...
```

PDF 페이지 수가 1장이면 섹션이 잘렸을 가능성 — `@page` 가 먹었는지, 콘텐츠가
한 화면에 압축됐는지 확인. 정상 브랜드 북은 보통 4-8 페이지.

## Anti-patterns

- ❌ 토큰 없이 시작 → "모던한 디자인 시스템" 같은 추측 생성. 반드시 소스 우선.
- ❌ 이모지를 아이콘으로 사용 → 인라인 SVG 만 (전역 AI-slop 규칙).
- ❌ 4색 이상 팔레트 → accent/text/bg 3색 + 파생 음영까지만.
- ❌ Inter 폰트 / pure `#000` / pure `#FFF` → Pretendard·tinted neutral.
- ❌ Firefox 로 PDF 시도 → print-to-pdf 미지원, 실패함.
- ❌ HTML 에 raw hex 직접 박기 → 토큰 드리프트. `:root` 변수만.
- ❌ 외부 JS/프레임워크 끌어오기 → zero build 깨짐. CSS+SVG 로 충분.
- ❌ 상대경로 폰트/이미지 → PDF 렌더 시 깨짐. CDN 또는 base64 인라인.
- ❌ 브라우저 없다고 전체 중단 → HTML 은 내고 PDF 만 수동 안내.

## Related skills

- `simon-design-first` — 방향이 없을 때 먼저. 이 skill 의 upstream.
- `founder-context` — `design.md` 산출. 이 skill 의 입력 소스.
- `design-system-keeper` — 토큰 영속화 + 드리프트 감사 (catalog 가 아닌 enforcement).
- `/design-html` — production 페이지 1장 (catalog 아님).
- `make-pdf` / `office-docs` — 일반 문서 PDF (브랜드 북 특화 아님).
