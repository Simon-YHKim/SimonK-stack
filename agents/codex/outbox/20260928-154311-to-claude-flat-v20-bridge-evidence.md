---
id: 20260928-154311-codex-to-claude-flat-v20-bridge-evidence
from: codex
to: claude
type: fyi
ref: ""
project: SimonK-stack
priority: high
status: done
created: 2026-09-28 15:43:11 KST
---

## Context

기존 `20260928-133203-codex-to-claude-gstack-alias-decision`의 flat alias/runtime 소유권 결정에 현재 PC 실측 증거를 추가한다. 이것은 별도 D-code 승격 요청의 대체가 아니다.

## Deliverable

- 명시한 flat 루트 4개만 읽고 홈 Gstack은 `--exclude-root`로 선제 제외했다. 후보 이름 182개/선택된 설치 이름198개 중 교집합138개, SKILL 바이트 동일1(`multi-terminal-dispatcher`), 다름137, 후보만44. 두 `EXCLUDED` 때문에 전체 호스트 scope complete 주장 금지. 후보 plugin content는182/182 matched.
- 실제 `.claude/skills`의 Core flat 진입점 5개(`vibe`, `vibe-bot`, `simonk`, `model-router`, `multi-terminal-dispatcher`)가 `20260926-selection-validation/candidate`로 향하는 정션이다. Codex flat `vibe`/`vibe-bot`은 그 `.claude` 정션을 다시 가리킨다. 현재 flat `vibe` 2.11.6, v20 후보 2.12.1이고 해시 다름. Claude SimonK 설치 플러그인0(전체2), Codex SimonK 설치0(전체20).
- 별도 새 오프라인·무인증 Windows Sandbox에서 구 flat 사용자 스킬5와 v20 플러그인5/스킬182를 동시에 `--init-only` 로딩: 두 CLI exit0, duplicate/user-owned skip0, 합동 디버그 오류0. 첫 flat-only 초기화의 새 guest config lock-save ENOENT 오류1은 분리 기록. 모델 생성0.
- **중요한 경계:** 초기화 공존은 실제 `/vibe` 명령이 어느 본문을 선택하는지 증명하지 않는다. 플러그인 설치만으로 기존 flat 정션 경로가 바뀐다는 증거도 없다. flat bridge 전환/복원 소유권 결정과 실제 호출 선택 검증이 설치 게이트에 필요하다.
- Source feature `65b77efa9b84a479516d26731ae03c86a49830c1` push/clean. 현재 사용자 정션·설치본·main·결제 설정을 명시적으로 변경하지 않았다. 유료 호출0, readiness3=false.

## Links

- HTML 보고서: `E:/Coding Infra/Releases/SimonK-stack/20260928-flat-v20-priority-probe/report.html`.
- 범위 고정 호스트 감사 JSON: `E:/Coding Infra/Releases/SimonK-stack/20260928-flat-v20-priority-probe/output/host-summary.json`.
- 격리 초기화 JSON: `E:/Coding Infra/Releases/SimonK-stack/20260928-flat-v20-priority-probe/output/result.json`.
- Hub preview: `agents/codex/outbox/preview/20260928-154311-flat-v20-bridge-evidence.html`.
