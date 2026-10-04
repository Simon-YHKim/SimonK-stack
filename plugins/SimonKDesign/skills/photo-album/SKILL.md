---
name: photo-album
description: >
  Use when the user wants their real photos arranged into an album or photo book layout —
  사용자의 실사 사진을 앨범·포토북 레이아웃으로 배치한다. 트리거 "사진첩", "포토북", "사진 모음",
  "앨범 만들어줘", "사진 정리해서 책으로", photo album, photo book, 또는 /photo-album. Produces 사용자가
  올리거나 고른 실제 사진을 그리드·콜라주·페이지 레이아웃으로 배치하고 캡션을 달아 인쇄용 HTML 로 만든다 —
  사진을 새로 생성하지 않는다. 사진 인테이크(업로드·선택, 고령 사용자는 보호자 보조) → 레이아웃 → 캡션
  순서를 지키며, 큰글씨·심플 모드를 기본으로 둔다. 인쇄/PDF 제본은 office-docs(Core)로 핸드오프한다.
  skdesign 의 "사진 배치" 경로 전용 스킬.
allowed-tools:
  - Read
  - Write
  - AskUserQuestion
version: 1.0.0
author: simon-stack
---

# /photo-album — 실사 사진 앨범·포토북 레이아웃

사용자가 가진 **실제 사진**을 한 권의 앨범처럼 배치한다. 그리드·콜라주·페이지 레이아웃에 사진을 앉히고 캡션을 달아 인쇄용 HTML 로 만든다. 바로 찍어내지 않는다 — 사진 인테이크 → 레이아웃 → 캡션 순서를 지킨다.

## 발동 조건

- 한국어: "사진첩", "포토북", "사진 모음", "앨범 만들어줘", "사진 정리해서 책으로", "여행 사진 묶어줘"
- 영어: photo album, photo book, arrange my photos
- 슬래시: `/photo-album`
- `skdesign` 의 "사진 배치" 경로에서 위임받아 진입

## Boundaries (중요)

- **사진을 생성하지 않는다.** 이 스킬은 사용자가 가진 실사 사진을 **배치**한다. AI 이미지 생성은 `/social-graphic`(SNS 그래픽) · `/coloring-art`(색칠 라인아트)이다.
- HTML 페이지의 시각 산출까지만 한다. **PDF 제본·인쇄용 묶기는 `office-docs`(Core)로 핸드오프**한다.
- 디자인 시스템(색·폰트 규칙) 자체를 정의하지 않는다 → 그건 `/design-consultation` · `/simon-design-first`.

## Step 1. 사진 인테이크 (심플 모드 기본)

먼저 사진이 **어디 있는지** 확인한다. `AskUserQuestion` 으로 묻되, 고령·저테크 사용자가 쓸 수 있으니 **전문용어 금지, 쉬운 말 + 예시**.

| 물어볼 것 | 보기 (일상어) |
|---|---|
| 사진이 어디 있나 | 폴더 통째로 / 파일 몇 장 직접 고름 / 아직 정리 전 |
| 누가 쓰나 | 본인 / 부모님·조부모님(보호자 보조) / 아이 |
| 어떤 앨범인가 | 여행 / 가족·기념일 / 일상 모음 / 추모·회고 |

인테이크 규칙:
- 폴더를 주면 **그 폴더의 이미지 파일 경로만 받는다.** 사진 내용을 일일이 Read 하지 말 것(용량·토큰 낭비).
- 고령 사용자: "휴대폰 사진을 컴퓨터 폴더로 옮겨 드릴 보호자가 있나요?"처럼 보조 경로를 먼저 확인. 못 옮기면 "사진이 든 폴더 경로만 알려주세요"로 단순화.
- 사진 순서가 중요하면(시간순·여행 동선) 사용자가 부르는 순서를 그대로 따른다. 모르면 파일명 정렬.
- 사진 수가 많으면(예: 50장+) "몇 장씩 한 페이지에 넣을까요?"로 페이지 분량을 먼저 합의.

## Step 2. 레이아웃 선택

`AskUserQuestion` 으로 레이아웃을 고른다. 각 보기에 **한 줄 설명**을 붙인다.

| 레이아웃 | 설명 | 적합 |
|---|---|---|
| `grid` | 같은 크기 사진을 격자로 정렬 | 여러 장을 깔끔하게 모아보기 |
| `collage` | 크기를 섞어 한 페이지에 모자이크 | 표지·하이라이트 페이지 |
| `page` | 한 페이지에 큰 사진 1~2장 + 캡션 | 사진 한 장 한 장이 주인공 |

레이아웃 규칙:
- 한 화면(페이지)당 **메시지·주인공 사진은 하나**가 원칙(정보 밀도). `page` 가 가장 안전한 기본값.
- `grid` 컬럼 수는 사진 수·세로/가로에 따라 자동(2~4열). 사용자가 지정하면 우선.
- 여백을 넉넉히 — 사진끼리 붙이지 말 것. A4 인쇄 안전영역 고려.
- 색·장식 최소: 흰/아이보리 배경 + 사진 + 캡션 텍스트. gradient·이모지·둥근 컬러보더 금지.

## Step 3. 캡션 (선택, 큰글씨)

사진마다 또는 페이지마다 짧은 캡션을 받는다. 강제하지 않는다 — 없으면 비운다.

- 캡션은 **한 줄**이 기본(날짜·장소·한마디). 길어지면 페이지 레이아웃으로 권유.
- **큰글씨 기본**: 본문 캡션 ≥18pt, 제목 ≥24pt. 고령 사용자 가독성 우선.
- 한국어 기본 폰트는 Pretendard 계열. 영문 Inter 금지.
- 사용자가 사진별 캡션을 부르면 사진 순서와 1:1로 매핑. 개수가 안 맞으면 어느 사진인지 한 줄 확인.

## Step 4. 레이아웃 생성 (scripts/build_album.mjs)

사진 경로 목록·레이아웃·캡션을 JSON 으로 모아 결정론적으로 인쇄용 HTML 한 벌을 만든다. **AI 생성이 아니라 기하 계산**이다.

```bash
node "<skill_dir>/scripts/build_album.mjs" \
  --spec "<프로젝트>/album.spec.json" \
  --out "<프로젝트>/album/index.html"
```

또는 인자로 직접:

```bash
node "<skill_dir>/scripts/build_album.mjs" \
  --photos "trip/a.jpg,trip/b.jpg,trip/c.jpg,trip/d.jpg" \
  --layout grid \
  --title "제주 여행 2026" \
  --out "<프로젝트>/album/index.html"
```

| 인자 | 설명 | 예 |
|---|---|---|
| `--spec` | 페이지·사진·캡션을 담은 JSON (templates/album.spec.example.json 참고) | `./album.spec.json` |
| `--photos` | 쉼표 구분 사진 경로 (spec 없이 단일 페이지 빠른 생성) | `a.jpg,b.jpg` |
| `--layout` | `grid` / `collage` / `page` (기본 grid) | `page` |
| `--columns` | grid 컬럼 강제 (미지정 시 사진 수로 자동) | `3` |
| `--title` | 앨범 제목(표지·페이지 헤더) | `"가족 앨범"` |
| `--caption` | 페이지 캡션(쉼표로 사진별 매핑도 가능) | `"첫째 돌잔치"` |
| `--big` | 큰글씨 모드 강제(기본 on, `--big false` 로 해제) | `--big` |
| `--out` | 결과 HTML 경로 (기본 ./album/index.html) | `./album/index.html` |

`--spec` 과 `--photos` 가 둘 다 있으면 spec 우선. 스크립트는 성공 시 결과 HTML 절대경로 한 줄을 stdout 으로 출력한다.

`--spec` JSON 형식은 `templates/album.spec.example.json` 에 예시가 있다. 페이지 배열, 각 페이지의 layout·photos·captions·title 을 담는다.

생성된 HTML 경로를 사용자에게 보여주고(브라우저로 열면 미리보기), "이 배치 맞나요? / 다른 레이아웃? / 캡션 고칠까요?" 로 확인 → 인자·spec 바꿔 재생성.

## Step 5. 인쇄·PDF 제본 — office-docs(Core) 핸드오프

한 권으로 인쇄·PDF 제본하려면 **이 스킬에서 PDF 를 만들지 않는다.** 생성한 HTML 경로를 `office-docs`(SimonKCore)로 넘긴다:

> "이 앨범 HTML(경로: ...)을 A4 인쇄용 PDF 한 권으로 묶어줘. 페이지 나눔 유지, 여백 포함."

office-docs 는 weasyprint 로 HTML → PDF 를 만든다. `build_album.mjs` 가 넣는 `@page` / `page-break` CSS 가 페이지 경계를 보존한다.

office-docs 미설치면: "PDF 제본은 `/plugin install simonk-core@simonk-core` 후 office-docs 로 가능. 지금은 인쇄용 HTML 까지 만들었어요(브라우저에서 인쇄해도 됩니다)" 안내.

## 완료 기준

사용자 사진이 선택한 레이아웃으로 배치된 인쇄용 HTML 이 생성되고, 사용자가 "이대로 좋다" 확인. 제본이 필요하면 office-docs 핸드오프까지.

## Anti-patterns

- 사진을 **생성**하려 시도(이 스킬은 배치만 — 생성은 social-graphic/coloring-art)
- 사진 파일을 일일이 Read 해 내용 분석(경로만 받는다 — 용량·토큰 낭비)
- 한 페이지에 사진을 빽빽이 욱여넣어 여백·정보 밀도 위반
- 작은 캡션 폰트(고령 사용자 가독성 무시) — 큰글씨 기본 어김
- 이 스킬에서 직접 PDF 제본 시도(→ office-docs 위임)
- gradient·이모지·둥근 컬러보더 등 과잉장식 추가

## Related

- `office-docs`(Core) — 인쇄·PDF 제본 핸드오프 대상
- `design-consultation` — 색·폰트·톤 자체를 정의해야 할 때 먼저
- `social-graphic` — 사진 배치가 아니라 SNS 그래픽을 **생성**할 때

## Operational notes

- 외부 의존: Node 18+ (표준 라이브러리만 사용, 추가 패키지·API 키 불필요). 사진은 **사용자 로컬 파일** — 외부 업로드·전송 없음.
- HTML 은 사진을 상대경로로 참조한다. office-docs 핸드오프 시 사진 폴더와 HTML 의 상대 위치가 깨지지 않게 같은 트리에 둔다.
- 실패 시: 어느 단계(사진 경로 없음 / 지원 안 하는 확장자 / out 경로 못 씀)에서 막혔는지 명시하고 사용자 결정을 받는다.
- 시크릿 불필요 — API 키·env 를 요구하지 않는다. 요구하는 변형이 생기면 절대 하드코딩하지 말 것.

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
