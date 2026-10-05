---
name: persona-validate
version: 0.1.0
description: >
  Use when the user wants to validate any artifact, plan, or deliverable before launch against a panel of diverse user and domain-expert personas to find gaps. Triggers on "페르소나 검증", "전문가 리뷰 패널", "이거 검증해줘", "출시 전 점검", "expert review", /persona-validate. Produces a prioritized improvement backlog, scoring accessibility and coverage with general-user personas (varied age, job, assets, tech) and accuracy, risk, and best-practices with professional expert personas. Applies to every domain (build, design, marketing, AI, docs, planning). Shared SimonKCore skill.
allowed-tools:
  - Read
  - Grep
  - Glob
  - AskUserQuestion
  - Skill
  - Task
---

# /persona-validate — 페르소나 + 전문가 검증 패널

작업물을 "끝까지 데려가는가(사용자)" + "프로답게 옳은가(전문가)" 두 축으로 검증한다. SimonK 플러그인 자체 개발에 썼던 하네스를 일반화한 것.

## 언제
- 산출물/계획/스킬/PR/디자인/캠페인을 **출시·머지 전** 점검.
- 오케스트레이터(`/skstack`·`/skdesign`·`/skmarket`·`/skaihub`)가 완료 직전 게이트로 호출.
- "이거 빈틈 없나?" 류 요청.

## 0. 대상·도메인 감지
검증 대상(파일/디렉터리/계획 텍스트)과 도메인을 파악: build / design / marketing / ai / doc / plan / product. 복합이면 복수 선택.

## 1. 패널 구성 (두 풀 혼합)
`[[experts]]`(전문가 라이브러리)와 `[[personas]]`(일반 사용자 라이브러리)에서 대상 도메인에 맞춰 패널을 뽑는다.
- **전문가 풀(필수, 프로 기준)** — 도메인별 시니어 전문가. 정확성·리스크·베스트프랙티스·완결성을 깐깐하게 본다. 예: build→Staff Eng·Security·SRE·접근성, design→아트디렉터·UX리서처·디자인시스템리드, marketing→CMO·그로스리드·퍼포먼스마케터, ai→ML엔지니어·AI평가/안전·프롬프트엔지니어. (전체 목록·관점은 experts.md)
- **사용자 풀(대표성)** — 유아~90대, 직업·자산·테크 다양(개발자·사업자·디자이너·마케터 필수). 접근성·실사용 적합성을 본다. (personas.md)
- 기본 패널 = 전문가 4~6 + 사용자 4~8, 도메인에 맞게 가감. "빠르게"면 전문가 3 + 사용자 3.

## 2. 루브릭 (도메인 적응)
각 페르소나가 0~2로 채점:
- **전문가 축**: 정확성(correctness) · 견고성/리스크(robustness) · 베스트프랙티스 준수 · 완결성(빠진 단계/엣지) · 도메인 고유 기준(보안·접근성·성능·법규·브랜드 등).
- **사용자 축**: 의도 적합 · 끝까지 완주(coverage) · 접근성(저테크·고령 포함) · 반복/수정 용이성.
1인당 합계 + 한 줄 평결 + 구체 gap 목록(최대 5).

## 3. 실행
- 패널이 크면(>4) `agent-delegate`/`Task`로 **병렬 팬아웃**(페르소나 1인 = 에이전트 1, 대상을 실제로 읽고 채점). 작으면 인라인.
- 각 에이전트는 추측 금지 — 대상 파일/계획을 실제로 읽고 근거 기반 채점, 후하게 주지 않기(전문가는 특히 깐깐하게, refute 우선).

## 4. 종합
- 도메인/축별 평균 점수, 가장 약한 항목.
- 여러 페르소나가 공통으로 막힌 것 우선 → **ICE/impact 우선순위 backlog**(item·why·impact).
- 전문가가 든 치명 리스크(보안·법규·데이터손실)는 impact 무관 최상단 플래그.

## 5. 출력
점수표(도메인×축) + 우선순위 backlog + 3~5문장 요약(어느 층/관점에 약한지, 시급 3가지). 필요 시 `BACKLOG.md`에 누적.

## 6. 반복 루프
수정 반영 → 동일 패널 재검증 → 점수 변화 측정. 목표 점수 도달 또는 전문가 치명 리스크 0 까지 반복(과거 5.0→8.5 사례처럼).

## Boundaries
- 수정은 하지 않음 — 검증·진단·backlog만. 수정은 해당 도메인 스킬/오케스트레이터가.
- 단일 정답 강요 금지: 전문가 의견 갈리면 양론 병기.

관련: [[agent-delegate]], [[grill-me]](단일 인터뷰), [[perspectives]](다관점), [[experts]], [[personas]].

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
