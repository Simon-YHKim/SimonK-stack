---
name: scientific-paper
description: >-
  Use when the user wants to write an academic paper in LaTeX — triggers "논문 작성", "LaTeX 수식", "학술 시각화", "BibTeX 인용", "arXiv 제출", "IEEE 논문", "peer review 형식", "scientific paper", "latex equations", "academic figures", "bibtex citations", "arxiv submission", or /scientific-paper. Produces a reproducible LaTeX project — document class choice (article / IEEEtran / acmart / Nature templates), sectioning, math via amsmath/amssymb, BibTeX or biblatex+biber citation workflow, vector figures exported from matplotlib/plotly (PDF/SVG), booktabs tables, a latexmk build, and an arXiv-ready tarball. Different from /document-generate (general docs) and /office-docs (Office formats) — this is academic-format specific.
version: 1.0.0
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebSearch
compatibility: [claude-code]
author: simon-stack
---

# scientific-paper

LaTeX 학술 논문 프로젝트를 **재현 가능하게** 세팅·작성하는 skill. 문서 클래스 선택 → 섹션·수식 → 인용 워크플로 → 벡터 그림 → 빌드(latexmk) → arXiv 제출 준비까지.

## When to use / boundaries

쓸 때:
- "논문 LaTeX로 써줘", "IEEE 양식으로", "arXiv 올릴 거", "수식·인용 정리"
- matplotlib/plotly 결과를 논문용 벡터 그림(PDF/SVG)으로 내보내야 할 때
- 인용이 깨지거나(`?` 표시), BibTeX/biber 빌드가 실패할 때

쓰지 말 것:
- 일반 문서·README → `/document-generate`
- Word/PowerPoint/Excel 산출물 → `/office-docs`
- 발표 슬라이드 → `/slides`
- 순수 수식 렌더 미리보기(논문 아님) → 그냥 KaTeX/MathJax

## 선행 체크 (toolchain)

```bash
# 로컬 TeX 설치 여부. 없으면 Docker/Overleaf 경로로 안내.
for t in latexmk pdflatex lualatex biber bibtex python; do
  command -v "$t" >/dev/null 2>&1 && echo "OK   $t" || echo "MISS $t"
done
latexmk --version 2>/dev/null | head -1
```

`latexmk`/`pdflatex` 가 MISS 면 둘 중 하나로 진행:

| 상황 | 경로 |
|---|---|
| 로컬 설치 가능 | TeX Live 2025 (`apt install texlive-full` / `winget install TeXLive` / MacTeX) |
| 설치 회피 | Docker `texlive/texlive:latest` 로 빌드만 (아래 §7) |
| 클라우드 협업 | Overleaf (TeX Live 2025 호환) — 빌드는 그쪽, 파일은 여기서 작성 |

> arXiv는 현재 **TeX Live 2025**(biblatex 3.20 / Biber 2.20 / bbl 3.3)와 2023을 둘 다 지원. 로컬도 2023+ 면 안전.

## 1. 문서 클래스 결정

질문 한 줄로 확정한 뒤 진행한다("어디 낼 거예요? IEEE/ACM/arXiv/Nature/일반?").

| 제출처 | `\documentclass` | 인용 스타일 | 비고 |
|---|---|---|---|
| 범용·프리프린트 | `article` (또는 `scrartcl`) | natbib + `plainnat` | 가장 유연, arXiv 무난 |
| IEEE 학회·저널 | `IEEEtran` | IEEEtran.bst (BibTeX) | `\documentclass[conference]{IEEEtran}` |
| ACM | `acmart` | **natbib 기본** + ACM-Reference-Format | `\documentclass[sigconf]{acmart}` |
| Nature 계열 | `sn-jnl` (Springer Nature) | sn-bibliography | 저널별 공식 템플릿 우선 |
| 학위논문 | `report`/`book` 또는 학교 클래스 | biblatex | 장(chapter) 구조 |

선택 기준:
- **arXiv만** 목표면 `article` + natbib 이 마찰 최소.
- **biblatex+biber** 는 한국어/유니코드·복잡 인용에 강하지만 arXiv에 `.bbl` 버전 호환을 맞춰야 함(§6 주의).
- 저널이 공식 템플릿(.cls)을 주면 **그걸 그대로** 쓴다. 클래스 자작 금지.

## 2. 프로젝트 레이아웃

arXiv는 **단일 디렉터리·서브폴더 비선호**라 처음부터 평평하게 둔다.

```
paper/
├── main.tex          # 본문 + preamble
├── refs.bib          # BibTeX 데이터베이스 (소스 오브 트루스)
├── figs/             # 작성 중에는 폴더 OK (제출 직전 평탄화)
│   ├── fig_loss.pdf
│   └── make_figs.py  # 그림 생성 스크립트 (재현성)
├── latexmkrc         # 빌드 설정
└── .gitignore        # 빌드 산출물 무시
```

`.gitignore`:

```gitignore
*.aux
*.log
*.out
*.bbl
*.blg
*.bcf
*.run.xml
*.fls
*.fdb_latexmk
*.toc
*.synctex.gz
main.pdf
```

## 3. main.tex preamble (article 예시)

```latex
\documentclass[11pt]{article}

% --- 인코딩·폰트 (pdflatex 기준) ---
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}

% --- 수식 ---
\usepackage{amsmath,amssymb,amsthm}
\usepackage{mathtools}            % \coloneqq, \mathclap 등
\usepackage{siunitx}              % 단위: \SI{3.2}{\milli\second}

% --- 그림·표 ---
\usepackage{graphicx}
\usepackage{booktabs}             % \toprule \midrule \bottomrule
\usepackage{subcaption}           % subfigure
\usepackage[font=small]{caption}

% --- 인용 (BibTeX 경로) ---
\usepackage[numbers,sort&compress]{natbib}

% --- 하이퍼링크는 마지막 근처 ---
\usepackage[hidelinks]{hyperref}
\usepackage{cleveref}             % \cref{eq:loss}, \Cref 자동 라벨

\title{A Reproducible Title}
\author{Simon Kim\thanks{Affiliation, email}}
\date{\today}

\begin{document}
\maketitle
\begin{abstract}
One paragraph. Problem, method, key result with a number.
\end{abstract}

\section{Introduction}\label{sec:intro}
% ... 본문 ...

\bibliographystyle{plainnat}
\bibliography{refs}
\end{document}
```

> tinted-neutral / AI-slop 규칙은 코드엔 무관하나, 그림 색은 §5에서 절제된 팔레트로.

## 4. 수식 작성 규칙

번호·라벨이 붙는 식은 `equation`, 정렬 다중식은 `align`. 인라인엔 `$...$`.

```latex
% 라벨 + cref 연동
\begin{equation}\label{eq:loss}
  \mathcal{L}(\theta) = \frac{1}{N}\sum_{i=1}^{N}
    \bigl\lVert y_i - f_\theta(x_i) \bigr\rVert_2^2 .
\end{equation}

\begin{align}
  \nabla_\theta \mathcal{L}
    &= -\frac{2}{N}\sum_i (y_i - f_\theta(x_i))\,\nabla_\theta f_\theta(x_i)
       \label{eq:grad}\\
  \theta_{t+1} &= \theta_t - \eta\, \nabla_\theta \mathcal{L} . \label{eq:sgd}
\end{align}

\Cref{eq:loss} 를 \cref{eq:sgd} 로 최소화한다.
```

수식 안티패턴:
- `$$ ... $$` (plain TeX) 금지 → `\[ ... \]` 또는 `equation`.
- 수동 번호(`(3)`) 타이핑 금지 → 항상 `\label`+`\cref`.
- `\mid`/`|` 혼용으로 절댓값 → `\lvert \rvert` / `\lVert \rVert`.
- 변수에 `\text{}` 남발 금지. 연산자는 `\operatorname{}` 또는 `amsmath`의 `\DeclareMathOperator`.

## 5. 그림: matplotlib/plotly → 벡터(PDF/SVG)

래스터(PNG)는 인쇄·확대에서 깨진다. 논문 그림은 **벡터 PDF**(pdflatex) 또는 SVG가 기본.

`figs/make_figs.py`:

```python
import matplotlib
matplotlib.use("Agg")                 # 헤드리스
import matplotlib.pyplot as plt

plt.rcParams.update({
    "figure.figsize": (3.4, 2.4),     # 단단 컬럼 폭(inch)
    "font.size": 9,
    "savefig.bbox": "tight",
    "pdf.fonttype": 42,               # TrueType 임베드 (arXiv/저널 요구)
    "ps.fonttype": 42,
})

fig, ax = plt.subplots()
ax.plot(xs, train, label="train")
ax.plot(xs, val,   label="val")
ax.set_xlabel("epoch"); ax.set_ylabel("loss")
ax.legend(frameon=False)
fig.savefig("figs/fig_loss.pdf")      # ← 벡터 PDF
```

Plotly(인터랙티브 → 정적 벡터)는 `kaleido` 필요:

```python
import plotly.io as pio               # pip install -U kaleido
pio.write_image(fig, "figs/fig3.pdf", width=480, height=320, scale=1)
# SVG가 필요하면: fig.write_image("figs/fig3.svg")
```

본문 삽입(부동 환경 + booktabs 표):

```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=\columnwidth]{figs/fig_loss.pdf}
  \caption{Training vs.\ validation loss.}\label{fig:loss}
\end{figure}

\begin{table}[t]
  \centering
  \caption{Results. Bold = best.}\label{tab:res}
  \begin{tabular}{lcc}
    \toprule
    Method & Acc.\ (\%) & Params (M) \\
    \midrule
    Baseline & 91.2 & 25 \\
    Ours     & \textbf{94.6} & \textbf{18} \\
    \bottomrule
  \end{tabular}
\end{table}
```

그림 안티패턴: PNG 스크린샷 삽입, 그림 안에 제목 텍스트 박아넣기(캡션과 중복), `\vline`/세로 줄(booktabs는 세로선 금지), 색만으로 구분(색맹 접근성 → 선스타일·마커 병용).

## 6. 인용 워크플로

`refs.bib` 가 **유일한 소스**. BibTeX와 biblatex 중 하나만 일관되게.

```bibtex
@article{vaswani2017attention,
  title   = {Attention Is All You Need},
  author  = {Vaswani, Ashish and Shazeer, Noam and others},
  journal = {Advances in Neural Information Processing Systems},
  year    = {2017}
}
```

본문: `\citep{vaswani2017attention}` (괄호형) / `\citet{...}` (서술형).

| 경로 | preamble | bib 명령 | 빌드 |
|---|---|---|---|
| **BibTeX**(arXiv 안전) | `\usepackage[numbers]{natbib}` | `\bibliographystyle{plainnat}` + `\bibliography{refs}` | latex→bibtex→latex×2 |
| **biblatex+biber** | `\usepackage[backend=biber,style=numeric]{biblatex}`+`\addbibresource{refs.bib}` | `\printbibliography` | latex→biber→latex×2 |

biblatex 주의 (arXiv):
- arXiv는 BibTeX/Biber를 **돌리지 않음** → 로컬에서 만든 `.bbl`을 같이 업로드.
- 본문과 `.bbl`은 **같은 백엔드**로 생성해야 함(biber로 빌드했으면 biber `.bbl`). 섞으면 에러.
- TeX Live 2025의 bbl 포맷은 3.3. 너무 옛 biblatex로 만든 `.bbl`은 거부될 수 있음.

깨진 인용(`[?]`) 디버그:

```bash
grep -n "Citation .* undefined" main.log      # 미정의 키
grep -n "I couldn't open\|empty" main.blg      # bib 파일/엔트리 문제
# 흔한 원인: refs.bib 키 오타, bibtex 단계 누락, .aux 캐시 → latexmk -C 후 재빌드
```

## 7. 재현 가능한 빌드 (latexmk)

수동으로 latex을 여러 번 돌리지 말 것 — `latexmk`가 수렴까지 반복·캐시한다.

`latexmkrc`:

```perl
$pdf_mode = 1;            # pdflatex 사용 (lualatex이면 4)
$bibtex_use = 2;          # bib 항상 실행
$out_dir = 'build';
$clean_ext = 'bbl run.xml bcf synctex.gz';
```

명령:

```bash
latexmk -pdf main.tex          # 전체 빌드 (latex/bibtex/biber 자동 반복)
latexmk -pvc -pdf main.tex     # 파일 변경 감시 + 자동 재빌드 (작성 중)
latexmk -C                     # 산출물 전부 정리 (캐시 꼬임 해결)
```

Docker(로컬 TeX 미설치):

```bash
docker run --rm -v "$PWD":/work -w /work texlive/texlive:latest \
  latexmk -pdf main.tex
```

## 8. arXiv 제출 준비

```bash
# 1) clean 빌드로 .bbl 생성 (arXiv는 bibtex/biber 안 돌림)
latexmk -C && latexmk -pdf main.tex

# 2) 제출 tarball: main.tex + .bbl + figs(평탄화) + 커스텀 .sty/.cls
#    (.bib 자체는 불필요, .bbl이 대체)
mkdir -p submit && cp main.tex main.bbl submit/ 2>/dev/null
cp figs/*.pdf submit/ 2>/dev/null
( cd submit && tar czf ../arxiv.tar.gz . )
tar tzf arxiv.tar.gz
```

체크:
- [ ] `main.bbl` 포함(없으면 참고문헌 누락으로 보임).
- [ ] 그림은 **PDF/EPS**(pdflatex) — 서브폴더 경로면 `\graphicspath{{figs/}}` 또는 평탄화.
- [ ] 기본 컴파일러는 **pdfLaTeX**. lualatex/xelatex 필요하면 첫 줄에 `%!TEX TS-program` 명시 또는 제출 시 선택.
- [ ] `\input`/`\include` 한 보조 파일 전부 동봉.
- [ ] 절대 경로·로컬 폰트 의존 제거.

## 검증

```bash
# (1) 빌드가 에러 0으로 끝나는가
latexmk -C && latexmk -pdf main.tex; echo "exit=$?"
test -f main.pdf && echo "PDF_OK"

# (2) 미해결 참조·인용이 없는가 (있으면 출력됨 → 0줄이어야 통과)
grep -E "Citation .* undefined|Reference .* undefined|There were undefined references" main.log || echo "REFS_OK"

# (3) Overfull/심각 경고 요약
grep -c "Overfull \\\\hbox" main.log | sed 's/^/Overfull hboxes: /'

# (4) 그림이 벡터인가 (PDF여야; PNG면 경고)
ls figs/*.pdf >/dev/null 2>&1 && echo "FIGS_VECTOR_OK" || echo "WARN: raster figures?"
```

`exit=0` + `PDF_OK` + `REFS_OK` 면 빌드 성공. Overfull hbox는 0에 가깝게(레이아웃 넘침).

## 안티패턴 (정리)

- `\\` 로 문단 줄바꿈 남용 → 빈 줄로 문단 분리.
- 그림/표 위치 강제 `[H]`(`float` 패키지) 남발 → `[t]`/`[tb]`로 LaTeX에 맡기기.
- `refs.bib` 두 벌 관리 → 단일 파일.
- 빌드 산출물(`.aux/.bbl/.pdf`) git 커밋 → `.gitignore`.
- BibTeX `.bbl`을 biblatex 문서에, 또는 그 반대로 섞기 → arXiv 거부.
- 그림 안에 캡션 텍스트 박기, PNG 스크린샷, 세로 표선.
- 클래스 자작/저널 공식 .cls 무시 → 데스크 리젝트 위험.
