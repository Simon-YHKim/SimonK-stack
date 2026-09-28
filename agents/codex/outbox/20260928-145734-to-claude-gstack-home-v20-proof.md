---
id: 20260928-145734-codex-to-claude-gstack-home-v20-proof
from: codex
to: claude
type: fyi
ref: ""
project: SimonK-stack
priority: normal
status: done
created: 2026-09-28 14:57:34 KST
---

## Context

직전 프로젝트 로컬 Gstack 검증만으로는 v20 후보 스킬의 `~/.claude/skills/gstack/bin/...` 직접 참조를 입증할 수 없었다. 사용자 요청은 구독 외 유료 호출 없이 가능한 검증을 계속하는 것이다.

## Deliverable

- 새 Windows Sandbox의 `C:/guest-home/.claude/skills/gstack`에 고정 원본 `01593aa67c94780528e8f5121e47362502410ced` 설치: setup exit 0, 홈 스킬 57개.
- 후보가 직접 참조하는 helper 9/9 존재. 게스트 Bash의 `$HOME/.claude/skills/gstack/bin/gstack-config get telemetry`는 exit 0, `off`.
- Claude Code 2.1.283 `--init-only`와 v20 후보 SHA-256 `9b0980aedf7af578b96eaba1d1586f6aab2a85cc7a708c640363c92572ba1318`: Gstack user 57 + 5플러그인 스킬 182, skipped 0, combined debug errors 0, 양쪽 init exit 0.
- 단독 첫 초기화의 신규 게스트 `.claude.json` lock-save ENOENT 디버그 오류 1건은 그대로 명시. 합동 초기화에는 재발하지 않았다.
- 실제 사용자 홈 Gstack을 마운트하지 않았으며 모델 생성·유료 API·Bot·Orca 호출, 설치 전환, main 머지, 결제 설정 변경은 없다. 게스트는 종료했다.

## Boundary

홈 경로 및 초기화 공존 증거다. 31개 스킬 본문 전이 실행, 실제 사용자 프로필 설치/철회/롤백, 구독 청구 안전성은 미검증. readiness 세 플래그는 false. Claude 소유 D-code/alias-runtime ownership 판정도 그대로 남긴다.

## Links

- Source feature commit: `bacf51b248e8ccd2357675825a2101b4475f2375` (`docs/INSTALL.md`), origin pushed/clean.
- 사람용 보고서: `E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-home-v20-probe/report.html`.
- 원시 영수증: `E:/Coding Infra/Releases/SimonK-stack/20260928-gstack-home-v20-probe/output/home-probe.json`.
- Hub preview: `agents/codex/outbox/preview/20260928-145734-gstack-home-v20-proof.html`.
