---
name: completion-report
version: 0.3.0
description: >
  Use when a plugin task finishes and the user wants a self-contained completion report. Triggers on "작업 보고서", "완료 리포트", "HTML 보고", "결과 보고서 만들어", "completion report", /completion-report. Creates a self-contained HTML report that leads with a simple at-a-glance summary plus intuitive images/screenshots, tables, and inline-SVG charts — each item has a [자세히] expand button (progressive disclosure), and button toggles switch language (KO/EN) and explanation depth (Simple/Expert), where both depths always state purpose and reason. Stamped with local time in locale format. Shared SimonKCore skill called by every skill/orchestrator (skstack, skdesign, skmarket, skaihub) right after completion.
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
---

# /completion-report — 완료 보고 HTML (사용자 언어 + 현지시간)

작업이 끝나면 "무엇을·어떻게·결과"를 한 장의 HTML로. **글보다 시각**(표·차트·이미지)이 우선.

## 0. 원칙
- **자체완결 HTML** — 인라인 CSS + 인라인 SVG 차트 + `<details>` + ~10줄 토글 JS. 외부 의존·빌드·네트워크 없음. 어디서 열어도 동일.
- **심플 우선 + 점진 공개(progressive disclosure)** — 첫 화면은 한눈 요약(심플 카드 한 줄). 각 항목 옆 **[자세히] 버튼**(`<details><summary>`)을 누르면 상세가 펼쳐진다. 상세를 처음부터 쏟지 않는다.
- **설명 2종 (버튼 토글, 필수)** — 같은 내용을 ① **전문가**(기술 디테일) ② **쉬운 설명**(코딩 지식 0, 초등학생도 이해하는 일상어)로 작성. **둘 다 목적(왜 만들었나)·이유를 함께 기술.** 전문용어 쓰면 1줄 풀이.
- **언어 2종 (버튼 토글, 필수)** — **한국어 + 영어** 두 버전을 한 파일에 넣고 버튼으로 전환. 기본 표시는 사용자 언어.
- **시각 우선** — 표 + 차트(인라인 SVG bar/line/donut) + 이미지/스크린샷 적극. 설명이 길면 그래픽이 실패한 것.
- **현지 시간 명시** — 완료 시각을 로케일 형식으로(아래 표). 추정 금지 — 시스템 시간을 실제로 읽는다.

**토글 구현**: `<body>` 클래스(`lang-ko/lang-en`, `mode-easy/mode-expert`) + CSS 가시성 규칙으로 활성 조합만 노출. 각 항목 상세는 4 변형(`easy·ko / easy·en / expert·ko / expert·en`). 외부 i18n 라이브러리 금지 — 인라인 바닐라 JS만.

## 1. 완료 시각 (로케일 형식)
`node scripts/localtime.mjs` 실행 → 시스템 타임존을 감지해 형식화. 국가/로케일별 기본 형식:

| 지역 | 형식 |
|---|---|
| 한국 (Asia/Seoul) | `[YYYY-MM-DD / HH:MM:SS KST]` |
| 미국 (America/*) | `[MM/DD/YYYY / hh:MM:SS AM/PM PST]` (12h, TZ 약어) |
| 영국·EU (Europe/*) | `[DD/MM/YYYY / HH:MM:SS CET]` (24h) |
| 일본 (Asia/Tokyo) | `[YYYY-MM-DD / HH:MM:SS JST]` |
| 그 외 | ISO: `[YYYY-MM-DD / HH:MM:SS ±HH:MM]` |

타임존이 사용자와 다르면 `--tz`/`--locale`로 오버라이드. 표에 없는 나라는 그 나라 관용 날짜순서(혹은 ISO) + 해당 TZ 약어로.

## 2. 보고서 섹션 (순서)
1. **헤더** — 작업명 · 플러그인 · **완료 시각(로케일 형식)** · 한 줄 요약
2. **무엇을 했나** — 항목별 카드: 심플 한 줄(이름 · 상태 색배지 · 산출물) + **[자세히] 버튼**(`<details>`)을 펼치면 그 항목의 상세(무엇을·왜·어떻게). 첫 화면은 요약만.
3. **결과·지표** — 인라인 SVG 차트(전/후 비교 bar, 추세 line, 비율 donut). 숫자가 있으면 반드시 차트로. 수치 근거·계산은 [자세히] 안에.
4. **시각 증거** — 스크린샷/생성 이미지/다이어그램(있으면 `<img>` 임베드 또는 base64). 디자인·UI 작업은 필수
5. **다음 단계** — 남은 일·권장 후속(체크리스트)
6. **푸터** — 생성 시각·도구·관련 링크

**점진 공개 규칙**: 한 화면에 글 폭주 금지(정보 밀도 — 한 메시지·한 그래픽). 요약은 스캔 가능하게, 깊이는 버튼 뒤로. 펼침은 `<details>`, 언어·설명수준 전환만 ~10줄 인라인 JS 허용 — 외부 라이브러리 금지로 자체완결 유지.

각 항목 [자세히] 상세는 4 변형으로: `easy·ko / easy·en / expert·ko / expert·en`. 쉬운/전문가 둘 다 **목적·이유** 포함(쉬운 쪽은 일상어로).

## 3. 생성 절차
1. 사용자 언어 확정. `localtime.mjs`로 완료 시각 획득.
2. `templates/report.template.html`을 복제해 섹션 채움(표·SVG 차트·이미지). 데이터 없는 섹션은 생략(빈 차트 금지).
3. `reports/completion-<YYYYMMDD-HHMMSS>.html`로 저장.
4. 사용자에게 파일 경로 안내 + (가능하면) 자동 열기/프리뷰. 파일 경로만 던지지 말 것.

## 4. 차트 가이드 (인라인 SVG)
- bar: 전/후·항목 비교. line: 시간 추세(점수 라운드별 등). donut: 구성비.
- 색은 3색 이내(accent+text+muted), 접근성(대비·라벨). 축·범례·값 라벨 포함. 애니메이션 불필요.

## Boundaries
- 데이터 없는데 차트 만들지 않음(가짜 시각화 금지). 추정 시각 금지(실제 시스템 시간).
- `simonk-report`(하네스 세션 리포트)와 다름 — 이건 **플러그인 작업 완료 보고**(로케일 시간 + 사용자 언어 표준).
관련: [[html-default-output]], [[simonk-report]], [[persona-validate]].
