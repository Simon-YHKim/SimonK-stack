---
name: find-skill
description: >
  Use when the user wants find skill — triggers "스킬 찾아", "스킬 검색", "이런 거 하는 스킬", "find a skill", "search skills", "is there a skill for", or /find-skill. Produces 외부 awesome-claude-skills (26k+ star GitHub 카탈로그) 검색 + SimonK Stack INDEX.md 검색을 합쳐 사용자가 원하는 기능을 가진 skill 추천. 키워드에서 매칭되는 외부 skill 이름·URL 과 내부 등가물 비교. WebFetch 기반 slim 구현. Different from INDEX.md browse (manual) — this is automated search. Different from /skill-gen-agent (creates new skills) — this finds existing ones.
version: 1.0.0
allowed-tools:
  - WebFetch
  - Read
  - Bash
---

# /find-skill

외부 awesome-claude-skills (26k+ star GitHub 카탈로그) 검색 + SimonK Stack INDEX.md 검색을 합쳐 사용자가 원하는 기능을 가진 skill 추천. 키워드에서 매칭되는 외부 skill 이름·URL 과 내부 등가물 비교. WebFetch 기반 slim 구현.

## When to use

Trigger phrases:
- Korean: 스킬 찾아, 스킬 검색, 이런 거 하는 스킬
- English: find a skill, search skills, is there a skill for
- Slash: `/find-skill`

## What it does

외부 awesome-claude-skills (26k+ star GitHub 카탈로그) 검색 + SimonK Stack INDEX.md 검색을 합쳐 사용자가 원하는 기능을 가진 skill 추천. 키워드에서 매칭되는 외부 skill 이름·URL 과 내부 등가물 비교. WebFetch 기반 slim 구현.

## Boundaries

Different from INDEX.md browse (manual) — this is automated search. Different from /skill-gen-agent (creates new skills) — this finds existing ones.

## Operational notes

- 검증 가능 산출물: 사용자가 직접 확인 가능한 파일/URL 우선 생성
- 외부 의존: SKILL body 에 명시 (Vercel CLI, Expo CLI, LaTeX 등)
- 실패 시: 어떤 단계에서 막혔는지 명시, 사용자 결정 받기
