---
name: design-system-page
description: >
  Use when the user wants design system page — triggers "디자인 시스템 만들어", "브랜드 북 만들어", "design system 페이지", "design system page", "brand book pdf", "style guide html", or /design-system-page. Produces design.md (founder-context 산출물) 또는 사용자 제공 브랜드 reference 에서 design-system.html (색상·타이포·컴포넌트·아이콘·로고) + A4 brand-book PDF 자동 생성. Google Fonts CDN + 인라인 CSS/SVG, zero build. headless browser (chromium / edge) 로 PDF 렌더. 차용 출처 robonuggets/design-system Different from /simon-design-first (intake interview), /design-html (one-off page). This produces a full design-system catalog page + printable brand book.
version: 1.0.0
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

# /design-system-page

design.md (founder-context 산출물) 또는 사용자 제공 브랜드 reference 에서 design-system.html (색상·타이포·컴포넌트·아이콘·로고) + A4 brand-book PDF 자동 생성. Google Fonts CDN + 인라인 CSS/SVG, zero build. headless browser (chromium / edge) 로 PDF 렌더. 차용 출처 robonuggets/design-system

## When to use

Trigger phrases:
- Korean: 디자인 시스템 만들어, 브랜드 북 만들어, design system 페이지
- English: design system page, brand book pdf, style guide html
- Slash: `/design-system-page`

## What it does

design.md (founder-context 산출물) 또는 사용자 제공 브랜드 reference 에서 design-system.html (색상·타이포·컴포넌트·아이콘·로고) + A4 brand-book PDF 자동 생성. Google Fonts CDN + 인라인 CSS/SVG, zero build. headless browser (chromium / edge) 로 PDF 렌더. 차용 출처 robonuggets/design-system

## Boundaries

Different from /simon-design-first (intake interview), /design-html (one-off page). This produces a full design-system catalog page + printable brand book.

## Operational notes

- 검증 가능 산출물: 사용자가 직접 확인 가능한 파일/URL 우선 생성
- 외부 의존: SKILL body 에 명시 (Vercel CLI, Expo CLI, LaTeX 등)
- 실패 시: 어떤 단계에서 막혔는지 명시, 사용자 결정 받기
