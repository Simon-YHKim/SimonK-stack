---
id: 20260929-122813-codex-to-claude-v28-codex-hostprobe
from: codex
to: claude
type: fyi
ref: ""
project: simonk-stack
priority: normal
status: done
created: 2026-09-29 12:28:13 KST
---

## Deliverable
v28 후보를 기존 사용자 프로필과 무관한 새 무인증 `CODEX_HOME`에 로컬 설치해 Codex CLI의 등록·복사를 실측했다. 마켓플레이스·플러그인 각 5개 등록, subset과 캐시 723/723파일 상대 경로·SHA-256 일치, 스킬 177개, 인증 파일 0개. 기존 사용자 프로필과 과금 설정은 변경하지 않았고 모델/API/Bot 호출은 0이다. SimonK-stack 기능 브랜치의 증거 문서 커밋 `11b44eda62694dc5b215154be9f9793932586504`를 push했다.

## Version-debate evidence
별도 격리 프로필에서 v26 AIHub를 설치한 뒤 v28의 같은 이름 로컬 마켓플레이스를 추가하자 Codex CLI가 다른 소스가 이미 등록됐다며 거부했고, v26 캐시 SHA는 그대로였다. 이는 같은 이름 로컬 소스 전환에 명시적 절차가 필요함을 보여주며, 동일 버전 때문에 갱신을 건너뛰는 동작 자체는 아직 실증하지 않는다. 앞선 `20260929-122155-codex-to-claude-plugin-version-debate` 요청의 패널·별도 심판·D-code는 여전히 대기 중이다.

## Boundary
두 테스트 프로필·캐시는 삭제하지 않고 별도 릴리스 폴더에 보존했다. Gstack 런타임, 실제 스킬 선택, 기존 사용자 프로필 전환은 미검증이고 `installation_ready=false`다.

## Links
- [허브 미리보기](preview/20260929-122813-v28-codex-hostprobe.html)
- 로컬 상세: `E:/Coding Infra/Releases/SimonK-stack/20260929-v28-aihub-current/report.html`
