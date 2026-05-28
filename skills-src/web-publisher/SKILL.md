---
name: web-publisher
description: >
  Use when the user wants web publisher — triggers "웹사이트에 올려", "자동 로그인 후 게시", "폼 자동 작성", "publish to website", "auto-login and post", "form automation", or /web-publisher. Produces 기존 웹사이트를 개인 도구로 — 로그인, 폼 작성, 파일 업로드, 정보 추출을 자동화. browse skill (헤드리스 브라우저) + cookies (setup-browser-cookies) + form schema 결합. 사용자가 자주 가는 사이트에 한 번 매핑 정의 후 이후 한 줄 명령으로 자동화. 차용 출처 slide deck x-article-publisher Different from /browse (general headless browser), /pair-agent (remote agent). This is purpose-built site automation with stored credentials + form schemas.
version: 1.0.0
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

# /web-publisher

기존 웹사이트를 개인 도구로 — 로그인, 폼 작성, 파일 업로드, 정보 추출을 자동화. browse skill (헤드리스 브라우저) + cookies (setup-browser-cookies) + form schema 결합. 사용자가 자주 가는 사이트에 한 번 매핑 정의 후 이후 한 줄 명령으로 자동화. 차용 출처 slide deck x-article-publisher

## When to use

Trigger phrases:
- Korean: 웹사이트에 올려, 자동 로그인 후 게시, 폼 자동 작성
- English: publish to website, auto-login and post, form automation
- Slash: `/web-publisher`

## What it does

기존 웹사이트를 개인 도구로 — 로그인, 폼 작성, 파일 업로드, 정보 추출을 자동화. browse skill (헤드리스 브라우저) + cookies (setup-browser-cookies) + form schema 결합. 사용자가 자주 가는 사이트에 한 번 매핑 정의 후 이후 한 줄 명령으로 자동화. 차용 출처 slide deck x-article-publisher

## Boundaries

Different from /browse (general headless browser), /pair-agent (remote agent). This is purpose-built site automation with stored credentials + form schemas.

## Operational notes

- 검증 가능 산출물: 사용자가 직접 확인 가능한 파일/URL 우선 생성
- 외부 의존: SKILL body 에 명시 (Vercel CLI, Expo CLI, LaTeX 등)
- 실패 시: 어떤 단계에서 막혔는지 명시, 사용자 결정 받기
