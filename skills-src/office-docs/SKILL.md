---
name: office-docs
description: >
  Use when the user wants native Office files generated programmatically — triggers "워드 문서 만들어", "엑셀 만들어", "PPT 만들어", "PDF 만들어", "보고서 docx로", "표 엑셀로 뽑아", "create docx", "create xlsx", "build a pptx", "generate office document", "export to PDF", or /office-docs. Produces real .docx / .xlsx / .pptx / .pdf files via python-docx (1.2.0), openpyxl (3.1.5), python-pptx (1.0.0), and weasyprint (69.0) — picking the format from the request, installing the prerequisite libs, running minimal working code, and verifying the output file exists and opens. Different from /design-html and /slides (web HTML), and /make-pdf gstack (markdown→PDF only). This emits binary Office formats Word/Excel/PowerPoint can open directly.
version: 1.0.0
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
compatibility: [claude-code]
---

# office-docs

네이티브 MS Office 파일(.docx / .xlsx / .pptx)과 .pdf 를 파이썬으로 생성한다. HTML 이 아니라 Word·Excel·PowerPoint 가 바로 여는 바이너리를 만든다.

## When to use / boundaries

쓸 때:
- "보고서를 워드로", "데이터를 엑셀 multi-sheet 로", "PPT 슬라이드 자동 생성", "HTML 을 PDF 로"
- 생산기술 산출물 자동화: UPH/tact 분석표(xlsx), 설비 점검 보고서(docx), 리뷰 deck(pptx)

쓰지 말 것 (다른 skill 로):
- 웹에서 보는 HTML 산출물 → `/design-html`, `html-default-output`
- 발표용 HTML 슬라이드(브라우저) → `/slides`
- 마크다운 → PDF 단순 변환 → `make-pdf` (gstack)
- python-pptx 로 안 되는 고급 그래픽/애니메이션 → Canva MCP 또는 디자이너

| 원하는 결과 | 라이브러리 | 확장자 |
|---|---|---|
| Word 문서 (제목/문단/표) | python-docx | .docx |
| Excel (셀/수식/multi-sheet/차트) | openpyxl | .xlsx |
| PowerPoint (슬라이드/텍스트박스/표) | python-pptx | .pptx |
| 인쇄용 PDF (스타일 풍부) | weasyprint (HTML→PDF) | .pdf |
| PDF (이미 만든 docx 에서) | LibreOffice headless 변환 | .pdf |

## 0. 필수 사전 설치 (PREREQUISITE — 생략 금지)

코드 실행 전에 **반드시** 필요한 라이브러리를 깐다. 한 줄:

```bash
pip install "python-docx>=1.2.0" "openpyxl>=3.1.5" "python-pptx>=1.0.0" "weasyprint>=69.0"
```

import 이름 주의 (패키지명 != import명):

| pip 패키지 | import 구문 | 비고 |
|---|---|---|
| python-docx | `from docx import Document` | `pip install docx` 는 **다른 패키지** — 설치 금지 |
| openpyxl | `from openpyxl import Workbook` | 동일 |
| python-pptx | `from pptx import Presentation` | |
| weasyprint | `from weasyprint import HTML` | 네이티브 의존성 있음(아래) |

설치 확인:

```bash
python -c "import docx, openpyxl, pptx; print('docx', docx.__version__ if hasattr(docx,'__version__') else 'ok'); print('openpyxl', openpyxl.__version__); print('pptx', pptx.__version__)"
```

### ⚠️ Windows 의 weasyprint = GTK/Pango 필요

weasyprint 는 텍스트 렌더링에 **Pango / GDK-PixBuf / Cairo (GTK 스택)** 의 네이티브 DLL 을 요구한다. `pip install weasyprint` 만으로는 Windows 에서 `cannot load library 'libgobject-2.0-0'` 같은 에러가 난다.

Windows 해결 (택1):
1. **MSYS2 GTK3 설치 후 PATH 추가** (weasyprint 공식 권장):
   ```bash
   # MSYS2 설치 후 MSYS2 셸에서:
   pacman -S mingw-w64-x86_64-pango
   # 그 다음 C:\msys64\mingw64\bin 을 시스템 PATH 에 추가하고 셸 재시작
   ```
2. **GTK3 runtime installer** (tschoonj/GTK-for-Windows-Runtime-Environment-Installer) 실행 → PATH 자동 등록.
3. **회피책**: PDF 가 목적이고 GTK 설치가 막히면 weasyprint 대신
   - docx/pptx 를 만든 뒤 **LibreOffice headless** 로 PDF 변환 (8절), 또는
   - `make-pdf` (gstack, 마크다운→PDF) 사용.

검증:
```bash
python -c "from weasyprint import HTML; print('weasyprint OK')"
```
이게 실패하면 PDF 단계만 건너뛰고 docx/xlsx/pptx 는 정상 진행. 어느 단계에서 막혔는지 사용자에게 명시한다.

## 1. 워크플로

1. 요청에서 **형식 결정** (위 표). 명시 없으면: 표·숫자 위주→xlsx, 서술형 보고서→docx, 발표→pptx, 인쇄/배포→pdf.
2. 0절 설치 + 확인. weasyprint 가 필요한데 GTK 미설치면 사용자에게 고지하고 대안 제시.
3. 출력 경로를 **절대경로**로 정하고 생성 스크립트를 `Write` 로 떨군 뒤 `python` 실행. (인라인 `-c` 보다 재실행·디버깅 쉬움)
4. **검증**(7절): 파일 존재 + 크기 > 0 + 가능하면 다시 열어 내용 확인.
5. 한국어 문서면 폰트 처리(6절).

## 2. Word — python-docx (최소 작동 예제)

```python
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# 제목 (built-in 스타일 Heading 0~9)
doc.add_heading("설비 가동 분석 보고서", level=0)
doc.add_heading("1. 요약", level=1)

# 문단 + 인라인 서식
p = doc.add_paragraph("프레스 라인 ")
run = p.add_run("UPH 1,240")
run.bold = True
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
p.add_run(" 달성, 목표 대비 +4%.")
p.alignment = WD_ALIGN_PARAGRAPH.LEFT

# 불릿 / 번호 (built-in 스타일명)
doc.add_paragraph("병목: 조립 3 스테이션", style="List Bullet")
doc.add_paragraph("개선안: by-pass 라인 추가", style="List Number")

# 표
tbl = doc.add_table(rows=1, cols=3)
tbl.style = "Light Grid Accent 1"
hdr = tbl.rows[0].cells
hdr[0].text, hdr[1].text, hdr[2].text = "라인", "tact(s)", "UPH"
for line, tact, uph in [("A", "2.9", "1240"), ("B", "3.4", "1058")]:
    c = tbl.add_row().cells
    c[0].text, c[1].text, c[2].text = line, tact, uph

doc.add_page_break()
doc.save(r"E:\Coding Infra\out\report.docx")
print("saved report.docx")
```

핵심 API: `Document()`, `add_heading(text, level)`, `add_paragraph(text, style)`, `para.add_run().bold/italic/font`, `add_table(rows, cols)` + `table.add_row()`, `add_picture(path, width=Inches(n))`, `add_page_break()`, `doc.save(path)`. 단위는 `Pt`, `Inches`, `Cm` 헬퍼로.

## 3. Excel — openpyxl (셀/수식/multi-sheet)

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = Workbook()
ws = wb.active
ws.title = "UPH"

# 헤더 + 스타일
headers = ["라인", "tact(s)", "가동시간(h)", "UPH"]
hdr_fill = PatternFill("solid", fgColor="1A1A2E")
hdr_font = Font(bold=True, color="FFFFFF")
for col, h in enumerate(headers, start=1):
    c = ws.cell(row=1, column=col, value=h)
    c.fill, c.font = hdr_fill, hdr_font
    c.alignment = Alignment(horizontal="center")

# 데이터 + 수식 (UPH = 3600 / tact)
rows = [("A", 2.9, 20), ("B", 3.4, 20), ("C", 4.1, 18)]
for i, (line, tact, hrs) in enumerate(rows, start=2):
    ws.cell(row=i, column=1, value=line)
    ws.cell(row=i, column=2, value=tact)
    ws.cell(row=i, column=3, value=hrs)
    ws.cell(row=i, column=4, value=f"=ROUND(3600/B{i},0)")  # 실제 수식

# 열 너비 자동 비슷하게
for col in range(1, 5):
    ws.column_dimensions[get_column_letter(col)].width = 14

# 두 번째 시트 (multi-sheet)
ws2 = wb.create_sheet("요약")
ws2["A1"] = "평균 UPH"
ws2["B1"] = "=AVERAGE(UPH!D2:D4)"  # 시트 간 참조

wb.save(r"E:\Coding Infra\out\analysis.xlsx")
print("saved analysis.xlsx")
```

핵심 API: `Workbook()`, `wb.active`, `wb.create_sheet(name)`, `ws.cell(row, column, value)` 또는 `ws["A1"]`, `=` 로 시작하면 **수식**, `styles.Font/PatternFill/Alignment/Border`, `column_dimensions[L].width`, `ws.freeze_panes="A2"`, `wb.save(path)`. 차트는 `openpyxl.chart.BarChart` + `Reference`.

## 4. PowerPoint — python-pptx (슬라이드/텍스트박스)

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

prs = Presentation()  # 16:9 기본은 prs.slide_width/height 로 지정 가능

# 슬라이드 1: 제목 레이아웃(layouts[0])
slide = prs.slides.add_slide(prs.slide_layouts[0])
slide.shapes.title.text = "설비 가동 리뷰"
slide.placeholders[1].text = "2026 Q2 · 생산기술"

# 슬라이드 2: 빈 레이아웃(layouts[6]) + 직접 텍스트박스
blank = prs.slides.add_slide(prs.slide_layouts[6])
box = blank.shapes.add_textbox(Inches(0.7), Inches(0.7), Inches(8.5), Inches(1))
tf = box.text_frame
tf.text = "핵심 지표"
tf.paragraphs[0].font.size = Pt(28)
tf.paragraphs[0].font.bold = True
tf.paragraphs[0].font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
p = tf.add_paragraph()
p.text = "UPH 1,240 (+4% vs 목표)"
p.font.size = Pt(18)

# 표 추가
rows, cols = 3, 2
tbl = blank.shapes.add_table(rows, cols, Inches(0.7), Inches(2.2),
                             Inches(5), Inches(1.5)).table
tbl.cell(0, 0).text, tbl.cell(0, 1).text = "라인", "UPH"
tbl.cell(1, 0).text, tbl.cell(1, 1).text = "A", "1240"
tbl.cell(2, 0).text, tbl.cell(2, 1).text = "B", "1058"

prs.save(r"E:\Coding Infra\out\deck.pptx")
print("saved deck.pptx")
```

레이아웃 인덱스(기본 템플릿): 0=Title, 1=Title+Content, 5=Title Only, 6=Blank. 핵심 API: `Presentation()`, `slides.add_slide(slide_layout)`, `shapes.title`, `placeholders[idx]`, `shapes.add_textbox(l,t,w,h).text_frame`, `text_frame.add_paragraph()`, `shapes.add_table(...).table`, `shapes.add_picture(path,l,t,w,h)`, `prs.save(path)`.

## 5. PDF — weasyprint (HTML→PDF)

```python
from weasyprint import HTML

html = """
<!doctype html><html><head><meta charset="utf-8"><style>
  @page { size: A4; margin: 18mm; }
  body { font-family: 'Malgun Gothic', 'Pretendard', sans-serif; color:#1a1a2e; }
  h1 { font-size: 22pt; border-bottom: 2px solid #1a1a2e; padding-bottom:6px; }
  table { width:100%; border-collapse:collapse; margin-top:12px; }
  th,td { border:1px solid #ccc; padding:6px 10px; text-align:left; }
  th { background:#1a1a2e; color:#fff; }
</style></head><body>
  <h1>설비 가동 분석 보고서</h1>
  <p>프레스 라인 <strong>UPH 1,240</strong> 달성 (목표 대비 +4%).</p>
  <table><tr><th>라인</th><th>tact(s)</th><th>UPH</th></tr>
    <tr><td>A</td><td>2.9</td><td>1240</td></tr>
    <tr><td>B</td><td>3.4</td><td>1058</td></tr></table>
</body></html>
"""
HTML(string=html).write_pdf(r"E:\Coding Infra\out\report.pdf")
print("saved report.pdf")
```

`HTML(string=...)` 또는 `HTML(filename="page.html")` 또는 `HTML(url=...)`. CSS `@page` 로 용지/여백, `@media print` 적용됨. 한국어는 시스템 한글 폰트(`Malgun Gothic`)를 `font-family` 에 명시.

## 6. 한국어 폰트 처리

- **docx/pptx/xlsx**: 폰트는 **여는 PC** 가 렌더하므로 Windows 기본 `맑은 고딕`(Malgun Gothic)·`나눔고딕`을 run/cell font.name 에 지정하면 안전. 별도 임베드 불필요.
  ```python
  run.font.name = "맑은 고딕"          # python-docx
  # 동아시아 폰트는 rPr 의 eastAsia 속성도 맞춰야 일부 Word 에서 정상:
  from docx.oxml.ns import qn
  run._element.rPr.rFonts.set(qn('w:eastAsia'), "맑은 고딕")
  ```
- **PDF(weasyprint)**: 렌더 시점에 폰트가 박히므로 `font-family` 에 시스템에 실재하는 한글 폰트명을 써야 □□ 안 깨짐.

## 7. 검증 (필수)

생성 후 **반드시** 파일이 실제로 만들어졌고 비어있지 않은지 확인한다.

```bash
# 존재 + 크기(0 이면 실패)
python - <<'PY'
import os
for f in [r"E:\Coding Infra\out\report.docx",
          r"E:\Coding Infra\out\analysis.xlsx",
          r"E:\Coding Infra\out\deck.pptx"]:
    print(f, os.path.getsize(f), "bytes" if os.path.exists(f) else "MISSING")
PY
```

내용 round-trip 확인 (열어서 다시 읽기):
```bash
python - <<'PY'
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation
print("docx paras:", len(Document(r"E:\Coding Infra\out\report.docx").paragraphs))
print("xlsx sheets:", load_workbook(r"E:\Coding Infra\out\analysis.xlsx").sheetnames)
print("pptx slides:", len(Presentation(r"E:\Coding Infra\out\deck.pptx").slides))
PY
```

사용자 눈으로 확인: `start "" "E:\Coding Infra\out\report.docx"` (Windows, 기본 앱으로 열기). 산출물 **절대경로**를 사용자에게 전달한다.

## 8. docx/pptx → PDF (weasyprint 가 막힐 때 대안)

GTK 설치가 안 되거나 docx 의 레이아웃 그대로 PDF 가 필요하면 LibreOffice headless 변환:

```bash
# soffice 가 PATH 에 있어야 함 (LibreOffice 설치)
soffice --headless --convert-to pdf --outdir "E:\Coding Infra\out" "E:\Coding Infra\out\report.docx"
```

## 안티패턴 (하지 말 것)

- ❌ `pip install docx` — python-docx 가 아닌 **방치된 다른 패키지**. 반드시 `python-docx`.
- ❌ openpyxl 에서 `f"=SUM(...)"` 결과값을 코드가 계산해 줄 거라 기대 — openpyxl 은 **수식 문자열만 저장**, 계산은 Excel 이 연다. 계산값이 필요하면 직접 파이썬으로 계산해 값으로 넣거나 `data_only=True` 로 (이미 계산된) 파일을 읽기.
- ❌ Windows 에서 weasyprint GTK 미설치 상태로 PDF 생성 강행 후 에러 무시 — 먼저 0절 검증, 실패 시 8절/`make-pdf` 로 폴백.
- ❌ 한국어 PDF 에서 `font-family: Inter/Arial` 만 지정 → 한글 □□ 깨짐. 시스템 한글 폰트 명시.
- ❌ 상대경로로 저장 후 "어디 갔지" — 항상 절대경로 + 7절 검증.
- ❌ docx run 의 스타일을 `paragraph.style` 로만 주고 인라인 서식 무시 — bold/size 는 `run.font` 에.
- ❌ 거대한 인라인 `python -c "..."` 한 줄 — 멀티라인은 `Write` 로 스크립트 파일 만든 뒤 실행(디버깅·재실행 용이).

## Operational notes

- 외부 의존: python-docx/openpyxl/python-pptx (순수 파이썬, 무문제) · weasyprint (Windows 네이티브 GTK 필요) · soffice (선택, PDF 폴백).
- 실패 시: 어느 형식 단계에서 막혔는지 명시. weasyprint 만 막혔다면 나머지 3종은 정상 산출하고 PDF 는 폴백 안내.
- 산출물은 사용자가 직접 열 수 있는 절대경로 파일로 전달, 7절 검증 통과 후 보고.

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
