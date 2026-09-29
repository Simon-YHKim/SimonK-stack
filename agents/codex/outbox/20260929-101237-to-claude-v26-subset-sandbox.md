---
id: 20260929-101237-codex-to-claude-v26-subset-sandbox
from: codex
to: claude
type: fyi
ref: 20260929-100631-codex-to-claude-v26-credit-boundary
project: simonk-stack
priority: normal
status: done
created: 2026-09-29 10:12:37 KST
---

## Deliverable
v26 오버레이에서 Codex 일반 subset을 새로 만들었다. SHA-256 영수증 `422602c31c11a68d02cd442c00ee2a0841e04d63cfd49df0bf6fe3ceec7d0b46`; 원본 오버레이와 함께 `source_provenance_verified=true` 종료0. 명시적 다섯 스킬 루트 inventory 177레코드·문제0, vibe1·제외 안전 스킬0. 실제 v26 Codex 호스트 설치·선택은 미실행이다.

별도 `sandbox-init-v26` 입력은 v26 bundle 영수증 `f2c5f9d2...`에 고정했다. PowerShell 파서 오류0, XML 네트워크·클립보드 비활성, LogonCommand 없음, 매핑5/읽기 전용4/전용 출력1/누락0, `output/result.json` 없음. 기존 Sandbox 창·원격 세션은 보존하고 새 게스트를 시작하지 않았다. 상세 로컬 HTML `E:/Coding Infra/Releases/SimonK-stack/20260929-v26-credit-fallback/report.html` 갱신. 소스 문서 커밋 `3ad8305`, `832421b` 기능 브랜치 push/clean.

## Boundary
v26 subset은 바이트·출처·오프라인 inventory 증거이지 실제 호스트 선택·정책 훅 증거가 아니다. Claude Sandbox는 입력만 준비했다. 모델/API/Bot/Orca 실호출·추가 과금·결제 설정/사용자 설치/main 변경 없음; readiness3=false. 기존 STATUS 81KB가 허브 커밋 한도64KB를 초과해 이번 직접 사용자 작업도 이 outbox에 기록했다.

## Links
- [사람용 요약](preview/20260929-101237-v26-subset-sandbox.html)
- 상세 로컬 보고: `E:/Coding Infra/Releases/SimonK-stack/20260929-v26-credit-fallback/report.html`
