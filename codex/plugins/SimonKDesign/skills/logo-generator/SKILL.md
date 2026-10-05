---
name: logo-generator
description: >
  Use when the user wants a logo or brand identity mark generated — 로고·브랜드 아이덴티티를
  Gemini 이미지 생성으로 만든다 — 트리거 "로고 만들어", "브랜드 마크", "워드마크", "심볼 디자인",
  "로고 디자인", 또는 /logo-generator. Produces 마크/워드마크/심볼/모노그램 컨셉을 3~5개 변형으로
  생성하고, 선택받아 정제한다. 브랜드 가치·성격을 먼저 진단한 뒤 벡터화(SVG)·배경 제거·export 경로를
  안내한다. AI-slop 방지(모노톤 3색 이내·gradient/이모지/3D 금지·작은 크기 식별성)를 프롬프트 단계에서
  강제한다. scripts/gen_logo.mjs 로 실제 PNG 를 생성한다(GEMINI_API_KEY 필요).
version: 1.0.0
author: simon-stack
allowed-tools: Read, Write, Bash, AskUserQuestion
---

# /logo-generator

브랜드 로고·마크를 Gemini 이미지 생성으로 만든다. 곧장 그리지 않고 **브랜드 가치·성격을 먼저 진단**한 뒤, 종류별 컨셉을 여러 시안으로 뽑아 선택 → 정제 → 벡터화 안내까지 한 흐름으로 끌고 간다. `scripts/gen_logo.mjs` 가 실제 PNG 를 생성한다.

## When to use

트리거:
- Korean: 로고 만들어, 브랜드 마크, 워드마크, 심볼 디자인, 로고 디자인, 앱 아이콘 로고, 모노그램
- English: make a logo, brand mark, wordmark, symbol design, logo concept, app icon mark
- Slash: `/logo-generator`

## Boundaries

- 디자인 시스템 전체(색 팔레트·타이포 스케일·컴포넌트)를 정의하는 작업이 아니다 → 그건 `/design-consultation` · `/design-system-page`. 이 skill 은 그 안의 **로고 1요소**를 만든다. 시스템이 이미 있으면 그 토큰을 주입한다.
- SNS·마케팅 그래픽(카드뉴스·포스터)이 아니다 → `/social-graphic`.
- 최종 산출물은 **래스터 PNG 시안**이다. 벡터(SVG) 변환은 마지막 단계에서 외부 도구로 안내한다(아래 "벡터화 / export").

## 로고 종류 (`--kind`)

| 종류 | `--kind` | 설명 | 적합한 경우 |
|---|---|---|---|
| 심볼/아이콘 | `symbol` | 텍스트 없는 추상·구상 마크 | 앱 아이콘, 파비콘, 작은 크기 |
| 워드마크 | `wordmark` | 브랜드명 타이포그래피 | 이름 자체가 자산일 때 |
| 콤비네이션 | `combination` | 심볼 + 워드마크 | 범용. 분리·결합 모두 사용 |
| 모노그램 | `monogram` | 이니셜 레터마크 | 이름이 길거나 이니셜이 강할 때 |

작은 크기(앱 아이콘·파비콘)가 1순위면 `symbol` 또는 `monogram` 을 권한다. 콤비네이션은 작게 줄면 텍스트가 뭉갠다.

## Workflow

### Step 1. 진단 먼저 (바로 생성하지 않는다)

`templates/brand-brief.md` 를 기준으로 핵심을 좁힌다. `AskUserQuestion` 으로 한 번에 묻되, 메시지에 이미 있으면 생략한다. 최소 4가지:

1. **브랜드명·한 줄 설명·업종** — 정확한 철자/대소문자 포함.
2. **브랜드 성격** — 형용사 축으로 (진지함↔장난, 클래식↔모던, 대중적↔프리미엄, 기하학적↔유기적).
3. **로고 종류** — 위 표에서 선택. 1순위 노출처(앱 아이콘/웹 헤더/명함)도 함께.
4. **색·폰트 방향** — accent/text/bg, 한국어는 Pretendard 계열·영문 산세리프(Inter 금지).

브랜드 토큰 처리:
- 프로젝트에 `DESIGN.md` · `tokens.ts` · `design-system.html` 이 있으면 **Read 해서 색/폰트를 그대로 주입**한다.
- 아무 정보도 없으면: "브랜드 색·폰트가 정해져 있나요? 없으면 `/design-consultation` 으로 먼저 정하길 권합니다. 일단 진행하려면 모노톤 기본값(차분한 neutral + accent 1색)으로 시안을 뽑을까요?" 라고 묻고 사용자 결정을 받는다.

리뉴얼이면 기존 로고 경로를 받아 무엇을 유지/탈피할지 명확히 한다.

### Step 2. 브랜드 일관 프롬프트 작성 (AI-slop 방지 강제)

진단 결과를 프롬프트의 재료로 쓴다. 다음을 **반드시 명시**한다(스크립트가 종류별·공통 사양을 자동 보강하지만, 프롬프트 본문에도 톤을 담아야 결과가 좋다):

- **마크 하나만** — 한 캔버스에 여러 변형 늘어놓기 금지. 목업(명함·간판) 합성 없이 마크 단독.
- **모노톤 3색 이내** — accent + text + bg. 4색 이상 multi-color·무지개 금지.
- **평평한 벡터 스타일** — gradient, glassmorphism, 사실적 질감, 3D 베벨, 드롭섀도 금지(벡터화·확장성 위해).
- **작은 크기 식별성** — 굵고 균일한 선폭, 단순한 형태, 또렷한 실루엣.
- **폰트 톤** — 워드마크/콤비/모노그램이면 영문 Inter 금지, 한국어 Pretendard 계열 명시.

프롬프트 골격 예:
```
<브랜드명> — <한 줄 설명>, <업종>. 성격: <형용사 3개>.
모티프: <상징 아이디어 또는 "추상 기하학적 형태">.
스타일: 모노톤 — 배경 <bg hex 또는 흰색>, 마크 <accent hex> 단색. 평평한 벡터, 효과 없음.
작은 크기에서도 식별 가능한 단순하고 또렷한 형태.
```

### Step 3. 생성 — scripts/gen_logo.mjs 실행

```bash
node "<skill_dir>/scripts/gen_logo.mjs" \
  --prompt "<Step 2 프롬프트>" \
  --kind symbol \
  --n 4 \
  --out "<프로젝트>/assets/brand/logo.png"
```

옵션:
- `--kind` — symbol / wordmark / combination / monogram. 기본 `symbol`.
- `--n` — 변형 시안 개수. 기본 **4**(로고는 비교가 중요), 최대 8. 파일명에 `-1`~`-N` 접미사.
- `--out` 미지정 시 cwd 에 `logo-<kind>-<timestamp>.png`.

스크립트는 정사각 1024x1024·단색 배경·중앙 정렬·벡터화 친화 사양을 자동 주입한다. 환경 변수 `GEMINI_API_KEY`(없으면 `GOOGLE_API_KEY`) 필요. 키/SDK 누락 시 설치·설정 안내를 출력하니 그대로 사용자에게 전달한다.

### Step 4. 시안 검토 → 선택 → 정제

생성된 PNG 들을 사용자에게 보여준다(`SendUserFile` 가능하면 활용):

- 사용자가 1~2개 방향을 고른다.
- 정제 루프: 고른 시안의 프롬프트에서 한 번에 **하나의 축만** 바꿔 재생성한다.
  - 형태 단순화 / 비율 조정 / 색 교체 / 워드마크 자간·정렬 / 심볼-텍스트 무게 균형.
- 종류를 바꿔 비교하고 싶으면 `--kind` 만 바꿔 다시 돌린다(같은 브랜드 프롬프트 유지).

"이 방향으로 갈까요, 아니면 어디를 바꿀까요?" 로 닫는다. 사용자가 멈추라 할 때까지 시안 → 피드백 루프를 돈다.

### Step 5. 벡터화 / export 안내

PNG 시안이 확정되면, 실사용을 위해 벡터로 옮기는 경로를 안내한다(이 skill 은 PNG 까지 만들고, 벡터 변환은 외부 도구 권장):

| 목적 | 방법 |
|---|---|
| 빠른 자동 벡터화 | 온라인 트레이서(예: vectorizer 류) 또는 Inkscape `Path > Trace Bitmap` 으로 SVG 변환 후 노드 정리 |
| 정밀 재현(권장) | 확정 시안을 레퍼런스로 Figma/Illustrator 에서 **다시 그려** 깔끔한 벡터로. 펜 도구 기반이 가장 깨끗 |
| 배경 제거 | 단색 배경이므로 색상 키 제거 쉬움. 투명 PNG 가 필요하면 배경 제거 도구 사용 |
| 다중 export | 확정 SVG 에서 앱 아이콘(1024/512/192/180/57px), 파비콘(32/16px), 라이트·다크 변형 파생 |

벡터 원본이 생기면 다중 크기·라이트/다크 export 와 디자인 시스템 등록은 `/design-system-page` 로 이어 가길 권한다.

## Anti-patterns

- 진단 없이 곧장 화려한 multi-color 로고를 임의 생성
- 한 캔버스에 변형 여러 개를 늘어놓거나 명함·간판 목업으로 합성해 정작 마크가 안 보이는 결과
- gradient·glassmorphism·3D 베벨·사실적 질감 — 벡터화·확장성을 해친다
- 영문 Inter 폰트, 이모지 아이콘, 4색 이상
- 작은 크기 식별성을 무시한 디테일 과다(가는 선·미세 패턴)
- 사용자 확인 없이 시안을 무한 생성해 유료 쿼터 낭비
- PNG 시안을 그대로 최종 로고로 납품(벡터화 단계 생략)

## Operational notes

- 외부 의존: Node 18+, `@google/genai`, 그리고 `GEMINI_API_KEY` 또는 `GOOGLE_API_KEY`.
- 모델 ID 는 `scripts/gen_logo.mjs` 상단 `MODEL` 상수에서 한 곳만 교체한다(주석으로 명시). 최신 이미지 모델로 갱신 시 이 한 줄만.
- 종류별/공통 사양 문구는 스크립트의 `KINDS` 와 `COMMON_SPEC` 상수에 결정론적으로 들어있다 — 톤을 조정하려면 그곳을 수정한다.
- 실패 시: 어느 단계(키 누락 / SDK 미설치 / 응답에 이미지 없음)에서 막혔는지 명시하고 사용자 결정을 받는다.
- 유료 API 호출이므로 `--n` 은 보수적으로(기본 4). 확인 후 늘린다.
- 시크릿은 항상 환경 변수로. API 키를 프롬프트·파일·로그에 하드코딩하지 않는다.

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
