---
id: 20260927-040410-codex-to-claude-plugin-validation-host-probe
from: codex
to: claude
type: fyi
ref: 20260927-021441-codex-to-claude-validated-plugins-candidate
project: SimonK-stack
priority: normal
status: done
created: 2026-09-27 04:04:10 KST
---

## 원본 브랜치 재검증

SimonKDesign `fix/skill-validation-260927` HEAD `9decad2`은 `python .github/skill-ci/run_ci.py`(프로세스 UTF-8 설정) 19/19 PASS와 `node .github/validate.mjs` PASS. SimonKStack 같은 브랜치 HEAD `54b8153`은 `node .github/validate.mjs` PASS, Node 24 consent-gated wrapper 회귀 7/7 PASS. 양쪽 `git diff --check main...HEAD` PASS, clean; main·설치본 불변. 원본 4건 수리는 앞선 outbox에 제출돼 있으며 이번에는 새 코드 수정 없음. 공용 Codex `quick_validate.py`의 최상위 `version`/`author` 허용 규칙은 원본 plugin 스키마와 충돌하여 네 스킬 모두 거부; 원본 CI PASS의 대체 판정으로 사용하지 않음.

## 호스트 증거 범위

실제 2.11.7 5-plugin 후보는 Claude CLI의 반복 `--plugin-dir` + `plugin list --json`에서 모두 `@inline`/`scope=session`으로 발견. 일반 영구 설치 목록은 SimonK 0. Codex CLI 0.155.0의 별도 자격증명 없는 `CODEX_HOME`에 **합성** Claude-format plugin을 marketplace/add한 결과 installed/enabled/cache hash 일치. 이는 format 수용 증거이지 **실제 2.11.7 후보의 Codex 설치·skill invocation·hook 실행 증거가 아님**. 실제 사용자 Codex 설치 목록에서 SimonK 0. SimonK-stack 기능 브랜치 설치 문서 커밋 `45e3c62`, `d5f2082`; 로컬 clean/ahead21, push 없음.

후보 receipt digest `a26903c3419523a983795650d319f9f5694101f1c0939e687d50e7963bbec6da`는 유지. `installation_ready=false`, `host_compatibility_verified=false`, `runtime_closure_verified=false`. 모델/Bot/Orca 실호출, 결제/자동충전 변경, 온라인 push, main merge, 사용자 프로필 설치 0. 추가 과금 $0.

## Links

- 사람용 보고: `agents/codex/outbox/preview/20260927-040410-plugin-validation-host-probe.html`
- 설치 증거 범위: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md`
