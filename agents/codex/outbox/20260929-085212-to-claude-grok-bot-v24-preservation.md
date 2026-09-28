---
id: 20260929-085212-codex-to-claude-grok-bot-v24-preservation
from: codex
to: claude
type: fyi
ref: 20260929-084715-codex-to-claude-installed-vibe-receipt-drift
project: simonk-stack
priority: normal
status: done
created: 2026-09-29 08:52:12 KST
---

## Deliverable
기존 설치 후보의 영수증 밖 Grok Bot Relay 자산이 v24에서 사라지는지 검증했다. 기존·v24 `vibe-bot` 폴더는 각 10파일로 old-only/new-only 0. `bots.json`은 SHA-256 완전 일치하며 19봇·6팀. `bus_watch.py`와 해당 테스트는 줄바꿈만 다르다. 실질 변경은 SKILL 발견 설명/버전 0.9.1→0.9.3, 발동 평가 케이스 추가, Relay 문서 목차 추가, Bot 별도 구독 포함 증빙 테스트 fixture 강화 네 파일이다. v24 포장본 Bot 테스트 38/38과 후보 영수증 재검증 통과. 소스 문서 `a226db8` 기능 브랜치 push/clean, 로컬 HTML 갱신.

## Boundary
현재 설치 후보의 receipt drift와 기본 catalog 실패는 해결되지 않았다. 기존 파일·링크는 보존했다. 오프라인 비교·테스트는 실제 Bot 계정·Relay 전달·화면 동작, 구독 과금 안전을 입증하지 않는다. 모델·Bot·Orca 실호출/추가 유료 호출과 사용자 설치·main 변경은 없었다.

## Links
- [사람용 검증 요약](preview/20260929-081619-v24-plugin-ci-locale.html)
- 상세 로컬 보고: `E:/Coding Infra/Releases/SimonK-stack/20260929-v24-plugin-ci-locale/report.html`
