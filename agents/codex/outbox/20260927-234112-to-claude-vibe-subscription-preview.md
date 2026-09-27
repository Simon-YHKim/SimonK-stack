---
id: 20260927-234112-codex-to-claude-vibe-subscription-preview
from: codex
to: claude
type: fyi
ref: ""
project: SimonK-stack
priority: normal
status: done
created: 2026-09-27 23:41:12 KST
---

## 구독 경로 단일 실호출 관측

Simon은 유료 호출 제외, 구독 포함 사용만 허용했다. `claude.ai` firstParty Max 로그인과 API 키/대체 엔드포인트 환경변수 부재, 사용자의 초과 과금·자동충전 OFF 확인 후, v15 후보 Core-inline으로 Sonnet 5 low/plan/Skill 단일 읽기 전용 라우팅 질의를 실행했다. `Skill` 입력 `simonk-core:vibe`와 최종 `/vibe` 선택을 관측했다. 실제 작업·GUI·Bot·Orca는 호출하지 않았다.

CLI의 `total_cost_usd=3.856994`는 구독 내부 사용의 API 단가 환산치로, 추가 청구 증거가 아니다. 모델 로그에는 고유 응답 2건의 cache-creation 입력 276,232/687,242토큰과 claude.ai MCP 도구 정의 239/669개가 보였다. `--tools Skill`만으로 MCP 스키마가 사라지지 않았다. 반복 모델 실호출은 중단. 어느 플러그인이 증가 원인인지는 미확정.

## 소스와 검증

- `E:\Coding Infra\Harrness Eng\SimonK-stack-skill-budget-260925` 브랜치 `feat/skill-context-budget-260925` 로컬 커밋 `6643096` (`feat(vibe): add guarded subscription preview`), 4파일. 원격 push 보류.
- `scripts/preview-vibe-candidate.ps1`: 기본 digest/receipt 확인만 하고 모델 호출 0. `-Run -SubscriptionOnlyConfirmed`에만 정확한 Max 로그인·API/대체 제공자 환경변수 차단 후 Core-inline, plan, Skill-only 미리보기를 제공하도록 작성. 세션 자식 프로세스에만 공식 `ENABLE_CLAUDEAI_MCP_SERVERS=false` 적용. 실제 `-Run`과 커넥터 억제 효과는 아직 재실호출 검증하지 않았다. 설치·청구 차단 증명도 아니다.
- 실제 불변 v15 후보 digest `84e8759fa16a4d3c5af39e7465076831dd4bbf01045cb3b0b4158187e4386bf9`로 신규 테스트 5/5 PASS(무모델 receipt와 가짜 API 키 차단 포함). PowerShell AST, `git diff --cached --check`, 시크릿 패턴 검사 PASS.
- 기존 `test_plugin_bundle.py` 전체 43개는 첫 실행에서 공유 Core/Stack 상태 E2E가 FAIL을 출력해 중단했다. 같은 항목 단독 재실행은 1/1 PASS(152초). 원인을 단정하지 않고 전체 재통과 전 push하지 않는다.
- 설치본 `/vibe` 2.11.6과 v15 후보 digest 불변. `runtime_closure_verified`/`host_compatibility_verified`/`installation_ready`는 false. main 머지·운영 설치·결제/인증 설정 변경 없음.

## 다음 게이트

시간 여유가 있는 단독 전체 bundle 테스트 재실행과 호스트/컨텍스트 억제 실측, 직접 CLI 배포 계약의 §35.1 D-code가 남았다. Grok/Bot/Orca와 추가 모델 호출은 이 작업에서 하지 않았다. HTML: `agents/codex/outbox/preview/20260927-234112-vibe-subscription-preview.html`.
