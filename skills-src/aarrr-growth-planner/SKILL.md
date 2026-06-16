---
name: aarrr-growth-planner
description: "Use when the user wants to plan growth strategy or generate ideas using the AARRR framework—triggers \"AARRR 분석\", \"그로스 전략\", \"퍼널 설계\", \"유저 획득 전략\", \"리텐션 개선\", \"growth framework\", \"pirate metrics\", \"funnel strategy\". Produces an AARRR analysis (Acquisition→Activation→Retention→Referral→Revenue) with specific tactics per stage, KPIs, and experiment backlog prioritized by ICE score."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# aarrr-growth-planner

AARRR (해적 지표) 프레임워크로 그로스 전략을 수립하는 skill.

## 발동 조건

- "AARRR 분석해줘", "그로스 전략 세워줘", "퍼널 설계"
- "유저 획득 전략", "리텐션 개선", "바이럴 루프"
- 아이디어 단계에서 체계적 그로스 플래닝 필요 시

## AARRR 5단계 프레임워크

### 1. Acquisition (획득)

"유저가 어떻게 우리를 발견하는가?"

| 채널 | CAC 수준 | 적합한 서비스 |
|---|---|---|
| SEO/콘텐츠 마케팅 | 낮음 (장기) | SaaS, 블로그, 도구 |
| 소셜 미디어 (유기적) | 낮음 | B2C, 커뮤니티 |
| 유료 광고 (Meta/Google) | 높음 (즉시) | 이커머스, 앱 |
| Product-Led Growth | 매우 낮음 | 도구형 SaaS |
| 커뮤니티/밋업 | 중간 | B2B, 개발자 도구 |
| 앱스토어 ASO | 낮음 | 모바일 앱 |

### 2. Activation (활성화)

"유저가 핵심 가치를 처음 경험하는 순간 (= Aha Moment)"

- TTFV (Time to First Value) 최소화
- 온보딩 퍼널 설계 (3단계 이하)
- `aha-moment-optimizer`와 연동

### 3. Retention (유지)

"유저가 다시 돌아오는가?"

| 주기 | 지표 | 건강한 수준 |
|---|---|---|
| D1 | 다음날 복귀 | >40% (앱), >20% (웹) |
| D7 | 주간 복귀 | >20% |
| D30 | 월간 복귀 | >10% |

전략: 푸시 알림, 이메일 시퀀스, 습관 루프, 콘텐츠 업데이트

### 4. Referral (추천)

"유저가 다른 사람을 데려오는가?"

- 바이럴 계수 (K-factor): K > 1이면 자연 성장
- 추천 프로그램: 양쪽 보상 (추천인 + 피추천인)
- 내장 공유 기능 (결과물 공유, 초대 링크)

### 5. Revenue (수익)

"유저가 돈을 지불하는가?"

- `monetization-planner`와 연동
- LTV > 3×CAC 이면 건강한 유닛 이코노미
- 전환율 벤치마크: Free→Paid 2-5% (B2C), 5-15% (B2B)

## 산출물

`GROWTH-PLAN.md`:
- AARRR 각 단계별 현재 상태 + 목표
- 실험 백로그 (ICE 점수: Impact × Confidence × Ease)
- 핵심 KPI 대시보드 설계
- 주간 그로스 미팅 어젠다 템플릿

## Related Skills

- `aha-moment-optimizer` — Activation 단계 심화
- `pmf-analyzer` — PMF 달성 여부 판단
- `analytics-integrator` — KPI 추적 도구 세팅
- `growth-engine` — 실제 마케팅 도구 구현

## 완료 보고 (HTML) — 표준
작업을 끝내면 **HTML 완료 보고서**를 생성한다 (SimonKCore `completion-report` 표준).
- 첫 화면은 **심플 요약**(한눈 카드 한 줄) + 직관 그래픽/차트(인라인 SVG)·이미지.
- 각 항목 옆 **[자세히] 버튼**(`<details>`)을 펼치면 상세 — 처음부터 쏟지 않는다(progressive disclosure).
- 자체완결 1파일(인라인 CSS/SVG, 무JS) · 사용자 언어 · 현지시간 스탬프.
- Core 있으면 `completion-report` 호출, 없으면 동일 형식으로 인라인 생성.
