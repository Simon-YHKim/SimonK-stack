---
name: coloring-art
description: >
  Use when the user wants kids/educational coloring pages or line art — 유아·아동·교육용
  색칠공부/라인아트 생성 스킬. 트리거 "색칠 그림", "공룡 색칠", "컬러링 페이지", "라인아트",
  "색칠공부 만들어줘", coloring page, line art, 또는 /coloring-art. Produces 굵은 검은 윤곽선·흰
  배경·면이 단순화된 색칠 페이지나 단순 라인 일러스트를 Gemini 이미지 생성으로 만든다. 대상 연령·소재·난이도를
  먼저 확인하고(심플 모드: 보호자·아동 친화 질문), 안전·연령 적합 프롬프트로 생성한 뒤 인쇄용 PDF 묶기는
  office-docs(Core)로 핸드오프한다. skdesign 의 "그림·래스터·색칠" 경로 전용 생성 스킬.
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
version: 1.0.0
author: SimonKDesign
---

# /coloring-art — 색칠공부·라인아트 생성

아이가 색칠할 수 있는 **굵은 검은 외곽선 / 흰 배경 / 음영 없는** 페이지, 또는 단순 라인 일러스트를 만든다.
바로 찍어내지 않는다 — 대상 연령·소재·난이도를 먼저 좁힌 뒤 안전 프롬프트로 생성한다.

## 발동 조건

- 한국어: "색칠 그림", "공룡 색칠", "컬러링 페이지", "색칠공부 만들어줘", "라인아트"
- 영어: coloring page, line art, line drawing to color
- 슬래시: `/coloring-art`
- `skdesign` 의 "그림·래스터·색칠" 경로에서 위임받아 진입

## Step 1. 대상·소재·난이도 진단 (심플 모드 기본)

`AskUserQuestion` **1회**로 다음을 확정한다. 보호자나 아동이 쓸 수 있으니 **전문용어 금지, 쉬운 말 + 예시**.

| 물어볼 것 | 보기 (일상어) |
|---|---|
| 누가 색칠하나 | 3~4세 / 5~7세 / 8~10세 / 11세+ |
| 무엇을 그릴까 | 동물(공룡·고양이) / 탈것(자동차·로켓) / 자연(꽃·바다) / 캐릭터 |
| 얼마나 단순하게 | 아주 쉽게(큰 면) / 보통 / 디테일 많게 |

규칙:
- 연령만 주면 난이도 자동 매핑: ~7세 = easy, 8~10세 = medium, 11세+ = hard.
- "알아서 해" / 갈피 못 잡음 → AI가 정하고 첫 결과물에서 확인.
- 한 번에 여러 장 요청 시 소재 목록만 받고 루프로 생성.

## Step 2. 안전·연령 적합 프롬프트

생성 전 **반드시** 다음을 보장한다(스크립트가 강제):

- 검은 외곽선 only — 음영·그레이·채색·텍스트·워터마크 0
- 흰 배경, 닫힌 단순 면(색칠하기 쉬움), 여백 넉넉, A4 인쇄 적합
- 아동 친화 카툰 톤
- 폭력·공포·무기·성인 소재 단어 입력 시 **거부**하고 다른 소재 요청

소재가 모호하면(예: "동물") 구체화: "어떤 동물? 공룡? 고양이?" 한 줄 확인.

## Step 3. 생성 (scripts/gen_lineart.mjs)

```bash
node "<skill_dir>/scripts/gen_lineart.mjs" --subject "공룡 티라노" --age 5 --out ./out/dino.png
```

인자:

| 인자 | 설명 | 예 |
|---|---|---|
| `--subject` | 그릴 소재 (필수) | `"cute cat in a garden"` |
| `--age` | 대상 연령 → 난이도 자동 | `5` |
| `--difficulty` | 직접 지정(있으면 age보다 우선) | `easy` / `medium` / `hard` |
| `--out` | 저장 경로 (기본 ./lineart.png) | `./out/dino.png` |

환경변수 — `gemini.ts` 와 동일 규약:

| 변수 | 용도 |
|---|---|
| `GOOGLE_API_KEY` | 직접 호출 시 필수 |
| `EXPO_PUBLIC_USE_VERTEX=true` | Vertex 경로 사용 |
| `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION` | Vertex 시 |
| `GEMINI_IMAGE_MODEL` | 모델 override (기본 `gemini-2.5-flash-image`) |

스크립트는 성공 시 저장 경로 한 줄을 stdout 으로 출력한다. 결과 PNG 경로를 사용자에게 보여주고
"이 느낌 맞나요? / 더 단순하게? / 다른 소재?" 로 확인 → 필요 시 인자 바꿔 재생성.

## Step 4. 인쇄용 PDF 묶기 — office-docs(Core) 핸드오프

여러 장을 한 권으로 묶거나 A4 인쇄용으로 정리하려면 **이 스킬에서 PDF를 만들지 않는다.**
생성된 PNG 경로 목록을 `office-docs`(SimonKCore)로 넘긴다:

> "색칠 페이지 N장(경로: ...)을 A4 인쇄용 PDF 한 권으로 묶어줘. 페이지당 한 장, 여백 포함."

office-docs 미설치면: "PDF 묶기는 `/plugin install simonk-core@simonk-core` 후 office-docs 로 가능. 지금은 개별 PNG 까지 만들었어요" 안내.

## 완료 기준

소재·연령에 맞는 색칠 페이지 PNG 가 생성되고, 사용자가 "이대로 좋다" 확인. 인쇄 묶음이 필요하면 office-docs 핸드오프까지.

## Anti-patterns

- 연령·소재 확인 없이 바로 생성
- 음영·채색이 들어간 "라인아트 아님" 결과를 그대로 전달
- 폭력·공포·성인 소재 생성
- 이 스킬에서 직접 PDF 제본 시도 (→ office-docs 위임)
- 텍스트·워터마크가 박힌 페이지 전달

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
