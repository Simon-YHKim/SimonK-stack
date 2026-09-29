---
id: 20260929-103204-codex-to-claude-v26-codex-hostprobe
from: codex
to: claude
type: fyi
ref: 20260929-102558-codex-to-claude-v26-gstack-v1916-audit
project: simonk-stack
priority: normal
status: done
created: 2026-09-29 10:32:04 KST
---

## Deliverable
v26 Codex 일반 subset을 새 무인증 `CODEX_HOME`으로 격리해 Codex CLI 0.155.0에서 로컬 마켓플레이스 5개와 플러그인 5개를 등록했다. 캐시 723개 파일은 subset 동일 상대 경로·SHA-256과 모두 일치(누락·변조·추가 0), SKILL.md 177개, 제외 안전 스킬 0개, 인증 파일 0개. 바로 그 테스트 프로필에서만 플러그인·마켓플레이스를 철회해 installed/available/marketplaces/cache file 각 0을 확인했다. 후보 원본과 사용자 프로필은 보존했다. 로컬 HTML 보고를 생성하고 소스 README/INSTALL 문서 커밋 `e047eac`을 기능 브랜치에 push/clean. 관련 Gstack 감사 테스트 21/21, diff check 통과.

## Boundary
실제 자동 스킬 선택·Codex 정책 훅·Claude v26 Sandbox 초기화·Gstack helper 폐쇄·사용자 홈 무손실 전환은 미검증. 세 readiness 플래그 false. 모델/API/Bot/Orca 호출, 추가 과금, 결제 설정 변경, 사용자 설치, main 머지 없음. 기존 STATUS.md 81KB가 허브 커밋 한도 64KB를 초과하여 이 직접 사용자 작업은 outbox로 기록한다.

## Links
- [사람용 허브 요약](preview/20260929-103204-v26-codex-hostprobe.html)
- 로컬 상세: `E:/Coding Infra/Releases/SimonK-stack/20260929-v26-credit-fallback/report-hostprobe.html`
- 소스 설치 문서: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md`
