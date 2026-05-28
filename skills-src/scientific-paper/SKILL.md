---
name: scientific-paper
description: >
  Use when the user wants claude scientific — triggers "논문 작성", "LaTeX 수식", "학술 시각화", "peer review", "scientific paper", "latex equations", "academic figures", or /scientific-paper. Produces 학술 논문 작성 — LaTeX 수식, BibTeX 인용, matplotlib/plotly 시각화, peer review 형식 (IEEE/ACM/Nature), arxiv 제출 준비. 차용 출처 slide deck claude-scientific Different from /document-generate (general docs) and /office-docs (Office formats). This is academic-format specific with LaTeX/BibTeX/figure pipelines.
version: 1.0.0
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
---

# /scientific-paper

학술 논문 작성 — LaTeX 수식, BibTeX 인용, matplotlib/plotly 시각화, peer review 형식 (IEEE/ACM/Nature), arxiv 제출 준비. 차용 출처 slide deck claude-scientific

## When to use

Trigger phrases:
- Korean: 논문 작성, LaTeX 수식, 학술 시각화, peer review
- English: scientific paper, latex equations, academic figures
- Slash: `/scientific-paper`

## What it does

학술 논문 작성 — LaTeX 수식, BibTeX 인용, matplotlib/plotly 시각화, peer review 형식 (IEEE/ACM/Nature), arxiv 제출 준비. 차용 출처 slide deck claude-scientific

## Boundaries

Different from /document-generate (general docs) and /office-docs (Office formats). This is academic-format specific with LaTeX/BibTeX/figure pipelines.

## Operational notes

- 검증 가능 산출물: 사용자가 직접 확인 가능한 파일/URL 우선 생성
- 외부 의존: SKILL body 에 명시 (Vercel CLI, Expo CLI, LaTeX 등)
- 실패 시: 어떤 단계에서 막혔는지 명시, 사용자 결정 받기
