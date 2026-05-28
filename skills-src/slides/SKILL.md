---
name: slides
description: >
  Use when the user wants slides — triggers "슬라이드 만들어", "발표자료 만들어", "피치덱 만들어", "프레젠테이션", "pitch deck", "slide deck", "presentation slides", "html slides", or /slides. Produces zero-dependency HTML 슬라이드 (16:9 고정, embedded CSS/JS). 사용자가 발표 내용 알려주면 LLM 이 3 visual style preview 생성 후 사용자가 하나 선택하면 그 톤으로 전체 deck 생성. PPT 파일도 web 변환 지원. /simon-design-first show-don-t-tell 패턴 적용. 차용 출처 zarazhangrui/frontend-slides Different from /design-html (general HTML) and /design-shotgun (design variants exploration). This is specifically presentation decks with 3-preview pattern.
version: 1.0.0
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - AskUserQuestion
  - SendUserFile
---

# /slides

zero-dependency HTML 슬라이드 (16:9 고정, embedded CSS/JS). 사용자가 발표 내용 알려주면 LLM 이 3 visual style preview 생성 후 사용자가 하나 선택하면 그 톤으로 전체 deck 생성. PPT 파일도 web 변환 지원. /simon-design-first show-don-t-tell 패턴 적용. 차용 출처 zarazhangrui/frontend-slides

## When to use

Trigger phrases:
- Korean: 슬라이드 만들어, 발표자료 만들어, 피치덱 만들어, 프레젠테이션
- English: pitch deck, slide deck, presentation slides, html slides
- Slash: `/slides`

## What it does

zero-dependency HTML 슬라이드 (16:9 고정, embedded CSS/JS). 사용자가 발표 내용 알려주면 LLM 이 3 visual style preview 생성 후 사용자가 하나 선택하면 그 톤으로 전체 deck 생성. PPT 파일도 web 변환 지원. /simon-design-first show-don-t-tell 패턴 적용. 차용 출처 zarazhangrui/frontend-slides

## Boundaries

Different from /design-html (general HTML) and /design-shotgun (design variants exploration). This is specifically presentation decks with 3-preview pattern.

## Operational notes

- 검증 가능 산출물: 사용자가 직접 확인 가능한 파일/URL 우선 생성
- 외부 의존: SKILL body 에 명시 (Vercel CLI, Expo CLI, LaTeX 등)
- 실패 시: 어떤 단계에서 막혔는지 명시, 사용자 결정 받기
