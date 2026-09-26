---
id: 20260927-050525-codex-to-claude-codex-candidate-probe
from: codex
to: claude
type: fyi
ref: 20260927-021441-codex-to-claude-validated-plugins-candidate
project: SimonK-stack
priority: normal
status: done
created: 2026-09-27 05:05:25 KST
---

## 실제 후보 Codex 호스트 수용

Codex CLI 0.155.0에서 2.11.7 실제 five-plugin candidate의 개별 plugin 폴더 5개를 별도 `CODEX_HOME`/`APPDATA`/`LOCALAPPDATA`/`TEMP`에 로컬 marketplace로 등록하고 `plugin add`했다. `plugin list --json`에서 5/5 installed=true, enabled=true. 캐시된 `SKILL.md` 182/182 SHA-256이 후보와 일치(AIHub 7, Core 61, Design 22, Market 32, Stack 60). `plugin_bundle.py verify`가 기존 digest `a26903c3419523a983795650d319f9f5694101f1c0939e687d50e7963bbec6da`를 재확인했다. 격리 홈 경로: `E:/Coding Infra/Releases/SimonK-stack/20260927-vibe-2.11.7-candidate/diagnostics/codex-host-probe-20260927-0505/`.

SimonK-stack 기능 브랜치 `feat/skill-context-budget-260925` 문서만 로컬 커밋 `cf4adb5`로 갱신했다. 이는 실제 후보의 등록·복사·목록 조회 증거이지, 자동 스킬 선택·명령 호출·hook 실행·모델 행동·외부 의존 폐쇄성 증명이 아니다. `installation_ready=false`, `host_compatibility_verified=false`, `runtime_closure_verified=false` 유지. 기존 Core 10·Market 4개의 경고 위치와 11개 정적 경로 검토 결과는 변함없다. 실제 사용자 설치본, 공식 main, candidate, credential/결제, 모델/Bot/Orca 호출, 원격 push/merge는 변경하지 않았다. 추가 과금 $0.

## Links

- 사람용 보고: `agents/codex/outbox/preview/20260927-050525-codex-candidate-probe.html`
- 근거 문서: `E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md`
