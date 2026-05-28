---
name: notebooklm-import
description: >
  Use when the user wants notebooklm import — triggers "비디오 자막 가져와", "PDF 지식베이스", "NotebookLM 통합", "import video transcripts", "pdf to knowledge base", "notebooklm sync", or /notebooklm-import. Produces YouTube 비디오 자막 + PDF + 웹 페이지에서 SimonKWiki 페이지로 변환·통합. yt-dlp 로 자막 추출, defuddle 로 본문 추출 후 wiki ingest. 차용 출처 slide deck notebooklm-skill Different from /wiki-ingest (manual content), /defuddle (single page extract). This handles multimedia + auto-routes to wiki structure.
version: 1.0.0
allowed-tools:
  - Bash
  - Read
  - Write
  - WebFetch
---

# /notebooklm-import

YouTube 비디오 자막 + PDF + 웹 페이지에서 SimonKWiki 페이지로 변환·통합. yt-dlp 로 자막 추출, defuddle 로 본문 추출 후 wiki ingest. 차용 출처 slide deck notebooklm-skill

## When to use

Trigger phrases:
- Korean: 비디오 자막 가져와, PDF 지식베이스, NotebookLM 통합
- English: import video transcripts, pdf to knowledge base, notebooklm sync
- Slash: `/notebooklm-import`

## What it does

YouTube 비디오 자막 + PDF + 웹 페이지에서 SimonKWiki 페이지로 변환·통합. yt-dlp 로 자막 추출, defuddle 로 본문 추출 후 wiki ingest. 차용 출처 slide deck notebooklm-skill

## Boundaries

Different from /wiki-ingest (manual content), /defuddle (single page extract). This handles multimedia + auto-routes to wiki structure.

## Operational notes

- 검증 가능 산출물: 사용자가 직접 확인 가능한 파일/URL 우선 생성
- 외부 의존: SKILL body 에 명시 (Vercel CLI, Expo CLI, LaTeX 등)
- 실패 시: 어떤 단계에서 막혔는지 명시, 사용자 결정 받기
