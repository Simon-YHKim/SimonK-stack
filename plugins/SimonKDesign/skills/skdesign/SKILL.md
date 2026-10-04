---
name: skdesign
version: 0.1.0
description: >
  Use when the user wants a single entry point for any art/design task and needs intent
  diagnosis and routing — SimonKDesign 오케스트레이터, 예술·디자인 작업의 단일 진입점. 트리거
  "디자인 해줘", "UI 만들어줘", "로고/브랜드", "발표자료", "디자인 시스템", "skdesign", 또는 /skdesign.
  Produces a rough intent diagnosis, routes to the right sub-design skill, and iteratively
  develops each output with the user — 바로 코드/픽셀을 찍어내지 않고 진단 → 레퍼런스 → 방향 확정
  → 산출 → 리뷰 순서를 지킨다.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
  - Skill
---

# /skdesign — SimonKDesign 오케스트레이터

예술·디자인 작업의 진입점. **바로 만들지 않는다.** 의도를 좁히고, 레퍼런스로 방향을 맞추고, 산출물마다 사용자와 디벨롭한다.

## 0. SimonKCore 감지 (graceful degrade)
시작 시 공유 인프라 존재를 확인한다:
- `agent-delegate`, `model-router`, `grill-me`, `perspectives` 스킬이 설치돼 있는가? (`/plugin` 목록 또는 skills 디렉터리로 확인)
- 있으면: 큰 작업은 `agent-delegate`로 위임, 모델 선택은 `model-router`에 위임, 방향이 모호하면 `grill-me`로 인터뷰.
- 없으면: "SimonKCore 미설치 — 위임/라우팅 없이 단독 진행합니다. 전체 기능은 `/plugin install simonk-core@simonk-core` 후 사용 가능." 한 줄 안내 후 계속 진행(중단하지 않음).

## 1. 의도 진단 (러프 + 쉬운말 + 연령·테크 티어)
먼저 대화 톤·어휘로 **테크/연령 수준을 빠르게 감지**하고 그에 맞춰 질문한다.
`AskUserQuestion` **1회**, 각 선택지에 **일상어 별칭 + 한 줄 설명**:
- 디자인 시스템 — "브랜드 색·폰트·규칙 한 벌"
- UI·화면 — "내 사이트/앱 화면 꾸미기"
- 로고·브랜드 — "로고·간판 느낌"
- 발표자료 — "PPT·슬라이드"
- 그림·이미지 — "포스터·카드뉴스·색칠·사진" (래스터)
- 인쇄물 — "안내문·소책자·PDF·큰글씨"
- 모션·영상 — "움직이는 그래픽"

**심플 모드** (저연령·고령·저테크 감지 시 자동): 전문용어 제거, 선택지를 짧은 문장·예시로, 보호자/자녀 보조·음성 입력 허용, 기본 폰트 Pretendard·"못 정하면 AI가 정함"·큰글씨(본문 ≥18pt) 자동. 영문 갤러리 brausing 대신 완성 목업 2~3개 picker로 확인.

"알아서 해"/갈피 못 잡음 → AI가 방향 정해 진행하되 1번 산출물에서 확인.

## 2. 라우팅 (의도 → 파이프라인)
**복합 목표**(예: 브랜드+발표자료)는 단일 선택으로 자르지 말 것 — 해당 경로들을 순차 실행하고 brand→deck처럼 색·폰트·로고 토큰을 다음 단계로 주입한다.

| 의도 | 파이프라인 (하위 스킬 순서) |
|---|---|
| 디자인 시스템 | `simon-design-first` → `design-consultation` → `design-system-page` · `design-system-keeper` |
| UI·화면 | `design-consultation` → `design-shotgun` → `design-html` → `design-review` |
| 네이티브 UI | `building-native-ui` → `design-review` |
| 발표자료 | `slides` (브랜드 토큰 있으면 주입) |
| 인쇄물·산문 PDF | `office-docs`(Core) — 안내문·소책자·회고록·큰글씨 문서 |
| 로고·브랜드 마크 | `logo-generator`(Gemini 이미지: 마크/워드마크/심볼 + SVG export) |
| 사진첩·포토북 | `photo-album`(사용자 사진 배치·레이아웃 → 인쇄는 office-docs) |
| 모션·영상 | `remotion-best-practices` |
| 논문·문서 비주얼 | `scientific-paper` |
| SNS 그래픽·포스터·카드뉴스 | `social-graphic`(Gemini 이미지: 1:1·4:5·9:16·카드뉴스 시리즈, 브랜드 토큰 주입) |
| 색칠·라인아트 | `coloring-art`(Gemini 이미지: 검은 외곽선 색칠 페이지) → 인쇄 묶음은 `office-docs`(Core) |
| (그 외 래스터 미지원) | fallback: "그건 아직 못 하지만 Y는 가능" 대체 제시 또는 Pixy(`Simon-YHKim/Pixy`) 안내 |
| 플랜 단계 디자인 리뷰 | `plan-design-review` |

각 하위 스킬은 `Skill`로 호출. **범위 밖 요청도 막다른 안내(punt) 금지** — 항상 "X는 못 하지만 Y는 가능"으로 대체 출력을 제시한다.

## 3. 반복 디벨롭 (핵심)
파이프라인을 한 번에 쏟지 않는다. **단계마다 산출물 → 사용자 확인 → 반영 → 다음.**
- "이 방향 맞나요? / 다른 레퍼런스 볼까요?" 로 확인.
- 레퍼런스는 **접속 가능한 URL** 3–5개로 제시(dribbble, awwwards, lapa.ninja, 21st.dev).
- 폰트는 추천만 — Google Fonts 미리보기 URL 동봉, 한국어 기본 **Pretendard**. 선택은 사용자.

## 4. AI Slop 방지 3원칙 (항상 적용)
1. 불필요한 것 제거 — 이모지 아이콘·과잉 장식 금지.
2. 모노톤 — UI 색상 3개 이내(accent+text+bg).
3. 확정된 레퍼런스에서 착안.
금지: **Inter**(→Pretendard/대체 산세리프), pure black/gray(→tinted neutrals), 4색+ multi-color, bounce/elastic easing.

## 5. 페르소나 인지 + 전파 (필수)
사용자 수준에 맞춰 질문 깊이·전문용어 조절(초보=용어 풀어서·선택지 / 전문가=토큰·스펙).
**전파**: §1에서 감지한 저테크/고령/저연령 신호를 **하위 스킬 산출물까지** 전달한다 — 쉬운말, 큰글씨(본문 ≥18pt), 용어 첫 등장 1줄 풀이, TL;DR 3줄+다음 행동 1개. 산출 형식 자체를 페르소나별 스위치(전문가=스펙/토큰, 저테크=완성본+짧은 안내, 파일경로만 던지지 말고 인라인 미리보기/열기 안내).
**자급자족**: `office-docs` 번들 → 문서·PDF·회고록·큰글씨 안내문까지 Core 없이 단독 완주. 블로그/사이트 게시는 사용자 기존 플랫폼 안내(또는 Core `web-publisher` 자동 게시).

## 완료 기준
**출시 전 게이트**: 큰 산출물은 `persona-validate`(SimonKCore)로 디자인 전문가(아트디렉터·UX·접근성)+대상 사용자 패널 검증 → 치명 빈틈 반영. (Core 미설치 시 인라인 self-check — AI-slop 3원칙+접근성 체크+전문가 렌즈 1개로 대체, degrade 일관.)
산출물이 의도에 부합하고 사용자가 "이대로 좋다"라고 확인했을 때 완료. 미진하면 3번 루프로 되돌아간다.
**완료 후**: `completion-report`(Core)로 HTML 보고서 생성 — 사용자 언어 + 현지시간 로케일 형식(KR: `[YYYY-MM-DD / HH:MM:SS KST]`) + 표·차트·이미지(디자인 산출물 미리보기 임베드).

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
