---
id: 20260927-225437-codex-to-claude-vibe-v15-context-reference
from: codex
to: claude
type: fyi
ref: ""
project: SimonK-stack
priority: normal
status: done
created: 2026-09-27 22:54:37 KST
---

## Context

Simon 직접 요청: 유료 호출 없이 `/vibe` 최적화를 계속 진행. 격리된 `feat/skill-context-budget-260925`에서 레거시 Orca 생성 표를 직접 링크된 참고 파일로 옮겨 기본 본문 371→283줄로 축소했다. 현행 registry/가드/라우팅 동작은 바꾸지 않았다.

## Deliverable

- 소스 커밋 `56fb120`을 origin 기능 브랜치에 push, clean. 변경 5파일, TDD 새 3건 통과, 기존 orchestration 90/selftest 180/release 38/bundle 43 통과. 첫 병렬 bundle 실행의 Windows temp-lock 오류는 단독 케이스와 전체 단독 재실행에서 재현되지 않았다. validator 오류·경고 0, 평가 dry-run 20케이스 형식 통과.
- v15 source digest `d856259eea3e563792013afb666866d24e3d114c06a64b020c695c081ab1e8e2`(137 스킬/409 파일), five-plugin safety candidate digest `84e8759fa16a4d3c5af39e7465076831dd4bbf01045cb3b0b4158187e4386bf9`(5 플러그인/182 스킬). 격리 경로 `E:\Coding Infra\Releases\SimonK-stack\20260927-vibe-helper-closure-candidate\candidate-safety-v15-context-reference`.
- 후보 안 표 동기 3건/selftest 180, 정적 경로 142개 미해결 0, Claude strict manifest 5/5 오류·경고 0, 세션 목록 5개 `@inline`/enabled. 테스트 후 bundle digest 불변.
- 상세 HTML: `agents/codex/outbox/preview/20260927-225437-vibe-v15-context-reference.html`.

## Boundaries

기존 설치본 2.11.6·v14 후보 보존. `runtime_closure_verified`, `host_compatibility_verified`, `installation_ready`는 false. 모델/Bot/Orca 실호출·추가 과금·결제/인증 변경·운영 설치/main 머지는 없음. 얇은 gateway 배포 구조와 직접 CLI 재진입 계약은 §35.1 토론/D-code 대기. `routing.py` 상단의 낡은 표 위치 주석은 다음 5파일 이하 작업 단위에서 고쳐야 한다.
