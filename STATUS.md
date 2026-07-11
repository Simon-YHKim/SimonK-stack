---
owner: claude (orchestrator)
updated: 2026-07-11
state: running
---

# STATUS.md — 허브 상태 보드 (오케스트레이터)

> 런-스테이트 **정본은 `CONTROL.md`**(`state:` 세마포어). 이 파일은 요약 뷰 — 불일치 시 CONTROL 우선(RUNBOOK §1).
> 상세 per-AI 상태 = `agents/<ai>/STATUS.md`, 측정 골든셋 = `loop-baseline.md`.

- **CONTROL state**: running (2026-07-04 수리 윈도우 종료 후 재개 — CONTROL.md 참조)
- **머신**: 이 허브의 라이브 머신 = **E: (DESKTOP-Q02Q4FG, 202502)**. 07-03 SOHA/C: PC 백업에서 이관 완료. **SOHA PC에서 레인 재가동 금지**(split-brain — CONTROL 브로드캐스트 참조).
- **마지막 오케스트레이터 작업**: 2026-07-11 — 허브 8차원 감사(16-agent WF, 적대검증) → 28확정 발견 + 2026 best-in-class 로드맵(`Output/hub-audit-roadmap-20260711.html`) + WAVE 1 착수: `hub-insight.ps1`(가치/신규성 탐지 — Codex degenerate loop 계량)·`hub-events.ps1`(OTel-GenAI 사이클 트레이스, TIMEOUT/p95)·gitignore 하드닝·거버넌스 드리프트 수정(BACKLOG/DECISIONS/STATUS). agy UAC 픽스(auto-update off). WAVE 2(commit-path dedup 게이트 등) 진행 중.
> ⓘ 이 서술은 요약이며 매 오케스트레이터 사이클마다 갱신되지 않을 수 있음 — 실시간 정본 = `CONTROL.state` + `git log` + `DECISIONS` 변경로그 (감사 G4).
- **이전 오케스트레이터 작업**: 2026-07-04 — 백업 복원 정합 수리 사이클(7-agent 감사 → 46건 발견 → 수리). 좀비 오더 1,832건 격리(`_restore-quarantine-20260704/`), origin 분기(17↓/3↑) 머지·푸시(`ac22ae9e`), HubBackup 재등록(매시간, ff-가드 신설), 데몬 하드닝 배치(로그 뮤텍스·타임아웃 자식킬·AG 폴백 배선·커밋가드 강화·워치독 fail-closed+푸시감시+grok큐), PS5.1 mojibake 소스 ASCII화, AG 날조 QA 3건 무효(BOARD 참조), C:→E: 경로 전면 현행화.
- **좌석 상태**: Codex 데몬 정상(gpt-5.5) · AG 데몬 정상(agy-headless, gemini-3.1-pro-preview — 단 헤드리스 사이클은 에뮬 QA 불가, RULES QA-truthfulness 규칙 신설) · Grok 요청전용 대기(watchdog가 대기오더 감지) · Claude 인터랙티브 오케스트레이터.

> 작게 유지 — 무한 append 금지(64KB 캡). 상세 이력은 BOARD.md/INCIDENTS.md.
