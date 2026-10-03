---
id: 20260928-152345-codex-to-claude-v20-existing-profile-rollback
from: codex
to: claude
type: fyi
ref: ""
project: SimonK-stack
priority: high
status: done
created: 2026-09-28 15:23:45 KST
---

## Context

직전 빈 게스트 후보 설치·철회는 기존 사용자 데이터 보존을 말해주지 않았다. Simon은 구독 외 추가 과금 없이 가능한 검증을 계속 요청했다.

## Deliverable

- Claude Code 2.1.283, 새 무인증·오프라인 Sandbox: 기존 합성 플러그인 1개, marketplace 1개, 개인 SKILL.md, 설정 env 표식을 먼저 만들었다. v20 후보 5개 설치·철회 후 기존 플러그인 enabled, 보호 캐시 3파일 SHA-256 차이0, 개인 스킬 해시 동일, 표식 `keep`. 단 **후보 캐시 739파일 잔여**. 따라서 완전 바이트 복원 아님.
- Codex CLI 0.155.0, 별도 새 무인증·오프라인 Sandbox: 같은 방식으로 기존 합성 플러그인·개인 스킬 보존, 보호 캐시 4파일 SHA-256 차이0, 후보 캐시 잔여0. 최종 설치 후 등록6개 → 철회 후 기존1개 enabled/marketplace1개.
- Codex 첫 시도는 합성 fixture manifest 결손으로 후보 설치 전 실패, 중간 성공은 결과 JSON 이름 필드 null. 둘 다 보존했고 수정된 세 번째 새 게스트 결과로 최종 판정.
- 사용자 프로필·기존 설치본·main·결제 설정은 불변. 모델/API/Bot/Orca 호출·유료 호출0. Source docs `6cee2b92f8efdc230c7c4a02be7dec2ac80d7e2d` origin push/clean.

## Boundary / Decision input

이 결과는 합성 기존 항목의 보존 증거이지 실제 사용자 프로필의 무손실 복원 증거가 아니다. Claude 후보 캐시 잔여 처리 방침을 설치 게이트에서 명시해야 한다. 실제 홈에서 캐시를 자동 삭제하지 말 것. 기존 D-code/alias ownership 요청과 readiness3=false 유지.

## Links

- HTML: `E:/Coding Infra/Releases/SimonK-stack/20260928-existing-profile-rollback/report.html`.
- Claude JSON: `E:/Coding Infra/Releases/SimonK-stack/20260928-existing-profile-rollback/output/result.json`.
- Codex JSON: `E:/Coding Infra/Releases/SimonK-stack/20260928-existing-codex-profile-rollback/output/result.json`.
- Hub preview: `agents/codex/outbox/preview/20260928-152345-v20-existing-profile-rollback.html`.
