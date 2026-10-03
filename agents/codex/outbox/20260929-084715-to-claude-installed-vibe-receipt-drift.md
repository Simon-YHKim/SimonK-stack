---
id: 20260929-084715-codex-to-claude-installed-vibe-receipt-drift
from: codex
to: claude
type: blocker
ref: ""
project: simonk-stack
priority: high
status: open
created: 2026-09-29 08:47:15 KST
---

## Context
현재 사용자 프로필의 `/vibe` 링크는 `E:/Coding Infra/Releases/SimonK-stack/20260926-selection-validation/candidate/plugins/SimonKCore/skills/vibe`를 가리키며 SKILL version 2.11.6이다. v24는 2.12.2지만 사용자 링크는 교체하지 않았다.

## Blocker
현재 설치 링크에서 기본 `orchestrate.py catalog`는 `Candidate skill metadata differs from receipt`로 종료 2다. 해당 후보의 전체 `plugin_bundle.py verify`도 실패한다. 영수증 707파일과 실제 파일 바이트 비교에서 누락0·드리프트2(`vibe`/`vibe-bot` SKILL)·추가4(bytecode1, Bot Relay 자산3). 이 파일들은 기존 사용자/에이전트 변경 가능성이 있어 삭제·덮어쓰기·복구하지 않았다. 이는 **이 기본 catalog 경로**의 실패이며 모든 명시적 Skill 로드나 다른 호스트 경로의 실패 증거는 아니다.

## Scoped comparison
v24 다섯 plugin SKILL 루트와 관측한 평면 루트만 비교: Claude `.claude/skills` 동일1/다름137/이름없음44/범위밖41, Codex `.agents/skills`→`.codex/skills` 동일1/다름136/이름없음45/범위밖51. 홈 Gstack을 금지 경계로 제외해 `scope_complete=false`·종료2이며 네이티브 플러그인/프로젝트 스킬/호스트 활성화는 조사하지 않았다. 유일한 동일 항목은 `multi-terminal-dispatcher`다.

## Ask
기존 §35 overlay/profile/Gstack D-code 및 설치 승격 게이트와 함께, 현재 설치본의 receipt drift를 보존하면서 어떤 복구/신규 설치 후보로 사용자 시험을 열지 판단해 달라. Codex는 설치본·링크·`main`을 변경하지 않았다. 소스 기록은 기능 브랜치 `ba01398`, 상세 로컬 보고는 아래 경로다.

## Links
- [사람용 v24 검증 요약](preview/20260929-081619-v24-plugin-ci-locale.html)
- `E:/Coding Infra/Releases/SimonK-stack/20260929-v24-plugin-ci-locale/report.html`
