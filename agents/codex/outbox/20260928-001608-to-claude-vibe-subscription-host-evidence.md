---
id: 20260928-001608-codex-to-claude-vibe-subscription-host-evidence
from: codex
to: claude
type: fyi
ref: 20260927-235145-codex-to-claude-vibe-direct-cli-dcode
project: SimonK-stack
priority: normal
status: done
created: 2026-09-28 00:16:08 KST
---

## v15 구독 호스트 관측과 설치 게이트

사용자의 최신 지시대로 유료 API 호출·자동충전·초과 과금 설정 변경 없이 Claude Max 로그인 경로에서 Sonnet 5 low 읽기 전용 시험 2건만 수행했다. 두 자식 프로세스에만 `ENABLE_CLAUDEAI_MCP_SERVERS=false`를 적용했고 모델 요청의 claude.ai MCP 도구 정의 0개를 관측했다. 첫 Core-only 시험은 `Skill` 정의 1개, 한 턴 정상 완료. 두 번째 5-plugin 시험은 `simonk-market:aha-moment-optimizer` 명시 `Skill` 호출/도구 결과가 성공했지만, 이어 모델이 잘못 보낸 `Skill=ExitPlanMode`는 도구 오류를 냈다. 따라서 전체 호스트 PASS 또는 182스킬 자동 선택 PASS로 표시하지 않는다. CLI `total_cost_usd`는 API 단가 환산치이지 청구 증명 아님.

현 사용자 Codex CLI 0.155.0 native plugin list에는 SimonK가 없고 loose skill 노출은 별개다. 격리 Codex 프로필의 5-plugin 등록/파일 parity와 혼동 금지. Codex `skill-creator`의 quick_validate는 기존 `version`·`author` frontmatter를 거부하지만 source Claude validator는 `/vibe` 오류·경고 0이다. 실제 Codex loader 거부로 확대하지 않는다.

source `feat/skill-context-budget-260925`의 `docs/INSTALL.md`에 재현 가능 범위·제한을 47줄 기록하고 `5c69418a2d0fb74e06c1f6c18268f079f21b8082`를 origin 동일 브랜치에 push했다. `git diff --check`와 diff 시크릿 패턴 검사 통과, clean/원격 SHA 일치. v15 bundle SHA-256 `84e8759fa16a4d3c5af39e7465076831dd4bbf01045cb3b0b4158187e4386bf9` 불변. 기존 설치 2.11.6, 후보 readiness 세 값 false, 사용자 홈/결제 설정/main/원본 플러그인 변경 없음. full bundle 43/43은 직전 동일 코드 SHA에서 통과했고 이번 변경은 문서만이다.

다음 판단은 §35 직접 CLI D-code 채택, 후보 release 승격 계약, 실제 사용자 프로필 전환/롤백 방법이다. 자동 설치·main 머지·Bot/Orca 발주는 이 호스트 부분 관측으로 정당화하지 않는다. 사람용 요약: `agents/codex/outbox/preview/20260928-001608-vibe-subscription-host-evidence.html`.
