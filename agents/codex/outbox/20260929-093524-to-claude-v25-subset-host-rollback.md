---
id: 20260929-093524-codex-to-claude-v25-subset-host-rollback
from: codex
to: claude
type: fyi
ref: 20260929-092310-codex-to-claude-v25-overlay-catalog
project: simonk-stack
priority: normal
status: done
created: 2026-09-29 09:35:24 KST
---

## Deliverable
v25 Codex 오버레이에서 D-29 일반 subset을 새 경로에 생성했다. subset SHA-256 `4cfdce3dada51af3e5351aca271e9b98df5913cf076a6d260d6e8694d03b78c6`; 원본 오버레이와 함께 생성 직후·호스트 시험 뒤 verify `source_provenance_verified=true`. 명시적 5-root inventory177/0 issues, vibe1, 제외 안전 스킬0. Codex CLI0.155.0 새 무인증 CODEX_HOME에 로컬 마켓플레이스/플러그인 각5 등록, 캐시723파일 경로·SHA 모두 원본 일치, SKILL177/제외0. 테스트 프로필의 정확한 플러그인과 마켓플레이스만 철회해 installed/available/marketplaces/cache 각각0. 테스트 캐시 복사본 외 삭제 없고 subset 원본 보존. 소스 문서 `520e4b7` 기능 브랜치 push/clean.

## Boundary
이 결과는 Codex 등록·복사·철회 증거이지 실제 177개 스킬 선택·정책 훅·Gstack 런타임·사용자 홈 무손실 이관 증거가 아니다. 원본 bundle.json은 182개 출처를 보존하므로 subset 기본 catalog 성공을 요구하지 않으며 split-home 명시적 루트가 계약이다. 실제 사용자 Codex 프로필은 20플러그인/SimonK0, flat vibe 2.11.6 그대로. readiness false, 설치 전환/main 머지/모델·API·Bot·Orca 실호출/추가 과금 없음.

## Links
- [사람용 요약](preview/20260929-093524-v25-subset-host-rollback.html)
- 상세 로컬 보고: `E:/Coding Infra/Releases/SimonK-stack/20260929-v25-overlay-catalog/report-subset.html`
