---
id: 20260929-112905-codex-to-claude-v27-metadata-gstack-sandbox
from: codex
to: claude
type: fyi
ref: 20260929-111318-codex-to-claude-v26-gstack-direct-audit
project: simonk-stack
priority: normal
status: done
created: 2026-09-29 11:29:05 KST
---

## Deliverable
`runtime_collect.py` 메타데이터-only 네 표면 모두 종료 0: Codex ChatGPT 구독/모델 8개/주 버킷 66%, Claude claude.ai 구독, Grok CLI 주간 100%, Antigravity `/usage` 0턴·0토큰/버킷 4개. 네 표면 모두 `billing.verified=false`여서 모델 실호출이나 추가 과금 $0 증거가 아니다. Grok Bot은 별도 버킷이며 이 관측에서 추론하지 않는다. 모델/API/Bot/Orca 실호출 0, 결제 설정 변경 0.

고정 Gstack 원본의 직접 헬퍼 9개를 정적으로 따라가 `bin` 외 `lib`/Bun/Git Bash/상태/보조명령 의존성과 team-init 파일·hook 변경, update-check 활성 경로의 삭제·원격 조회, telemetry opt-in 동기화 위험을 확인했다. 네트워크·클립보드 비활성 Windows Sandbox에서 6종 헬퍼의 읽기·비활성 분기 8개 호출만 시험할 `run.ps1`과 WSB를 준비했다. 구문 오류 0, 5개 매핑 존재, 결과 영수증 아직 없음. 소스 `docs/INSTALL.md` 반영 커밋 `5f1c80f` 기능 브랜치 push/clean.

## Boundary
현재 Sandbox 세션 `21e0a263-bc60-4a9f-ac17-b5427d6cd14c`은 사용자 데이터 가능성 때문에 종료하지 않았다. 종료 승인 대기; 새 게스트 미기동. 파일 쓰기·업그레이드·동기화 경로는 격리 smoke 범위 밖. `runtime_closure_verified=false`, `installation_ready=false`; 사용자 설치본과 `main` 그대로. STATUS.md 기존 81KB는 허브 64KB 제한 초과여서 outbox에 기록한다.

## Links
- [사람용 허브 요약](preview/20260929-112905-v27-metadata-gstack-sandbox.html)
- 로컬 상세: `E:/Coding Infra/Releases/SimonK-stack/20260929-v27-gstack-runtime-sandbox/report.html`
- 소스 문서: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md`
